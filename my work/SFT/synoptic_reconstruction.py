from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap, Normalize
import numpy as np
from pathlib import Path
from scipy.interpolate import RectBivariateSpline

ROTATIONS = (2119, 2120, 2121)
FITS_FOLDER = Path(__file__).resolve().parent.parent / "fits_files"
DISPLAY_LIMIT = 100  # Gauss; values outside +/- this limit saturate in the plot.


def sunalyse_colormap():
    """Reproduce Sunalyse's photosphere color mapping."""
    value = np.linspace(0, 1, 65536)
    colors = np.empty((value.size, 3))
    low = value < 0.4
    t = value[low] / 0.4
    colors[low] = np.column_stack((100 + 155 * t, 200 * t, np.zeros_like(t)))
    low_mid = (value >= 0.4) & (value < 0.48)
    t = (value[low_mid] - 0.4) / 0.08
    colors[low_mid] = np.column_stack((255 - 55 * t, 200 - 50 * t, 150 * t))
    colors[(value >= 0.48) & (value < 0.52)] = (150, 150, 150)
    high_mid = (value >= 0.52) & (value < 0.6)
    t = (value[high_mid] - 0.52) / 0.08
    colors[high_mid] = np.column_stack((150 - 150 * t, 150 + 105 * t, 150 - 50 * t))
    high = value >= 0.6
    t = (value[high] - 0.6) / 0.4
    colors[high] = np.column_stack((np.zeros_like(t), 255 - 255 * t, 100 + 155 * t))
    cmap = ListedColormap(colors / 255, name="sunalyse_photosphere")
    cmap.set_bad("#303038")  # Missing pixels are distinct from neutral field.
    return cmap


PHOTO_CMAP = sunalyse_colormap()
PHOTO_NORM = Normalize(vmin=-DISPLAY_LIMIT, vmax=DISPLAY_LIMIT, clip=True)


def load_maps(folder=FITS_FOLDER / "720x360", rotations=ROTATIONS):
    """Load the three maps; default to the shared my work/fits_files inputs."""
    paths = [Path(folder) / f"hmi.Synoptic_Mr_small.{rotation}.fits" for rotation in rotations]
    loaded = [fits.getdata(path, header=True) for path in paths]
    return [item[0] for item in loaded], [item[1] for item in loaded]


def calculate_coordinates(data, header):
    """Calculate physical HMI synoptic longitude and latitude in degrees.

    SunPy's HMI convention uses a positive longitude step for the data array
    even when the archived HMI header has a negative CDELT1.
    """
    x = np.arange(data.shape[1])
    y = np.arange(data.shape[0])
    longitude = (header["CRVAL1"] + (x + 1 - header["CRPIX1"]) * abs(header["CDELT1"])) % 360
    sin_latitude = header["CRVAL2"] + (y + 1 - header["CRPIX2"]) * header["CDELT2"]
    sin_latitude = np.where(np.abs(sin_latitude) <= 1, sin_latitude, np.nan)
    latitude = np.degrees(np.arcsin(sin_latitude))
    return longitude, latitude


def calculate_delta_t(longitude):
    """Calculate approximate time offsets in days using the original model."""
    return (longitude - 180) / 13.2


def calculate_rotation_rate(latitude):
    """Calculate the latitude-corrected rotation law in degrees per day."""
    sin_latitude = np.sin(np.radians(latitude))
    return 0.18 - 2.3 * sin_latitude**2 - 1.62 * sin_latitude**4


def calculate_ananya_rotation_rate(latitude):
    """Reproduce the original initialization's latitude-as-colatitude input."""
    cos_latitude = np.cos(np.radians(latitude))
    return 0.18 - 2.3 * cos_latitude**2 - 1.62 * cos_latitude**4


def calculate_phi_prime(longitude, delta_t, rotation_rate):
    """Calculate corrected longitudes in degrees for each map pixel."""
    return longitude[None, :] + rotation_rate[:, None] * delta_t[None, :]


def select_source_map(phi_prime):
    """Choose a map index (previous=0, current=1, next=2) and wrap longitude."""
    source = np.where(phi_prime < 0, 0, np.where(phi_prime >= 360, 2, 1))
    return source, phi_prime % 360


def interpolate_field(maps, headers, latitude, source_map, wrapped_longitude):
    """Sample each source with a cubic spline; leave incomplete rows missing."""
    field = np.full(source_map.shape, np.nan)
    for index, (data, header) in enumerate(zip(maps, headers)):
        source_longitude, source_latitude = calculate_coordinates(data, header)
        valid_rows = np.isfinite(data).all(axis=1) & np.isfinite(source_latitude)
        # Sort after longitude wrapping; the spline requires increasing axes.
        order = np.argsort(source_longitude)
        source_longitude = source_longitude[order]
        spline = RectBivariateSpline(source_latitude[valid_rows], source_longitude,
                                    data[valid_rows][:, order])
        lat_grid = np.broadcast_to(latitude[:, None], source_map.shape)
        use = ((source_map == index)
               & (lat_grid >= source_latitude[valid_rows].min())
               & (lat_grid <= source_latitude[valid_rows].max())
               & (wrapped_longitude >= source_longitude.min())
               & (wrapped_longitude <= source_longitude.max()))
        field[use] = spline.ev(lat_grid[use], wrapped_longitude[use])
    return field


def plot_maps(maps, headers):
    """Plot the three maps with a shared color scale."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
    for ax, data, header, rotation in zip(axes, maps, headers, ROTATIONS):
        image = ax.imshow(data, origin="lower", cmap=PHOTO_CMAP, norm=PHOTO_NORM)
        ax.set_title(f"CR {rotation}")
        x_ticks = np.linspace(0, data.shape[1] - 1, 5)
        tick_longitudes = (header["CRVAL1"] + (x_ticks + 1 - header["CRPIX1"]) * abs(header["CDELT1"])) % 360
        ax.set_xticks(x_ticks, [f"{value:.0f}°" for value in tick_longitudes])
        tick_latitudes = np.array([-60, -30, 0, 30, 60])
        y_ticks = (np.sin(np.radians(tick_latitudes)) - header["CRVAL2"]) / header["CDELT2"] + header["CRPIX2"] - 1
        ax.set_yticks(y_ticks, [f"{value}°" for value in tick_latitudes])
        ax.set_xlabel("Carrington longitude")
        ax.set_ylabel("Latitude")
    fig.colorbar(image, ax=axes, label="Magnetic field (G)", extend="both", shrink=0.8)
    plt.show()


def plot_reconstruction(current, reconstructed, header):
    """Compare maps and show differences over pixels valid in both."""
    valid = np.isfinite(current) & np.isfinite(reconstructed)
    difference = np.where(valid, reconstructed - current, np.nan)
    values = difference[valid]
    bias = np.mean(values)
    mae = np.mean(np.abs(values))
    rmse = np.sqrt(np.mean(values**2))

    fig = plt.figure(figsize=(14, 8), constrained_layout=True)
    grid = fig.add_gridspec(2, 1, height_ratios=(5, 1), hspace=0.35)
    ax = fig.add_subplot(grid[0])
    stats = fig.add_subplot(grid[1])
    image = ax.imshow(current, origin="lower", cmap=PHOTO_CMAP, norm=PHOTO_NORM,
                      aspect="auto")
    title = ax.set_title(f"Original CR {ROTATIONS[1]}", fontsize=15)
    phi_ticks = np.array([45, 90, 180, 270, 315])
    longitude_offset = (phi_ticks - header["CRVAL1"] + 180) % 360 - 180
    x_ticks = longitude_offset / abs(header["CDELT1"]) + header["CRPIX1"] - 1
    ax.set_xticks(x_ticks, [f"{value}°" for value in phi_ticks])
    theta_ticks = np.array([30, 60, 90, 120, 150])
    sin_latitude = np.cos(np.radians(theta_ticks))
    y_ticks = (sin_latitude - header["CRVAL2"]) / header["CDELT2"] + header["CRPIX2"] - 1
    ax.set_yticks(y_ticks, [f"{value}°" for value in theta_ticks])
    ax.set_xlabel("Carrington longitude φ")
    ax.set_ylabel("Colatitude θ")
    fig.colorbar(image, ax=ax, label="Magnetic field (G)", extend="both", shrink=0.9)
    stats.axis("off")
    stats.text(0.5, 0.7,
               f"Mean difference (bias): {bias:.3f} G     |     "
               f"Mean absolute difference: {mae:.3f} G     |     "
               f"Root mean square difference: {rmse:.3f} G\n\n"
               f"Compared pixels: {valid.sum():,} / {valid.size:,}     |     "
               "Difference = reconstructed − original",
               transform=stats.transAxes, ha="center", va="center", fontsize=11)

    def animate(frame):
        image.set_data((current, reconstructed)[frame])
        title.set_text((f"Original CR {ROTATIONS[1]}", "Reconstructed")[frame])
        return image, title

    animation = FuncAnimation(fig, animate, frames=(0, 0, 0, 1), interval=1000,
                              repeat=True, blit=False)
    plt.show()


if __name__ == "__main__":
    maps, headers = load_maps()
    longitude, latitude = calculate_coordinates(maps[1], headers[1])
    delta_t = calculate_delta_t(longitude)
    rotation_rate = calculate_rotation_rate(latitude)
    phi_prime = calculate_phi_prime(longitude, delta_t, rotation_rate)
    source_map, wrapped_longitude = select_source_map(phi_prime)
    interpolated_field = interpolate_field(maps, headers, latitude, source_map, wrapped_longitude)
    plot_reconstruction(maps[1], interpolated_field, headers[1])
