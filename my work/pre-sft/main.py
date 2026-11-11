"""Load the three neighboring HMI synoptic maps used before SFT."""

from pathlib import Path

from astropy.io import fits


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


MAP_PATHS = {
    "CR2190 (Previous)": PREVIOUS_PATH,
    "CR2191 (Current)": CURRENT_PATH,
    "CR2192 (Next)": NEXT_PATH,
}


def calculate_delta_t(phi, theta):
    """Calculate the time offset for a longitude, in days.

    Parameters
    ----------
    phi : float
        Input longitude in degrees.
    theta : float
        Input latitude in degrees. Accepted for the later latitude-dependent
        calculation; it does not affect delta t yet.
    """
    del theta
    return (REFERENCE_LONGITUDE - phi) / OMEGA_0


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
    phi = float(input("Enter phi (longitude in degrees): "))
    theta = float(input("Enter theta (latitude in degrees): "))
    delta_t = calculate_delta_t(phi, theta)
    print(f"delta t: {delta_t} days")
