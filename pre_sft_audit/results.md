# Calculated results

All eight primary variants and the untouched central map were evaluated at all three available epochs. The literal original block was also executed on each HMI triple, but has no finite results because of unmasked NaNs; its errors are unavailable, not zero. Thus all percentages labeled “vs 000” refer explicitly to the existing HMI-grid baseline.

Pooled over 77,098 pixels, 111 has RMSE **34.874 G**, versus 56.679 G for 000 and 34.994 G for central: 38.47% and 0.34% reductions respectively. Its pooled MAE is 11.836 G versus central's 11.782 G, so the MAE worsens by 0.46%. The small RMSE advantage is inconsistent across epochs and does not establish a general improvement.

## Actual observation epochs and common coverage

| CR | HMI T_OBS UTC | Crossing UTC | Offset (s) | N | Surface area (%) |
|---|---|---|---|---|---|
| 2120 | 2012-02-19T22:54:50.000 | 2012-02-19T22:54:54.688 | -4.69 | 25693 | 9.9132 |
| 2122 | 2012-04-14T13:39:13.000 | 2012-04-14T13:39:31.801 | -18.80 | 25705 | 9.9178 |
| 2124 | 2012-06-08T00:29:33.000 | 2012-06-08T00:29:36.874 | -3.87 | 25700 | 9.9159 |

Primary mu >= 0.8 samples about 9.9% of the whole solar surface (about one fifth of a hemisphere). Surface area is not projected image area. Every primary variant shares the exact same mask at a given CR. No observed pixel uses a neighboring rotation.

## CR2120: all primary runs

| Variant | Bias (G) | MAE (G) | RMSE (G) | r | RMSE gain vs 000 (%) | RMSE gain vs central (%) |
|---|---|---|---|---|---|---|
| central | 0.073 | 9.018 | 23.821 | 0.8254 | 50.59 | 0.00 |
| 000 | -0.337 | 12.104 | 48.209 | 0.3694 | 0.00 | -102.38 |
| 100 | 0.032 | 9.017 | 23.685 | 0.8265 | 50.87 | 0.57 |
| 010 | -0.080 | 11.733 | 41.155 | 0.4345 | 14.63 | -72.77 |
| 001 | -0.337 | 12.104 | 48.209 | 0.3694 | 0.00 | -102.38 |
| 110 | 0.096 | 9.102 | 23.968 | 0.8229 | 50.28 | -0.62 |
| 101 | 0.032 | 9.017 | 23.685 | 0.8265 | 50.87 | 0.57 |
| 011 | -0.080 | 11.733 | 41.155 | 0.4345 | 14.63 | -72.77 |
| 111 | 0.096 | 9.102 | 23.968 | 0.8229 | 50.28 | -0.62 |

## CR2122: all primary runs

| Variant | Bias (G) | MAE (G) | RMSE (G) | r | RMSE gain vs 000 (%) | RMSE gain vs central (%) |
|---|---|---|---|---|---|---|
| central | 0.158 | 11.504 | 35.247 | 0.3881 | 18.93 | 0.00 |
| 000 | 0.406 | 14.453 | 43.480 | 0.0159 | 0.00 | -23.36 |
| 100 | 0.194 | 11.728 | 35.166 | 0.3831 | 19.12 | 0.23 |
| 010 | 0.500 | 14.556 | 43.045 | 0.0293 | 1.00 | -22.12 |
| 001 | 0.406 | 14.453 | 43.480 | 0.0159 | 0.00 | -23.36 |
| 110 | 0.132 | 11.582 | 35.675 | 0.3671 | 17.95 | -1.21 |
| 101 | 0.194 | 11.728 | 35.166 | 0.3831 | 19.12 | 0.23 |
| 011 | 0.500 | 14.556 | 43.045 | 0.0293 | 1.00 | -22.12 |
| 111 | 0.132 | 11.582 | 35.675 | 0.3671 | 17.95 | -1.21 |

## CR2124: all primary runs

| Variant | Bias (G) | MAE (G) | RMSE (G) | r | RMSE gain vs 000 (%) | RMSE gain vs central (%) |
|---|---|---|---|---|---|---|
| central | -0.074 | 14.824 | 43.171 | 0.6930 | 41.38 | 0.00 |
| 000 | 0.040 | 23.888 | 73.642 | 0.1500 | 0.00 | -70.58 |
| 100 | -0.071 | 15.011 | 43.282 | 0.6894 | 41.23 | -0.26 |
| 010 | -0.380 | 21.333 | 70.464 | 0.1431 | 4.32 | -63.22 |
| 001 | 0.040 | 23.888 | 73.642 | 0.1500 | 0.00 | -70.58 |
| 110 | -0.066 | 14.824 | 42.440 | 0.7017 | 42.37 | 1.69 |
| 101 | -0.071 | 15.011 | 43.282 | 0.6894 | 41.23 | -0.26 |
| 011 | -0.380 | 21.333 | 70.464 | 0.1431 | 4.32 | -63.22 |
| 111 | -0.066 | 14.824 | 42.440 | 0.7017 | 42.37 | 1.69 |

`100` (latitude only) improves RMSE strongly relative to 000, but is close to central and worsens central-map MAE for CR2122/2124. `010` (sampling sign only) improves RMSE relative to 000 at each epoch but remains much worse than central. `001` (seam only) has zero observational effect. Adding the sign switch to latitude correction (`100 -> 110`) worsens CR2120/2122 RMSE, while improving CR2124. Enabling all switches does not dominate the individual latitude switch across all observed epochs. All conditional toggle differences in RMSE/MAE/r, including pair contexts, are in `factorial_effects.csv`; error metrics are nonlinear so pair effects need not add.

## Pooled comparison

| Variant | N | Bias (G) | MAE (G) | RMSE (G) | r |
|---|---|---|---|---|---|
| central | 77098 | 0.052 | 11.782 | 34.994 | 0.6759 |
| 000 | 77098 | 0.036 | 16.815 | 56.679 | 0.1949 |
| 100 | 77098 | 0.052 | 11.919 | 34.981 | 0.6739 |
| 010 | 77098 | 0.013 | 15.875 | 53.266 | 0.2045 |
| 001 | 77098 | 0.036 | 16.815 | 56.679 | 0.1949 |
| 110 | 77098 | 0.054 | 11.836 | 34.874 | 0.6767 |
| 101 | 77098 | 0.052 | 11.919 | 34.981 | 0.6739 |
| 011 | 77098 | 0.013 | 15.875 | 53.266 | 0.2045 |
| 111 | 77098 | 0.054 | 11.836 | 34.874 | 0.6767 |

Pooled scores concatenate residuals and recompute correlation, rather than average three correlations/RMSEs. Pixels and epochs are correlated; no significance, confidence interval or independent-sample claim is made.

## Forward-generated synthetic validation

Each source map is generated directly as F(l,t)=F0(l-w*t,latitude), with t=(180-l)/13.2+k*360/13.2 and k=-1,0,+1 for previous/current/next. Ground truth is F0 at t=0. The equal-area mock grid has 720 longitudes and 181 sine-latitude rows, including the equator and both hemispheres. Smooth harmonics cover broad spatial scales; signed localized features cover longitude seams and interior longitudes. Missing-data tests remove edge rows and an interior row segment. All synthetic variants share a common finite mask with central, exact and oracle fields. Exact-pole rates and 0/360 queries are tested separately because the mock source centers exclude pole/longitude endpoints.

RMSE in G (all eight variants and full metrics in `synthetic_metrics.csv`):

| Case | Central | 000 | 100 | 110 | 111 | 111 exact | Known-rate exact oracle |
|---|---|---|---|---|---|---|---|
| smooth_rotation | 5.0465 | 23.7855 | 8.52702 | 3.6901 | 0.659735 | 2.20592e-07 | 2.20592e-07 |
| seam_features | 6.91651 | 10.8158 | 7.87847 | 6.80722 | 2.06616 | 5.28427e-06 | 5.28427e-06 |
| missing_data | 6.95512 | 10.8757 | 7.92244 | 6.84522 | 2.07769 | 3.31349e-05 | 3.31349e-05 |
| stationary_control | 0 | 22.9376 | 5.0465 | 5.28164 | 5.28164 | 5.76073 | 4.8263e-15 |
| opposite_rotation_control | 5.28164 | 22.4375 | 0.997637 | 9.03334 | 9.29625 | 9.52727 | 2.67806e-07 |
| evolving_control | 7.24377 | 10.5312 | 8.09945 | 8.00804 | 3.34385 | 2.6591 | 2.6591 |

The oracle uses the *actual* synthetic rate, independent of which rate the eight fixed-model variants assume. In the stationary control, central is exact while every nonzero-rate model damages it. Reversing the true trajectory's rate favors a different fixed-model sign; the known-rate exact oracle remains accurate. A uniform time-tagged evolving component cannot be removed by any longitude remapping, leaving a nonzero oracle residual. These controls show what the geometry can and cannot establish; synthetic scores are not observational evidence.

## Exact inverse, interpolation and epoch sensitivity

RMSE in G at mu >= 0.8 on a common sensitivity mask:

| CR | 111 cubic first order | 111 cubic exact | 111 linear | 111 exact local rate/epoch |
|---|---|---|---|---|
| 2120 | 23.968045 | 23.965834 | 23.479264 | 23.965325 |
| 2122 | 35.674908 | 35.671372 | 34.607618 | 35.672639 |
| 2124 | 42.440401 | 42.445125 | 40.968096 | 42.448213 |

| CR | Largest exact vs first-order query difference (deg) | Full common-map field RMSE difference (G) |
|---|---|---|
| 2120 | 19.758 | 8.279 |
| 2122 | 19.758 | 7.791 |
| 2124 | 19.758 | 7.130 |

The exact inverse is material over the full latitude range even though its near-center observational scores barely change. Linear interpolation gives smaller snapshot RMSE here, plausibly by damping subpixel/strong-field structure; it changes the interpolation treatment and does not prove a better physical reconstruction. The primary comparison retains cubic splines. No interpolation or rate was tuned to the reference.

Tighter mu cuts change the sampled magnetic structures. RMSE in G, central / 111:

| CR | mu >= 0.9 | mu >= 0.95 |
|---|---|---|
| 2120 | 25.024 / 25.402 | 12.205 / 11.929 |
| 2122 | 21.396 / 21.099 | 10.132 / 10.019 |
| 2124 | 45.346 / 44.667 | 42.019 / 41.057 |

## Investigation of resolution and registration discrepancies

The raw snapshot has a different spatial/temporal footprint from a boxcar-reduced synoptic map. Holding every model field fixed, detector Gaussian sigma is varied on a common mask. RMSE in G (central / 111):

| CR | sigma=3 detector pixels | sigma=6 | sigma=12 |
|---|---|---|---|
| 2120 | 23.821 / 23.968 | 20.158 / 20.271 | 21.294 / 21.282 |
| 2122 | 35.247 / 35.675 | 30.055 / 30.228 | 25.774 / 25.525 |
| 2124 | 43.171 / 42.440 | 37.261 / 36.465 | 34.563 / 33.842 |

A separate central-map scan samples source longitude offsets [-1,-0.5,0,0.5,1] degrees and latitude offsets [-0.5,0,0.5] degrees, comparing all 15 with one mask. The grid minimum is an **in-sample diagnostic**, not an independently established WCS correction:

| CR | Nominal central RMSE (G) | Grid-min RMSE (G) | Source query offset lon / lat (deg) |
|---|---|---|---|
| 2120 | 23.821 | 23.821 | 0.0 / 0.0 |
| 2122 | 35.247 | 35.143 | 0.0 / 0.5 |
| 2124 | 43.171 | 43.171 | 0.0 / 0.0 |

These sensitivities quantify how resolution, sampling and subdegree alignment can change errors without changing the rotation physics. A single fixed Gaussian does not reproduce the varying synoptic pixel footprint or multi-hour averaging; optimizing registration on the scored image would make an optimistic accuracy comparison. No grid-min offset or alternative sigma is applied to any primary result. Full scores are in `smoothing_sensitivity.csv` and `registration_offset_sensitivity.csv`.

## Longitude/seam sources and whole-map changes

CR2120 geometric source queries (all target cells, including unsupported/NaN queries). Counts and **physical area** for each CR and valid-source pixels are fully recorded in `longitude_sources.csv`:

| Variant | Previous count | Current count | Next count | Neighbor area (%) | Finite output pixels |
|---|---|---|---|---|---|
| 000 | 32 | 259132 | 36 | 0.0261 | 257018 |
| 100 | 314 | 258554 | 332 | 0.2492 | 256844 |
| 010 | 17876 | 223372 | 17952 | 13.8236 | 256434 |
| 001 | 36 | 259132 | 32 | 0.0261 | 257018 |
| 110 | 7966 | 243218 | 8016 | 6.1646 | 256594 |
| 101 | 332 | 258554 | 314 | 0.2492 | 256844 |
| 011 | 17952 | 223372 | 17876 | 13.8236 | 256434 |
| 111 | 8016 | 243218 | 7966 | 6.1646 | 256594 |

`map_differences.csv` contains every pair of central/primary variants on the same full-map finite intersection; these are map **differences**, not observational errors. Source query fractions can differ from valid-contribution fractions because of missing northern rows and finite spline support. Source area includes all geometric query cells, and the CSV separately counts actually finite source values. Plots show each variant's seam selection, not only the preferred candidate.

## Original-source and grid checks

Literal original output has 0 finite pixels for all three supplied HMI triples. A finite-array source-execution test agrees with an independent vectorized original-grid implementation at 1e-12 tolerance. The primary physical-grid 000 and existing reconstruction helper agree exactly, and prior arrays agree within 1e-9 G. Previously reported 000/100 observational metrics and masks are reproduced.

The original grid spans 0..360 degrees with both endpoints and arcsin(linspace(-1,1,ny)); HMI uses pixel centers from its metadata (for CR2120, longitude approximately 0.3..359.8 degrees). A separate original-grid diagnostic omits incomplete rows explicitly, reconstructs on the old grid, then resamples to the physical grid. It differs appreciably at individual pixels:

| CR | Diagnostic RMSE vs observation (G) | Diagnostic map RMSE vs 000 (G) | Max abs map difference (G) |
|---|---|---|---|
| 2120 | 48.834 | 5.443 | 197.024 |
| 2122 | 43.464 | 3.595 | 76.038 |
| 2124 | 73.501 | 5.568 | 109.222 |

This extra resampling and row omission are explicitly outside the three tested switches. Treating that diagnostic, the literal original, and HMI-grid 000 as identical would conceal a reproducibility problem.

## Representative identical pixels

Values in G; longitude/latitude are actual grid centers. Every row is valid for all primary variants and the observation. Selection uses five fixed geometric targets plus strongest observed positive/negative pixels; it is not chosen by which variant wins. `sample_br.csv` includes all variants and 111 exact.

| CR | Longitude | Latitude | mu | Reference | Central | 000 | 100 | 111 |
|---|---|---|---|---|---|---|---|---|
| 2120 | 179.80 | -0.16 | 0.993 | -0.30 | -0.14 | -0.44 | -0.12 | -0.15 |
| 2120 | 175.30 | 16.29 | 0.914 | 1647.04 | 1420.12 | 530.79 | 1415.56 | 1424.59 |
| 2120 | 179.30 | 14.97 | 0.927 | -1581.97 | -1547.44 | -1328.86 | -1547.95 | -1546.93 |
| 2122 | 179.80 | -0.16 | 0.995 | 7.79 | 17.19 | 17.51 | 17.15 | 17.23 |
| 2122 | 203.80 | 6.22 | 0.894 | 1268.15 | 512.28 | -16.29 | 672.16 | 252.95 |
| 2122 | 210.30 | 5.90 | 0.843 | -1004.04 | 4.91 | -9.91 | 1.51 | 4.30 |
| 2124 | 179.80 | -0.16 | 1.000 | -2.24 | 0.55 | 0.59 | 0.55 | 0.55 |
| 2124 | 199.30 | -16.63 | 0.902 | 1801.72 | 1831.17 | -0.98 | 1820.09 | 1835.88 |
| 2124 | 202.30 | 15.96 | 0.890 | -1043.42 | -149.61 | -49.33 | -153.72 | -145.58 |

## Limitations that remain

- Only three near-center snapshots, covering about 9.9% of the Sun per epoch, are scored. Far-side, polar and seam accuracy are not observationally validated.
- LOS/mu assumes radial fields; snapshot noise, horizontal fields, spatial correlation, temporal evolution and synoptic averaging remain. The 3-pixel detector Gaussian does not match the synoptic spatial/temporal kernel exactly.
- The seven unique HMI maps are already Carrington-stretched (CARSTRCH=1); exact historic processing and per-pixel temporal weights are unavailable. A central-meridian-column model is an approximation.
- Header T_ROT, SunPy ephemeris and HMI record-derived crossings differ. The small empirical rate/epoch sensitivity does not explain the full discrepancy.
- Original MDI FITS are absent; the full original research run cannot be reproduced or scored. No full SFT evolution or SFT/PFSS accuracy claim was attempted.
- The exact inverse assumes constant observer meridian rate and prescribed latitude-dependent feature rotation. No emergence, diffusion, meridional transport, uncertainty model or instrument cross-calibration is inferred from these three snapshots.

Raw-byte FITS checksums pass for all 221 maps, including every audited input. Astropy's header-normalization path reports checksum failures for 135 unrelated maps with nonstandard `nan` cards; direct raw-byte one's-complement sums show these are parsing/normalization artifacts, not evidence of damaged files. No header was written back. `check_fits.py` and `evidence/raw_fits_checksums.json` reproduce this investigation.
