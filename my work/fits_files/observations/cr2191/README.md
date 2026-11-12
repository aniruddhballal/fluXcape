# CR2191 observational reference inputs

Original full-resolution JSOC data for comparing pre-SFT reconstructions.
Acquisition does not execute either reconstruction or any SFT code.

## Records

The local CR2191 synoptic header specifies reference time
`2017.06.09_10:56:34_TAI`. Each series below has records at
`2017.06.09_10:48:00_TAI`, `2017.06.09_11:00:00_TAI`, and
`2017.06.09_11:12:00_TAI`. Their `T_OBS` values are eight seconds later
than `T_REC`; use the saved metadata rather than treating the filename as an
exact exposure time. The nearest record's `T_OBS` is 3 minutes 34 seconds
after the synoptic reference time. All six records have `QUALITY=0x00000000`.

- `hmi.B_720s/`: field strength, inclination, azimuth, disambiguation bits,
  disambiguation confidence, three parameter errors, three pairwise error
  terms, inversion convergence flags, and information masks (13 segments
  per timestamp).
- `hmi.M_720s/`: line-of-sight magnetograms (one segment per timestamp).
- `manifest.json`: source URLs, record identifiers, SHA-256 hashes, byte
  counts, decoded shapes, finite-pixel counts, verification times, and any
  download failures. A complete acquisition contains 42 FITS files and no errors.
- Each `*.record.json`: complete JSOC record keywords and unmodified query
  response, including segment paths.
- Each `series_structure.json`: JSOC keyword types and segment definitions,
  including units and compression/scaling information.

## Preservation and verification

FITS downloads retain their original bytes, including compression. Direct
SUMS segment files can omit record-level coordinate keywords: their adjacent
JSON metadata is an essential part of this dataset. No header synthesis,
reprojection, disambiguation, field conversion, or spatial resampling has been
performed. Astropy checks FITS structure, decodes each image, verifies the
4096-by-4096 shape and finite pixels, and checks FITS checksums where present.
SHA-256 hashes record local integrity; they are not archive-provided signatures.

Source: JSOC `http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info` and the original
SUMS segment URLs returned by it. The main host's HTTPS endpoint failed TLS
negotiation during acquisition, so these downloads use its working HTTP
endpoint. Exact query and download URLs are recorded locally.

To repeat or resume acquisition with Python containing Astropy and NumPy:

```bash
python3 'my work/download_pre_sft_observations.py'
```

## Interpretation for the future comparison

`hmi.B_720s` field strength is not radial field. A later validation must
apply the appropriate azimuth disambiguation and transform the vector using
the record's observer geometry. Use confidence and inversion masks, and consult
the series definitions before interpreting the pairwise error segments.
`hmi.M_720s` measures line-of-sight field, so compare it with a projected
prediction or document the radial-field assumption and viewing-angle mask.

These snapshots are separate observational products, but share the HMI
instrument and may share contributing measurements with the synoptic map.
They are an observational reference, not statistically independent,
noise-free, full-sphere ground truth. Visible coverage, temporal mismatch,
and common instrument systematics must be reported. The adjacent records
support a local timing-sensitivity check, not a multi-rotation generalization.

Relevant primary documentation:

- HMI vector pipeline: https://arxiv.org/abs/1404.1881
- HMI full-disk vector data notice:
  https://spd.aas.org/solarnews/2016/18/
- Archive recovery/access status:
  https://solarweb1.stanford.edu/JSOC_Emergency_Resources.html

This folder contains inputs and acquisition provenance only. It contains no
reconstruction comparisons or validation results.
