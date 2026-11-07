from astropy.io import fits
import matplotlib.pyplot as plt

folder = r"D:\engg\2024summr\Project-NagaSurya\fits_files"
previous = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2096.fits")
current = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2097.fits")
next_map = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2098.fits")

plt.imshow(current, origin="lower", cmap="gray")
plt.colorbar(label="Magnetic field (Mx/cm²)")
plt.show()
