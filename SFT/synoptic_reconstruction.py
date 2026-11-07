"""Tools for loading Carrington rotation synoptic magnetic-field maps."""

from pathlib import Path

import numpy as np
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


def validate_maps(maps):
    """Check loaded maps for compatibility and return missing-pixel counts.

    Raise ValueError with all detected problems if the maps are incompatible.
    Non-finite pixels are counted and reported, since real synoptic maps may
    contain gaps; a map with no finite pixels is invalid.
    """
    labels = ("previous", "current", "next")
    errors = []
    missing = {}
    headers = {}
    shapes = {}
    coordinate_keys = ("CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "CRPIX1",
                       "CRPIX2", "CRVAL1", "CRVAL2", "CDELT1", "CDELT2")
    numeric_keys = ("CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2", "CDELT1", "CDELT2")

    for label in labels:
        item = maps.get(label)
        if not isinstance(item, dict):
            errors.append(f"{label}: map is missing")
            continue
        data, header = item.get("data"), item.get("header")
        if not isinstance(data, np.ndarray) or data.ndim != 2 or not np.issubdtype(data.dtype, np.number) or np.iscomplexobj(data):
            errors.append(f"{label}: expected a two-dimensional numeric image")
        else:
            shapes[label] = data.shape
            finite = np.isfinite(data)
            missing[label] = int(data.size - np.count_nonzero(finite))
            if not np.any(finite):
                errors.append(f"{label}: image has no finite pixels")

        if header is None:
            errors.append(f"{label}: FITS header is missing")
            continue
        headers[label] = header
        for key in (*coordinate_keys, "BUNIT", "CAR_ROT"):
            if key not in header or header[key] is None or (isinstance(header[key], str) and not header[key].strip()):
                errors.append(f"{label}: missing {key} metadata")
        for key in numeric_keys:
            if key in header:
                try:
                    value = float(header[key])
                    if not np.isfinite(value) or (key.startswith("CDELT") and value == 0):
                        raise ValueError
                except (TypeError, ValueError):
                    errors.append(f"{label}: invalid {key} metadata")
        if "CAR_ROT" in header:
            value = header["CAR_ROT"]
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0:
                errors.append(f"{label}: invalid CAR_ROT metadata")

    if len(shapes) == 3 and len(set(shapes.values())) != 1:
        errors.append("maps have different image dimensions")
    if len(headers) == 3:
        reference = headers["current"]
        # CRVAL1 changes by 360 degrees between these HMI maps; compare it
        # modulo a full turn while preserving all other coordinate parameters.
        for label in ("previous", "next"):
            header = headers[label]
            for key in (*coordinate_keys, "BUNIT"):
                if key not in header or key not in reference:
                    continue
                a, b = header[key], reference[key]
                if key in numeric_keys:
                    try:
                        a, b = float(a), float(b)
                        if key == "CRVAL1":
                            difference = (a - b + 180) % 360 - 180
                            same = np.isfinite(difference) and np.isclose(difference, 0, atol=1e-6)
                        else:
                            same = np.isfinite(a) and np.isfinite(b) and np.isclose(a, b, rtol=1e-7, atol=1e-9)
                    except (TypeError, ValueError):
                        continue
                else:
                    same = str(a).strip().casefold() == str(b).strip().casefold()
                if not same:
                    errors.append(f"{label}: {key} differs from current map")
        rotations = [headers[label].get("CAR_ROT") for label in labels]
        if all(isinstance(x, (int, np.integer)) and not isinstance(x, bool) and x > 0 for x in rotations):
            if rotations != list(range(rotations[0], rotations[0] + 3)):
                errors.append("CAR_ROT values must be consecutive in previous, current, next order")

    if errors:
        raise ValueError("Map validation failed:\n- " + "\n- ".join(errors))
    return {label: {"missing_pixels": missing[label], "total_pixels": int(maps[label]["data"].size)} for label in labels}
