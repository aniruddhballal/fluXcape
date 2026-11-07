from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.interpolate import RectBivariateSpline

ROTATIONS = (2119, 2120, 2121)


def load_maps(folder):
    """Load the three maps and their FITS headers."""
    paths = [f"{folder}/hmi.Synoptic_Mr_small.{rotation}.fits" for rotation in ROTATIONS]
    loaded = [fits.getdata(path, header=True) for path in paths]
    return [item[0] for item in loaded], [item[1] for item in loaded]


def calculate_coordinates(data, header):
    """Calculate longitude and latitude in degrees for the map's pixels."""
    x = np.arange(data.shape[1])
    y = np.arange(data.shape[0])
    longitude = (header["CRVAL1"] + (x + 1 - header["CRPIX1"]) * header["CDELT1"]) % 360
    sin_latitude = header["CRVAL2"] + (y + 1 - header["CRPIX2"]) * header["CDELT2"]
    sin_latitude = np.where(np.abs(sin_latitude) <= 1, sin_latitude, np.nan)
    latitude = np.degrees(np.arcsin(sin_latitude))
    return longitude, latitude


def calculate_delta_t(longitude):
    """Calculate approximate time offsets in days using the original model."""
    return (longitude - 180) / 13.2


def calculate_rotation_rate(latitude):
    """Calculate the original model's rotation law in degrees per day."""
    sin_latitude = np.sin(np.radians(latitude))
    return 0.18 - 2.3 * sin_latitude**2 - 1.62 * sin_latitude**4


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
        # FITS longitude decreases across columns; the spline requires increasing axes.
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
    vmin = min(np.nanmin(data) for data in maps)
    vmax = max(np.nanmax(data) for data in maps)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
    for ax, data, header, rotation in zip(axes, maps, headers, ROTATIONS):
        image = ax.imshow(data, origin="lower", cmap="gray", vmin=vmin, vmax=vmax)
        ax.set_title(f"CR {rotation}")
        x_ticks = np.linspace(0, data.shape[1] - 1, 5)
        tick_longitudes = (header["CRVAL1"] + (x_ticks + 1 - header["CRPIX1"]) * header["CDELT1"]) % 360
        ax.set_xticks(x_ticks, [f"{value:.0f}°" for value in tick_longitudes])
        tick_latitudes = np.array([-60, -30, 0, 30, 60])
        y_ticks = (np.sin(np.radians(tick_latitudes)) - header["CRVAL2"]) / header["CDELT2"] + header["CRPIX2"] - 1
        ax.set_yticks(y_ticks, [f"{value}°" for value in tick_latitudes])
        ax.set_xlabel("Carrington longitude")
        ax.set_ylabel("Latitude")
    fig.colorbar(image, ax=axes, label="Magnetic field (Mx/cm²)")
    plt.show()


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent / "fits_files" / "720x360"
    maps, headers = load_maps(folder)
    longitude, latitude = calculate_coordinates(maps[1], headers[1])
    delta_t = calculate_delta_t(longitude)
    rotation_rate = calculate_rotation_rate(latitude)
    phi_prime = calculate_phi_prime(longitude, delta_t, rotation_rate)
    source_map, wrapped_longitude = select_source_map(phi_prime)
    interpolated_field = interpolate_field(maps, headers, latitude, source_map, wrapped_longitude)
    plot_maps(maps, headers)
