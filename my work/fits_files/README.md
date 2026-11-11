# Shared HMI synoptic FITS inputs

Synoptic maps live here so they can be shared by the projects in `my work/`.
The downloader and updater is `my work/download_synoptic_maps.py`; it also
extracts the JSOC record metadata into the downloaded FITS headers.
The local `.gitattributes` marks FITS files as binary to preserve their exact bytes
in Git.

From the repository root, install the downloader dependency and run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r ".\my work\requirements.txt"
.\.venv\Scripts\python.exe ".\my work\download_synoptic_maps.py"
```

Choose `1` for `720x360/` (`hmi.mrsynop_small_720s`) or `2` for
`3600x1440/` (`hmi.synoptic_mr_720s`). The script checks the archive, skips
existing files, and asks before downloading missing rotations. Downloads
always go into this directory, regardless of the shell's working directory.
The downloader's Astropy dependency is declared in `my work/requirements.txt`.

These synoptic inputs and their downloader are independent of the deleted
reconstruction/comparison experiment. The downloader resolves this directory
from its own script location and requires no files from that experiment.

**Deleted:** `my work/SFT/`, including its reconstruction and observation
validator, coordinate tests, comparison reports, cached HMI 45-second snapshot
observations, and validation outputs. Its React viewer and exporter had already
been deleted. Historical findings are retained in
`my work/pre_sft_audit_record.md`; the tracked implementation remains in Git
history. The shared synoptic maps in this directory are retained.
