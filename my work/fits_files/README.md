# Shared HMI synoptic FITS inputs

Synoptic maps live here so they can be shared by the projects in `my work/`.
The downloader and updater is `my work/download_synoptic_maps.py`; it also
extracts the JSOC record metadata into the downloaded FITS headers.
The local `.gitattributes` marks FITS files as binary to preserve their exact bytes
in Git.

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe ".\my work\download_synoptic_maps.py"
```

Choose `1` for `720x360/` (`hmi.mrsynop_small_720s`) or `2` for
`3600x1440/` (`hmi.synoptic_mr_720s`). The script checks the archive, skips
existing files, and asks before downloading missing rotations. Downloads
always go into this directory, regardless of the shell's working directory.
The existing Python dependencies are in `my work/SFT/requirements.txt`.

The SFT reconstruction, observation validator and viewer exporter use the
shared default path defined by `FITS_FOLDER` in
`my work/SFT/synoptic_reconstruction.py`. Explicit folders can still be passed
to `load_maps()` when needed.

HMI 45-second snapshot observations and validation results remain in
`my work/SFT/validation_data/`. Their saved fingerprint labels such as
`fits_files/720x360/...` are logical input identifiers; the actual synoptic
files are here. Historical results are preserved, and the existing provenance
checks will flag changed calculation scripts when regenerating viewer data.
