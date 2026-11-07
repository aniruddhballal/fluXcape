from astropy.io import fits
import matplotlib.pyplot as plt

path = r"D:\engg\2024summr\Project-NagaSurya\fits_files\hmi.Synoptic_Mr_small.2097.fits"
data = fits.getdata(path)
plt.imshow(data, origin="lower", cmap="gray")
plt.colorbar(label="Magnetic field (Mx/cm²)")
plt.show()
