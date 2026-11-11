# Observational validation of synoptic reconstructions

This compares three maps with independent HMI 45-second line-of-sight
magnetograms: the unchanged central synoptic map, the reconstruction using
Ananya's initialization rotation expression, and the reconstruction using the
latitude-corrected rotation expression. All three scores for each rotation use
exactly the same observation and pixel mask. These are snapshot comparisons,
not validation of a full solar rotation or of Ananya's complete pipeline.

## Longitude registration

The archived CR 2119 through 2127 headers have `CDELT1 = -0.5` degrees per
pixel, `CRLN-CEA` coordinates and a Carrington longitude reference at 180
degrees. SunPy's [`HMISynopticMap` documentation](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html)
and its installed HMI source code both state that the HMI data array uses the
**positive** step even when the header value is negative. We now use
`abs(CDELT1)` in one shared `calculate_coordinates()` function for
reconstruction, interpolation and observational registration. Viewer
coordinates are exported with the same positive step. The original FITS files
and pixel arrays are not modified.

As an independent registration check, the unchanged central map was compared
with each full-disk HMI observation on a common visible mask. We compared the
physical positive-step orientation with an alternative that treats the negative
header sign as physical, reflecting and linearly sampling the map. This is a
registration diagnostic, not a replacement for the published convention; the
alternative has one extra interpolation step.

| CR | Pixels | Positive step: RMSE / Pearson r | Negative step: RMSE / Pearson r |
|---|---:|---:|---:|
| 2120 | 25,693 | 23.821 G / 0.825 | 54.623 G / 0.035 |
| 2122 | 25,705 | 35.247 G / 0.388 | 44.199 G / -0.032 |
| 2124 | 25,700 | 43.171 G / 0.693 | 74.076 G / 0.049 |

The positive orientation agrees substantially better in these checks, supporting
SunPy's convention for these specific files. It does not resolve all other
registration, timing or instrument uncertainties.

For CR 2120, correcting the longitude convention barely changes the scores in
the observed region: the old and new reconstructed pixel values agree to
numerical precision on the common observation mask. With this 180-degree
reference, reflecting longitude also reflects the time offset, so the two
sign changes cancel for same-map sampling. The full maps are not identical:
source-map selection changes at some rotation boundaries. The prior CR 2120
scores happen to remain the same; this does not make the previous coordinate
labels correct.

## Reference timestamps and observations

The reference time is not uniquely established across the available conventions.
For each central rotation, the code brackets `CRLN_OBS = 180` using adjacent
quality-zero HMI 45-second records and linearly interpolates their observation
times. It then chooses the closest quality-zero image.

| CR | Estimated crossing, UTC | Selected HMI `T_OBS`, UTC | Observation minus crossing |
|---|---|---|---:|
| 2120 | 2012-02-19 22:54:54.688 | 2012-02-19 22:54:50 | -4.69 s |
| 2122 | 2012-04-14 13:39:31.801 | 2012-04-14 13:39:13 | -18.80 s |
| 2124 | 2012-06-08 00:29:36.874 | 2012-06-08 00:29:33 | -3.87 s |

For CR 2120, the header's nominal `T_ROT` is 22:51:59 TAI (22:51:25 UTC).
SunPy's default Earth-observer `carrington_rotation_time(2120.5)` gives
22:47:46.384 TAI (22:47:12.384 UTC). These differ from the crossing estimated
from the HMI record. The cause, including observer and light-time conventions,
has not been established. The numbers in the table are interpolation estimates
under the HMI record convention, not convention-independent exact timestamps.
See [SunPy's L0 documentation](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.L0.html).

The script obtains the `hmi.M_45s` images and metadata from JSOC and records
URLs, timestamps, QUALITY, and image SHA-256 in each JSON result. HMI's
45-second and 720-second products use separate camera measurements according
to the [HMI dataset description](https://spase-metadata.org/NASA/NumericalData/SDO/HMI/LOS_Magnetogram/PT720S.html),
but share an instrument, solar scene and potential systematic errors. Each
45-second image has a finite temporal response, not one instantaneous exposure.

## Comparison method

1. Project each observation onto the same physical Carrington longitude and
   sine-latitude pixel grid as its central reconstruction, using the HMI record
   time, observer metadata, image WCS and SunPy coordinate transforms.
2. Smooth the high-resolution detector image using a 3-detector-pixel Gaussian
   and bilinearly sample it. This reduces aliasing but does not exactly match
   the synoptic data's point-spread function or multi-hour time averaging.
3. Divide the observed line-of-sight field by `mu`, the cosine of the angle
   between the surface normal and line of sight, to estimate radial field. This
   assumes the field is radial and amplifies noise away from disk center.
4. Keep only pixels with `mu >= 0.8`, finite observation and original-map
   values, and finite values in **both** reconstructions. The snapshot has
   `QUALITY=0`. The identical intersection is used for all three scores.
   The 45-second measurement is an observational reference, not exact ground
   truth. It covers only a limited portion of the visible disk.

## Results on the shared mask

Residual = map minus HMI radial-field estimate. Bias, MAE and RMSE are in G;
correlation is Pearson's r. The two models use the same FITS-derived grid and
cubic-spline treatment; their rotation-rate expressions differ.

| CR | Compared pixels | Version | Bias | MAE | RMSE | Pearson r |
|---|---:|---|---:|---:|---:|---:|
| 2120 | 25,693 | Original | +0.073 | 9.018 | 23.821 | 0.825 |
| 2120 | 25,693 | Ananya expression | -0.337 | 12.104 | 48.209 | 0.369 |
| 2120 | 25,693 | Latitude corrected | +0.032 | 9.017 | 23.685 | 0.826 |
| 2122 | 25,705 | Original | +0.158 | 11.504 | 35.247 | 0.388 |
| 2122 | 25,705 | Ananya expression | +0.406 | 14.453 | 43.480 | 0.016 |
| 2122 | 25,705 | Latitude corrected | +0.194 | 11.728 | 35.166 | 0.383 |
| 2124 | 25,700 | Original | -0.074 | 14.824 | 43.171 | 0.693 |
| 2124 | 25,700 | Ananya expression | +0.040 | 23.888 | 73.642 | 0.150 |
| 2124 | 25,700 | Latitude corrected | -0.071 | 15.011 | 43.282 | 0.689 |

The corrected expression scores better than the Ananya initialization
expression in these three snapshots. Its scores are, however, close to the
unchanged map: for CR 2124 it is slightly worse than the baseline in both MAE
and RMSE, and for CR 2122 its MAE is slightly worse. This does not establish
that reconstruction improves the data relative to leaving the synoptic map
untouched. The latitude/colatitude mismatch is real, but the magnitude of its
impact cannot be generalized from three correlated maps and snapshots.

Each results JSON also records scores at `mu >= 0.9` and `mu >= 0.95` using a
shared mask. Scores vary as the evaluated region changes. Pixels are spatially
correlated; raw pixel counts are not independent sample counts, and no
uncertainty or significance claim follows from these numbers. Other limitations
include the unresolved timestamp discrepancy, LOS-to-radial assumption,
45-second versus 720-second noise, observer registration, interpolation,
missing data, solar evolution, and the HMI synoptic product's prior
`CARSTRCH=1` differential-rotation processing. The Ananya option reproduces
her rotation expression within this project's pipeline, not her entire original
implementation.

## Reproduce

Install project dependencies in the virtual environment and run from the repo
root. The validation command accepts any central CR with three consecutive
compatible inputs and an available HMI record. It queries JSOC and downloads the
observation if needed.

```powershell
.\.venv\Scripts\python.exe -m pip install -r SFT\requirements.txt
.\.venv\Scripts\python.exe SFT\validate_observations.py --rotation 2120
.\.venv\Scripts\python.exe SFT\validate_observations.py --rotation 2122
.\.venv\Scripts\python.exe SFT\validate_observations.py --rotation 2124
.\.venv\Scripts\python.exe SFT\prepare_viewer_data.py
```

Metrics JSON, arrays and diagnostic plots are saved in `SFT/validation_data`.
Large FITS, NPZ and PNG files are ignored by Git. The viewer export includes
observational scores only when its input maps and calculation scripts match the
saved result hashes. Its generated data file remains ignored by Git.
