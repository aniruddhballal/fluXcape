from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

folder = r"D:\engg\2024summr\Project-NagaSurya\fits_files"
previous, previous_header = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2096.fits", header=True)
current, current_header = fits.getdata(fwe havent"{folder}/hmi.Synoptic_Mr_small.2097.fits", header=True)
next_map, next_header = fits.getdata(f"{folder}/hmi.Synoptic_Mr_small.2098.fits", header=True)

maps = [previous, current, next_map]
# Approximate time offset in days, using the original model's reference and rate.
x = np.arange(current.shape[1])
longitude = (current_header["CRVAL1"] + (x + 1 - current_header["CRPIX1"]) * current_header["CDELT1"]) % 360
delta_t = (longitude - 180) / 13.2

vmin = min(np.nanmin(data) for data in maps)
vmax = max(np.nanmax(data) for data in maps)

fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
for ax, data, header, rotation in zip(axes, maps, (previous_header, current_header, next_header), (2096, 2097, 2098)):
    image = ax.imshow(data, origin="lower", cmap="gray", vmin=vmin, vmax=vmax)
    ax.set_title(f"CR {rotation}")
    x_ticks = np.linspace(0, data.shape[1] - 1, 5)
    tick_longitudes = (header["CRVAL1"] + (x_ticks + 1 - header["CRPIX1"]) * header["CDELT1"]) % 360
    ax.set_xticks(x_ticks, [f"{value:.0f}°" for value in tick_longitudes])
    latitude = np.array([-60, -30, 0, 30, 60])
    y_ticks = (np.sin(np.radians(latitude)) - header["CRVAL2"]) / header["CDELT2"] + header["CRPIX2"] - 1
    ax.set_yticks(y_ticks, [f"{value}°" for value in latitude])
    ax.set_xlabel("Carrington longitude")
    ax.set_ylabel("Latitude")
fig.colorbar(image, ax=axes, label="Magnetic field (Mx/cm²)")
plt.show()
