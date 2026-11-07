from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

folder = r"D:\engg\2024summr\Project-NagaSurya\fits_files"
previous = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2096.fits")
current = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2097.fits")
next_map = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2098.fits")

maps = [previous, current, next_map]
vmin = min(np.nanmin(data) for data in maps)
vmax = max(np.nanmax(data) for data in maps)

fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
for ax, data, rotation in zip(axes, maps, (2096, 2097, 2098)):
    image = ax.imshow(data, origin="lower", cmap="gray", vmin=vmin, vmax=vmax)
    ax.set_title(f"CR {rotation}")
fig.colorbar(image, ax=axes, label="Magnetic field (Mx/cm²)")
plt.show()
