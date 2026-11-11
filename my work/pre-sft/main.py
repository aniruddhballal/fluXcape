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


MAP_PATHS = {
    "CR2190 (Previous)": PREVIOUS_PATH,
    "CR2191 (Current)": CURRENT_PATH,
    "CR2192 (Next)": NEXT_PATH,
}


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


def print_grid_info():
    """Print the grid size and spatial resolution for each synoptic map."""
    for label, path in MAP_PATHS.items():
        info = grid_info(path)
        print(label)
        print(f"  latitudes: {info['latitudes']}")
        print(f"  longitudes: {info['longitudes']}")
        print(
            "  spatial resolution: "
            f"{info['longitude_resolution']} {info['longitude_unit']} longitude, "
            f"{info['latitude_resolution']} {info['latitude_unit']} latitude"
        )


if __name__ == "__main__":
    print_grid_info()
