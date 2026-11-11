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
