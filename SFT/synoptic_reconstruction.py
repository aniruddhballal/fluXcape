"""Load and inspect Carrington rotation synoptic maps."""

import numpy as np
from astropy.io import fits


def load_fits(previous_path, current_path, next_path):
    """Load the image and header from each of three FITS files."""
    maps = {}
    for label, path in zip(
        ("previous", "current", "next"),
        (previous_path, current_path, next_path),
    ):
        with fits.open(path, memmap=False) as hdus:
            maps[label] = {"path": path, "data": hdus[0].data.copy(),
                           "header": hdus[0].header.copy()}
    return maps


def validate_maps(maps):
    """Return basic compatibility checks and missing-pixel counts."""
    previous, current, next_map = (maps[name] for name in ("previous", "current", "next"))
    all_maps = (previous, current, next_map)
    headers = [item["header"] for item in all_maps]
    coordinate_keys = ("CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "CRPIX1",
                       "CRPIX2", "CRVAL2", "CDELT1", "CDELT2")
    rotations = [header["CAR_ROT"] for header in headers]

    return {
        "matching_dimensions": all(item["data"].shape == current["data"].shape for item in all_maps),
        "matching_coordinates": (
            all(header[key] == headers[1][key] for header in headers for key in coordinate_keys)
            and all(np.isclose((header["CRVAL1"] - headers[1]["CRVAL1"]) % 360, 0) for header in headers)
        ),
        "matching_units": all(header["BUNIT"] == headers[1]["BUNIT"] for header in headers),
        "consecutive_rotations": rotations == [rotations[1] - 1, rotations[1], rotations[1] + 1],
        "missing_pixels": {name: int(np.count_nonzero(~np.isfinite(item["data"])))
                           for name, item in maps.items()},
    }
