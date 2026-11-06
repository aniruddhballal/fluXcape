"""Angles in degrees, times in days, and synthetic radial field in gauss.

Longitude increases in the direction of rotation. The map's observation order
is a teaching convention, not a statement about every instrument's FITS layout.
"""

from dataclasses import dataclass

import numpy as np

SYNODIC_PERIOD = 27.27
CARRINGTON_RATE = 14.1844  # sidereal deg/day (Archinal et al. 2018 via SunPy)
# Howard et al. (1990), as tabulated by SunPy, converted from microrad/s.
HOWARD_COEFFICIENTS = np.array([2.894, -0.428, -0.370]) * 1e-6 * 86400 * 180 / np.pi
LONGITUDES = np.arange(360, dtype=float)
LATITUDES = np.arange(-90, 91, 2, dtype=float)


def wrap_longitude(longitude):
    return np.mod(longitude, 360.0)


def observation_time(longitude, rotation_offset=0):
    """Absolute time relative to central rotation's 0-degree observation.

    Do NOT wrap longitude here: 360 means the preceding boundary in time,
    whereas 0 means the newest column, despite sharing a spatial meridian.
    """
    return rotation_offset * SYNODIC_PERIOD - np.asarray(longitude) * SYNODIC_PERIOD / 360


def rotation_rate(latitude, differential=False):
    latitude = np.asarray(latitude, dtype=float)
    if not differential:
        return np.full_like(latitude, CARRINGTON_RATE)
    a, b, c = HOWARD_COEFFICIENTS
    sin2 = np.sin(np.deg2rad(latitude)) ** 2
    return a + b * sin2 + c * sin2**2


def drift_rate(latitude, differential=False):
    return rotation_rate(latitude, differential) - CARRINGTON_RATE


def displacement(latitude, elapsed_days, differential=False):
    """Positive displacement moves right, toward increasing displayed longitude."""
    return drift_rate(latitude, differential) * np.asarray(elapsed_days)


def base_field(longitude, latitude):
    """Smooth periodic analytic field, balanced bipolar pairs plus axial dipole.

    Same-latitude positive/negative lobes have equal spherical integrals. The
    high-latitude regions are deliberately exaggerated educational tracers.
    """
    lon, lat = np.broadcast_arrays(longitude, latitude)
    field = 3 * np.sin(np.deg2rad(lat))
    # longitude, latitude, strength, longitude width, latitude width
    regions = [(48, 0, 85, 5, 7), (145, 30, 100, 6, 7),
               (282, 60, 85, 8, 6), (210, -30, 90, 6, 8),
               (340, -60, 75, 8, 6), (105, -15, 55, 4, 5)]
    for center_lon, center_lat, strength, width, height in regions:
        envelope = np.exp(-0.5 * ((lat - center_lat) / height) ** 2)
        # cos(latitude)^2 makes the non-axisymmetric field vanish at the poles.
        envelope *= np.cos(np.deg2rad(lat)) ** 2 / np.cos(np.deg2rad(center_lat)) ** 2
        for sign in (-1, 1):
            distance = (lon - (center_lon + sign * width) + 180) % 360 - 180
            field = field + sign * strength * envelope * np.exp(-0.5 * (distance / width) ** 2)
    return field


def field_at(longitude, latitude, time_days, differential=False):
    """Exact advected synthetic truth: B(phi,lat,t)=B0(phi-v(lat)*t,lat)."""
    source = np.asarray(longitude) - displacement(latitude, time_days, differential)
    return base_field(wrap_longitude(source), latitude)


def instantaneous_map(time_days, differential=False):
    return field_at(LONGITUDES[None, :], LATITUDES[:, None], time_days, differential)


def synoptic_map(differential=False, rotation_offset=0):
    """Each column is sampled at ITS observation time, never from a static map."""
    return field_at(LONGITUDES[None, :], LATITUDES[:, None],
                    observation_time(LONGITUDES, rotation_offset)[None, :], differential)


def accumulated_map(synoptic, time_days):
    observed = observation_time(LONGITUDES) <= time_days + 1e-10
    return np.where(observed[None, :], synoptic, np.nan)


@dataclass
class RemapResult:
    field: np.ndarray
    weight: np.ndarray
    numerator: np.ndarray
    positions: np.ndarray

    @property
    def supported(self):
        return self.weight > 1e-12


def periodic_remap(values, positions, fill_gaps=True):
    """Deposit every sample into two neighboring periodic 1-degree grid nodes.

    Weighted averaging handles collisions without last-write-wins data loss.
    A field measurement is an intensive quantity, not an integrated flux packet.
    The numerator and weight retain ALL contributions, but their ratio is not
    a flux-conserving remap of synoptic pixel areas. Unobserved nodes are either
    NaN or explicitly filled by periodic linear interpolation; weight stays zero.
    """
    values = np.asarray(values, dtype=float)
    positions = np.asarray(positions, dtype=float)
    if values.ndim != 2 or values.shape != positions.shape:
        raise ValueError("values and positions must be matching 2-D arrays")
    if not np.all(np.isfinite(positions)):
        raise ValueError("positions must be finite")
    rows = values.shape[0]
    numerator = np.zeros((rows, 360))
    weight = np.zeros_like(numerator)
    wrapped = wrap_longitude(positions)
    left = np.floor(wrapped).astype(int)
    fraction = wrapped - left
    valid = np.isfinite(values)
    row_index = np.broadcast_to(np.arange(rows)[:, None], values.shape)
    for index, contribution in ((left, 1 - fraction), ((left + 1) % 360, fraction)):
        np.add.at(numerator, (row_index[valid], index[valid]), (values * contribution)[valid])
        np.add.at(weight, (row_index[valid], index[valid]), contribution[valid])
    result = np.full_like(numerator, np.nan)
    np.divide(numerator, weight, out=result, where=weight > 1e-12)
    if fill_gaps:
        for row in range(rows):
            supported = weight[row] > 1e-12
            if supported.any():
                result[row, ~supported] = np.interp(
                    LONGITUDES[~supported], LONGITUDES[supported], result[row, supported], period=360
                )
    return RemapResult(result, weight, numerator, wrapped)


def reconstruct(synoptic, reference_time=0.0, differential=False, progress=1.0, fill_gaps=True):
    """Progress interpolates transport paths; intermediate states aren't snapshots."""
    if not 0 <= progress <= 1:
        raise ValueError("progress must be between 0 and 1")
    elapsed = reference_time - observation_time(LONGITUDES)
    positions = LONGITUDES[None, :] + progress * displacement(
        LATITUDES[:, None], elapsed[None, :], differential
    )
    return periodic_remap(synoptic, positions, fill_gaps)


def area_weighted_rmse(estimate, truth, mask=None):
    """Latitude-area weighted RMS; exclude missing samples and optional mask."""
    valid = np.isfinite(estimate) & np.isfinite(truth)
    if mask is not None:
        valid &= mask
    weights = np.broadcast_to(np.cos(np.deg2rad(LATITUDES))[:, None], truth.shape)
    if not valid.any():
        return float("nan")
    return float(np.sqrt(np.average((estimate[valid] - truth[valid]) ** 2, weights=weights[valid])))
