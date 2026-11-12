"""Check and download missing HMI synoptic maps from the JSOC archive."""

import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlencode
from urllib.request import urlopen
import warnings

from astropy.io import fits


JSOC = "http://jsoc.stanford.edu"
FOLDER = Path(__file__).resolve().parent.parent / "hmi_fits_data"
SERIES = {
    "1": ("hmi.mrsynop_small_720s", "720x360", "hmi.Synoptic_Mr_small", (360, 720)),
    "2": ("hmi.synoptic_mr_720s", "3600x1440", "hmi.Synoptic_Mr", (1440, 3600)),
}


def query(endpoint, **params):
    url = f"{JSOC}/cgi-bin/ajax/{endpoint}?{urlencode(params)}"
    with urlopen(url, timeout=60) as response:
        result = json.load(response)
    if result.get("status") != 0:
        raise RuntimeError(result.get("error", "JSOC query failed"))
    return result


def archive_records(series):
    """Get image paths and metadata for the archive's current record range."""
    structure = query("jsoc_info", op="series_struct", ds=series)
    interval = structure["Interval"]
    first = int(re.search(r"\[(\d+)\]", interval["FirstRecord"]).group(1))
    last = int(re.search(r"\[(\d+)\]", interval["LastRecord"]).group(1))
    result = query("jsoc_info", op="rs_list", ds=f"{series}[{first}-{last}]",
                   key="**ALL**", seg="synopMr")
    columns = {item["name"]: item["values"] for item in result["keywords"]}
    types = {item["name"]: item["type"] for item in structure["keywords"]}
    paths = result["segments"][0]["values"]
    return first, last, columns, types, paths


def make_header(columns, types, index, series):
    """Put JSOC record metadata into a FITS header for the image segment."""
    header = fits.Header()
    for key, values in columns.items():
        value = values[index]
        if value == "MISSING" or key in ("COMMENT", "HISTORY"):
            continue
        kind = types.get(key, "string")
        if kind in ("int", "short", "longlong", "char"):
            value = int(value, 0) if value.lower().startswith(("0x", "-0x")) else int(value)
        elif kind in ("float", "double"):
            value = float(value)
            if not math.isfinite(value):
                continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", fits.verify.VerifyWarning)
            header[key] = value
    header.add_history(f"JSOC {series} synopMr image; metadata from its JSOC record.")
    return header


def download_map(folder, name, rotation, shape, segment, header):
    """Download and check one map, then place it in the destination folder."""
    destination = folder / f"{name}.{rotation}.fits"
    temporary = destination.with_suffix(".fits.part")
    try:
        with urlopen(JSOC + segment, timeout=120) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        with fits.open(temporary, memmap=False, checksum=True) as hdus:
            data = hdus[0].data.copy()
        if data.shape != shape:
            raise ValueError(f"expected {shape}, got {data.shape}")
        fits.PrimaryHDU(data=data, header=header).writeto(temporary, overwrite=True, checksum=True)
        with fits.open(temporary, checksum=True) as hdus:
            if hdus[0].header["CAR_ROT"] != rotation or hdus[0].data.shape != shape:
                raise ValueError("FITS verification failed")
            if hdus[0].verify_checksum() != 1 or hdus[0].verify_datasum() != 1:
                raise ValueError("FITS checksum verification failed")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    print("Choose map resolution:")
    print("  1. Low:  720 x 360")
    print("  2. High: 3600 x 1440")
    choice = input("Resolution (1 or 2): ").strip()
    if choice not in SERIES:
        print("Please choose 1 or 2.")
        return 1

    series, dimensions, name, shape = SERIES[choice]
    folder = FOLDER / dimensions
    first, last, columns, types, paths = archive_records(series)
    rotations = [int(value) for value in columns["CAR_ROT"]]
    local = list(folder.glob("*.fits")) if folder.exists() else []
    missing = [(i, rotation) for i, rotation in enumerate(rotations)
               if not (folder / f"{name}.{rotation}.fits").exists()]
    available = len(rotations)
    print(f"Folder: {folder}")
    print(f"FITS files in folder: {len(local)}")
    print(f"JSOC records: {available} (CR {first} to CR {last})")
    print(f"Already saved from this series: {available - len(missing)}")
    print(f"Missing: {len(missing)}")
    if not missing:
        return 0
    print("Missing rotations:", ", ".join(str(rotation) for _, rotation in missing))
    size_gb = len(missing) * shape[0] * shape[1] * 4 / 1_000_000_000
    print(f"Approximate image data to download: {size_gb:.2f} GB")
    if input("Download missing maps? (y/N): ").strip().lower() not in ("y", "yes"):
        print("Download skipped.")
        return 0

    folder.mkdir(parents=True, exist_ok=True)
    failed = []
    for number, (index, rotation) in enumerate(missing, 1):
        print(f"[{number}/{len(missing)}] CR {rotation}...", end=" ", flush=True)
        try:
            header = make_header(columns, types, index, series)
            download_map(folder, name, rotation, shape, paths[index], header)
            print("saved")
        except Exception as exc:
            failed.append(rotation)
            print(f"failed: {exc}")
    if failed:
        print("Failed rotations:", ", ".join(map(str, failed)))
        return 1
    print("All available missing maps downloaded.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"Could not check the JSOC archive: {exc}", file=sys.stderr)
        sys.exit(1)
