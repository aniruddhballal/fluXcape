# In this file I am plotting fits data 

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

# Load the FITS file
filename = "hmi.sharp_cea_720s.4698.20141022_000000_TAI.Br.fits"
with fits.open(filename) as hdul:
    hdul.info()  # Show the structure of the FITS file
    data = hdul[1].data  # Load the main image data from HDU 1

# Check the shape of the data
print("Data Shape:", data.shape)

# Plot the data
plt.figure(figsize=(10, 5))
plt.imshow(data, origin='lower', cmap='seismic', aspect='auto',
           vmin=-2500, vmax=2500)  # Adjust limits for visibility
plt.colorbar(label="Magnetic Field Strength (Gauss)")
plt.xlabel("Longitude Pixels")
plt.ylabel("Latitude Pixels")
plt.title("HMI SHARP CEA Br Magnetic Field Visualization")
plt.show()

plt.figure(figsize=(10, 5))



