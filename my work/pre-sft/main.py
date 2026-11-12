"""Load the three neighboring HMI synoptic maps used before SFT."""

from pathlib import Path
from math import cos, radians

from astropy.io import fits
import numpy as np


DATA_DIR = Path(__file__).resolve().parent.parent / "fits_files" / "720x360"

PREVIOUS_PATH = DATA_DIR / "hmi.Synoptic_Mr_small.2190.fits"
CURRENT_PATH = DATA_DIR / "hmi.Synoptic_Mr_small.2191.fits"
NEXT_PATH = DATA_DIR / "hmi.Synoptic_Mr_small.2192.fits"


# Load the primary image data into arrays for the next pre-SFT step.
B_prev = fits.getdata(PREVIOUS_PATH)
B_curr = fits.getdata(CURRENT_PATH)
B_next = fits.getdata(NEXT_PATH)


# Use the current map's WCS reference longitude as the working "now"
# longitude.  CRVAL1 is stored as an absolute Carrington longitude, so
# normalize it to one 0--360 degree Carrington-longitude cycle.
CURRENT_HEADER = fits.getheader(CURRENT_PATH)
REFERENCE_LONGITUDE = float(CURRENT_HEADER["CRVAL1"]) % 360.0
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



def current_map_value(phi, theta):
    """Return b(phi, theta) from CR2191 before any remapping.

    The FITS map stores latitude, while the calculation uses colatitude, so
    theta is converted with latitude = 90 - theta.  The nearest grid cell is
    returned because the map is discrete.
    """
    target_latitude = 90.0 - theta
    longitude_distance = np.abs((LONGITUDES - phi + 180.0) % 360.0 - 180.0)
    longitude_index = np.argmin(longitude_distance)
    latitude_index = np.argmin(np.abs(LATITUDES - target_latitude))

    return B_curr[latitude_index, longitude_index]


def nearest_longitude_index(phi):
    """Return the index of the closest supported longitude grid cell."""
    distance = np.abs((LONGITUDES - phi + 180.0) % 360.0 - 180.0)
    return int(np.argmin(distance))


def reconstruct_b_new():
    """Reconstruct the central map using nearest-neighbor backward sampling."""
    B_new = np.empty_like(B_curr)

    for latitude_index, theta in enumerate(COLATITUDES):
        for longitude_index, phi_dest in enumerate(LONGITUDES):
            phi_src = calculate_phi_src(phi_dest, theta)

            if phi_src < 0.0:
                source_map = B_next
                phi_src %= 360.0
            elif phi_src >= 360.0:
                source_map = B_prev
                phi_src %= 360.0
            else:
                source_map = B_curr

            source_longitude_index = nearest_longitude_index(phi_src)
            B_new[latitude_index, longitude_index] = source_map[
                latitude_index, source_longitude_index
            ]

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
    remapped_value = current_map_value(phi_src, theta)
    print(f"b(phi_dest, theta) before remapping: {current_value} G")
    print(f"delta t: {delta_t} days")
    print(f"omega(theta): {rotation_rate} degrees/day")
    print(f"phi_src: {phi_src} degrees")
    print(f"b(phi_src, theta): {remapped_value} G")
