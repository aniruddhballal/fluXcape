# CR 2120 observational comparison

This compares the existing two reconstructions with a separately acquired HMI
45-second line-of-sight magnetogram, rather than calling the CR 2120 synoptic
map ground truth. The three existing input maps and reconstruction calculations
are unchanged. The comparison tests these particular implementations and one
snapshot; it is not a validation of all dates or of Ananya's entire pipeline.

## Reference time and observation

The reconstruction defines its reference at Carrington longitude 180 degrees.
There is **not yet a uniquely established exact timestamp** for that reference:

- The CR 2120 synoptic FITS header gives `T_ROT = 2012-02-19 22:51:59 TAI`
  (22:51:25 UTC), described by JSOC as the rotation middle time.
- In quality-zero HMI 45-second records, `CRLN_OBS` is 180.000717 degrees at
  `T_OBS = 22:55:24 TAI` and 179.993835 degrees at `22:56:09 TAI`. Linear
  interpolation gives **22:55:28.688 TAI / 22:54:54.688 UTC** for the crossing
  in that record's longitude convention. This is an estimate, not an exact
  exposure time or a convention-independent timestamp.
- For comparison, SunPy's default Earth-observer
  `carrington_rotation_time(2120.5)` gives **22:47:46.384 TAI / 22:47:12.384
  UTC**. This and the header/record times are not interchangeable. The source
  of the several-minute discrepancy, including observer and light-time
  conventions, has not been resolved. SunPy documents the options used in its
  [L0 calculation](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.L0.html).

We select the `hmi.M_45s` record with `T_REC = 2012.02.19_22:55:30_TAI`,
`T_OBS = 2012.02.19_22:55:24_TAI` (22:54:50 UTC), quality zero, and
`CRLN_OBS = 180.000717` degrees. Its observation time is about 4.69 seconds
before the interpolated crossing under the HMI record convention. The image is
an observation with a finite temporal response, not a simultaneous measurement
of the entire Sun.

The JSOC segment and its record metadata are kept separately, because the
archive's compressed image segment does not contain the full record header.
The exact source URL and SHA-256 are recorded in
`validation_data/cr2120_observational_metrics.json`. The 45-second and
720-second HMI line-of-sight products use separate cameras and measurements,
according to the [HMI dataset description](https://spase-metadata.org/NASA/NumericalData/SDO/HMI/LOS_Magnetogram/PT720S.html).
They still share the same instrument, solar scene, and potential systematic
errors. The synoptic map is made from 720-second observations collected over
many days, with each longitude averaged over a time window around central
meridian passage. See the [NASA synoptic chart description](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field).

## Coordinates and comparison mask

1. Use the original maps' pixel grid and the observation's `T_OBS`,
   `CRLN_OBS`, `CRLT_OBS`, `DSUN_OBS`, solar radius and image WCS metadata.
   The observer is anchored to the HMI `CRLN_OBS` value before transforming
   Carrington surface positions to image-plane positions with SunPy.
2. For observational registration, use the **absolute value of the synoptic
   header's `CDELT1`**. SunPy documents that HMI synoptic data can require a
   positive longitude step even when their header has a negative step; see
   [SunPy's HMI synoptic map notes](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html).
   Our current reconstruction functions still use the negative header value.
   They were not changed, as requested. This mismatch is a serious limitation
   when interpreting the reconstruction and its shifts.
3. Smooth the HMI detector image with a Gaussian of sigma 3 detector pixels,
   track missing-pixel weights, and sample it bilinearly at projected map
   positions. This is a simple anti-aliasing choice, not an exact match to the
   synoptic product's spatial point-spread function or temporal averaging.
4. Convert line-of-sight field to an approximate radial field by dividing by
   `mu`, the cosine of the angle between the outward surface normal and the
   observer direction. This assumes the field is radial. Only use `mu >= 0.8`,
   a quality-zero record, finite observation neighbourhoods, and pixels where
   the original map **and both reconstructions** are finite. The 25,693 pixels
   are the same for both scores. This is roughly the central portion of the
   visible disk; pixels in the far hemisphere are not observationally tested.

## Results

The residual is `reconstruction - HMI radial estimate`. Correlation is the
Pearson correlation across the common mask. All field differences are in G.

| Version | Pixels | Bias | MAE | RMSE | Pearson r |
|---|---:|---:|---:|---:|---:|
| Ananya rotation expression | 25,693 | -0.337 | 12.104 | 48.209 | 0.369 |
| Latitude-corrected expression | 25,693 | +0.032 | 9.017 | 23.685 | 0.826 |

On this snapshot and mask, the latitude-corrected version has lower MAE and RMSE
and higher correlation. For context only, the unmodified central synoptic map on
the same mask has MAE 9.018 G, RMSE 23.821 G and r 0.825. The fixed
reconstruction's scores are therefore very close to leaving the central map
unchanged in this observed region.

The ranking is unchanged in this one snapshot when tightening the shared mask:

| Minimum mu | Pixels | Ananya MAE / RMSE / r | Fixed MAE / RMSE / r |
|---|---:|---:|---:|
| 0.80 | 25,693 | 12.104 / 48.209 / 0.369 | 9.017 / 23.685 / 0.826 |
| 0.90 | 12,851 | 13.176 / 57.727 / 0.444 | 8.471 / 25.285 / 0.890 |
| 0.95 | 6,416 | 6.771 / 15.066 / 0.102 | 5.584 / 12.262 / 0.434 |

These tests do not resolve the longitude-sign and reference-time discrepancies,
or do they establish statistical significance across independently sampled
solar regions. Spatially adjacent pixels are correlated. Changes in observation
noise, HMI camera calibration, line-of-sight projection, temporal evolution,
the synoptic-map processing (including `CARSTRCH=1`), missing data and
interpolation can affect all scores. In particular, choosing a different
reference convention or comparing more rotations could change the outcome.
The current result is evidence for this implementation on this limited test,
not proof that either formula is physically correct or that reconstruction is
better than the original synoptic map.

## Reproduce

Install the project dependencies in the virtual environment, then from the
repository root run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r SFT\requirements.txt
.\.venv\Scripts\python.exe SFT\validate_observations.py
.\.venv\Scripts\python.exe SFT\prepare_viewer_data.py
```

The validation script queries JSOC to derive the crossing and observation,
downloads the image if missing, and writes the metrics JSON, arrays and a
comparison PNG under `SFT/validation_data`. Large FITS, NPZ and PNG files are
ignored by Git. The viewer export only includes the saved observational scores
when hashes of the input maps and calculation scripts match the validation;
otherwise it prompts for validation to be rerun. The viewer data file remains
ignored by Git and must be generated separately for a static deployment.
