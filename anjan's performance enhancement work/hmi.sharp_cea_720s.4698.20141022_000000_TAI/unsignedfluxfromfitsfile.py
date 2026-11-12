import numpy as np
from astropy.io import fits

# -------------------------------------------------
# Open SHARP radial field FITS file
# -------------------------------------------------

fname = "hmi.sharp_cea_720s.4698.20141022_000000_TAI.Br.fits"

hdul = fits.open(fname)

Br = hdul[1].data.astype(np.float64)
header = hdul[1].header

# -------------------------------------------------
# Remove NaNs
# -------------------------------------------------

Br[np.isnan(Br)] = 0.0

# -------------------------------------------------
# Solar radius in cm
# -------------------------------------------------

Rsun = 6.96e10  # cm

# -------------------------------------------------
# Pixel size in radians
# CEA SHARP pixel size usually 0.03 degree
# -------------------------------------------------

dx_deg = abs(header["CDELT1"])
dy_deg = abs(header["CDELT2"])

dx = np.deg2rad(dx_deg)
dy = np.deg2rad(dy_deg)

# -------------------------------------------------
# Pixel area on solar surface
# -------------------------------------------------

dA = (Rsun**2) * dx * dy

# -------------------------------------------------
# Unsigned magnetic flux
# -------------------------------------------------

unsigned_flux = np.sum(np.abs(Br)) * dA

print("Unsigned Flux = {:.3e} Mx".format(unsigned_flux))
