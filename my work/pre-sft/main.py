"""Load the three neighboring HMI synoptic maps used before SFT."""

from pathlib import Path
from math import cos, radians

from astropy.io import fits
import numpy as np
from scipy.interpolate import CubicSpline


DATA_DIR = Path(__file__).resolve().parent.parent / "fits_files" / "720x360"

PREVIOUS_PATH = DATA_DIR / "hmi.Synoptic_Mr_small.2190.fits"
CURRENT_PATH = DATA_DIR / "hmi.Synoptic_Mr_small.2191.fits"
NEXT_PATH = DATA_DIR / "hmi.Synoptic_Mr_small.2192.fits"


# Load the primary image data into arrays for the next pre-SFT step.
B_prev = fits.getdata(PREVIOUS_PATH)
B_curr = fits.getdata(CURRENT_PATH)
B_next = fits.getdata(NEXT_PATH)


CURRENT_HEADER = fits.getheader(CURRENT_PATH)
OMEGA_0 = 13.2  # degrees per day


def map_coordinates():
    """Return the current map's longitude, latitude, and colatitude grids."""
    longitude_pixels = np.arange(B_curr.shape[1]) + 1
    latitude_pixels = np.arange(B_curr.shape[0]) + 1

    longitudes = (
        CURRENT_HEADER["CRVAL1"]
        + (longitude_pixels - CURRENT_HEADER["CRPIX1"])
        * abs(CURRENT_HEADER["CDELT1"])
    ) % 360.0
    latitudes = np.degrees(
        np.arcsin(
            CURRENT_HEADER["CRVAL2"]
            + (latitude_pixels - CURRENT_HEADER["CRPIX2"])
            * CURRENT_HEADER["CDELT2"]
        )
    )
    return longitudes, latitudes, 90.0 - latitudes


LONGITUDES, LATITUDES, COLATITUDES = map_coordinates()


MAP_PATHS = {
    "CR2190 (Previous)": PREVIOUS_PATH,
    "CR2191 (Current)": CURRENT_PATH,
    "CR2192 (Next)": NEXT_PATH,
}


def calculate_delta_t(phi_dest, theta):
    """Calculate delta t = t_ref - t_obs in days.

    Parameters
    ----------
    phi_dest : float
        Destination longitude at t_ref in degrees.
    theta : float
        Colatitude in degrees.
    """
    return (phi_dest - 180.0) / (OMEGA_0 + omega(theta))


def omega(theta):
    """Return the differential rotation rate for colatitude theta.

    Parameters
    ----------
    theta : float
        Colatitude in degrees.

    Returns
    -------
    float
        Differential rotation rate in degrees per day.
    """
    cos_theta = cos(radians(theta))
    return 0.18 - 2.3 * cos_theta**2 - 1.62 * cos_theta**4


def calculate_phi_src(phi_dest, theta):
    """Return the source longitude at t_obs for a destination pixel at t_ref."""
    delta_t = calculate_delta_t(phi_dest, theta)
    return phi_dest - omega(theta) * delta_t



class LongitudeSpline:
    """Cubic interpolation within valid spans, preserving missing-data gaps."""

    def __init__(self, longitudes, values):
        finite = np.isfinite(values)
        edges = np.diff(np.r_[False, finite, False].astype(int))
        self.segments = [
            CubicSpline(longitudes[start:stop], values[start:stop], extrapolate=False)
            for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))
            if stop - start >= 4
        ]

    def __call__(self, longitude):
        longitude = np.asarray(longitude, dtype=float)
        result = np.full(longitude.shape, np.nan)
        for spline in self.segments:
            inside = (longitude >= spline.x[0]) & (longitude <= spline.x[-1])
            result[inside] = spline(longitude[inside])
        return result


def build_source_splines():
    """Build longitude splines across Next CR, Current CR, and Previous CR.

    Sorting also reorders the field columns, since the WCS longitude grid
    may wrap within the array. Neighboring rotations provide boundary data
    rather than assuming that a single observed map is periodic.
    """
    order = np.argsort(LONGITUDES)
    longitudes = LONGITUDES[order]
    extended_longitudes = np.concatenate(
        (longitudes - 360.0, longitudes, longitudes + 360.0)
    )
    extended_field = np.concatenate(
        (B_next[:, order], B_curr[:, order], B_prev[:, order]), axis=1
    )
    return [
        LongitudeSpline(extended_longitudes, row)
        for row in extended_field
    ]


SOURCE_SPLINES = build_source_splines()


def source_map_value(phi_src, theta):
    """Sample the source spline at unwrapped longitude and nearest colatitude.

    Negative longitudes sample Next CR; longitudes >= 360 sample Previous
    CR. Longitude is interpolated; latitude is unchanged by the remapping.
    """
    latitude_index = np.argmin(np.abs(COLATITUDES - theta))
    return float(SOURCE_SPLINES[latitude_index](phi_src))


def current_map_value(phi, theta):
    """Sample CR2191 with cubic longitude interpolation at nearest colatitude."""
    return source_map_value(phi % 360.0, theta)


def reconstruct_b_new():
    """Reconstruct the central map using cubic-spline backward sampling."""
    B_new = np.empty(B_curr.shape, dtype=float)

    for latitude_index, theta in enumerate(COLATITUDES):
        # Keep source longitudes unwrapped so the spline selects the correct CR.
        phi_src = calculate_phi_src(LONGITUDES, theta)
        B_new[latitude_index] = SOURCE_SPLINES[latitude_index](phi_src)

    return B_new


B_new = reconstruct_b_new()
B_old = B_curr
B = B_new


def print_field_statistics(name, field):
    """Print average, maximum, and minimum finite field values in gauss."""
    print(name)
    print(f"  b_avg: {np.nanmean(field)} G")
    print(f"  b_max: {np.nanmax(field)} G")
    print(f"  b_min: {np.nanmin(field)} G")


def grid_info(path):
    """Return the grid dimensions and spatial resolution from a FITS file."""
    with fits.open(path, memmap=False) as hdul:
        data = hdul[0].data
        header = hdul[0].header

    return {
        "longitudes": int(data.shape[1]),
        "latitudes": int(data.shape[0]),
        "longitude_resolution": abs(float(header["CDELT1"])),
        "longitude_unit": header.get("CUNIT1", ""),
        "latitude_resolution": abs(float(header["CDELT2"])),
        "latitude_unit": header.get("CUNIT2", ""),
    }


if __name__ == "__main__":
    print(f"B_new reconstructed with shape: {B_new.shape}")
    print_field_statistics("B_old (original CR2191)", B_old)
    print_field_statistics("B (reconstructed)", B)

    phi_dest = float(input("Enter phi_dest (destination longitude in degrees): "))
    theta = float(input("Enter theta (colatitude in degrees): "))
    current_value = current_map_value(phi_dest, theta)
    delta_t = calculate_delta_t(phi_dest, theta)
    rotation_rate = omega(theta)
    phi_src = calculate_phi_src(phi_dest, theta)
    remapped_value = source_map_value(phi_src, theta)
    print(f"b(phi_dest, theta) before remapping: {current_value} G")
    print(f"delta t: {delta_t} days")
    print(f"omega(theta): {rotation_rate} degrees/day")
    print(f"phi_src: {phi_src} degrees")
    print(f"b(phi_src, theta): {remapped_value} G")
