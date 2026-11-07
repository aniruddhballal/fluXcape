"""Tools for loading Carrington rotation synoptic magnetic-field maps."""

from pathlib import Path

from astropy.io import fits


def load_fits(previous_path, current_path, next_path):
    """Load three FITS primary images and their headers, in rotation order.

    Each path may be a string or pathlib.Path. Return a dictionary keyed by
    ``previous``, ``current``, and ``next``; each value contains the source
    ``path``, magnetic-field ``data`` array, and complete FITS ``header``.
    Arrays and headers are independent of the closed FITS files.

    Map compatibility and rotation sequence are checked in a later step.
    """
    maps = {}
    for label, path in (
        ("previous", previous_path),
        ("current", current_path),
        ("next", next_path),
    ):
        path = Path(path)
        with fits.open(path, memmap=False) as hdus:
            data = hdus[0].data
            maps[label] = {
                "path": path,
                "data": None if data is None else data.copy(),
                "header": hdus[0].header.copy(),
            }
    return maps
