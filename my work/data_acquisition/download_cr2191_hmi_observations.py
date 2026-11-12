"""Acquire original JSOC observations only; never import reconstruction/SFT code.

Run with Python containing NumPy and Astropy. Raw segment FITS files are kept
unchanged; JSOC's record keywords (including WCS) are saved separately because
direct SUMS segment files need not contain the full record metadata.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import urlopen

from astropy.io import fits
import numpy as np


ROOT = Path(__file__).resolve().parent.parent / "hmi_fits_data" / "observations" / "cr2191"
BASE = "http://jsoc.stanford.edu"
TIMES = ["2017.06.09_10:48:00_TAI", "2017.06.09_11:00:00_TAI",
         "2017.06.09_11:12:00_TAI"]
SERIES = {
    "hmi.B_720s": ["field", "inclination", "azimuth", "disambig",
                   "conf_disambig", "field_err", "inclination_err",
                   "azimuth_err", "field_inclination_err", "field_az_err",
                   "inclin_azimuth_err", "info_map", "conv_flag"],
    "hmi.M_720s": ["magnetogram"],
}


def query(**params):
    url = BASE + "/cgi-bin/ajax/jsoc_info?" + urlencode(params)
    with urlopen(url, timeout=60) as response:
        result = json.load(response)
    if result.get("status") != 0:
        raise RuntimeError(result)
    return url, result


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def acquire(task):
    path, url, identity = task
    temporary = path.with_suffix(".fits.part")
    for attempt in range(3):
        try:
            if not path.exists():
                with urlopen(url, timeout=120) as response, temporary.open("wb") as out:
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
                temporary.replace(path)
            # Decode compressed data as well as checking the FITS structure.
            with fits.open(path, memmap=False) as hdus:
                hdus.verify("exception")
                images = [h for h in hdus if h.data is not None]
                if len(images) != 1 or images[0].data.shape != (4096, 4096):
                    raise ValueError(f"Unexpected image layout: {path}")
                data = images[0].data
                finite_count = int(np.count_nonzero(np.isfinite(data)))
                if not finite_count:
                    raise ValueError(f"No finite pixels: {path}")
                checksums = []
                for index, hdu in enumerate(hdus):
                    if "CHECKSUM" in hdu.header:
                        value = hdu.verify_checksum()
                        checksums.append({"hdu": index, "checksum": value})
                        if value != 1:
                            raise ValueError(f"FITS checksum failure: {path}")
            digest = hashlib.sha256()
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
            result = dict(identity, path=str(path.relative_to(ROOT)), url=url,
                          bytes=path.stat().st_size, sha256=digest.hexdigest(),
                          shape=[4096, 4096], finite_pixels=finite_count,
                          fits_checksums=checksums,
                          verified_at_utc=datetime.now(timezone.utc).isoformat())
            print(f"Verified {result['path']} ({result['bytes']} bytes)", flush=True)
            return result
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    tasks = []
    for series, segments in SERIES.items():
        folder = ROOT / series
        folder.mkdir(exist_ok=True)
        url, structure = query(op="series_struct", ds=series)
        save_json(folder / "series_structure.json", {"url": url, "response": structure})
        for timestamp in TIMES:
            record = f"{series}[{timestamp}]"
            url, response = query(op="rs_list", ds=record, key="**ALL**",
                                  seg=",".join(segments))
            if response.get("count") != 1:
                raise RuntimeError(f"Expected one record: {record}")
            keywords = {item["name"]: item["values"][0]
                        for item in response["keywords"]}
            if int(keywords["QUALITY"], 0) != 0:
                raise RuntimeError(f"Nonzero quality: {record}")
            stamp = timestamp.replace(".", "").replace(":", "")
            save_json(folder / f"{stamp}.record.json",
                      {"query_url": url, "record": record, "keywords": keywords,
                       "response": response})
            by_name = {s["name"]: s for s in response["segments"]}
            for segment in segments:
                source = by_name[segment]["values"][0].replace("\\/", "/")
                if not source.startswith("/"):
                    raise RuntimeError(f"Unavailable segment {record}: {segment}: {source}")
                tasks.append((folder / f"{series}.{stamp}.{segment}.fits", BASE + source,
                              {"record": record, "series": series, "segment": segment,
                               "t_rec_tai": timestamp, "t_obs_tai": keywords.get("T_OBS"),
                               "quality": keywords["QUALITY"]}))
    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(acquire, task): task for task in tasks}
        for future in as_completed(pending):
            try:
                results.append(future.result())
            except Exception as exc:
                task = pending[future]
                errors.append({"record": task[2], "error": str(exc)})
                print(f"FAILED {task[0].name}: {exc}", flush=True)
            save_json(ROOT / "manifest.json", {
                "reference_time_tai": "2017.06.09_10:56:34_TAI",
                "files": sorted(results, key=lambda r: r["path"]), "errors": errors})
    if errors:
        raise RuntimeError(f"{len(errors)} downloads failed; see manifest.json")
    print(f"Complete: {len(results)} verified observational FITS files", flush=True)


if __name__ == "__main__":
    main()
