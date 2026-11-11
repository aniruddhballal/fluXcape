# Pre-SFT reconstruction audit: complete research record

Consolidated on **2026-11-11 (Asia/Calcutta)** from the completed audit and its saved results. This file sits at the repository root, outside `pre_sft_audit/`, so it remains available if that implementation folder is removed. This consolidation adds no scientific runs, observations, measurements, or new issue verdicts.

**Component status update — 2026-11-11:** The React viewer at
`my work/SFT/viewer/` (historically `SFT/viewer/`) and the exporter
`prepare_viewer_data.py` are **deleted**, including the app's dependencies,
build outputs and generated map JSON. Every reference to the viewer, its
exporter, React/Vite setup or viewer launch commands in this record is a
historical reference to a deleted component, not a current instruction.
Archived text payloads and their original hashes remain unchanged as evidence.
The reconstruction, shared FITS inputs and standalone observation validator
remain available; the current validator no longer requires the deleted exporter.
Historical recovery/reproduction examples may restore or depend on deleted
components and should be read in that context.

## 1. Intent and the question we were trying to answer

The work examined the three-map synoptic magnetic-field reconstruction **before surface flux transport (SFT)**. A synoptic map assembles observations from different times across a Carrington rotation. The reconstruction attempts to sample three neighboring rotation maps to estimate the surface field at one reference epoch.

We wanted to establish whether three suspected problems were genuine, measure each change independently and together, and ask whether any reconstruction agrees with observations better than **using the central synoptic map unchanged**. The three questions concerned latitude versus colatitude, the sign of backward longitude sampling, and which neighboring rotation supplies a longitude that crosses a seam.

Correcting an internal coordinate inconsistency and improving observational accuracy are separate claims. This audit was designed to distinguish them. It did not evolve the SFT model, validate the full original research pipeline, or validate a simultaneous full-Sun magnetic map.

The user required preservation of everything in `ananya_research_work-main/` and isolation of the implementation in `pre_sft_audit/`. Historical research instructions suggesting edits were treated as document contents, not permission to change the research. The saved audit preservation check found all 281 pre-existing project files unchanged, including 13 files in the protected research tree.

## 2. What we did and what the findings mean

We inventoried the repository, inspected the original reconstruction and existing validation infrastructure, checked FITS coordinates and chronology, executed the literal original reconstruction block without running SFT evolution, and built eight combinations of three independent switches. We compared them with the untouched central map on synthetic fields and three real HMI snapshot references. We also checked exact versus first-order inversion, interpolation order, observation epoch/rate conventions, smoothing, coordinate registration, missing data, and source selection at rotation seams.

The main findings are:

- **Latitude/colatitude mismatch: confirmed in source.** The initialization supplies latitude to a colatitude rotation law. The equatorial rate changes from -3.74 to +0.18 degrees/day when that mismatch is corrected.
- **Sampling sign: verified under the HMI central-meridian-column time model.** The inverse must be derived from the feature trajectory. The proposed minus sign is its first-order approximation; exact inversion can differ materially at high latitude. Applicability to absent original MDI data and exact processed-product temporal kernels remains conditional.
- **Neighboring rotation at a seam: verified under HMI chronology.** A source query below 0 degrees uses the next CR, and a query above 360 degrees uses the previous CR. The three observed masks contain no seam-source pixels, so they cannot test that change observationally.
- **Observational improvement over an untouched map: mixed and small.** The all-switch reconstruction substantially outperforms the existing HMI-grid Ananya-expression baseline, but does not consistently beat the central map. Pooled RMSE improves by approximately 0.34% relative to central, while pooled MAE worsens by approximately 0.46%.
- **A faithful original research-run comparison is unavailable.** The original MDI FITS inputs are missing. Supplying the available HMI triples to the literal original reconstruction yields no finite values because unmasked NaNs propagate through its global cubic splines. That outcome is not a zero error, and the numerical `000` baseline is explicitly a separate HMI-grid implementation.

The scientific takeaway is that the coordinate mismatch is real, but fixing the reconstruction mathematics has **not established a general observational advantage over leaving the central map alone**. The snapshots test about 9.9% of the solar surface per epoch; they do not validate the far side, poles, seams, or full SFT evolution.

## 3. How to use this single file

Quick navigation: [methods](#5-comparison-method-and-fairness), [issue verdicts](#6-scientific-questions-derivations-and-issue-verdicts), [numerical findings](#7-numerical-findings-and-their-interpretation), [files and recovery](#11-file-map-what-can-be-removed-and-recovery), [full-precision table index](#14-full-precision-table-index-and-reading-guidance), and [complete text archive](#16-verified-text-archive).

The narrative below preserves the methods, derivations, interpreted results, limitations, and repository context. The appendices retain the original full-precision CSV tables, observation/header evidence, environment, input hashes, test logs, and audit text/source files. Each archived text file has an explicit original path and byte hash, and can be found by searching for its filename. References such as `metrics.csv` or `evidence/cr2120.json` are historical paths whose text is embedded here; reading the record does not require those files to remain on disk.

This file is a self-contained **research and text-implementation record**, not a binary data archive. It does not embed the FITS observations, NPZ pixel arrays, PNG plots, or ZIP bundle. Their paths, sizes, and hashes are listed below. The committed plots and implementation can be recovered from Git; ignored NPZ arrays require the retained original inputs and a rerun. This distinction matters if future work needs pixel-level recalculation rather than the saved scalar/tabular results.

No existing files were deleted or moved to create this record. Removing `pre_sft_audit/` later would remove its local generated files; it would not remove the original `SFT/` inputs or protected research tree. The Git recovery and text-extraction instructions below explain how to reconstruct the audit if needed.

---

<!-- CONSOLIDATED CONTENT AND VERIFIED TEXT ARCHIVE FOLLOW -->

## 4. Inputs, epochs, baselines, and variants

The three experiments used overlapping triples of seven unique **HMI** small synoptic maps. There were nine input uses, not nine different source FITS files. All selected maps are 720 columns by 360 rows. Carrington rotation (CR) is the rotation index; LOS is line-of-sight; Br is the estimated radial magnetic field; mu is the finite-distance surface-normal/LOS cosine. A gauss (G) is also Mx/cm^2 for these field values.

| Central CR | Previous / current / next | Raw HMI 45-second observation and metadata stem |
|---|---|---|
| 2120 | 2119 / 2120 / 2121 | hmi.M_45s.20120219_225530_TAI |
| 2122 | 2121 / 2122 / 2123 | hmi.M_45s.20120414_133945_TAI |
| 2124 | 2123 / 2124 / 2125 | hmi.M_45s.20120608_003000_TAI |

- Synoptic maps: `../SFT/fits_files/720x360/hmi.Synoptic_Mr_small.{2119..2125}.fits` (seven unique files; triples centered on 2120, 2122 and 2124).
- Raw HMI 45-second compressed FITS and separate `.jsoc.json` metadata: `../SFT/validation_data/hmi.M_45s.20120219_225530_TAI.*`, `20120414_133945_TAI.*`, `20120608_003000_TAI.*`.
- Prior `cr2120`, `cr2122`, `cr2124` observational metrics JSON and arrays NPZ in that directory, used as reproducibility controls. Raw FITS are freshly projected; cached observations are not substituted.
- Existing helpers: `../SFT/synoptic_reconstruction.py`, `../SFT/validate_observations.py`. Original reference block: `../ananya_research_work-main/SFT/SFT.py` lines 18–21 and 83–117, executed via selected AST nodes with arrays supplied in memory, never imported as a full solver.
- All input SHA-256 values: `original_manifest.json`; observation metadata, hashes, headers and timing: `evidence/cr*.json`. `available_inputs.json` inventories all 221 available synoptic FITS and possible complete triples.

The original hard-coded `CR_MDI2095.fits`, `CR_MDI2096.fits`, `CR_MDI2097.fits` are absent. The seven files above are HMI data, not replacements proven equivalent to those MDI products. Full-disk observations away from the three selected epochs and per-pixel synoptic observation-time/weight maps are unavailable. These are explicit limits, not fabricated inputs.

### Source-map chronology from the actual headers

| CR | T_START (TAI) | T_ROT (TAI) | T_STOP (TAI) | CARSTRCH | Finite pixels (header DATAVALS) |
|---|---|---|---|---|---|
| 2119 | 2012.01.09_22:35:48_TAI | 2012.01.23_14:40:39_TAI | 2012.02.06_06:47:12_TAI | 1 | 257546 |
| 2120 | 2012.02.06_06:47:12_TAI | 2012.02.19_22:51:59_TAI | 2012.03.04_14:50:52_TAI | 1 | 257040 |
| 2121 | 2012.03.04_14:50:52_TAI | 2012.03.18_06:39:38_TAI | 2012.03.31_22:14:46_TAI | 1 | 257040 |
| 2122 | 2012.03.31_22:14:46_TAI | 2012.04.14_13:34:06_TAI | 2012.04.28_04:37:05_TAI | 1 | 257447 |
| 2123 | 2012.04.28_04:37:05_TAI | 2012.05.11_19:24:54_TAI | 2012.05.25_10:00:13_TAI | 1 | 258280 |
| 2124 | 2012.05.25_10:00:13_TAI | 2012.06.08_00:26:50_TAI | 2012.06.21_14:49:05_TAI | 1 | 258752 |
| 2125 | 2012.06.21_14:49:05_TAI | 2012.07.05_05:11:27_TAI | 2012.07.18_19:38:00_TAI | 1 | 258193 |

Raw snapshot filenames append `.magnetogram.fits` to the stem above; separate metadata filenames append `.jsoc.json`. Their complete JSOC keyword values, raw FITS headers, prior report, bracketing records, and hashes are retained in the archived `evidence/cr*.json` text.

### The three independent bits

| Variant | fix_latitude | invert_sample_shift | reverse_cr_seam | Interpretation |
|---|---|---|---|---|
| central | N/A | N/A | N/A | Untouched central FITS pixel array; no reconstruction |
| 000 | off | off | off | Existing HMI-grid Ananya-expression baseline |
| 100 | on | off | off | Latitude switch only |
| 010 | off | on | off | Sampling-sign switch only |
| 001 | off | off | on | Chronological seam switch only |
| 110 | on | on | off | Latitude plus sampling sign |
| 101 | on | off | on | Latitude plus seam |
| 011 | off | on | on | Sampling sign plus seam |
| 111 | on | on | on | All three switches; still first-order sampling |

Suffix `_exact` enables the separately tested analytic inverse. Suffix `_linear` changes spline degree to one. `111_epoch_rate_exact` uses the selected-image longitude and the locally inferred central-meridian rate. Synthetic `known_rate_exact` is an oracle using the actual rate used to generate that case; it is not an additional fitted observational model.

## 5. Comparison method and fairness

Bits in order are `fix_latitude`, `invert_sample_shift`, `reverse_cr_seam`. The eight runs are `000`, `100`, `010`, `001`, `110`, `101`, `011`, `111`. `central` is the actual unresampled input array. `000` is **the existing repository's HMI-grid Ananya-expression baseline**, not a claim to reproduce the entire original research pipeline. See `issue_verdicts.md` for the literal-original failure and original-grid sensitivity.

Primary runs use cubic `RectBivariateSpline` in latitude degrees and longitude degrees, no smoothing on synoptic arrays, identical 13.2 deg/day time convention, 180-degree reference, physical HMI positive longitude step and the existing whole-incomplete-row omission. Source index 0/1/2 means previous/current/next rotation. Splines never extrapolate outside retained coordinate support. Omission of an interior incomplete row can interpolate across that row; no zeros are treated as missing measurements. Synthetic masks explicitly exclude nonfinite central input pixels.

Exactly 0 and 360 degrees stay in the current rotation, preserving the research block's strict `<0`/`>360` comparisons. The existing project helper instead uses `>=360` and modulo; no primary HMI query lands at exactly 360, so baseline reproduction is unaffected. HMI source centers do not include 0 or 360; those unsupported exact endpoint queries remain NaN. No periodic padding, gap filling or interpolation-order change is hidden in a switch.

All primary variants and central use the same intersection mask: finite reference and every map, mu >= 0.8. HMI LOS data are smoothed once with sigma=3 detector pixels, bilinearly sampled, and divided by finite-distance mu. Snapshot QUALITY must be zero, and smoothed valid weight must be >=0.999. Observation processing is identical for every variant. A second, analytic sphere/perspective projection independently checks the reused SunPy frame transformations.

Bias = mean(model-reference), MAE = mean absolute residual, RMSE = sqrt(mean squared residual), all in G; r is Pearson correlation. CSVs also include median and 95th percentile absolute error. Improvements are `100*(1-error_variant/error_baseline)`; negative means worse. No percentage is produced for a zero baseline error. Physical surface-area fractions use clipped sine-latitude cell edges and longitude width divided by 4*pi; primary errors are unweighted pixel means on an almost equal-area grid. Pooled scores concatenate valid pixels from the three epochs; they are not uncertainty estimates.

Separate sensitivities use exact inverse sampling, linear interpolation, tighter mu cuts, a locally inferred central-meridian rate/selected-image epoch, the old dimension-derived coordinate grid, detector Gaussian sigma 3/6/12, and a fixed small registration-offset grid. Every sensitivity uses a common mask within its own comparison. Exact inversion is not silently folded into the primary eight runs. Smoothing/registration diagnostics do not choose parameters for the primary metrics.

For the exact grid calculation used here, physical longitude is `(CRVAL1 + (x+1-CRPIX1)*abs(CDELT1)) mod 360`; latitude is `asin(CRVAL2 + (y+1-CRPIX2)*CDELT2)` in degrees. The archived HMI negative longitude-step header is interpreted with the documented positive-array convention. For central CR2120, header CRVAL1 is 763020 degrees, CRPIX1 is 360.4, CDELT1 is -0.5 degree/pixel, CRPIX2 is 180.5, CRVAL2 is zero, and CDELT2 is 0.005556 in sine latitude. The physical longitude centers are approximately 0.3 to 359.8 degrees. The original dimension-derived grid has different endpoints and latitude registration.

The observational projection uses the separate HMI metadata (including the selected observation time, observer longitude/latitude, Sun-observer distance, solar radius, and detector WCS). Source and observer geometry, radial conversion, interpolation, and the valid mask are identical for all primary variants at each epoch. Residuals are model minus the HMI radial estimate. Improvement percentages are relative changes in error magnitudes, not errors expressed in percent of magnetic field. A small bias alone does not establish accurate reconstruction.

## 6. Scientific questions, derivations, and issue verdicts

**Issue 1 is a confirmed coordinate inconsistency. Issues 2 and 3 are confirmed sampling/chronology inconsistencies under the verified HMI longitude convention and a central-meridian-column time model. Their applicability to the unavailable MDI inputs and the full processed HMI observation kernels remains conditional. Neither mathematical correction establishes better observational accuracy.**

### 1. Latitude versus colatitude — confirmed in source

`ananya_research_work-main/SFT/SFT.py:18–21` defines omega using cosine of colatitude and returns radians/second. Line 88 constructs `theta_original=arcsin(linspace(-1,1,ny))`, which is latitude. Line 101 supplies it unchanged to omega. The later velocities at lines 256 and 260 use actual colatitude. The inconsistency is internal to the source, independent of HMI metadata.

The audit changes only cosine to sine when this bit is enabled. It does not also convert the argument. Rates in degrees/day:

| Latitude (deg) | Original call | Latitude-corrected |
|---|---|---|
| 0 | -3.74000 | 0.18000 |
| 30 | -2.45625 | -0.49625 |
| 60 | -0.49625 | -2.45625 |
| 90 | 0.18000 | -3.74000 |
| -90 | 0.18000 | -3.74000 |

Tests cover signed northern/southern latitudes and exact pole rates. This confirms the coordinate inconsistency, not the physical optimality of the adopted coefficients.

### 2. Signed time offset and backward sampling — confirmed under stated HMI column-time model

Use phi for a desired target longitude at reference time t0, s for a source longitude on an **unwrapped chronological mosaic**, and w for a feature's physical Carrington longitude rate in deg/day (positive toward increasing longitude). SunPy documents the HMI positive array-longitude step despite negative archived CDELT1; the installed source was also read. The reflected-header observational control strongly favors the positive orientation. [SunPy HMI convention](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html)

For the same observer, L_CM(t)=180-Omega0*(t-t0) locally, so a central-meridian column at s has tau=t_obs-t0=(180-s)/Omega0. Thus Ananya's Delta_t_A=(phi-180)/Omega0 is reference-minus-observation time evaluated at the *target* longitude, not a forward elapsed time. Increasing physical Carrington longitude is the prograde direction. The SFT velocity definition uses positive omega for this direction; changing the physical meaning of omega would change the assumed trajectory.

A feature at phi at t0 lies at phi+w*tau when the source column observes it. Backward **sampling**, as implemented by evaluating a spline at each target coordinate, therefore requires

```
s = phi + w*(180-s)/Omega0
s_exact = 180 + (phi-180)/(1+w/Omega0)
s_first_order = phi - (w/Omega0)*(phi-180)
```

The original plus-sign expression is not this inverse. It can resemble a forward coordinate transport, but the code assigns `B_target(phi)=B_synoptic(s)`; that is a backward sampler. For a feature at phi=90 deg with w=+1 deg/day, solving its trajectory gives observation time (180-90)/(13.2+1)=6.3380 days and source longitude 96.3380 deg. The minus candidate gives 96.8182 deg to first order; the original plus expression gives 83.1818 deg. Tests solve intersections in time independently for positive, zero and negative w and for endpoints/interior longitudes.

The first-order error is `s_first_order-s_exact=-(phi-180)*(w/Omega0)^2/(1+w/Omega0)`. It is material at high latitudes, where |w/Omega0| is not tiny. Synthetic forward maps recover the reference to interpolation precision with the exact inverse; wrong-rate, stationary and evolving controls do not falsely validate the candidate. See numeric tables in `results.md`.

This verdict is conditional on representing the processed product as columns at their effective central-meridian epochs and on omega being the feature's Carrington rate. Per-pixel temporal kernels are absent. The sign is derived, not chosen to minimize snapshot error: near-center observational results do **not** consistently prefer the inverse-sign candidate over the opposite sign.

### 3. Neighbor-CR seam choice — confirmed for verified HMI chronology; not identifiable observationally here

Increasing CR number is later time. Within one rotation the observer central meridian moves from near 360 toward 0. The current unwrapped interval is [0,360], previous rotation is [360,720], and next rotation is [-360,0]. Therefore:

| Source query | Physical wrapped longitude | Chronological source |
|---|---|---|
| s < 0 | s + 360 | Next CR |
| 0 <= s <= 360 | s | Current CR (endpoint policy above) |
| s > 360 | s - 360 | Previous CR |

Original source lines 103–113 choose the opposite neighbor for out-of-range queries. SunPy rotation-time calculations, local L0 evaluations and all nine input header times independently establish the ordering; the underlying rotation-number definition also increases in time. [SunPy Carrington time definition](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.carrington_rotation_time.html)

A synthetic tracer whose field equals its observation time checks the two neighbor assignments without using the feature-rotation formula. Original selection associates a wrapped seam query with a time two rotations away from the intended branch, a 54.54545-day error in the constant-13.2 model. Source-count tables show how the sampling-sign switch changes which rows cross seams. Exact endpoint tests preserve deterministic strict comparisons.

All observed masks lie near longitude 180; every included pixel in every variant samples the central CR. Consequently 000=001, 100=101, 010=011 and 110=111 on these masks. This is **lack of observational sensitivity**, not evidence that both seam conventions are physically valid. No full-Sun seam accuracy claim follows from these snapshots.

### Baseline distinction and missing data

The original reconstruction block is executed literally through AST extraction, keeping its radians, dimension-derived coordinates, cubic splines and strict seam tests. Supplying each available HMI triple yields **zero finite output pixels**: NaN northern rows propagate through global cubic spline coefficients. No original missing pixels are filled. Hard-coded original MDI FITS are unavailable, so original research-run scores cannot be recovered.

`000` reproduces the existing HMI validator baseline to numerical precision, with its separate FITS-derived grid and row omission. The saved prior arrays differ by at most about 1e-10 G because the equivalent degree/radian arithmetic differs at floating-point precision. A finite random-array test independently confirms the source block versus vectorized original-grid arithmetic. An explicitly labeled row-omitted old-grid diagnostic is resampled to the physical grid and quantified separately; it is not called an untouched original method.

### Prior processing, time conventions and scope

All seven selected synoptic headers contain CARSTRCH=1 and DIFROT_A/B/C=13.562/-2.04/-1.4875. The archived JSOC synoptic source checks incoming Carrington-stretch flags/coefficients and propagates them into both full and small maps. This confirms existing preprocessing; it does not establish that the product is already a single-epoch full-Sun map. Exact historic input-kernel processing cannot be reconstructed from these flags alone. [JSOC synoptic source](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/brblossynoptic.c)

The SunPy apparent-longitude convention includes observer/light-travel effects, and different ephemeris choices can differ. Stored quality-zero HMI bracketing records are recomputed locally to define the 180-degree epoch; their cached existence is provenance, not a fresh JSOC query. Header T_ROT, SunPy Earth midrotation and HMI crossings disagree by minutes. The selected images are only seconds away from the chosen HMI crossing. Sensitivity runs use the local observed meridian rate and selected image longitude; they do not resolve all time conventions. [SunPy Carrington conventions](https://docs.sunpy.org/en/latest/topic_guide/coordinates/carrington.html)

HMI synoptic columns average multiple LOS observations, and the small product is boxcar reduced. A raw 45-second snapshot is therefore an imperfect reference, even after smoothing and LOS/mu conversion. These comparisons share an instrument and scene, and do not provide an independent calibration or a far-side test. [NASA description of small HMI maps](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field)

## 7. Numerical findings and their interpretation

All eight primary variants and the untouched central map were evaluated at all three available epochs. The literal original block was also executed on each HMI triple, but has no finite results because of unmasked NaNs; its errors are unavailable, not zero. Thus all percentages labeled “vs 000” refer explicitly to the existing HMI-grid baseline.

Pooled over 77,098 pixels, 111 has RMSE **34.874 G**, versus 56.679 G for 000 and 34.994 G for central: 38.47% and 0.34% reductions respectively. Its pooled MAE is 11.836 G versus central's 11.782 G, so the MAE worsens by 0.46%. The small RMSE advantage is inconsistent across epochs and does not establish a general improvement.

### Actual observation epochs and common coverage

| CR | HMI T_OBS UTC | Crossing UTC | Offset (s) | N | Surface area (%) |
|---|---|---|---|---|---|
| 2120 | 2012-02-19T22:54:50.000 | 2012-02-19T22:54:54.688 | -4.69 | 25693 | 9.9132 |
| 2122 | 2012-04-14T13:39:13.000 | 2012-04-14T13:39:31.801 | -18.80 | 25705 | 9.9178 |
| 2124 | 2012-06-08T00:29:33.000 | 2012-06-08T00:29:36.874 | -3.87 | 25700 | 9.9159 |

Primary mu >= 0.8 samples about 9.9% of the whole solar surface (about one fifth of a hemisphere). Surface area is not projected image area. Every primary variant shares the exact same mask at a given CR. No observed pixel uses a neighboring rotation.

### CR2120: all primary runs

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

### CR2122: all primary runs

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

### CR2124: all primary runs

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

### Pooled comparison

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

### Forward-generated synthetic validation

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

### Exact inverse, interpolation and epoch sensitivity

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

### Investigation of resolution and registration discrepancies

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

### Longitude/seam sources and whole-map changes

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

### Original-source and grid checks

Literal original output has 0 finite pixels for all three supplied HMI triples. A finite-array source-execution test agrees with an independent vectorized original-grid implementation at 1e-12 tolerance. The primary physical-grid 000 and existing reconstruction helper agree exactly, and prior arrays agree within 1e-9 G. Previously reported 000/100 observational metrics and masks are reproduced.

The original grid spans 0..360 degrees with both endpoints and arcsin(linspace(-1,1,ny)); HMI uses pixel centers from its metadata (for CR2120, longitude approximately 0.3..359.8 degrees). A separate original-grid diagnostic omits incomplete rows explicitly, reconstructs on the old grid, then resamples to the physical grid. It differs appreciably at individual pixels:

| CR | Diagnostic RMSE vs observation (G) | Diagnostic map RMSE vs 000 (G) | Max abs map difference (G) |
|---|---|---|---|
| 2120 | 48.834 | 5.443 | 197.024 |
| 2122 | 43.464 | 3.595 | 76.038 |
| 2124 | 73.501 | 5.568 | 109.222 |

This extra resampling and row omission are explicitly outside the three tested switches. Treating that diagnostic, the literal original, and HMI-grid 000 as identical would conceal a reproducibility problem.

### Representative identical pixels

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

### Limitations that remain

- Only three near-center snapshots, covering about 9.9% of the Sun per epoch, are scored. Far-side, polar and seam accuracy are not observationally validated.
- LOS/mu assumes radial fields; snapshot noise, horizontal fields, spatial correlation, temporal evolution and synoptic averaging remain. The 3-pixel detector Gaussian does not match the synoptic spatial/temporal kernel exactly.
- The seven unique HMI maps are already Carrington-stretched (CARSTRCH=1); exact historic processing and per-pixel temporal weights are unavailable. A central-meridian-column model is an approximation.
- Header T_ROT, SunPy ephemeris and HMI record-derived crossings differ. The small empirical rate/epoch sensitivity does not explain the full discrepancy.
- Original MDI FITS are absent; the full original research run cannot be reproduced or scored. No full SFT evolution or SFT/PFSS accuracy claim was attempted.
- The exact inverse assumes constant observer meridian rate and prescribed latitude-dependent feature rotation. No emergence, diffusion, meridional transport, uncertainty model or instrument cross-calibration is inferred from these three snapshots.

Raw-byte FITS checksums pass for all 221 maps, including every audited input. Astropy's header-normalization path reports checksum failures for 135 unrelated maps with nonstandard `nan` cards; direct raw-byte one's-complement sums show these are parsing/normalization artifacts, not evidence of damaged files. No header was written back. `check_fits.py` and `evidence/raw_fits_checksums.json` reproduce this investigation.

## 8. Additional reproducibility, timing, and projection evidence

These values come directly from saved per-CR evidence, not from a new reconstruction or web query during consolidation. Complete unrounded values and the underlying metadata remain in the text archive.

| CR | Derived CM rate (deg/day) | Observation minus header T_ROT (s) | Independent projection max Br difference (G) | Independent projection RMSE difference (G) | Primary mask equals prior mask |
|---|---|---|---|---|---|
| 2120 | 13.213440000036668 | 205.00000000000006 | 1.3853655711493218e-07 | 1.3449803809708932e-09 | True |
| 2122 | 13.18464000000024 | 340.999999999999 | 5.112429644071881e-07 | 3.3123787067746312e-09 | True |
| 2124 | 13.271040000000385 | 197.00000000000043 | 9.875150031035673e-07 | 7.401591244040148e-09 | True |

| CR | Variant | Existing helper max difference (G) | Saved prior map max difference (G) | Same finite mask as existing helper |
|---|---|---|---|---|
| 2120 | 000 | 0.0 | 1.2812506611226127e-10 | True |
| 2120 | 100 | 0.0 | 1.666222715357435e-11 | True |
| 2122 | 000 | 0.0 | 2.7569058147491887e-11 | True |
| 2122 | 100 | 0.0 | 1.91526794424135e-11 | True |
| 2124 | 000 | 0.0 | 8.162714948412031e-11 | True |
| 2124 | 100 | 0.0 | 1.0082601420435822e-11 | True |

| CR | Whole-map common pixels | Whole-map common surface-area fraction | Incomplete rows in previous / current / next maps |
|---|---|---|---|
| 2120 | 255770 | 0.9868060277777777 | [[357, 358, 359], [357, 358, 359], [357, 358, 359]] |
| 2122 | 255770 | 0.9868060277777777 | [[357, 358, 359], [357, 358, 359], [358, 359]] |
| 2124 | 256180 | 0.9884278333333334 | [[358, 359], [0, 359], [0, 1]] |

All 221 raw-byte synoptic FITS checksums passed. The 135 Astropy post-header-normalization failures are explained by its in-memory handling of nonstandard `nan` cards; the independent one's-complement sum of each original file is 0xffffffff. Normal Astropy checksum checks also pass for the seven audited inputs. No file was repaired on disk. The complete per-file values are archived in `evidence/raw_fits_checksums.json`.

## 9. What ran, tests, environment, and original-file preservation

The audit produced 27 primary observational rows (3 epochs times 9 maps including central), 66 synthetic rows (6 cases times 11 variants/oracles), and all sensitivity/difference/source/sample tables listed in the appendix index. There were **24 audit unit/integration tests and 3 existing coordinate-registration tests**, all passing. The saved execution record contains an initial full run and a later finish pass for the additional discrepancy diagnostics; repeated test/preservation entries are actual repeated checks, not additional independent datasets.

| Software/environment field | Recorded value |
|---|---|
| python | 3.12.7 (tags/v3.12.7:0b05ead, Oct  1 2024, 03:06:41) [MSC v.1941 64 bit (AMD64)] |
| platform | Windows-11-10.0.26200-SP0 |
| numpy | 2.5.4 |
| scipy | 1.18.1 |
| astropy | 7.2.3 |
| sunpy | 8.0.1 |
| matplotlib | 3.11.2 |
| automatic_network_downloads | False |

Pinned direct dependencies:

```text
numpy==2.5.4
scipy==1.18.1
astropy==7.2.3
matplotlib==3.11.2
sunpy==8.0.1
```

### Validation cases actually checked

`pre_sft_audit/test_audit.py` (24 tests):

| Class | Test |
|---|---|
| PhysicsTests | test_latitude_colatitude_equivalence |
| PhysicsTests | test_tabulated_rates |
| PhysicsTests | test_known_feature_trajectory_positive_and_negative_rates |
| PhysicsTests | test_first_order_error_is_second_order |
| PhysicsTests | test_time_tagged_seam_selects_chronological_neighbor |
| PhysicsTests | test_boundaries_are_current_and_no_unsupported_extrapolation |
| PhysicsTests | test_stationary_oracle_has_no_shift |
| PhysicsTests | test_north_south_symmetry |
| PhysicsTests | test_degenerate_inverse_fails |
| NumericalTests | test_literal_original_matches_independent_vectorization_on_finite_arrays |
| NumericalTests | test_primary_sampler_reproduces_existing_at_native_grid |
| NumericalTests | test_missing_edge_and_isolated_pixels_are_not_zero_measurements |
| NumericalTests | test_no_longitude_edge_extrapolation |
| NumericalTests | test_area_weights_cover_sphere_and_polar_cells |
| NumericalTests | test_metric_units_and_bias_direction |
| CompletedAuditTests | test_persisted_scores_and_identical_masks |
| CompletedAuditTests | test_observations_do_not_sample_seams |
| CompletedAuditTests | test_projection_registration_and_baseline_reproduction |
| CompletedAuditTests | test_actual_chronology_is_decreasing_longitude_in_increasing_time |
| CompletedAuditTests | test_all_original_files_unchanged |
| CompletedAuditTests | test_literal_HMI_reference_has_no_finite_results |
| CompletedAuditTests | test_synthetic_accuracy_and_controls |
| CompletedAuditTests | test_raw_fits_checksum_avoids_header_normalization_artifact |
| CompletedAuditTests | test_resolution_and_registration_diagnostics_use_common_masks |

`SFT/test_coordinate_registration.py` (3 tests):

| Class | Test |
|---|---|
| CoordinateRegistrationTests | test_hmi_negative_header_maps_to_increasing_physical_longitude |
| CoordinateRegistrationTests | test_original_sample_positions_reproduce_input |
| CoordinateRegistrationTests | test_rotation_boundary_chooses_and_samples_correct_map |

The original source contains a pre-existing invalid-escape SyntaxWarning (`\s`); it did not cause a test failure. Check the retained log text for exact outcomes. At audit verification, all 281 original manifest entries had unchanged bytes, and no added file was detected outside the audit folder. That is a historical verification of the audit run, not a fresh claim about unrelated repository changes made afterward. No scientific or preservation tests were rerun merely to consolidate this record.

## 10. Repository understanding and implementation boundaries

The initial read-only census covered all 281 existing project artifacts, including ignored scientific inputs/outputs and the viewer's generated data, with SHA-256 hashes. Git internals, the Python environment, node packages, bytecode and compiled frontend build directories were excluded as infrastructure/cache. All project text was read for the census, and Python imports/functions were indexed where parseable. Detailed source review focused on reconstruction, validator, FITS downloader, cached metadata/results, existing coordinate tests, research initialization/evolution conventions, the viewer exporter, and accompanying reports.

| Area | Existing role | Audit treatment |
|---|---|---|
| `ananya_research_work-main/SFT/SFT.py` | Three-map MDI-labeled initialization, grid conversion, vector-potential SFT evolution and BMR insertion | Never imported/executed wholesale. Only original omega and pre-SFT reconstruction AST nodes executed with in-memory arrays |
| Research `main.py`, `sharptools.py`, catalogue | SHARP/BMR preprocessing and source-driven evolution | Read as context; not needed for pre-SFT test |
| Research `test_*.py` | Hard-coded scientific experiments on harmonic power / inversion-line length | Not a conventional unit-test suite; not executed |
| Research PFSS scripts | Spherical harmonic PFSS and field-line plotting with missing hard-coded inputs | Separate from reconstruction, not executed |
| `SFT/synoptic_reconstruction.py` | Existing physical HMI coordinates, latitude/original rate functions, cubic interpolation and plotting | Read-only helpers reused and independently checked |
| `SFT/validate_observations.py` | JSOC querying, cached HMI images, SunPy projection, LOS/mu, shared mask | Only numerical projection/parser helpers used; all writes/network entry points avoided |
| `SFT/test_coordinate_registration.py` | Existing positive-longitude and native-sampling tests | Read; existing tests also executed separately and logged |
| `SFT/download_synoptic_maps.py` | Download and header-enrichment from JSOC | Read, not run; all required FITS already available |
| `SFT/validation_data/` | Three raw 4096x4096 HMI images, JSOC metadata, prior arrays/metrics/plots | Read-only raw inputs and reproduction controls |
| `SFT/fits_files/` | 221 HMI 720x360 synoptic maps, CR2096..2316 | Full shape/finite/checksum census; seven unique maps used in triples centered 2120/2122/2124 |
| `SFT/prepare_viewer_data.py`, `SFT/viewer/` | React/Three.js display of existing maps/metrics | Reviewed for baseline provenance, not changed or built |
| `magnetofriction/` | Empty engine/output stubs, input notes and theory Q&A | Context only; not part of numerical reconstruction |
| Root research/audit Markdown | Brief, planned scientific context and sun-layer notes | Read as task context; embedded instructions were not taken as permission to edit research files |

No AGENTS.md was found in the repository or checked parent directories. In particular, the research `Instruction.txt` suggestions to modify code are historical document content, not an override of the user's preservation rule.

The inventory found pre-existing parse errors; they are recorded without modification:

- `ananya_research_work-main/SFT/test_length_zero_line_diffusion.py`: expected an indented block after function definition on line 406 (<unknown>, line 408)
- `ananya_research_work-main/SFT/test_p_advection_diffusion.py`: expected an indented block after function definition on line 561 (<unknown>, line 563)
- `ananya_research_work-main/SFT/test_p_diffusion.py`: expected an indented block after function definition on line 381 (<unknown>, line 383)
- `magnetofriction/model_input.py`: unterminated string literal (detected at line 1) (<unknown>, line 1)

These do not block the isolated pre-SFT audit. Missing optional SunPy map extras also do not block the coordinate-frame API used here. The actual environment is Python 3.12.7, NumPy 2.5.4, SciPy 1.18.1, Astropy 7.2.3, SunPy 8.0.1, Matplotlib 3.11.2.

All 221 raw synoptic file checksums pass; all DATASUM values pass. `available_inputs.json` distinguishes Astropy's post-header-parse verification from the independent raw-byte checksum investigation. The audited seven input maps have passing normal Astropy checks too. Cached full-disk HMI image SHA-256 values match the previous reports and the supplied metadata T_REC/T_OBS exactly.

Scientific evidence retrieved during the audit: SunPy official HMI/Carrington documentation, NASA's HMI product description and JSOC-SDP synoptic source pinned to commit `0cf0b90d354705ed866fdba040772b0d712de785`. The source snapshots and provenance live in `evidence/`; they are explanatory evidence, not the historic binary pipeline proven to have produced these FITS.

Original-file preservation is checked by hashes in the automated tests and again with `inventory.py --verify`. The verification compares the original file set and flags new files outside the audit tree. The same data and scripts remain in their original locations.

## 11. File map, what can be removed, and recovery

### Scope of any later cleanup

The isolated implementation is `pre_sft_audit/`. Keep this root-level `pre_sft_audit_record.md` as the retained record. Nothing has been deleted by this consolidation. Original `SFT/` inputs and helpers, `ananya_research_work-main/`, the original root brief `pre_sft_correction_audit.md`, and unrelated work elsewhere in the repository are separate from that implementation. Their appearance in an input manifest does not make them cleanup targets.

All saved scalar/tabular results, narrative reports, code, JSON evidence, and log text are retained below. Binary arrays, plots, source FITS, and the ZIP are not embedded. After removing only `pre_sft_audit/`, the tracked implementation and plots can be recovered from the audit commit; ignored arrays must be regenerated from the original inputs. Deleting original observations as well would remove that rerun route unless separately backed up.

### Git recovery route

The audit was committed as **`b1548f9adc83b99c304b247add23d08ee60d0d4f`** on 2026-11-10 at 16:11:28 +05:30, with subject `Add reproducible pre-SFT reconstruction audit`. It contains 63 files, including the reports, CSVs, code, metadata, plots, `.gitignore`, and `.gitattributes`. The repository working tree was clean immediately after that commit. `arrays/` and `review_bundle.zip` were intentionally Git-ignored and remained local.

After the audit folder has been removed, recover its committed files from the retained Git repository with:

```powershell
git restore --source b1548f9adc83b99c304b247add23d08ee60d0d4f -- pre_sft_audit
```

That command restores the version recorded in the commit and can overwrite audit files if that folder already exists. It does not restore ignored NPZ arrays or the ZIP. It does not touch the protected research folder. The extraction example later in this file offers a second route for the archived text files when Git history is unavailable.

### Historical reproduction commands

These commands require the audit scripts to be restored/extracted and the original input paths in section 4 to remain available. The old `original_manifest.json` records the historical workspace, so its preservation test is byte-specific: changing original files or creating unrelated files outside the audit can cause that test to fail even if the numerical calculation can run. Do not present a later manifest failure as a changed scientific result.

```powershell
.\.venv\Scripts\python.exe -B pre_sft_audit\reproduce.py
```

This runs calculations, raw-byte FITS checksum verification, automated tests, original-file preservation verification, and report/bundle generation. Runtime is a few minutes on the supplied environment. `-B` prevents bytecode writes into existing source directories. Outputs may be regenerated only below `pre_sft_audit/`. The initial manifest is deliberately never replaced.

For a fresh Python 3.12 environment, install `pre_sft_audit/requirements.txt` into an environment of your choice. Exact versions used are in `environment.json`; direct dependencies are pinned. No `sunpy.map`, `reproject`, `mpl-animators`, Numba, SFT solver, frontend, or observation downloads are needed. Astropy IERS network downloads are disabled. Calculations are offline; archived external source evidence is supplied in `evidence/`.

Individual commands:

```powershell
.\.venv\Scripts\python.exe -B pre_sft_audit\run_audit.py
.\.venv\Scripts\python.exe -B pre_sft_audit\investigate_discrepancies.py
.\.venv\Scripts\python.exe -B pre_sft_audit\check_fits.py
.\.venv\Scripts\python.exe -B -m unittest discover -s pre_sft_audit -p test_audit.py -v
.\.venv\Scripts\python.exe -B pre_sft_audit\inventory.py --verify
.\.venv\Scripts\python.exe -B pre_sft_audit\make_reports.py
```

Do not run the original `SFT.py` or `validate_observations.py` entry points for this audit: their normal workflows write elsewhere. This audit imports only their read-only numerical helpers. To make a *new* initial manifest in a new checkout before any changes, run `inventory.py` without `--verify`; it refuses to overwrite an existing manifest.

### Functional map of implementation files

| Path | Role |
|---|---|
| pre_sft_audit/audit_core.py | Independent switches, source selection, cubic sampler, scores, area weights, literal original AST execution |
| pre_sft_audit/observations.py | Offline HMI loading, SunPy projection reuse, independent perspective projection, timing and cache checks |
| pre_sft_audit/synthetic.py | Forward-generated fields, time tags, stationary/opposite-rate/evolving controls, common-mask synthetic metrics |
| pre_sft_audit/run_audit.py | Eight-variant experiments, baselines, observational sensitivities, tables, arrays and diagnostic maps |
| pre_sft_audit/investigate_discrepancies.py | Detector smoothing and small registration-offset scans; final figure rendering |
| pre_sft_audit/check_fits.py | Independent raw-byte ones-complement FITS checksum verification |
| pre_sft_audit/inventory.py | Initial original-file hashes, text/source census and preservation checks |
| pre_sft_audit/test_audit.py | 24 independent physics, numerical and saved-result consistency tests |
| pre_sft_audit/reproduce.py | Subprocess orchestration, logs, exit codes and report generation |
| pre_sft_audit/make_reports.py | Human reports and compact review bundle rendered from saved calculations |
| pre_sft_audit/README.md | Historical setup, dependencies, exact commands, inputs and numerical policies |
| pre_sft_audit/issue_verdicts.md | Coordinate inconsistency, inverse derivation, chronology, conditional applicability |
| pre_sft_audit/results.md | Interpreted numerical results, sensitivity tables, representative values and limitations |
| pre_sft_audit/handoff.md | Historical completion summary and independent-analysis sharing guide |
| pre_sft_audit/repository_inventory.md | Repository roles, missing inputs, old parse errors and preservation context |
| pre_sft_audit/evidence/*.json | Full input headers, HMI keywords, saved prior checks, chronology, hashes and source provenance |
| pre_sft_audit/evidence/*.c | Archived official JSOC source evidence; pinned upstream commit and hashes, not a proven historic binary pipeline |
| pre_sft_audit/arrays/cr*.npz | Generated fields, observations, masks, coordinates, source maps and query longitudes; Git-ignored |
| pre_sft_audit/arrays/synthetic_*.npz | Synthetic input maps, true field/rate/times, masks and all reconstructed fields; Git-ignored |
| pre_sft_audit/plots/*.png | Saved field, residual, common-mask and seam-source diagnostics; committed |
| pre_sft_audit/logs/*.log | Actual computation/test/check stdout and stderr transcripts |
| pre_sft_audit/review_bundle.zip | Generated convenience review package; Git-ignored and not an independent source of results |

## 12. Diagnostic figures and source references

Figures are listed here rather than linked to soon-to-be-removed local images. They remain recoverable from the audit commit. All field/residual panels use a common -100 to +100 G display range; mask panels use 0=excluded and 1=included. Seam-source panels use 0=previous, 1=current, 2=next CR. Saturation is a display setting and does not clip the values used for metrics.

| Original plot path | What it records |
|---|---|
| pre_sft_audit/plots/cr2120.png | CR2120: central/reference/common mask, 000/100/111, observational residuals and 111-minus-central |
| pre_sft_audit/plots/cr2122.png | CR2122: central/reference/common mask, 000/100/111, observational residuals and 111-minus-central |
| pre_sft_audit/plots/cr2124.png | CR2124: central/reference/common mask, 000/100/111, observational residuals and 111-minus-central |
| pre_sft_audit/plots/cr2120_sources.png | CR2120: all eight source-selection maps, including unsupported queries that remain NaN |
| pre_sft_audit/plots/cr2122_sources.png | CR2122: all eight source-selection maps, including unsupported queries that remain NaN |
| pre_sft_audit/plots/cr2124_sources.png | CR2124: all eight source-selection maps, including unsupported queries that remain NaN |
| pre_sft_audit/plots/synthetic_seam_features.png | Known truth and reconstruction/residual diagnostic for localized seam/interior features |
| pre_sft_audit/plots/synthetic_seam_features_sources.png | All eight source-selection maps for synthetic seam features |
| pre_sft_audit/plots/synthetic_missing_data.png | Known truth and reconstruction/residual diagnostic with missing rows/segments |
| pre_sft_audit/plots/synthetic_missing_data_sources.png | All eight geometric source selections in the missing-data experiment |

External sources below were consulted during the original audit, not newly queried during this consolidation. Their role is coordinate/product provenance, not independent validation of the measured errors.

- [SunPy HMISynopticMap: positive physical longitude step despite negative HMI CDELT1](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html)
- [SunPy Carrington rotation time definition](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.carrington_rotation_time.html)
- [SunPy Carrington longitude, observer and light-travel conventions](https://docs.sunpy.org/en/latest/topic_guide/coordinates/carrington.html)
- [NASA description of small HMI radial synoptic maps](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field)

Official JSOC source snapshot commit: `0cf0b90d354705ed866fdba040772b0d712de785` in https://github.com/JSOC-SDP/proj. Complete per-file SHA-256 and pinned raw URLs are archived in `evidence/jsoc_source_provenance.json`. The source-C contents are not repeated in this record.

| Source filename | Pinned upstream source |
|---|---|
| brblossynoptic.c | [source](https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/brblossynoptic.c) |
| hmisynoptic.c | [source](https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/hmisynoptic.c) |
| maprojbrfromblos.c | [source](https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/maprojbrfromblos.c) |
| mrmlossynoptic.c | [source](https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/mrmlossynoptic.c) |

## 13. Complete implementation-file inventory at consolidation

Paths and byte hashes below describe the local artifacts read for this record, including ignored outputs. They do not instruct you to delete input files. Their original input-file hashes and 281-file historical manifest are separately retained in the JSON archive.

| Original relative path | Bytes | SHA-256 of original bytes | Retention in this record |
|---|---|---|---|
| pre_sft_audit/.gitattributes | 179 | 1467c12169aa7473efd7c6fc47e8fc7329f313d40b5d49c75c7efcb49070fdeb | text embedded below |
| pre_sft_audit/.gitignore | 91 | 4a3de3f45fff9623df9b16d9df5791b016e2c73d9f158494ae027f533b82aa1e | text embedded below |
| pre_sft_audit/arrays/cr2120.npz | 52568282 | 15fae01a03c47caa533094299be2956b3d288949aae17e1b8aa68e6b1a7f75b6 | binary omitted; see recovery |
| pre_sft_audit/arrays/cr2120_reference_sensitivity.npz | 624576 | 23e78dc2b98b643613e484f88a3883064d780b5828fe86a77e1e94d8d3c12339 | binary omitted; see recovery |
| pre_sft_audit/arrays/cr2122.npz | 52573860 | 523ffc452992cbc4bae973b19b6e42f12a96fe5d7b41d5e9779ba38ed9f49451 | binary omitted; see recovery |
| pre_sft_audit/arrays/cr2122_reference_sensitivity.npz | 624818 | 1598b1f229d1595453d18da94eabbc3ba0649d9fe0d1eae236df73bbf23ce07a | binary omitted; see recovery |
| pre_sft_audit/arrays/cr2124.npz | 52661072 | b677fcd63d7bed03f8d31359f740cb96e26f51ce8c8ce4a69f84c716d6b4fb41 | binary omitted; see recovery |
| pre_sft_audit/arrays/cr2124_reference_sensitivity.npz | 624606 | 3043e97777b8bc61d017b65596676d799f8bbc9c66478f3ac6ef8e707695845f | binary omitted; see recovery |
| pre_sft_audit/arrays/synthetic_evolving_control.npz | 15005534 | ab486e32a89247573abd957f006a7953f91a2e6c3811435bf66a43d5046acfb7 | binary omitted; see recovery |
| pre_sft_audit/arrays/synthetic_missing_data.npz | 14816485 | fde57b7cc4649b2afdf672549579bd442eb0751f0bf888b308fe57359d0d7e68 | binary omitted; see recovery |
| pre_sft_audit/arrays/synthetic_opposite_rotation_control.npz | 14929047 | 9fa54d2778320496518ceb15d3f4800ed4149e27cf2d680037111ad3f3bb7644 | binary omitted; see recovery |
| pre_sft_audit/arrays/synthetic_seam_features.npz | 14967542 | 9a48866b2908812fef92b0d29e306d318a8e377f2dfa36ba98c35de68a236d16 | binary omitted; see recovery |
| pre_sft_audit/arrays/synthetic_smooth_rotation.npz | 14931275 | eb969ab9976428f9cc1f8e7dbafb572eade030953cd325cd6bf81b9898e763c2 | binary omitted; see recovery |
| pre_sft_audit/arrays/synthetic_stationary_control.npz | 14921610 | 28782d8d689a2379d7668b28a62a62706014832d842d454b08475c537ae4baa6 | binary omitted; see recovery |
| pre_sft_audit/audit_core.py | 7439 | d17be73219316b79238880571114ed2035a95ca560ce4f75ec012f78fcb1a897 | text embedded below |
| pre_sft_audit/available_inputs.json | 58740 | 2498080ead2ec9b2feddfca0d5ae739abbfe0a221d70aef90a4482eb554bef0d | text embedded below |
| pre_sft_audit/check_fits.py | 1559 | b9ec187eab13f72caf058e24535265efff314e915b2b42404698d0d2029e0b34 | text embedded below |
| pre_sft_audit/environment.json | 301 | 28a493e28a6b6899a9eb83a806a4760f4f873075bf0ae45d22cf4be2ca9ac392 | text embedded below |
| pre_sft_audit/evidence/brblossynoptic.c | 64320 | 1923350eccf4ff55c9bb98518273c304a5f02f745b333b0447810c56cf36fb9d | pinned upstream source, not embedded |
| pre_sft_audit/evidence/cr2120.json | 20286 | bc3fbfb25a580d7e9bb79755904ff1bd6286bdbdaf0809f982f510c946352301 | text embedded below |
| pre_sft_audit/evidence/cr2122.json | 20292 | 9bb71b45cd5f1305408962f067e1da991df4de0bcb5c7a5f221efa9a9d52c625 | text embedded below |
| pre_sft_audit/evidence/cr2124.json | 20246 | 576c84de142a31dbb965f5d6b1b9f86ed7e3f394eef0839497e0cb402b03954d | text embedded below |
| pre_sft_audit/evidence/hmisynoptic.c | 57743 | d30474b4fc3f0b6d8b39a429174d8e3d3dc4bf745866a07c83ec45172132b168 | pinned upstream source, not embedded |
| pre_sft_audit/evidence/jsoc_source_provenance.json | 1220 | 4f09e16705da446e43baa4ca04cb1426d3fe4ff3b967a32911c1eb945d504d60 | text embedded below |
| pre_sft_audit/evidence/maprojbrfromblos.c | 30789 | cd23d4eaa5b407bfd0ba59e37b7d70765bb43c85f8392bd9df092df5527553da | pinned upstream source, not embedded |
| pre_sft_audit/evidence/mrmlossynoptic.c | 71393 | b90195f071f413f130cf1e33495b2102cc7a797f46207eeef129bf972af06b53 | pinned upstream source, not embedded |
| pre_sft_audit/evidence/raw_fits_checksums.json | 59835 | 7f7b2b50abe568ca6070801ae31368e536aeedcc2b473067ed2728d687f837c5 | text embedded below |
| pre_sft_audit/evidence/synthetic_diagnostics.json | 1195 | a79c68abf229db3968f469fa30406b2f59e240d3414035a9e87f176e0d54464d | text embedded below |
| pre_sft_audit/execution.json | 2479 | 95bb7de43d58560d8fe005dea046322525bcd9e99df0679abc19d51c52105be2 | text embedded below |
| pre_sft_audit/factorial_effects.csv | 2474 | 1f50fa6b55cee87df1b2d7ee9ee1e99409d4882e9088fc8c6ce95c57d61fa354 | text embedded below |
| pre_sft_audit/handoff.md | 4654 | cba61131f82805fbc67dc27d7b74ff815c21ca0f1ca053e74dca77d882002158 | text embedded below |
| pre_sft_audit/inventory.py | 3095 | 2d8e03803789ac8a5b0e74cc827612080a9bb724449f25b98cde4d7f4f9b6811 | text embedded below |
| pre_sft_audit/investigate_discrepancies.py | 3867 | 6ab999dd149e8f313ebbf590e4b9d39852ed410f8609b899bccd53b97f2ced50 | text embedded below |
| pre_sft_audit/issue_verdicts.md | 8738 | 6991f2c2716cf6f1d6c39b4bc443dca6b9834f1cbddd0c88148eaba2cc548e8c | text embedded below |
| pre_sft_audit/literal_original_metrics.csv | 452 | 8309d618d7d947c836580af3db4c2ad5503bf2aff5d03c3076cce4865425b56f | text embedded below |
| pre_sft_audit/logs/calculations.log | 2973 | dee8a9dc2b390674e69c7af7c16449ccb355944af7d8bee380205fe7894477dd | text embedded below |
| pre_sft_audit/logs/discrepancies.log | 233 | 47c687027ad8770ac5775fd10a6c66617e399de1c1bb16866df2b06a8f03b6d1 | text embedded below |
| pre_sft_audit/logs/existing_tests.log | 634 | 9df172113b0cdcad34d284734703e97353fb2073d059e015b68e21ddc925e7d8 | text embedded below |
| pre_sft_audit/logs/preservation.log | 252 | 74487505c6b558fb80962a249277e0cec98065df43da1849567e620948422a10 | text embedded below |
| pre_sft_audit/logs/raw_checksums.log | 159 | 7dd392e833c5965b066244104ad32ccd4567dc54369e4378828c44a8d7587211 | text embedded below |
| pre_sft_audit/logs/tests.log | 3291 | b143bde26926daf4af0518e8c503cc497f8f38f82c29c990231a95dee4ecc7ee | text embedded below |
| pre_sft_audit/longitude_sources.csv | 6008 | 290059fe8e5475193805d0af1a2608a67c39aaceb1be670242114afea26cb7e9 | text embedded below |
| pre_sft_audit/make_reports.py | 42451 | dc79560049810454ff1e7134aa1c6b0417b1b21f2b49895dbb222564bc3cbc7b | text embedded below |
| pre_sft_audit/map_differences.csv | 20085 | 9bd845a321484b9241b19b79fc5a71298d693fe967ccfcc1ec64519a6095c2e8 | text embedded below |
| pre_sft_audit/metrics.csv | 8008 | 265ceba4718becee3c3b654a8ce6c3e2311b0baea52b42aa8cd26f2e4cf28c7c | text embedded below |
| pre_sft_audit/observations.py | 5680 | b40fb0b3ccb7f2caf2bb165f17ddb54a83255bdd2142424e6c9d43c5184d81d1 | text embedded below |
| pre_sft_audit/original_grid_sensitivity.csv | 788 | 9d5d20be3778deb7937355cbb13bb3538d8757084cc790265fa3e561a32e8000 | text embedded below |
| pre_sft_audit/original_manifest.json | 65547 | 988125c0cc5e093b1539fa97bbbb7499d3235e482143e64d13dace8964f49762 | text embedded below |
| pre_sft_audit/plots/cr2120.png | 1945710 | bfb9daad1a3772ba75c1b4fd517681d8e8da98178821b50d27b1af5a0f95b38d | binary omitted; see recovery |
| pre_sft_audit/plots/cr2120_sources.png | 136359 | 8d23dc30b8a8e342192e664f6d4c255cc1369a2f444182961d331834d0561f56 | binary omitted; see recovery |
| pre_sft_audit/plots/cr2122.png | 1937905 | b4f6253f53635b01538a5873da42847626b3fdf803b4cd4aaef039479bcb248d | binary omitted; see recovery |
| pre_sft_audit/plots/cr2122_sources.png | 136061 | 8de17b8ee377c70b98d5b2cf16d0a6f607c7dfde1cb8a7e533e049ab49382a10 | binary omitted; see recovery |
| pre_sft_audit/plots/cr2124.png | 1946650 | d3c00cd8ca798936e38ba7019e586505afc2d49c1ddfe21f7c6eb2ebf3eb11ee | binary omitted; see recovery |
| pre_sft_audit/plots/cr2124_sources.png | 136249 | 49820496e33eddeb12c64cae29bbe29f72f6ad90f0dab6ebd521361eeb9b622a | binary omitted; see recovery |
| pre_sft_audit/plots/synthetic_missing_data.png | 384878 | d928c2d1c7b240f847d06a45e6e7cf182370605b9b404c19a3cac2c7a19004ce | binary omitted; see recovery |
| pre_sft_audit/plots/synthetic_missing_data_sources.png | 132861 | 101dc441b225b5d896fa131d89aefa9114e1bdbccd9a2286a2feab8a6ed65c25 | binary omitted; see recovery |
| pre_sft_audit/plots/synthetic_seam_features.png | 385313 | dc9b00c3e8263462e6e16e0c54a7cc7b6bcf2d5263e99c39618b1fe81511f680 | binary omitted; see recovery |
| pre_sft_audit/plots/synthetic_seam_features_sources.png | 133193 | 5d8575a388c3d26746edec0f5492ab2df7a240462eae813e9f0e803815aaaeab | binary omitted; see recovery |
| pre_sft_audit/pooled_metrics.csv | 1899 | e8e894ae2a97e9b3087745dd633c1ad78898ca12f8a62caffda59b99e936e577 | text embedded below |
| pre_sft_audit/preservation_check.json | 133 | 5a68acd7980ce3156ec211327790e2c7b15ebd850d40ea4ae0f267b9ad1ebd4a | text embedded below |
| pre_sft_audit/README.md | 7786 | fa807f0e8b1372ddf80e331f3004dd80265bc94ca26b7cb87dc682812ed5d7fa | text embedded below |
| pre_sft_audit/registration_metrics.csv | 970 | 4e03f7d801762441d32247a44f44be3e72aa50931d7f980c95864949f20dcaf5 | text embedded below |
| pre_sft_audit/registration_offset_sensitivity.csv | 8338 | 3469bf54afddfb40f9be24bd7d90dcfbb4af34ad34012dc54c109b785a41d199 | text embedded below |
| pre_sft_audit/repository_inventory.md | 5123 | c3af8c0d92182297bf97b0ee0969eff8534073892dff5279ed9ea1a75fc56be4 | text embedded below |
| pre_sft_audit/reproduce.py | 2088 | 4869a5909fda1a5dd6624e96f83e2b5f46c5891c9e79ec667a5d500630a214d5 | text embedded below |
| pre_sft_audit/requirements.txt | 74 | 7044b3b2c167fe09e24b1ae1c19850d13b3815709ddb55ae4ef991afe04cd5da | text embedded below |
| pre_sft_audit/results.md | 15196 | cd97c144774093189f6c47f547c19c8728c6fd80648a88eca4d50cde4cdafb05 | text embedded below |
| pre_sft_audit/review_bundle.zip | 7356476 | 95fdc2ba16f894db01975afb4bf40124e9917532fc16425644b90ecb9cd08cf7 | binary omitted; see recovery |
| pre_sft_audit/run_audit.py | 18060 | 82fce78ee6c7a90de7374025bf4a34b58dc775f534bd0eb5c2a1c860bcbfed59 | text embedded below |
| pre_sft_audit/run_summary.json | 440 | 2a43af330e25965ab2b42b3c52d834647e4fbb85bc211c6db20107cc00ba53ea | text embedded below |
| pre_sft_audit/sample_br.csv | 6647 | ac9e38bef00295fda4c8fc4288e302629b6764031d2c3068140c961d8cb4378c | text embedded below |
| pre_sft_audit/sensitivity_metrics.csv | 24111 | e92c292204bb9e47e1a05b6d985ac929d352bd46a2eff5f86649044263a26fb9 | text embedded below |
| pre_sft_audit/smoothing_sensitivity.csv | 14923 | b2f74c35afe229d5a1e88b274e75373e3454a9bd8df3588bbc7ffcd72893a198 | text embedded below |
| pre_sft_audit/synthetic.py | 4750 | adec08b45d24bcd42662d03749937b05649bfcf3ebfa90f79387262e2f8c43d5 | text embedded below |
| pre_sft_audit/synthetic_metrics.csv | 17346 | 4c6a0a4b92e3a771e49e996c707665292372a03101822f9c2bf81eeea64f28b3 | text embedded below |
| pre_sft_audit/test_audit.py | 11723 | e33e26ba33da6193b9298c6e49008e769111ec05a26cd83cb0cec6da3a00512d | text embedded below |

## 14. Full-precision table index and reading guidance

The narrative tables round values for readability. The complete original CSV cells are embedded below at their saved precision, including empty entries for unavailable metrics. They are not recomputed or rounded during consolidation. Case labels and masks are retained for each row. Map-difference rows are differences between maps, not errors relative to an observation.

| CSV filename | Data rows | Main purpose |
|---|---|---|
| factorial_effects.csv | 36 | Conditional individual-bit changes within every other-bit context |
| literal_original_metrics.csv | 3 | Unscoreable literal-original outcomes; zero finite output is not zero error |
| longitude_sources.csv | 24 | Query shifts, wrap counts, source counts, surface fractions and valid contributions |
| map_differences.csv | 108 | All 36 central/variant pairs per CR on a whole-map common mask |
| metrics.csv | 27 | All 27 primary observational scores, units, masks and gains vs 000/central |
| original_grid_sensitivity.csv | 3 | Explicit row omission on the original coordinate grid followed by physical-grid resampling |
| pooled_metrics.csv | 9 | Concatenated three-epoch scores and gains for all 9 primary maps |
| registration_metrics.csv | 6 | Positive physical HMI longitude versus reflected negative-header interpretation |
| registration_offset_sensitivity.csv | 45 | 15 small source-coordinate offsets per CR on a common mask |
| sample_br.csv | 21 | 21 identical selected coordinates with every primary field and reference Br |
| sensitivity_metrics.csv | 105 | Exact inversion, linear interpolation, selected epoch/rate and tighter mu masks |
| smoothing_sensitivity.csv | 81 | Sigma 3/6/12 detector smoothing for every primary map and CR |
| synthetic_metrics.csv | 66 | All synthetic cases, switches, exact inverses and known-rate oracles |

In total, **13 CSV files and 534 data rows** are retained without dropping columns. The archives also retain the standalone narrative reports, so any original phrasing can be checked against the consolidated explanation.

## 15. Restoring archived text files without Git

The archive below stores text in readable fenced blocks with per-file original hashes and line-ending metadata. The following optional Python example restores only missing paths inside `pre_sft_audit/`, verifies each reconstructed byte sequence, and refuses to overwrite an existing file. It skips the historical root brief. Run it from the repository root only when you want the implementation files back. It does not restore the excluded binary files or external C source snapshots. It is included as documentation and was not used to overwrite or delete any workspace file during consolidation.

```python
from pathlib import Path, PurePosixPath
import hashlib
import json
import re

base = Path.cwd().resolve()
text = (base / "pre_sft_audit_record.md").read_text(encoding="utf-8")
pattern = re.compile(
    r"<!-- ARCHIVED_TEXT ([^\n]+) -->\n`````[A-Za-z0-9_-]*\n"
    r"(.*?)\n`````\n<!-- END_ARCHIVED_TEXT -->",
    re.S,
)
restored = 0
for match in pattern.finditer(text):
    meta = json.loads(match.group(1))
    rel = PurePosixPath(meta["path"])
    if not rel.parts or rel.parts[0] != "pre_sft_audit":
        continue
    target = base.joinpath(*rel.parts).resolve()
    if not target.is_relative_to(base / "pre_sft_audit"):
        raise ValueError("Unsafe archived path")
    payload = match.group(2)
    if meta["line_endings"] == "CRLF":
        payload = payload.replace("\n", "\r\n")
    data = payload.encode("utf-8")
    if meta["utf8_bom"]:
        data = b"\xef\xbb\xbf" + data
    if len(data) != meta["bytes"] or hashlib.sha256(data).hexdigest() != meta["sha256"]:
        raise ValueError("Archive hash mismatch: " + meta["path"])
    if target.exists():
        raise FileExistsError("Refusing to overwrite: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    restored += 1
print("Restored text files:", restored)
```

## 16. Verified text archive

The historical task brief is retained as context, not as a new instruction to modify anything. The following source/report/log blocks are archival data. Missing binary inputs are never represented by invented values.

<details>
<summary>pre_sft_audit/factorial_effects.csv (2,474 bytes; 36 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/factorial_effects.csv", "bytes": 2474, "sha256": "1f50fa6b55cee87df1b2d7ee9ee1e99409d4882e9088fc8c6ce95c57d61fa354", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,switch,from,to,delta_rmse_G,delta_mae_G,delta_r
2120,latitude,000,100,-24.52407886123955,-3.0863722913297362,0.4570136272175047
2120,latitude,010,110,-17.186618300771162,-2.6309683557964334,0.3883524875731684
2120,latitude,001,101,-24.52407886123955,-3.0863722913297362,0.4570136272175047
2120,latitude,011,111,-17.186618300771162,-2.6309683557964334,0.3883524875731684
2120,sampling_sign,000,010,-7.054049248089008,-0.370335870799396,0.06506925900425198
2120,sampling_sign,100,110,0.28341131237937844,0.08506806473390682,-0.0035918806400843106
2120,sampling_sign,001,011,-7.054049248089008,-0.370335870799396,0.06506925900425198
2120,sampling_sign,101,111,0.28341131237937844,0.08506806473390682,-0.0035918806400843106
2120,seam,000,001,0.0,0.0,0.0
2120,seam,100,101,0.0,0.0,0.0
2120,seam,010,011,0.0,0.0,0.0
2120,seam,110,111,0.0,0.0,0.0
2122,latitude,000,100,-8.314271635641248,-2.7257403997366225,0.3672001115516502
2122,latitude,010,110,-7.370483055800854,-2.973917738272174,0.33786369302441666
2122,latitude,001,101,-8.314271635641248,-2.7257403997366225,0.3672001115516502
2122,latitude,011,111,-7.370483055800854,-2.973917738272174,0.33786369302441666
2122,sampling_sign,000,010,-0.4345840394997751,0.1028188124534779,0.013410824775982086
2122,sampling_sign,100,110,0.5092045403406189,-0.14535852608207378,-0.015925593751251466
2122,sampling_sign,001,011,-0.4345840394997751,0.1028188124534779,0.013410824775982086
2122,sampling_sign,101,111,0.5092045403406189,-0.14535852608207378,-0.015925593751251466
2122,seam,000,001,0.0,0.0,0.0
2122,seam,100,101,0.0,0.0,0.0
2122,seam,010,011,0.0,0.0,0.0
2122,seam,110,111,0.0,0.0,0.0
2124,latitude,000,100,-30.360101457225724,-8.876570881589503,0.5393081457374601
2124,latitude,010,110,-28.023131628356012,-6.509366645785162,0.5586544472473947
2124,latitude,001,101,-30.360101457225724,-8.876570881589503,0.5393081457374601
2124,latitude,011,111,-28.023131628356012,-6.509366645785162,0.5586544472473947
2124,sampling_sign,000,010,-3.1783020003269655,-2.5548525942397724,-0.006978152690506306
2124,sampling_sign,100,110,-0.8413321714572533,-0.18764835843543182,0.01236814881942827
2124,sampling_sign,001,011,-3.1783020003269655,-2.5548525942397724,-0.006978152690506306
2124,sampling_sign,101,111,-0.8413321714572533,-0.18764835843543182,0.01236814881942827
2124,seam,000,001,0.0,0.0,0.0
2124,seam,100,101,0.0,0.0,0.0
2124,seam,010,011,0.0,0.0,0.0
2124,seam,110,111,0.0,0.0,0.0

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/literal_original_metrics.csv (452 bytes; 3 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/literal_original_metrics.csv", "bytes": 452, "sha256": "8309d618d7d947c836580af3db4c2ad5503bf2aff5d03c3076cce4865425b56f", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,variant,finite_output_pixels,status,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G
2120,literal_original_on_available_HMI,0,not observationally scoreable on these NaN-containing HMI inputs,0,,,,,,
2122,literal_original_on_available_HMI,0,not observationally scoreable on these NaN-containing HMI inputs,0,,,,,,
2124,literal_original_on_available_HMI,0,not observationally scoreable on these NaN-containing HMI inputs,0,,,,,,

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/longitude_sources.csv (6,008 bytes; 24 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/longitude_sources.csv", "bytes": 6008, "sha256": "290059fe8e5475193805d0af1a2608a67c39aaceb1be670242114afea26cb7e9", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,variant,shift_min_deg,shift_max_deg,shift_mean_abs_deg,sample_longitude_min_deg,sample_longitude_max_deg,finite_reconstruction_pixels,finite_reconstruction_area_fraction,previous_query_count,previous_query_area_fraction,previous_finite_count,previous_observation_mask_count,current_query_count,current_query_area_fraction,current_finite_count,current_observation_mask_count,next_query_count,next_query_area_fraction,next_finite_count,next_observation_mask_count
2120,000,-50.94275097671721,50.91441796724884,15.164071938359465,-1.981085935460336,362.0823553211615,257018,0.9916212277777777,32,0.00012302222222222188,16,0,259132,0.9997386333333332,256986,25693,36,0.00013834444444444396,16,0
2120,100,-50.537333067299755,50.5092255405398,6.66120285145406,-2.1502129054082713,362.25157640739775,256844,0.9909497666666666,314,0.0012115166666666667,268,0,258554,0.9975075166666665,256308,25693,332,0.0012809666666666669,268,0
2120,010,-50.91441796724884,50.94275097671721,15.164071938359465,-50.61441796720227,410.7427509767638,256434,0.98936785,17876,0.06897156666666666,17766,0,223372,0.8617636333333333,220894,25693,17952,0.06926479999999999,17774,0
2120,001,-50.94275097671721,50.91441796724884,15.164071938359465,-1.981085935460336,362.0823553211615,257018,0.9916212277777777,36,0.00013834444444444396,16,0,259132,0.9997386333333332,256986,25693,32,0.00012302222222222188,16,0
2120,110,-50.5092255405398,50.537333067299755,6.66120285145406,-50.209225540493236,410.3373330673463,256594,0.9899851833333333,7966,0.03072670555555555,7646,0,243218,0.9383536722222222,241296,25693,8016,0.030919622222222217,7652,0
2120,101,-50.537333067299755,50.5092255405398,6.66120285145406,-2.1502129054082713,362.25157640739775,256844,0.9909497666666666,332,0.0012809666666666669,268,0,258554,0.9975075166666665,256308,25693,314,0.0012115166666666667,268,0
2120,011,-50.91441796724884,50.94275097671721,15.164071938359465,-50.61441796720227,410.7427509767638,256434,0.98936785,17952,0.06926479999999999,17774,0,223372,0.8617636333333333,220894,25693,17876,0.06897156666666666,17766,0
2120,111,-50.5092255405398,50.537333067299755,6.66120285145406,-50.209225540493236,410.3373330673463,256594,0.9899851833333333,8016,0.030919622222222217,7652,0,243218,0.9383536722222222,241296,25693,7966,0.03072670555555555,7646,0
2122,000,-50.94275097671721,50.91441796724884,15.164071938359465,-1.981085935460336,362.0823553211615,257021,0.9916328027777777,32,0.00012302222222222188,16,0,259132,0.9997386333333332,256986,25705,36,0.00013834444444444396,19,0
2122,100,-50.537333067299755,50.5092255405398,6.66120285145406,-2.1502129054082713,362.25157640739775,256844,0.9909497666666666,314,0.0012115166666666667,268,0,258554,0.9975075166666665,256308,25705,332,0.0012809666666666669,268,0
2122,010,-50.91441796724884,50.94275097671721,15.164071938359465,-50.61441796720227,410.7427509767638,256434,0.98936785,17876,0.06897156666666666,17766,0,223372,0.8617636333333333,220894,25705,17952,0.06926479999999999,17774,0
2122,001,-50.94275097671721,50.91441796724884,15.164071938359465,-1.981085935460336,362.0823553211615,257021,0.9916328027777777,36,0.00013834444444444396,16,0,259132,0.9997386333333332,256986,25705,32,0.00012302222222222188,19,0
2122,110,-50.5092255405398,50.537333067299755,6.66120285145406,-50.209225540493236,410.3373330673463,256671,0.990282275,7966,0.03072670555555555,7646,0,243218,0.9383536722222222,241296,25705,8016,0.030919622222222217,7729,0
2122,101,-50.537333067299755,50.5092255405398,6.66120285145406,-2.1502129054082713,362.25157640739775,256844,0.9909497666666666,332,0.0012809666666666669,268,0,258554,0.9975075166666665,256308,25705,314,0.0012115166666666667,268,0
2122,011,-50.91441796724884,50.94275097671721,15.164071938359465,-50.61441796720227,410.7427509767638,256434,0.98936785,17952,0.06926479999999999,17774,0,223372,0.8617636333333333,220894,25705,17876,0.06897156666666666,17766,0
2122,111,-50.5092255405398,50.537333067299755,6.66120285145406,-50.209225540493236,410.3373330673463,256671,0.990282275,8016,0.030919622222222217,7652,0,243218,0.9383536722222222,241296,25705,7966,0.03072670555555555,7723,0
2124,000,-50.94275097671721,50.91441796724884,15.164071938359465,-1.981085935460336,362.0823553211615,257738,0.9944386722222222,32,0.00012302222222222188,19,0,259132,0.9997386333333332,257700,25700,36,0.00013834444444444396,19,0
2124,100,-50.537333067299755,50.5092255405398,6.66120285145406,-2.1502129054082713,362.25157640739775,257564,0.9937677666666667,314,0.0012115166666666667,268,0,258554,0.9975075166666665,257028,25700,332,0.0012809666666666669,268,0
2124,010,-50.91441796724884,50.94275097671721,15.164071938359465,-50.61441796720227,410.7427509767638,257154,0.9921858499999999,17876,0.06897156666666666,17766,0,223372,0.8617636333333333,221614,25700,17952,0.06926479999999999,17774,0
2124,001,-50.94275097671721,50.91441796724884,15.164071938359465,-1.981085935460336,362.0823553211615,257738,0.9944386722222222,36,0.00013834444444444396,19,0,259132,0.9997386333333332,257700,25700,32,0.00012302222222222188,19,0
2124,110,-50.5092255405398,50.537333067299755,6.66120285145406,-50.209225540493236,410.3373330673463,257316,0.9928021222222222,7966,0.03072670555555555,7723,0,243218,0.9383536722222222,241864,25700,8016,0.030919622222222217,7729,0
2124,101,-50.537333067299755,50.5092255405398,6.66120285145406,-2.1502129054082713,362.25157640739775,257564,0.9937677666666667,332,0.0012809666666666669,268,0,258554,0.9975075166666665,257028,25700,314,0.0012115166666666667,268,0
2124,011,-50.91441796724884,50.94275097671721,15.164071938359465,-50.61441796720227,410.7427509767638,257154,0.9921858499999999,17952,0.06926479999999999,17774,0,223372,0.8617636333333333,221614,25700,17876,0.06897156666666666,17766,0
2124,111,-50.5092255405398,50.537333067299755,6.66120285145406,-50.209225540493236,410.3373330673463,257316,0.9928021222222222,8016,0.030919622222222217,7729,0,243218,0.9383536722222222,241864,25700,7966,0.03072670555555555,7723,0

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/map_differences.csv (20,085 bytes; 108 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/map_differences.csv", "bytes": 20085, "sha256": "9bd845a321484b9241b19b79fc5a71298d693fe967ccfcc1ec64519a6095c2e8", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,variant_a,variant_b,mask,surface_area_fraction,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G
2120,central,000,full sphere common central+all8,0.9868060277777777,255770,0.16716685637925505,11.723085600794967,37.64026197894446,0.10943607434659075,4.140085665896796,43.67513567499077
2120,central,100,full sphere common central+all8,0.9868060277777777,255770,0.014266482353809657,8.797609738429136,22.15716497649961,0.664985041681215,3.5815616310364913,32.637783795108824
2120,central,010,full sphere common central+all8,0.9868060277777777,255770,-0.14046783701056653,11.434607756180153,35.75469906225217,0.11746497559435368,4.103146193460413,42.35495905418644
2120,central,001,full sphere common central+all8,0.9868060277777777,255770,0.1675052025110173,11.722455369450529,37.640032237211585,0.10944229550847331,4.1396055891503565,43.67513567499077
2120,central,110,full sphere common central+all8,0.9868060277777777,255770,0.01517363542432544,8.775710994253672,22.088004340993567,0.6662963710508081,3.60212144969012,32.62025331256193
2120,central,101,full sphere common central+all8,0.9868060277777777,255770,0.013832975467804196,8.796588136854675,22.156062368976308,0.6650105989596706,3.580267371198201,32.63166397984587
2120,central,011,full sphere common central+all8,0.9868060277777777,255770,-0.07993548569625389,11.377247640057435,35.605294039126576,0.11806031712649144,4.09813548264656,42.07962689338431
2120,central,111,full sphere common central+all8,0.9868060277777777,255770,-0.017761984302554996,8.74232389308746,22.007352639326918,0.6681209675311587,3.5920654396342897,32.52054083047059
2120,000,100,full sphere common central+all8,0.9868060277777777,255770,-0.1529003740254454,12.180454832513382,37.47183127074089,0.10938110383178828,4.483307384318796,44.891795751058005
2120,000,010,full sphere common central+all8,0.9868060277777777,255770,-0.3076346933898215,12.185650469715183,38.45477572190929,0.05182981381741324,4.431845563259875,44.70227295303592
2120,000,001,full sphere common central+all8,0.9868060277777777,255770,0.00033834613176227,0.0013211600484843383,0.16543396188122333,0.9999839108783893,0.0,0.0
2120,000,110,full sphere common central+all8,0.9868060277777777,255770,-0.15199322095492962,12.465480405547574,37.87690557035224,0.08794278496971962,4.682436925921945,45.607829012694424
2120,000,101,full sphere common central+all8,0.9868060277777777,255770,-0.1533338809114509,12.18092670239769,37.47305343042304,0.10930340053381901,4.484034507916414,44.88889952937025
2120,000,011,full sphere common central+all8,0.9868060277777777,255770,-0.24710234207550894,12.122999608570021,38.33146784850149,0.051138407643961194,4.42079399103368,44.299120890336795
2120,000,111,full sphere common central+all8,0.9868060277777777,255770,-0.1849288406818101,12.436395316508447,37.83341959685952,0.08846234771319059,4.675922203977194,45.50369420589131
2120,100,010,full sphere common central+all8,0.9868060277777777,255770,-0.15473431936437618,12.24294753545696,36.13561614879248,0.08946718522004776,4.636447501492288,45.0059416245228
2120,100,001,full sphere common central+all8,0.9868060277777777,255770,0.15323872015720766,12.180419483826599,37.47171101967868,0.10938210228984778,4.483307384318796,44.889029528136724
2120,100,110,full sphere common central+all8,0.9868060277777777,255770,0.0009071530705157901,9.744223465017944,26.32190821571317,0.5213074654823333,3.995135840223706,35.56291481623086
2120,100,101,full sphere common central+all8,0.9868060277777777,255770,-0.00043350688600546475,0.01305966980360193,0.4771189606150746,0.9998430938284761,0.0,0.0
2120,100,011,full sphere common central+all8,0.9868060277777777,255770,-0.09420196805006356,12.186148350746919,36.011069043828364,0.08865736446457022,4.621697746946403,44.73531006693308
2120,100,111,full sphere common central+all8,0.9868060277777777,255770,-0.032028466656364635,9.727036846077612,26.281146013089682,0.5218832914271453,3.9860897158595203,35.534720299129035
2120,010,001,full sphere common central+all8,0.9868060277777777,255770,0.30797303952158384,12.184950052145977,38.45438749436349,0.05184402711091935,4.431697975976711,44.69970259140871
2120,010,110,full sphere common central+all8,0.9868060277777777,255770,0.15564147243489196,11.922513850960035,35.721359068461,0.10805286790588949,4.473882825719615,43.861338158285996
2120,010,101,full sphere common central+all8,0.9868060277777777,255770,0.1543008124783707,12.242107802778554,36.13513697923477,0.08946917188745956,4.636447501492288,45.01108487791493
2120,010,011,full sphere common central+all8,0.9868060277777777,255770,0.06053235131431266,1.7299837704611278,15.057571202108237,0.838783016293856,0.0,6.535025359374661
2120,010,111,full sphere common central+all8,0.9868060277777777,255770,0.12270585270801151,11.905198919062288,35.69272920108657,0.1077563527992261,4.46129522793807,43.7896371177213
2120,001,110,full sphere common central+all8,0.9868060277777777,255770,-0.15233156708669188,12.464881859343212,37.87656407304006,0.08795443492176856,4.682334560115117,45.60555661580481
2120,001,101,full sphere common central+all8,0.9868060277777777,255770,-0.15367222704321315,12.180891353710908,37.472933183282755,0.10930439880610136,4.484034507916414,44.888066774707106
2120,001,011,full sphere common central+all8,0.9868060277777777,255770,-0.2474406882072712,12.122299191000815,38.331078372060155,0.051152701900037734,4.420559184896405,44.29621432638152
2120,001,111,full sphere common central+all8,0.9868060277777777,255770,-0.18526718681357235,12.436145676308323,37.83321217827519,0.08846753102152423,4.675922203977194,45.49635560601252
2120,110,101,full sphere common central+all8,0.9868060277777777,255770,-0.0013406599565212553,9.74414304544846,26.32119870680506,0.5213217605161006,3.9963805188412653,35.55249404036199
2120,110,011,full sphere common central+all8,0.9868060277777777,255770,-0.09510912112057933,11.865966185224444,35.58350420580596,0.10798179719617929,4.457740981146758,43.54192808212157
2120,110,111,full sphere common central+all8,0.9868060277777777,255770,-0.03293561972688044,0.5314632366604464,3.8552558392001686,0.9896890333028778,0.0,1.4261780915468014
2120,101,011,full sphere common central+all8,0.9868060277777777,255770,-0.09376846116405807,12.185892549501663,36.010383996321494,0.08866970630038294,4.623100044546073,44.731312263647354
2120,101,111,full sphere common central+all8,0.9868060277777777,255770,-0.031594959770359164,9.726956426508128,26.280435403699606,0.5218975839543013,3.9880662315603685,35.513329544390395
2120,011,111,full sphere common central+all8,0.9868060277777777,255770,0.062173501393698885,11.833681367074522,35.53873554191652,0.10848838462963115,4.4359377093684,43.47402113456294
2122,central,000,full sphere common central+all8,0.9868060277777777,255770,0.21669297508605562,12.486446067452867,42.5334778521245,0.02087790275116282,4.067732626648269,45.006875223061094
2122,central,100,full sphere common central+all8,0.9868060277777777,255770,0.013918097535112053,8.723024319441691,22.462359675953838,0.7204216783652163,3.5522221008643173,31.845046896893702
2122,central,010,full sphere common central+all8,0.9868060277777777,255770,-0.12235143779201069,12.261350832557616,42.171715787056435,0.007757815198778794,4.042032415933933,43.91546725008881
2122,central,001,full sphere common central+all8,0.9868060277777777,255770,0.21659967565580146,12.486901907756913,42.533651110558814,0.02087157426882968,4.0680207704469415,45.006875223061094
2122,central,110,full sphere common central+all8,0.9868060277777777,255770,-0.009974208058226509,8.67787714915607,22.43860666304354,0.7203975489396162,3.5363831834189368,31.786705974267136
2122,central,101,full sphere common central+all8,0.9868060277777777,255770,0.013409187455263823,8.72201501913159,22.461594751904848,0.7204365072019919,3.5514411480267065,31.84700430581723
2122,central,011,full sphere common central+all8,0.9868060277777777,255770,-0.12388846520055044,12.471906800502897,42.56348263474456,0.0069016863091351695,4.067552486894801,44.722841328085345
2122,central,111,full sphere common central+all8,0.9868060277777777,255770,0.015205778924041203,8.709521326623332,22.51586136491386,0.7190213742922267,3.542500749442193,31.920278110649402
2122,000,100,full sphere common central+all8,0.9868060277777777,255770,-0.2027748775509435,12.937944441612846,42.40879413060355,0.016671732820030292,4.416719922314991,45.586685568132154
2122,000,010,full sphere common central+all8,0.9868060277777777,255770,-0.33904441287806625,12.832145838135203,42.62368647020797,9.131587831165259e-05,4.369088155277061,45.922767917278414
2122,000,001,full sphere common central+all8,0.9868060277777777,255770,-9.329943025413226e-05,0.001329262180500472,0.15793280862137207,0.999986676674804,0.0,0.0
2122,000,110,full sphere common central+all8,0.9868060277777777,255770,-0.22666718314428208,13.107617465237674,42.52119529273088,0.009239734485464668,4.591527596347097,46.08232286656763
2122,000,101,full sphere common central+all8,0.9868060277777777,255770,-0.20328378763079172,12.936349547942381,42.40733494650419,0.016724531067428758,4.4163186507116166,45.579798704891864
2122,000,011,full sphere common central+all8,0.9868060277777777,255770,-0.34058144028660603,12.996073677763817,42.654770534354675,0.0159040977244945,4.392742388636949,46.96228450274349
2122,000,111,full sphere common central+all8,0.9868060277777777,255770,-0.20148719616201438,13.144955041630316,42.56893442894908,0.008990442109657958,4.604592790146744,46.34985392744669
2122,100,010,full sphere common central+all8,0.9868060277777777,255770,-0.13626953532712277,12.922257739639996,42.17519333190945,-0.0028529230580374523,4.569314354316843,44.88664540275261
2122,100,001,full sphere common central+all8,0.9868060277777777,255770,0.20268157812068938,12.938049443135899,42.40884755234883,0.01667092999341557,4.416719922314991,45.586685568132154
2122,100,110,full sphere common central+all8,0.9868060277777777,255770,-0.023892305593338537,9.814142174633602,27.227484933761726,0.5839172176116774,3.9509260469319365,35.075070113992076
2122,100,101,full sphere common central+all8,0.9868060277777777,255770,-0.0005089100798482301,0.014279280584070804,0.5796600347880098,0.9998118417394227,0.0,0.0
2122,100,011,full sphere common central+all8,0.9868060277777777,255770,-0.13780656273566252,13.121357157829344,42.547994665362324,-0.0026369296813307966,4.599636564394501,45.651213169542494
2122,100,111,full sphere common central+all8,0.9868060277777777,255770,0.0012876813889291677,9.855145611522005,27.296013027172403,0.582673637327497,3.9616713885214807,35.373202706311595
2122,010,001,full sphere common central+all8,0.9868060277777777,255770,0.3389511134478121,12.832309137514711,42.62378186274703,8.853879161447509e-05,4.368978518056245,45.922767917278414
2122,010,110,full sphere common central+all8,0.9868060277777777,255770,0.11237722973378422,12.661413372486727,42.111044989904975,-0.002119668339676273,4.390324023093639,44.126961439328305
2122,010,101,full sphere common central+all8,0.9868060277777777,255770,0.13576062524727453,12.922003267000374,42.175719445772366,-0.002893802785667851,4.569212486807093,44.89406899710603
2122,010,011,full sphere common central+all8,0.9868060277777777,255770,-0.0015370274085397461,2.0119176837270003,18.631669792839624,0.8065662963645605,0.0,6.700583021327743
2122,010,111,full sphere common central+all8,0.9868060277777777,255770,0.13755721671605192,12.701853154050019,42.15631353051777,-0.002203625015754729,4.402781676844288,44.39675451999381
2122,001,110,full sphere common central+all8,0.9868060277777777,255770,-0.2265738837140279,13.107375224146903,42.520895798019716,0.009255385504156612,4.591527596347097,46.05495651486664
2122,001,101,full sphere common central+all8,0.9868060277777777,255770,-0.20319048820053762,12.936454549465434,42.407388370087645,0.01672372808786512,4.4163186507116166,45.579798704891864
2122,001,011,full sphere common central+all8,0.9868060277777777,255770,-0.34048814085635193,12.996236977143328,42.654865857377914,0.015901342793648344,4.392640824842815,46.96228450274349
2122,001,111,full sphere common central+all8,0.9868060277777777,255770,-0.2013938967317602,13.144866930837516,42.569004225709286,0.008988880137573233,4.604517253429668,46.35401310466199
2122,110,101,full sphere common central+all8,0.9868060277777777,255770,0.02338339551349031,9.813253308476098,27.227274085636743,0.5839171099045817,3.9508451417759973,35.08444669191365
2122,110,011,full sphere common central+all8,0.9868060277777777,255770,-0.11391425714232396,12.872607428367086,42.46601091231795,-0.0010485817991695977,4.422485310305754,45.140498017635196
2122,110,111,full sphere common central+all8,0.9868060277777777,255770,0.025179986982267706,0.5135797948644533,3.6601855195096067,0.9924813638634667,0.0,1.358604694386098
2122,101,011,full sphere common central+all8,0.9868060277777777,255770,-0.1372976526558143,13.120965501735327,42.548501356301,-0.002676389060968205,4.599277625029362,45.667113632627895
2122,101,111,full sphere common central+all8,0.9868060277777777,255770,0.0017965914687773977,9.854256745364502,27.295802708396945,0.5826735434507464,3.961621424421639,35.3793164870535
2122,011,111,full sphere common central+all8,0.9868060277777777,255770,0.1390942441245917,12.902184893271647,42.50741877218895,-0.000969092916007582,4.429597788715011,45.3997086974604
2124,central,000,full sphere common central+all8,0.9884278333333334,256180,0.29015919668204543,14.528144659886875,54.9897144681864,0.029459724387448365,4.172036143038815,52.39826767063842
2124,central,100,full sphere common central+all8,0.9884278333333334,256180,0.0313601322284991,9.206357133956677,26.61207188494279,0.7466769722390447,3.62291846820274,31.83251636641648
2124,central,010,full sphere common central+all8,0.9884278333333334,256180,-0.08267082623378715,13.348372566914813,49.6565861765397,0.05724286001051621,4.075863534400103,47.83957780357968
2124,central,001,full sphere common central+all8,0.9884278333333334,256180,0.28884230481354123,14.526729163420375,54.98916137914722,0.02947429383927746,4.1715643641412985,52.396545963168634
2124,central,110,full sphere common central+all8,0.9884278333333334,256180,-0.01311760265832816,9.210270253929561,26.544624788546564,0.7475471696503018,3.6292996394061676,31.985637872835568
2124,central,101,full sphere common central+all8,0.9884278333333334,256180,0.030395731131114517,9.204295386536758,26.610666483902033,0.74669650210572,3.6207276190284494,31.82717811737629
2124,central,011,full sphere common central+all8,0.9884278333333334,256180,-0.14994985099997254,13.318176863240154,49.58950368646424,0.05725973274318384,4.082128386534,47.98285451639152
2124,central,111,full sphere common central+all8,0.9884278333333334,256180,-0.021209729350615138,9.189856143482306,26.524028779904526,0.7478773493653511,3.6280305349800432,31.897128132925737
2124,000,100,full sphere common central+all8,0.9884278333333334,256180,-0.2587990644535464,14.9090625550092,54.716900795811426,0.033072702444267,4.5582002324430135,52.21056149408099
2124,000,010,full sphere common central+all8,0.9884278333333334,256180,-0.3728300229158326,14.67808893207991,53.51486616521161,0.017960263379077947,4.435869830171329,52.18827559142459
2124,000,001,full sphere common central+all8,0.9884278333333334,256180,-0.0013168918685041698,0.0020786742087643183,0.2655125779923466,0.9999793594630395,0.0,0.0
2124,000,110,full sphere common central+all8,0.9884278333333334,256180,-0.30327679934037355,15.173157369022793,55.00610933212845,0.02129399832766869,4.729308610337011,53.018399282124236
2124,000,101,full sphere common central+all8,0.9884278333333334,256180,-0.25976346555093094,14.907153460414328,54.716311229130696,0.03306841236837493,4.557329634790658,52.21056149408099
2124,000,011,full sphere common central+all8,0.9884278333333334,256180,-0.4401090476820181,14.626165075546679,53.43223009608033,0.018650541552017844,4.436591406086283,52.19802590918147
2124,000,111,full sphere common central+all8,0.9884278333333334,256180,-0.3113689260326606,15.150344346282598,54.9948737405509,0.02147542371192252,4.71918961340543,52.892302203067175
2124,100,010,full sphere common central+all8,0.9884278333333334,256180,-0.11403095846228627,13.967166007255429,49.70024028701061,0.04846930993689397,4.632227932106293,48.058954315865144
2124,100,001,full sphere common central+all8,0.9884278333333334,256180,0.2574821725850422,14.908740659669252,54.71671383654499,0.033074305259830274,4.558096060942299,52.203107856029305
2124,100,110,full sphere common central+all8,0.9884278333333334,256180,-0.044477734886827276,10.49067923850254,32.62794610589674,0.6158636812224358,4.025916126798471,35.45294774022771
2124,100,101,full sphere common central+all8,0.9884278333333334,256180,-0.0009644010973845784,0.013729151205963235,0.5430357445000513,0.9998937710880849,0.0,0.0
2124,100,011,full sphere common central+all8,0.9884278333333334,256180,-0.1813099832284717,13.939770788394485,49.64350863533983,0.04806522072786935,4.636611692793841,48.29278853594242
2124,100,111,full sphere common central+all8,0.9884278333333334,256180,-0.05256986157911424,10.473265665799206,32.61536741445934,0.6160634117114188,4.023087199832206,35.37855067558283
2124,010,001,full sphere common central+all8,0.9884278333333334,256180,0.3715131310473284,14.677694165550573,53.5146413231373,0.01796305404358985,4.435994466619248,52.18827559142459
2124,010,110,full sphere common central+all8,0.9884278333333334,256180,0.06955322357545898,13.76367958748598,49.48811943575549,0.0548802402943397,4.4775376468498145,47.7630256509188
2124,010,101,full sphere common central+all8,0.9884278333333334,256180,0.11306655736490166,13.965412599134886,49.69969620052086,0.04846016742977126,4.6311616226085635,48.046417994337894
2124,010,011,full sphere common central+all8,0.9884278333333334,256180,-0.06727902476618543,1.5653060519718451,13.337148836201207,0.9261391107824977,0.0,6.0847335456482705
2124,010,111,full sphere common central+all8,0.9884278333333334,256180,0.06146109688317201,13.75017597183506,49.482029334718504,0.05485611977390596,4.470185980521797,47.69541172249031
2124,001,110,full sphere common central+all8,0.9884278333333334,256180,-0.3019599074718694,15.173103591927747,55.00567615212324,0.02130435970892566,4.729592234605992,52.9884273266724
2124,001,101,full sphere common central+all8,0.9884278333333334,256180,-0.2584465736824268,14.90683156507438,54.716124267849764,0.03307001438233693,4.5572537219956475,52.203107856029305
2124,001,011,full sphere common central+all8,0.9884278333333334,256180,-0.4387921558135139,14.625770309017339,53.432004906273136,0.018653281395251783,4.4367212955729975,52.19802590918147
2124,001,111,full sphere common central+all8,0.9884278333333334,256180,-0.3100520341641564,15.149464868461251,54.994601317316175,0.02148002492212072,4.718857377784856,52.892302203067175
2124,110,101,full sphere common central+all8,0.9884278333333334,256180,0.0435133337894427,10.488315632012299,32.62689508726041,0.6158771123301627,4.0232614223726015,35.444330537413585
2124,110,011,full sphere common central+all8,0.9884278333333334,256180,-0.1368322483416444,13.73863789076858,49.42467404101669,0.05473991639547458,4.484873513247511,47.87850092904061
2124,110,111,full sphere common central+all8,0.9884278333333334,256180,-0.008092126692286972,0.4629562564984031,2.9617206482163825,0.9968287479418242,0.0,1.2342840948893445
2124,101,011,full sphere common central+all8,0.9884278333333334,256180,-0.18034558213108712,13.937083060071284,49.642826888985695,0.0480612553204082,4.633887470781271,48.28710003409322
2124,101,111,full sphere common central+all8,0.9884278333333334,256180,-0.05160546048172967,10.470902059308964,32.61431599046608,0.6160768418680974,4.021412817737049,35.363681257995445
2124,011,111,full sphere common central+all8,0.9884278333333334,256180,0.12874012164935741,13.714471245810342,49.41445354101685,0.05487335124088182,4.477415523056851,47.789272847380076

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/metrics.csv (8,008 bytes; 27 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/metrics.csv", "bytes": 8008, "sha256": "265ceba4718becee3c3b654a8ce6c3e2311b0baea52b42aa8cd26f2e4cf28c7c", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,variant,reference,mask,surface_area_fraction,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G,rmse_improvement_vs_000_pct,rmse_improvement_vs_central_pct,mae_improvement_vs_000_pct,mae_improvement_vs_central_pct
2120,central,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,0.07300365545127543,9.018476889881612,23.821126003867285,0.8253540465211998,3.5970908714239576,33.714142498492095,50.58750888905096,0.0,25.490226195142608,0.0
2120,000,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,-0.33682984001317695,12.103750191889167,48.20871295555648,0.36943650074569223,4.037766184336146,39.63066146217111,0.0,-102.37797721119458,0.0,-34.210580563433226
2120,100,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,0.032412898172098636,9.017377900559431,23.68463409431693,0.826450127963197,3.7039580519450275,32.63031421516575,50.87063594468546,0.5729868081307155,25.499305937410554,0.012185974811484979
2120,010,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,-0.08041155933081816,11.733414321089771,41.15466370746747,0.4345057597499442,4.1279598072324,41.89413162053009,14.63231191131803,-72.76540034583647,3.05967873533578,-30.10416796936317
2120,001,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,-0.33682984001317695,12.103750191889167,48.20871295555648,0.36943650074569223,4.037766184336146,39.63066146217111,0.0,-102.37797721119458,0.0,-34.210580563433226
2120,110,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,0.09644029115472545,9.102445965293338,23.96804540669631,0.8228582473231126,3.6781011279182803,33.79332478177807,50.28275193989848,-0.6167609491053216,24.796481908615654,-0.9310782345734792
2120,101,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,0.032412898172098636,9.017377900559431,23.68463409431693,0.826450127963197,3.7039580519450275,32.63031421516575,50.87063594468546,0.5729868081307155,25.499305937410554,0.012185974811484979
2120,011,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,-0.08041155933081816,11.733414321089771,41.15466370746747,0.4345057597499442,4.1279598072324,41.89413162053009,14.63231191131803,-72.76540034583647,3.05967873533578,-30.10416796936317
2120,111,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09913215833333333,25693,0.09644029115472545,9.102445965293338,23.96804540669631,0.8228582473231126,3.6781011279182803,33.79332478177807,50.28275193989848,-0.6167609491053216,24.796481908615654,-0.9310782345734792
2122,central,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.15753879017161634,11.503933919466728,35.247419514037766,0.3880825550285347,3.7997154874047503,44.504034496960145,18.934131724658197,0.0,20.406083555820832,0.0
2122,000,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.40642512491024374,14.4532829057792,43.47997531380188,0.01585270032178364,4.441013293690263,58.425510007968576,0.0,-23.356478043691652,0.0,-25.637742766599537
2122,100,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.1939411017110041,11.727542506042578,35.16570367816063,0.3830528118734339,3.9612937116827105,44.69671553878898,19.122070736323625,0.2318349456606028,18.85897077851236,-1.9437575714639888
2122,010,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.49960759978547364,14.556101718232679,43.045391274302105,0.029263525097765725,4.4713601842491695,60.142661432696606,0.9995038781952181,-22.123525261639898,-0.7113872545341682,-26.53151365552555
2122,001,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.40642512491024374,14.4532829057792,43.47997531380188,0.01585270032178364,4.441013293690263,58.425510007968576,0.0,-23.356478043691652,0.0,-25.637742766599537
2122,110,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.13196486640325156,11.582183979960504,35.67490821850125,0.3671272181221824,3.9187116645104103,43.54520285364831,17.950946473566788,-1.2128226983913803,19.86468364685975,-0.6802026249591364
2122,101,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.1939411017110041,11.727542506042578,35.16570367816063,0.3830528118734339,3.9612937116827105,44.69671553878898,19.122070736323625,0.2318349456606028,18.85897077851236,-1.9437575714639888
2122,011,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.49960759978547364,14.556101718232679,43.045391274302105,0.029263525097765725,4.4713601842491695,60.142661432696606,0.9995038781952181,-22.123525261639898,-0.7113872545341682,-26.53151365552555
2122,111,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09917845833333333,25705,0.13196486640325156,11.582183979960504,35.67490821850125,0.3671272181221824,3.9187116645104103,43.54520285364831,17.950946473566788,-1.2128226983913803,19.86468364685975,-0.6802026249591364
2124,central,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.07386621646472177,14.82415463532096,43.17068507717338,0.6929857586079816,4.237868604841771,64.11612702260734,41.37749948207983,0.0,37.94311529949166,0.0
2124,000,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,0.03964899189660444,23.888009697656525,73.64183495375916,0.15004868794373635,5.266227155703948,112.83024830969272,0.0,-70.58296578364349,0.0,-61.1424751381064
2124,100,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.07133106477028843,15.011438816067022,43.281733496533434,0.6893568336811965,4.4150501987527715,64.48571556000572,41.22670419102036,-0.25723107975130777,37.15910615383046,-1.2633717426275837
2124,010,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.3798170542073068,21.333157103416752,70.46353295343219,0.14307053525323005,4.977973717742509,94.78996649909243,4.31589191432108,-63.220789356178145,10.695125406326378,-43.90808533922761
2124,001,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,0.03964899189660444,23.888009697656525,73.64183495375916,0.15004868794373635,5.266227155703948,112.83024830969272,0.0,-70.58296578364349,0.0,-61.1424751381064
2124,110,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.06550874647405848,14.82379045763159,42.44040132507618,0.7017249825006248,4.337383440618488,63.78467454628184,42.36916916624204,1.6916195580211957,37.94463982034534,0.0024566506376166863
2124,101,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.07133106477028843,15.011438816067022,43.281733496533434,0.6893568336811965,4.4150501987527715,64.48571556000572,41.22670419102036,-0.25723107975130777,37.15910615383046,-1.2633717426275837
2124,011,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.3798170542073068,21.333157103416752,70.46353295343219,0.14307053525323005,4.977973717742509,94.78996649909243,4.31589191432108,-63.220789356178145,10.695125406326378,-43.90808533922761
2124,111,HMI45s radial estimate,common central+all8; finite observation; mu>=0.8,0.09915916666666666,25700,-0.06550874647405848,14.82379045763159,42.44040132507618,0.7017249825006248,4.337383440618488,63.78467454628184,42.36916916624204,1.6916195580211957,37.94463982034534,0.0024566506376166863

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/original_grid_sensitivity.csv (788 bytes; 3 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/original_grid_sensitivity.csv", "bytes": 788, "sha256": "9d5d20be3778deb7937355cbb13bb3538d8757084cc790265fa3e561a32e8000", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,variant,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G,map_rmse_vs_physical_000_G,max_abs_map_difference_G
2120,original_grid_with_explicit_row_omission_then_resampling,25693,-0.3298104972320738,12.193761746779428,48.83448268919418,0.3527805867815168,4.068731179982321,39.544173424742546,5.442663153702916,197.0240530614795
2122,original_grid_with_explicit_row_omission_then_resampling,25705,0.39861140141140394,14.499693270839284,43.464059677523686,0.01419326081586119,4.447873613875848,58.66606948386165,3.594590173425287,76.0382681142739
2124,original_grid_with_explicit_row_omission_then_resampling,25700,0.040755176315771593,23.923843446235363,73.50094033159205,0.1530915409394929,5.352525780864173,111.30116013639508,5.5684554203688545,109.22216689884249

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/pooled_metrics.csv (1,899 bytes; 9 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/pooled_metrics.csv", "bytes": 1899, "sha256": "e8e894ae2a97e9b3087745dd633c1ad78898ca12f8a62caffda59b99e936e577", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
variant,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G,rmse_improvement_vs_000_pct,rmse_improvement_vs_central_pct,mae_improvement_vs_000_pct,mae_improvement_vs_central_pct
central,77098,0.05223035302767479,11.782421363191903,34.993890538113945,0.6759306338904346,3.8726692764998534,46.82928245651353,38.2600441666151,0.0,29.930306484395818,0.0
000,77098,0.03647264323461036,16.81528885318731,56.679487482223884,0.1949495307036008,4.535853022606738,68.35291683009395,0.0,-61.969665592029145,0.0,-42.71505266072055
100,77098,0.051685286876711166,11.919037434042654,34.98132877484089,0.6738777027159623,4.010646500146773,46.86930795653733,38.282206969828515,0.03589701825058578,29.117854958623447,-1.1594906228488577
010,77098,0.013166370923643962,15.874514856114828,53.26612900599113,0.20451801411090642,4.486456179893626,62.83043451177,6.022211258179189,-52.21551015591077,5.594753710663502,-34.73049695630952
001,77098,0.03647264323461036,16.81528885318731,56.679487482223884,0.1949495307036008,4.535853022606738,68.35291683009395,0.0,-61.969665592029145,0.0,-42.71505266072055
110,77098,0.054300014360302955,11.836371866355783,34.87377105676477,0.6766985280088064,3.9672077903790064,46.47277620688039,38.47197177338264,0.3432584359785551,29.609464519473793,-0.45788977919616336
101,77098,0.051685286876711166,11.919037434042654,34.98132877484089,0.6738777027159623,4.010646500146773,46.86930795653733,38.282206969828515,0.03589701825058578,29.117854958623447,-1.1594906228488577
011,77098,0.013166370923643962,15.874514856114828,53.26612900599113,0.20451801411090642,4.486456179893626,62.83043451177,6.022211258179189,-52.21551015591077,5.594753710663502,-34.73049695630952
111,77098,0.054300014360302955,11.836371866355783,34.87377105676477,0.6766985280088064,3.9672077903790064,46.47277620688039,38.47197177338264,0.3432584359785551,29.609464519473793,-0.45788977919616336

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/registration_metrics.csv (970 bytes; 6 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/registration_metrics.csv", "bytes": 970, "sha256": "4e03f7d801762441d32247a44f44be3e72aa50931d7f980c95864949f20dcaf5", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,orientation,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G
2120,positive_physical_step,25693,0.07300365545127543,9.018476889881612,23.821126003867285,0.8253540465211998,3.5970908714239576,33.714142498492095
2120,negative_header_step,25693,0.060736224025826215,13.395545648523413,54.62316855247139,0.03515812782779947,4.241517425519795,44.83742320608506
2122,positive_physical_step,25705,0.15753879017161634,11.503933919466728,35.247419514037766,0.3880825550285347,3.7997154874047503,44.504034496960145
2122,negative_header_step,25705,0.16411003740971178,15.161804329412266,44.19881564813937,-0.03156460666764174,4.648344338431687,62.07963094752859
2124,positive_physical_step,25700,-0.07386621646472177,14.82415463532096,43.17068507717338,0.6929857586079816,4.237868604841771,64.11612702260734
2124,negative_header_step,25700,-0.06761062869247461,25.89156253784061,74.07640276320913,0.04881719466262143,5.707146835489512,128.93460449179088

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/registration_offset_sensitivity.csv (8,338 bytes; 45 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/registration_offset_sensitivity.csv", "bytes": 8338, "sha256": "3469bf54afddfb40f9be24bd7d90dcfbb4af34ad34012dc54c109b785a41d199", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,source_query_longitude_offset_deg,source_query_latitude_offset_deg,mask,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G
2120,-1.0,-0.5,common all registration offsets and primary mask,25693,0.045810555966442255,11.827800675045433,47.91970960628867,0.2840744302090877,4.138999347677306,38.73244951686863
2120,-1.0,0.0,common all registration offsets and primary mask,25693,0.04318924184039099,11.69052131271354,47.4815205386315,0.30503549116301887,3.998754802111889,39.115591165240886
2120,-1.0,0.5,common all registration offsets and primary mask,25693,0.054577885105856414,12.063205085645839,50.978384276818936,0.19365755642730093,4.096070790324687,38.89732795717899
2120,-0.5,-0.5,common all registration offsets and primary mask,25693,0.06953675682682003,10.93352326839148,39.56136159804039,0.5125558150384706,4.029087577180745,37.33393413842253
2120,-0.5,0.0,common all registration offsets and primary mask,25693,0.06458383562514981,10.43269312388969,35.13154774546076,0.6199780903583942,3.8593379625376882,36.39995892000675
2120,-0.5,0.5,common all registration offsets and primary mask,25693,0.06284036846557,11.216673456455776,43.39043846940411,0.4159479256916856,4.002212472581592,37.13795689421986
2120,0.0,-0.5,common all registration offsets and primary mask,25693,0.06816947103676592,10.453736864420092,35.78716109299785,0.601311693049298,3.9208493375808318,35.68610618030543
2120,0.0,0.0,common all registration offsets and primary mask,25693,0.07300365545127538,9.018476889881612,23.821126003867285,0.8253540465212,3.5970908714239576,33.714142498492095
2120,0.0,0.5,common all registration offsets and primary mask,25693,0.08310752287878313,10.666115890000034,37.770458451757115,0.5583327318674645,3.970803929616191,36.1481718828175
2120,0.5,-0.5,common all registration offsets and primary mask,25693,0.06793197569246014,11.257802964610134,43.97774485158523,0.39781465267187466,4.0125826570599425,36.40896863507179
2120,0.5,0.0,common all registration offsets and primary mask,25693,0.09266287777405499,10.661915772489369,37.44087837616218,0.5691319971700906,3.8471398649302846,37.11361415425111
2120,0.5,0.5,common all registration offsets and primary mask,25693,0.12813801642653797,11.233170518441588,42.871344049939815,0.43347984770902787,3.9900867974293637,37.97217204400832
2120,1.0,-0.5,common all registration offsets and primary mask,25693,0.10297682627756242,12.056623820031469,51.03224544265547,0.19046600185726864,4.136130649329252,37.73958228253595
2120,1.0,0.0,common all registration offsets and primary mask,25693,0.15880477393127096,11.891657664118105,49.46828644227509,0.250892584917503,4.007549375061115,39.509697540375946
2120,1.0,0.5,common all registration offsets and primary mask,25693,0.1579862750181167,12.18187993395925,50.21780059121484,0.22589828031370396,4.203193851208796,39.66289289058889
2122,-1.0,-0.5,common all registration offsets and primary mask,25705,0.05820841182331759,13.307744379315752,40.253218754784506,0.17567575531314167,4.411837640832067,51.87595469747815
2122,-1.0,0.0,common all registration offsets and primary mask,25705,0.1299208934138663,13.009264552063083,39.05851607219192,0.2374401526961273,4.259926271037148,51.322545894941335
2122,-1.0,0.5,common all registration offsets and primary mask,25705,0.19559863809127737,13.097106633222815,37.958371472154525,0.2732327382664588,4.435730181031468,50.77184936872766
2122,-0.5,-0.5,common all registration offsets and primary mask,25705,0.08687938485854806,12.925202368924504,38.98507045587874,0.23249304839749452,4.347966365005356,50.26317129273691
2122,-0.5,0.0,common all registration offsets and primary mask,25705,0.15737316123564773,12.247912303949581,37.40704653877206,0.30506735622700787,4.0841897978216135,47.28120287581184
2122,-0.5,0.5,common all registration offsets and primary mask,25705,0.20642354906492685,12.499807533509093,35.6425755477476,0.365617037363278,4.321836246764172,48.43394784622741
2122,0.0,-0.5,common all registration offsets and primary mask,25705,0.10592553217227821,12.517785390317977,38.086040676405936,0.27044189370617167,4.204696762950025,48.32145276328529
2122,0.0,0.0,common all registration offsets and primary mask,25705,0.15753879017161626,11.503933919466728,35.247419514037766,0.3880825550285347,3.799715487404752,44.504034496960145
2122,0.0,0.5,common all registration offsets and primary mask,25705,0.21153097956875047,12.393419735329967,35.1430770219205,0.38554598561532505,4.236461596690784,48.70064734042398
2122,0.5,-0.5,common all registration offsets and primary mask,25705,0.11706297583523083,12.797327577985046,38.1913023941469,0.2666986760247192,4.267203301929776,49.69883901626701
2122,0.5,0.0,common all registration offsets and primary mask,25705,0.1558166158244961,12.295728858765754,36.26353049540308,0.3508649753931619,4.0946656360966625,48.23738491331078
2122,0.5,0.5,common all registration offsets and primary mask,25705,0.2075649340960687,12.938952650758651,37.67857331278025,0.28813071741259727,4.358815168456777,50.98487600789238
2122,1.0,-0.5,common all registration offsets and primary mask,25705,0.1300034147978817,13.277654118184442,39.26987816626249,0.22233846337891985,4.418429564639615,52.30767527695921
2122,1.0,0.0,common all registration offsets and primary mask,25705,0.17509727055057797,13.219480213410323,38.68477067677695,0.2564450796549526,4.305547004476265,53.033463896230344
2122,1.0,0.5,common all registration offsets and primary mask,25705,0.2155491618686397,13.59344059330277,40.44129562672486,0.17437138203946073,4.432726971956136,53.60851014603411
2124,-1.0,-0.5,common all registration offsets and primary mask,25700,0.12980186742985148,20.074093076667697,61.4109832946847,0.36328886607134214,5.073200777381597,91.29710447590898
2124,-1.0,0.0,common all registration offsets and primary mask,25700,0.11768243907343333,19.50131481852564,61.327618715973095,0.37250817446232415,4.8951224293435,86.84703098051126
2124,-1.0,0.5,common all registration offsets and primary mask,25700,0.09848162525826457,20.06955042897751,63.582283829617474,0.31925293915062264,5.0869777778543055,88.5986289205171
2124,-0.5,-0.5,common all registration offsets and primary mask,25700,0.03612253988297379,18.182602607685883,53.88119058146716,0.5133815314822731,4.910116448386706,81.32374775266285
2124,-0.5,0.0,common all registration offsets and primary mask,25700,0.011564497647761983,16.89953021386351,50.90360061297807,0.5717577590611134,4.596457932247011,74.97227318871454
2124,-0.5,0.5,common all registration offsets and primary mask,25700,-0.014871228226690347,18.535632576343552,57.20924676713371,0.45311271553864985,4.802880128713799,83.36880768638329
2124,0.0,-0.5,common all registration offsets and primary mask,25700,-0.05783190641609731,17.61081182485458,50.42023140277592,0.5757400371189879,4.808068089395313,78.81793308155007
2124,0.0,0.0,common all registration offsets and primary mask,25700,-0.07386621646472168,14.82415463532096,43.17068507717339,0.6929857586079815,4.237868604841771,64.11612702260727
2124,0.0,0.5,common all registration offsets and primary mask,25700,-0.0817980083259719,17.99958625924324,52.440680837901795,0.5417920191608461,4.696912587405441,82.33301224603213
2124,0.5,-0.5,common all registration offsets and primary mask,25700,-0.11033530917085906,19.045324388725152,55.19952351144287,0.4921011622272388,4.905391193934818,86.44994925181794
2124,0.5,0.0,common all registration offsets and primary mask,25700,-0.10748734106296642,17.712950414356825,50.23152009326938,0.5844353057818578,4.657648898947337,81.73715939697853
2124,0.5,0.5,common all registration offsets and primary mask,25700,-0.11398913932107195,19.17397060101773,54.33669540144135,0.508139223989439,4.891644429165823,89.62816309393739
2124,1.0,-0.5,common all registration offsets and primary mask,25700,-0.13614832297984514,20.607937924596612,61.88099392744886,0.3616862943752186,5.0352943699958805,94.7615881551064
2124,1.0,0.0,common all registration offsets and primary mask,25700,-0.1301346948382256,20.151968117545323,59.52978022441012,0.4163797055262898,4.863479971015173,95.48115975404734
2124,1.0,0.5,common all registration offsets and primary mask,25700,-0.14691523787806346,20.58414922576495,60.266884459003265,0.3952927614889174,5.06418037272761,94.39602593310644

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/sample_br.csv (6,647 bytes; 21 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/sample_br.csv", "bytes": 6647, "sha256": "ac9e38bef00295fda4c8fc4288e302629b6764031d2c3068140c961d8cb4378c", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,selection,row,column,longitude_deg,latitude_deg,mu,reference_Br_G,Br_central_G,Br_000_G,Br_100_G,Br_010_G,Br_001_G,Br_110_G,Br_101_G,Br_011_G,Br_111_G,Br_111_exact_G
2120,nearest_fixed_coordinate,179,359,179.80000000004657,-0.15916788021174622,0.9928043519427036,-0.2954837481562531,-0.13658805191516876,-0.44234338532314454,-0.12465644915194152,0.057522477382797865,-0.44234338532314454,-0.1487983425128788,-0.12465644915194152,0.057522477382797865,-0.1487983425128788,-0.1486322546088312
2120,nearest_fixed_coordinate,133,329,164.80000000004657,-14.972416718222696,0.9563909317695386,69.38525471271652,2.2172653675079346,-0.5153972518870616,1.9457882036344805,-1.1915893334410517,-0.5153972518870616,2.5058402671304476,1.9457882036344805,-1.1915893334410517,2.5058402671304476,2.505407852627652
2120,nearest_fixed_coordinate,226,389,194.80000000004657,14.972416718222696,0.8946082817372117,8.625730042799733,5.77238130569458,4.403681498561486,5.249022358065109,1.9428802470475042,4.403681498561486,6.361410750058364,5.249022358065109,1.9428802470475042,6.361410750058364,6.3605070179343075
2120,nearest_fixed_coordinate,103,359,179.80000000004657,-25.152815520358722,0.9497715952330633,-1.248430577147361,-0.575173020362854,-0.6555927819396976,-0.5842689462272315,-0.47822431145628597,-0.6555927819396976,-0.5658925364975518,-0.5842689462272315,-0.47822431145628597,-0.5658925364975518,-0.5656831802722316
2120,nearest_fixed_coordinate,256,359,179.80000000004657,25.152815520358722,0.8452711524927194,1.9326643093495584,0.25711721181869507,0.33972435919160326,0.26842830354118924,0.1175349952168909,0.33972435919160326,0.24515710765738788,0.26842830354118924,0.1175349952168909,0.24515710765738788,0.24488271153700514
2120,largest_observed_positive,230,350,175.30000000004657,16.294704573797958,0.9144993916442384,1647.0390251603258,1420.1182861328125,530.7926674556965,1415.5595748918502,314.05603733564726,530.7926674556965,1424.589126111365,1415.5595748918502,314.05603733564726,1424.589126111365,1424.5928535135622
2120,largest_observed_negative,226,358,179.30000000004657,14.972416718222696,0.926618662481738,-1581.9669798437876,-1547.4432373046875,-1328.8610585028869,-1547.9503026513025,-1501.5661286014363,-1328.8610585028869,-1546.9261316958368,-1547.9503026513025,-1501.5661286014363,-1546.9261316958368,-1546.9268925961683
2122,nearest_fixed_coordinate,179,359,179.80000000004657,-0.15916788021174622,0.9954282099313826,7.788163124504827,17.191680908203125,17.506104637711577,17.15472387528885,16.022221035387133,17.506104637711577,17.226531487355555,17.15472387528885,16.022221035387133,17.226531487355555,17.226076638475902
2122,nearest_fixed_coordinate,133,329,164.80000000004657,-14.972416718222696,0.9526067069209303,2.1189465964760887,0.43359169363975525,2.4281871655797618,0.3425304303106763,5.3995895995040755,2.4281871655797618,0.5106879221370432,0.3425304303106763,5.3995895995040755,0.5106879221370432,0.5105855348358906
2122,nearest_fixed_coordinate,226,389,194.80000000004657,14.972416718222696,0.9034269907204625,0.437060102523264,0.191581130027771,7.519056276961885,0.04865765373219119,3.1714922715258016,7.519056276961885,0.32413852352049327,0.04865765373219119,3.1714922715258016,0.32413852352049327,0.32395306638559374
2122,nearest_fixed_coordinate,103,359,179.80000000004657,-25.152815520358722,0.9418686958757239,7.434428461652815,10.69138240814209,10.212463270198954,10.649653354174731,11.005733776036038,10.212463270198954,10.731270135100536,10.649653354174731,11.005733776036038,10.731270135100536,10.732140177493338
2122,nearest_fixed_coordinate,256,359,179.80000000004657,25.152815520358722,0.8580579178872993,2.925286863796753,0.11384384334087372,0.2835727152128311,0.12946106292453738,-0.014375631500822272,0.2835727152128311,0.09869329275806737,0.12946106292453738,-0.014375631500822272,0.09869329275806737,0.0983602079246732
2122,largest_observed_positive,199,407,203.80000000004657,6.21974794630384,0.8937116547244122,1268.154140936738,512.2832641601562,-16.285746488362655,672.1636731869017,1.3178679658366088,-16.285746488362655,252.9520296498363,672.1636731869017,1.3178679658366088,252.9520296498363,255.98365436799864
2122,largest_observed_negative,198,420,210.30000000004657,5.899623475286083,0.8433465935617507,-1004.0409519239521,4.913925647735596,-9.90687763156236,1.5141595964789343,0.5628074004690673,-9.90687763156236,4.299476083773675,1.5141595964789343,0.5628074004690673,4.299476083773675,4.319482199380161
2124,nearest_fixed_coordinate,179,359,179.80000000004657,-0.15916788021174622,0.9999727477355941,-2.23657146684999,0.5526965856552124,0.5916714183049201,0.5507308633601591,0.5097846554374688,0.5916714183049201,0.5546532666169343,0.5507308633601591,0.5097846554374688,0.5546532666169343,0.5546270055723259
2124,nearest_fixed_coordinate,133,329,164.80000000004657,-14.972416718222696,0.9306817916355061,1.454370386435224,-2.4895529747009277,-1.4857861666299854,-2.419981270666726,13.938997156191997,-1.4857861666299854,-2.56200951411331,-2.419981270666726,13.938997156191997,-2.56200951411331,-2.5619020573911135
2124,nearest_fixed_coordinate,226,389,194.80000000004657,14.972416718222696,0.934367175409882,-273.66219644710117,-131.7760467529297,341.92893976898984,-137.02616286222772,-221.6107373292289,341.92893976898984,-127.01590220781408,-137.02616286222772,-221.6107373292289,-127.01590220781408,-127.02247733551356
2124,nearest_fixed_coordinate,103,359,179.80000000004657,-25.152815520358722,0.9027537570763418,1.1925649014856359,-0.7344731092453003,-2.0934719683920044,-0.858645299225811,0.2650130702920287,-2.0934719683920044,-0.6143273084146696,-0.858645299225811,0.2650130702920287,-0.6143273084146696,-0.6116898094176973
2124,nearest_fixed_coordinate,256,359,179.80000000004657,25.152815520358722,0.9059109683045646,2.9038857641163727,0.9753406643867493,0.7164389543341273,0.9463200846247546,1.2823227285741317,0.7164389543341273,1.0048932241440014,0.9463200846247546,1.2823227285741317,1.0048932241440014,1.0055592805280098
2124,largest_observed_positive,128,398,199.30000000004657,-16.626645138620265,0.9024344599854236,1801.715118011534,1831.172119140625,-0.9826727699016699,1820.0922015095628,-5.584021765478045,-0.9826727699016699,1835.882433598279,1820.0922015095628,-5.584021765478045,1835.882433598279,1835.884698847212
2124,largest_observed_negative,229,404,202.30000000004657,15.963325223062819,0.8895881049474788,-1043.4186613192692,-149.60986328125,-49.329423644440695,-153.7172498726809,-18.560436500385347,-49.329423644440695,-145.58371300354082,-153.7172498726809,-18.560436500385347,-145.58371300354082,-145.58273652804633

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/sensitivity_metrics.csv (24,111 bytes; 105 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/sensitivity_metrics.csv", "bytes": 24111, "sha256": "e92c292204bb9e47e1a05b6d985ac929d352bd46a2eff5f86649044263a26fb9", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,variant,mu_min,count_primary_mask,surface_area_fraction,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G,rmse_improvement_vs_000_pct,rmse_improvement_vs_central_pct,mae_improvement_vs_000_pct,mae_improvement_vs_central_pct
2120,central,0.8,25693,0.09913215833333333,25693,0.07300365545127543,9.018476889881612,23.821126003867285,0.8253540465211998,3.5970908714239576,33.714142498492095,50.58750888905096,0.0,25.490226195142608,0.0
2120,000,0.8,25693,0.09913215833333333,25693,-0.33682984001317695,12.103750191889167,48.20871295555648,0.36943650074569223,4.037766184336146,39.63066146217111,0.0,-102.37797721119458,0.0,-34.210580563433226
2120,100,0.8,25693,0.09913215833333333,25693,0.032412898172098636,9.017377900559431,23.68463409431693,0.826450127963197,3.7039580519450275,32.63031421516575,50.87063594468546,0.5729868081307155,25.499305937410554,0.012185974811484979
2120,010,0.8,25693,0.09913215833333333,25693,-0.08041155933081816,11.733414321089771,41.15466370746747,0.4345057597499442,4.1279598072324,41.89413162053009,14.63231191131803,-72.76540034583647,3.05967873533578,-30.10416796936317
2120,001,0.8,25693,0.09913215833333333,25693,-0.33682984001317695,12.103750191889167,48.20871295555648,0.36943650074569223,4.037766184336146,39.63066146217111,0.0,-102.37797721119458,0.0,-34.210580563433226
2120,110,0.8,25693,0.09913215833333333,25693,0.09644029115472545,9.102445965293338,23.96804540669631,0.8228582473231126,3.6781011279182803,33.79332478177807,50.28275193989848,-0.6167609491053216,24.796481908615654,-0.9310782345734792
2120,101,0.8,25693,0.09913215833333333,25693,0.032412898172098636,9.017377900559431,23.68463409431693,0.826450127963197,3.7039580519450275,32.63031421516575,50.87063594468546,0.5729868081307155,25.499305937410554,0.012185974811484979
2120,011,0.8,25693,0.09913215833333333,25693,-0.08041155933081816,11.733414321089771,41.15466370746747,0.4345057597499442,4.1279598072324,41.89413162053009,14.63231191131803,-72.76540034583647,3.05967873533578,-30.10416796936317
2120,111,0.8,25693,0.09913215833333333,25693,0.09644029115472545,9.102445965293338,23.96804540669631,0.8228582473231126,3.6781011279182803,33.79332478177807,50.28275193989848,-0.6167609491053216,24.796481908615654,-0.9310782345734792
2120,010_exact,0.8,25693,0.09913215833333333,25693,-0.2593778777036491,12.11429367689094,43.301356153489685,0.35719780898579934,4.151123432685761,43.59082796162519,10.179398082232305,-81.77711728009771,-0.0871092416368402,-34.32749038235843
2120,011_exact,0.8,25693,0.09913215833333333,25693,-0.2593778777036491,12.11429367689094,43.301356153489685,0.35719780898579934,4.151123432685761,43.59082796162519,10.179398082232305,-81.77711728009771,-0.0871092416368402,-34.32749038235843
2120,110_exact,0.8,25693,0.09913215833333333,25693,0.0969433855331101,9.102243149698287,23.965833686460503,0.8228983353525293,3.674048869703893,33.783923395656714,50.28733974177124,-0.6074762484767682,24.798157551220925,-0.9288293449047691
2120,111_exact,0.8,25693,0.09913215833333333,25693,0.0969433855331101,9.102243149698287,23.965833686460503,0.8228983353525293,3.674048869703893,33.783923395656714,50.28733974177124,-0.6074762484767682,24.798157551220925,-0.9288293449047691
2120,000_linear,0.8,25693,0.09913215833333333,25693,-0.3301853413905427,11.738937173284043,46.60105512735823,0.3733383784192336,3.910518056697701,38.35713904939783,3.3347868665988822,-95.62910300626719,3.014049470796154,-30.165407270208622
2120,100_linear,0.8,25693,0.09913215833333333,25693,0.033200757644779685,8.719019429930077,23.204834415662717,0.8308313274496705,3.574753561679166,31.446432471656408,51.86589105364583,2.5871639657357726,27.96431443394486,3.320488188948123
2120,111_linear,0.8,25693,0.09913215833333333,25693,0.09872659405853854,8.807142044461093,23.479264391597287,0.8272603871324321,3.5572271837600704,32.54947258604126,51.2966371592563,1.435119449074318,27.236254013546656,2.3433540718791224
2120,111_epoch_rate_exact,0.8,25693,0.09913215833333333,25693,0.09691833318755762,9.10216500807815,23.965324855002276,0.8229057635393817,3.6751174679285943,33.78628903340995,50.28839521790207,-0.6053401972332395,24.798803149642048,-0.927962883515665
2120,central,0.9,,0.049583441666666665,12851,0.4027038554912814,8.42936878461228,25.0235798066951,0.8928309567380952,3.1520402381321033,30.278870489998916,56.6514898594416,0.0,36.02539425202409,0.0
2120,000,0.9,,0.049583441666666665,12851,1.2299953586509007,13.176116813942187,57.726504845392945,0.4438446055222544,3.6262358986386407,41.765338875838566,0.0,-130.68843583262267,0.0,-56.3120222951337
2120,100,0.9,,0.049583441666666665,12851,0.40712244775860484,8.470924793455927,25.285016556043804,0.8902422501861321,3.2285238785357304,29.78751146233978,56.198601277240236,-1.0447615863448778,35.710005359906226,-0.49299075536364256
2120,010,0.9,,0.049583441666666665,12851,0.3105081673064589,12.494172290760158,52.13573671881308,0.4846438155689651,3.7542777240182406,40.05709921804669,9.684924007703987,-108.34643612767216,5.175610787394014,-48.22192040723301
2120,001,0.9,,0.049583441666666665,12851,1.2299953586509007,13.176116813942187,57.726504845392945,0.4438446055222544,3.6262358986386407,41.765338875838566,0.0,-130.68843583262267,0.0,-56.3120222951337
2120,110,0.9,,0.049583441666666665,12851,0.39553968645903753,8.471534500435027,25.402057634995565,0.8894323026455836,3.2072417343528032,29.862061207487276,55.995850254525045,-1.5124847492811622,35.705377995199996,-0.5002238827149341
2120,101,0.9,,0.049583441666666665,12851,0.40712244775860484,8.470924793455927,25.285016556043804,0.8902422501861321,3.2285238785357304,29.78751146233978,56.198601277240236,-1.0447615863448778,35.710005359906226,-0.49299075536364256
2120,011,0.9,,0.049583441666666665,12851,0.3105081673064589,12.494172290760158,52.13573671881308,0.4846438155689651,3.7542777240182406,40.05709921804669,9.684924007703987,-108.34643612767216,5.175610787394014,-48.22192040723301
2120,111,0.9,,0.049583441666666665,12851,0.39553968645903753,8.471534500435027,25.402057634995565,0.8894323026455836,3.2072417343528032,29.862061207487276,55.995850254525045,-1.5124847492811622,35.705377995199996,-0.5002238827149341
2120,central,0.95,,0.024755066666666665,6416,0.032064183963773564,5.559091000009462,12.20542842011989,0.4440656976816497,2.6873618001444584,20.068977259171646,18.984579635246167,0.0,17.89349853636819,0.0
2120,000,0.95,,0.024755066666666665,6416,-0.40422816141075824,6.770585642930849,15.065562043827798,0.10182063693051202,3.1380593778561217,24.221142293056463,0.0,-23.433291526196285,0.0,-21.79303492098481
2120,100,0.95,,0.024755066666666665,6416,0.036307160621627046,5.583789271835392,12.26169843394479,0.4342650425445981,2.6943921860044955,19.8611675270451,18.611078708687945,-0.46102448753164715,17.528710715513775,-0.4442861580407298
2120,010,0.95,,0.024755066666666665,6416,0.3866772073008575,7.013854843473711,16.00089612021315,0.09698747304277826,3.239739390933175,24.785995391570665,-6.208424708380167,-31.096554495675587,-3.5930304019838877,-26.169095693194677
2120,001,0.95,,0.024755066666666665,6416,-0.40422816141075824,6.770585642930849,15.065562043827798,0.10182063693051202,3.1380593778561217,24.221142293056463,0.0,-23.433291526196285,0.0,-21.79303492098481
2120,110,0.95,,0.024755066666666665,6416,0.02409134010144395,5.538909741913063,11.929023801734436,0.46534803050691714,2.697578409888094,19.90273209920023,20.819258073271605,2.26460398497621,18.19157109848799,0.36303161967243813
2120,101,0.95,,0.024755066666666665,6416,0.036307160621627046,5.583789271835392,12.26169843394479,0.4342650425445981,2.6943921860044955,19.8611675270451,18.611078708687945,-0.46102448753164715,17.528710715513775,-0.4442861580407298
2120,011,0.95,,0.024755066666666665,6416,0.3866772073008575,7.013854843473711,16.00089612021315,0.09698747304277826,3.239739390933175,24.785995391570665,-6.208424708380167,-31.096554495675587,-3.5930304019838877,-26.169095693194677
2120,111,0.95,,0.024755066666666665,6416,0.02409134010144395,5.538909741913063,11.929023801734436,0.46534803050691714,2.697578409888094,19.90273209920023,20.819258073271605,2.26460398497621,18.19157109848799,0.36303161967243813
2122,central,0.8,25705,0.09917845833333333,25705,0.15753879017161634,11.503933919466728,35.247419514037766,0.3880825550285347,3.7997154874047503,44.504034496960145,18.934131724658197,0.0,20.406083555820832,0.0
2122,000,0.8,25705,0.09917845833333333,25705,0.40642512491024374,14.4532829057792,43.47997531380188,0.01585270032178364,4.441013293690263,58.425510007968576,0.0,-23.356478043691652,0.0,-25.637742766599537
2122,100,0.8,25705,0.09917845833333333,25705,0.1939411017110041,11.727542506042578,35.16570367816063,0.3830528118734339,3.9612937116827105,44.69671553878898,19.122070736323625,0.2318349456606028,18.85897077851236,-1.9437575714639888
2122,010,0.8,25705,0.09917845833333333,25705,0.49960759978547364,14.556101718232679,43.045391274302105,0.029263525097765725,4.4713601842491695,60.142661432696606,0.9995038781952181,-22.123525261639898,-0.7113872545341682,-26.53151365552555
2122,001,0.8,25705,0.09917845833333333,25705,0.40642512491024374,14.4532829057792,43.47997531380188,0.01585270032178364,4.441013293690263,58.425510007968576,0.0,-23.356478043691652,0.0,-25.637742766599537
2122,110,0.8,25705,0.09917845833333333,25705,0.13196486640325156,11.582183979960504,35.67490821850125,0.3671272181221824,3.9187116645104103,43.54520285364831,17.950946473566788,-1.2128226983913803,19.86468364685975,-0.6802026249591364
2122,101,0.8,25705,0.09917845833333333,25705,0.1939411017110041,11.727542506042578,35.16570367816063,0.3830528118734339,3.9612937116827105,44.69671553878898,19.122070736323625,0.2318349456606028,18.85897077851236,-1.9437575714639888
2122,011,0.8,25705,0.09917845833333333,25705,0.49960759978547364,14.556101718232679,43.045391274302105,0.029263525097765725,4.4713601842491695,60.142661432696606,0.9995038781952181,-22.123525261639898,-0.7113872545341682,-26.53151365552555
2122,111,0.8,25705,0.09917845833333333,25705,0.13196486640325156,11.582183979960504,35.67490821850125,0.3671272181221824,3.9187116645104103,43.54520285364831,17.950946473566788,-1.2128226983913803,19.86468364685975,-0.6802026249591364
2122,010_exact,0.8,25705,0.09917845833333333,25705,0.4829319680110739,14.703638766010116,42.94855656492717,0.023849844544165503,4.516383989854258,59.84425297637822,1.2222149277670291,-21.848796754673995,-1.7321729731783586,-27.81400579091393
2122,011_exact,0.8,25705,0.09917845833333333,25705,0.4829319680110739,14.703638766010116,42.94855656492717,0.023849844544165503,4.516383989854258,59.84425297637822,1.2222149277670291,-21.848796754673995,-1.7321729731783586,-27.81400579091393
2122,110_exact,0.8,25705,0.09917845833333333,25705,0.13196043057439466,11.584776036651839,35.67137166061299,0.36725631432323486,3.9306462004815663,43.545057165473125,17.9590802359775,-1.2027891755491016,19.846749612715175,-0.7027345406453556
2122,111_exact,0.8,25705,0.09917845833333333,25705,0.13196043057439466,11.584776036651839,35.67137166061299,0.36725631432323486,3.9306462004815663,43.545057165473125,17.9590802359775,-1.2027891755491016,19.846749612715175,-0.7027345406453556
2122,000_linear,0.8,25705,0.09917845833333333,25705,0.40972722925594635,14.098229503264628,42.5970332800995,0.01678545057450407,4.289455608875017,57.06535037952286,2.0306866030397774,-20.85149457007669,2.45655886506313,-22.551377658801442
2122,100_linear,0.8,25705,0.09917845833333333,25705,0.19274912170194722,11.338110714241687,34.27237114230184,0.3959281358956629,3.8159526944323545,43.35117382661718,21.176654552003072,2.766297179138455,21.553388332915702,1.4414478245953655
2122,111_linear,0.8,25705,0.09917845833333333,25705,0.1336544871319818,11.184560356164642,34.607617684316395,0.38584339282850955,3.791029198158491,41.772370128522375,20.405617909054165,1.81517353197036,22.615779203405395,2.776211733637035
2122,111_epoch_rate_exact,0.8,25705,0.09917845833333333,25705,0.13193660703026794,11.584941292547523,35.67263893054946,0.3672128815474323,3.9304740774538036,43.565427006541604,17.95616563005299,-1.2063845307664245,19.84560623306392,-0.7041710570304671
2122,central,0.9,,0.049560291666666666,12845,-0.12674041554640236,8.108847983875712,21.396100314242336,0.46868915753531204,3.1505274264234293,29.82213361850631,13.199403174667879,0.0,13.266955540664238,0.0
2122,000,0.9,,0.049560291666666666,12845,0.02613324729128379,9.349202526469014,24.64971566646883,0.12121784105086174,3.6319317721051863,34.227645058756075,0.0,-15.206581126658492,0.0,-15.296310216441622
2122,100,0.9,,0.049560291666666666,12845,-0.19386453875727225,8.223951903715786,21.382248442999128,0.468832119785115,3.2591627663487657,30.185404501172563,13.255598026692283,0.06474016778650338,12.035792566986036,-1.419485481401983
2122,010,0.9,,0.049560291666666666,12845,-0.3441000776333469,12.251768431577402,36.80461344134422,0.039259986056935856,3.9006479472440323,47.9235676231265,-49.31049890936381,-72.01552105663478,-31.046133580813784,-51.09135669998754
2122,001,0.9,,0.049560291666666666,12845,0.02613324729128379,9.349202526469014,24.64971566646883,0.12121784105086174,3.6319317721051863,34.227645058756075,0.0,-15.206581126658492,0.0,-15.296310216441622
2122,110,0.9,,0.049560291666666666,12845,-0.04717520235665512,8.10034967086738,21.09864722044503,0.4732988423524677,3.2676112154552603,29.368997512983192,14.406123356848044,1.3902210656551506,13.357854341757392,0.10480296369139719
2122,101,0.9,,0.049560291666666666,12845,-0.19386453875727225,8.223951903715786,21.382248442999128,0.468832119785115,3.2591627663487657,30.185404501172563,13.255598026692283,0.06474016778650338,12.035792566986036,-1.419485481401983
2122,011,0.9,,0.049560291666666666,12845,-0.3441000776333469,12.251768431577402,36.80461344134422,0.039259986056935856,3.9006479472440323,47.9235676231265,-49.31049890936381,-72.01552105663478,-31.046133580813784,-51.09135669998754
2122,111,0.9,,0.049560291666666666,12845,-0.04717520235665512,8.10034967086738,21.09864722044503,0.4732988423524677,3.2676112154552603,29.368997512983192,14.406123356848044,1.3902210656551506,13.357854341757392,0.10480296369139719
2122,central,0.95,,0.024735774999999998,6411,-0.029880387789652983,5.1414863164138405,10.132224433424888,0.5129143759933378,2.646167634061798,17.588164549048916,21.30978573510737,0.0,18.041538548119195,0.0
2122,000,0.95,,0.024735774999999998,6411,0.33404325531645734,6.273283106262913,12.876092063133884,0.18638437717076203,3.1399563922605225,22.07471808711473,0.0,-27.080604537907128,0.0,-22.013027365956205
2122,100,0.95,,0.024735774999999998,6411,-0.024807862883522176,5.182109927045531,10.111406181259525,0.5121330001914405,2.6666773896925235,18.229705508854707,21.47146718366557,0.2054657622534095,17.39397315144303,-0.7901141446589488
2122,010,0.95,,0.024735774999999998,6411,0.22393302730978296,6.831374058136572,14.863204991706217,0.1365853591387605,3.2165025229579918,24.553834153874586,-15.432577825858562,-46.692417734791206,-8.89631381878,-32.867689180225604
2122,001,0.95,,0.024735774999999998,6411,0.33404325531645734,6.273283106262913,12.876092063133884,0.18638437717076203,3.1399563922605225,22.07471808711473,0.0,-27.080604537907128,0.0,-22.013027365956205
2122,110,0.95,,0.024735774999999998,6411,-0.0384047826279669,5.114415285562371,10.019177639602017,0.5191413733897791,2.6429528769066715,17.454575070404047,22.18774461633143,1.115715453853794,18.473067468349868,0.5265214995330614
2122,101,0.95,,0.024735774999999998,6411,-0.024807862883522176,5.182109927045531,10.111406181259525,0.5121330001914405,2.6666773896925235,18.229705508854707,21.47146718366557,0.2054657622534095,17.39397315144303,-0.7901141446589488
2122,011,0.95,,0.024735774999999998,6411,0.22393302730978296,6.831374058136572,14.863204991706217,0.1365853591387605,3.2165025229579918,24.553834153874586,-15.432577825858562,-46.692417734791206,-8.89631381878,-32.867689180225604
2122,111,0.95,,0.024735774999999998,6411,-0.0384047826279669,5.114415285562371,10.019177639602017,0.5191413733897791,2.6429528769066715,17.454575070404047,22.18774461633143,1.115715453853794,18.473067468349868,0.5265214995330614
2124,central,0.8,25700,0.09915916666666666,25700,-0.07386621646472177,14.82415463532096,43.17068507717338,0.6929857586079816,4.237868604841771,64.11612702260734,41.37749948207983,0.0,37.94311529949166,0.0
2124,000,0.8,25700,0.09915916666666666,25700,0.03964899189660444,23.888009697656525,73.64183495375916,0.15004868794373635,5.266227155703948,112.83024830969272,0.0,-70.58296578364349,0.0,-61.1424751381064
2124,100,0.8,25700,0.09915916666666666,25700,-0.07133106477028843,15.011438816067022,43.281733496533434,0.6893568336811965,4.4150501987527715,64.48571556000572,41.22670419102036,-0.25723107975130777,37.15910615383046,-1.2633717426275837
2124,010,0.8,25700,0.09915916666666666,25700,-0.3798170542073068,21.333157103416752,70.46353295343219,0.14307053525323005,4.977973717742509,94.78996649909243,4.31589191432108,-63.220789356178145,10.695125406326378,-43.90808533922761
2124,001,0.8,25700,0.09915916666666666,25700,0.03964899189660444,23.888009697656525,73.64183495375916,0.15004868794373635,5.266227155703948,112.83024830969272,0.0,-70.58296578364349,0.0,-61.1424751381064
2124,110,0.8,25700,0.09915916666666666,25700,-0.06550874647405848,14.82379045763159,42.44040132507618,0.7017249825006248,4.337383440618488,63.78467454628184,42.36916916624204,1.6916195580211957,37.94463982034534,0.0024566506376166863
2124,101,0.8,25700,0.09915916666666666,25700,-0.07133106477028843,15.011438816067022,43.281733496533434,0.6893568336811965,4.4150501987527715,64.48571556000572,41.22670419102036,-0.25723107975130777,37.15910615383046,-1.2633717426275837
2124,011,0.8,25700,0.09915916666666666,25700,-0.3798170542073068,21.333157103416752,70.46353295343219,0.14307053525323005,4.977973717742509,94.78996649909243,4.31589191432108,-63.220789356178145,10.695125406326378,-43.90808533922761
2124,111,0.8,25700,0.09915916666666666,25700,-0.06550874647405848,14.82379045763159,42.44040132507618,0.7017249825006248,4.337383440618488,63.78467454628184,42.36916916624204,1.6916195580211957,37.94463982034534,0.0024566506376166863
2124,010_exact,0.8,25700,0.09915916666666666,25700,-0.4836731824274433,21.502285664969822,70.68219989487946,0.11097671701312235,4.983999240649524,94.34804072143935,4.018958871323752,-63.7273065473146,9.987119324222093,-45.048983864058776
2124,011_exact,0.8,25700,0.09915916666666666,25700,-0.4836731824274433,21.502285664969822,70.68219989487946,0.11097671701312235,4.983999240649524,94.34804072143935,4.018958871323752,-63.7273065473146,9.987119324222093,-45.048983864058776
2124,110_exact,0.8,25700,0.09915916666666666,25700,-0.06552422707681585,14.824980565578164,42.44512498609075,0.701663743483158,4.344618933030119,63.81080013240533,42.362754794550284,1.6806777325530042,37.939657789771694,-0.00557151674089873
2124,111_exact,0.8,25700,0.09915916666666666,25700,-0.06552422707681585,14.824980565578164,42.44512498609075,0.701663743483158,4.344618933030119,63.81080013240533,42.362754794550284,1.6806777325530042,37.939657789771694,-0.00557151674089873
2124,000_linear,0.8,25700,0.09915916666666666,25700,0.03259242241083049,23.290287283426675,71.87268831054713,0.15675602553428591,5.111462670967656,110.03496110604495,2.402366323874061,-66.48493805939164,2.502185915842492,-57.110390820760706
2124,100_linear,0.8,25700,0.09915916666666666,25700,-0.06765852530999408,14.4801843652052,41.69027080859097,0.7038890278450494,4.284998130491096,61.63570776790803,43.38778924402287,3.4292118967673924,39.38304384301324,2.3203364952507632
2124,111_linear,0.8,25700,0.09915916666666666,25700,-0.05876249218839275,14.306519688890068,40.96809578075877,0.7143669686263212,4.20936503958067,61.1704990376208,44.36844789855756,5.102048513886648,40.11003901135567,3.4918345036521803
2124,111_epoch_rate_exact,0.8,25700,0.09915916666666666,25700,-0.0655950578594912,14.824893910496966,42.44821328422837,0.7016287331347585,4.340981681213545,63.82648663342354,42.358561121022774,1.6735240398744966,37.940020545322675,-0.004986963467334959
2124,central,0.9,,0.04955643333333333,12844,-0.2911969161336496,17.18950744763275,45.34582233389217,0.7723444416430391,4.101260197582123,83.85916775568258,40.975972473007104,0.0,38.58988848057289,0.0
2124,000,0.9,,0.04955643333333333,12844,2.2616742202787115,27.991330779776945,76.82603887570126,0.25225341346689845,5.605288261589771,141.45869626278747,0.0,-69.42252873927987,0.0,-62.8396326366627
2124,100,0.9,,0.04955643333333333,12844,-0.301181531813689,17.35548565648075,45.37762621610005,0.7703114312479041,4.302674045632998,83.4962787233319,40.934575203704526,-0.07013630048142705,37.996925573043264,-0.9655786202929173
2124,010,0.9,,0.04955643333333333,12844,0.3366144259187375,28.601208522510426,85.32408452960874,0.1986483162708967,5.363928801489058,141.88538724470735,-11.061413263355524,-88.1630548043589,-2.178809387562608,-66.38759783922276
2124,001,0.9,,0.04955643333333333,12844,2.2616742202787115,27.991330779776945,76.82603887570126,0.25225341346689845,5.605288261589771,141.45869626278747,0.0,-69.42252873927987,0.0,-62.8396326366627
2124,110,0.9,,0.04955643333333333,12844,-0.26726993550022893,17.113456663963817,44.66676790759797,0.7792694352717056,4.214152237383167,83.08014592667858,41.85985824433115,1.4975016249438866,38.861582542806886,0.4424256128374715
2124,101,0.9,,0.04955643333333333,12844,-0.301181531813689,17.35548565648075,45.37762621610005,0.7703114312479041,4.302674045632998,83.4962787233319,40.934575203704526,-0.07013630048142705,37.996925573043264,-0.9655786202929173
2124,011,0.9,,0.04955643333333333,12844,0.3366144259187375,28.601208522510426,85.32408452960874,0.1986483162708967,5.363928801489058,141.88538724470735,-11.061413263355524,-88.1630548043589,-2.178809387562608,-66.38759783922276
2124,111,0.9,,0.04955643333333333,12844,-0.26726993550022893,17.113456663963817,44.66676790759797,0.7792694352717056,4.214152237383167,83.08014592667858,41.85985824433115,1.4975016249438866,38.861582542806886,0.4424256128374715
2124,central,0.95,,0.024751208333333337,6415,0.14853525109519253,14.634988893909327,42.0193694623146,0.7366951631872931,3.533593839050898,67.63106191053211,38.07195875371264,0.0,44.10435831476175,0.0
2124,000,0.95,,0.024751208333333337,6415,3.273769322794426,26.1827012852316,67.85192719918895,0.3344814597436581,5.14091852971136,139.70554859557407,0.0,-61.47773768962068,0.0,-78.90482510805397
2124,100,0.95,,0.024751208333333337,6415,0.08484288301126372,14.984462763197074,42.439820362709995,0.730016194640048,3.711059852161163,69.79547619466246,37.45229927202821,-1.000612112403254,42.76960730690883,-2.3879339562272506
2124,010,0.95,,0.024751208333333337,6415,-3.13610983047917,24.234573149370927,64.16742622295854,0.36834367477179697,4.906567448989927,125.80218270923734,5.430208290788907,-52.70916018982055,7.440516219613746,-65.59338257821759
2124,001,0.95,,0.024751208333333337,6415,3.273769322794426,26.1827012852316,67.85192719918895,0.3344814597436581,5.14091852971136,139.70554859557407,0.0,-61.47773768962068,0.0,-78.90482510805397
2124,110,0.95,,0.024751208333333337,6415,0.18624403853757548,14.515959862623028,41.05734648512784,0.7477847171679283,3.629179772487321,65.52627221884572,39.48978580284363,2.289475043288214,44.55896775322117,0.8133182208005296
2124,101,0.95,,0.024751208333333337,6415,0.08484288301126372,14.984462763197074,42.439820362709995,0.730016194640048,3.711059852161163,69.79547619466246,37.45229927202821,-1.000612112403254,42.76960730690883,-2.3879339562272506
2124,011,0.95,,0.024751208333333337,6415,-3.13610983047917,24.234573149370927,64.16742622295854,0.36834367477179697,4.906567448989927,125.80218270923734,5.430208290788907,-52.70916018982055,7.440516219613746,-65.59338257821759
2124,111,0.95,,0.024751208333333337,6415,0.18624403853757548,14.515959862623028,41.05734648512784,0.7477847171679283,3.629179772487321,65.52627221884572,39.48978580284363,2.289475043288214,44.55896775322117,0.8133182208005296

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/smoothing_sensitivity.csv (14,923 bytes; 81 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/smoothing_sensitivity.csv", "bytes": 14923, "sha256": "b2f74c35afe229d5a1e88b274e75373e3454a9bd8df3588bbc7ffcd72893a198", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
central_cr,sigma_detector_pixels,variant,mask,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G
2120,3,central,intersection primary and all sigma values; mu>=0.8,25693,0.07300365545127543,9.018476889881612,23.821126003867285,0.8253540465211998,3.5970908714239576,33.714142498492095
2120,3,000,intersection primary and all sigma values; mu>=0.8,25693,-0.33682984001317695,12.103750191889167,48.20871295555648,0.36943650074569223,4.037766184336146,39.63066146217111
2120,3,100,intersection primary and all sigma values; mu>=0.8,25693,0.032412898172098636,9.017377900559431,23.68463409431693,0.826450127963197,3.7039580519450275,32.63031421516575
2120,3,010,intersection primary and all sigma values; mu>=0.8,25693,-0.08041155933081816,11.733414321089771,41.15466370746747,0.4345057597499442,4.1279598072324,41.89413162053009
2120,3,001,intersection primary and all sigma values; mu>=0.8,25693,-0.33682984001317695,12.103750191889167,48.20871295555648,0.36943650074569223,4.037766184336146,39.63066146217111
2120,3,110,intersection primary and all sigma values; mu>=0.8,25693,0.09644029115472545,9.102445965293338,23.96804540669631,0.8228582473231126,3.6781011279182803,33.79332478177807
2120,3,101,intersection primary and all sigma values; mu>=0.8,25693,0.032412898172098636,9.017377900559431,23.68463409431693,0.826450127963197,3.7039580519450275,32.63031421516575
2120,3,011,intersection primary and all sigma values; mu>=0.8,25693,-0.08041155933081816,11.733414321089771,41.15466370746747,0.4345057597499442,4.1279598072324,41.89413162053009
2120,3,111,intersection primary and all sigma values; mu>=0.8,25693,0.09644029115472545,9.102445965293338,23.96804540669631,0.8228582473231126,3.6781011279182803,33.79332478177807
2120,6,central,intersection primary and all sigma values; mu>=0.8,25693,0.10718834794904471,7.656431466282879,20.15761509107492,0.8652467568157151,2.961960127098892,29.316258664316116
2120,6,000,intersection primary and all sigma values; mu>=0.8,25693,-0.3026451475154078,10.9589187583135,45.051411296533225,0.39740921742431035,3.535703808737511,35.56803586799506
2120,6,100,intersection primary and all sigma values; mu>=0.8,25693,0.06659759066986778,7.6560286083759115,19.988378224112953,0.8662078899671275,3.0704165641914587,28.755618156489017
2120,6,010,intersection primary and all sigma values; mu>=0.8,25693,-0.046226866833049066,10.554208506681846,36.99505663018914,0.47796528815801986,3.570512602748969,38.08136993505071
2120,6,001,intersection primary and all sigma values; mu>=0.8,25693,-0.3026451475154078,10.9589187583135,45.051411296533225,0.39740921742431035,3.535703808737511,35.56803586799506
2120,6,110,intersection primary and all sigma values; mu>=0.8,25693,0.13062498365249467,7.757955818228791,20.27086054577697,0.8631308046403768,3.0213180537817204,29.261357810217607
2120,6,101,intersection primary and all sigma values; mu>=0.8,25693,0.06659759066986778,7.6560286083759115,19.988378224112953,0.8662078899671275,3.0704165641914587,28.755618156489017
2120,6,011,intersection primary and all sigma values; mu>=0.8,25693,-0.046226866833049066,10.554208506681846,36.99505663018914,0.47796528815801986,3.570512602748969,38.08136993505071
2120,6,111,intersection primary and all sigma values; mu>=0.8,25693,0.13062498365249467,7.757955818228791,20.27086054577697,0.8631308046403768,3.0213180537817204,29.261357810217607
2120,12,central,intersection primary and all sigma values; mu>=0.8,25693,0.11839213303395785,7.063643164345284,21.293861890338665,0.8610102636487942,2.6919705729835313,25.57906442998674
2120,12,000,intersection primary and all sigma values; mu>=0.8,25693,-0.2914413624304947,9.98220621432533,41.86287501257461,0.4269312678643007,3.253828765735963,31.292950223011616
2120,12,100,intersection primary and all sigma values; mu>=0.8,25693,0.07780137575478101,7.06098843419671,21.028593107607183,0.8629457826405231,2.792467896514953,25.002047960365907
2120,12,010,intersection primary and all sigma values; mu>=0.8,25693,-0.035023081748135954,9.59175169762028,33.09483544818482,0.5098755356900486,3.3062024370218004,33.55106153967467
2120,12,001,intersection primary and all sigma values; mu>=0.8,25693,-0.2914413624304947,9.98220621432533,41.86287501257461,0.4269312678643007,3.253828765735963,31.292950223011616
2120,12,110,intersection primary and all sigma values; mu>=0.8,25693,0.14182876873740788,7.154074030523126,21.282126555754708,0.8601517014686729,2.792396800073718,25.389911295732666
2120,12,101,intersection primary and all sigma values; mu>=0.8,25693,0.07780137575478101,7.06098843419671,21.028593107607183,0.8629457826405231,2.792467896514953,25.002047960365907
2120,12,011,intersection primary and all sigma values; mu>=0.8,25693,-0.035023081748135954,9.59175169762028,33.09483544818482,0.5098755356900486,3.3062024370218004,33.55106153967467
2120,12,111,intersection primary and all sigma values; mu>=0.8,25693,0.14182876873740788,7.154074030523126,21.282126555754708,0.8601517014686729,2.792396800073718,25.389911295732666
2122,3,central,intersection primary and all sigma values; mu>=0.8,25705,0.15753879017161634,11.503933919466728,35.247419514037766,0.3880825550285347,3.7997154874047503,44.504034496960145
2122,3,000,intersection primary and all sigma values; mu>=0.8,25705,0.40642512491024374,14.4532829057792,43.47997531380188,0.01585270032178364,4.441013293690263,58.425510007968576
2122,3,100,intersection primary and all sigma values; mu>=0.8,25705,0.1939411017110041,11.727542506042578,35.16570367816063,0.3830528118734339,3.9612937116827105,44.69671553878898
2122,3,010,intersection primary and all sigma values; mu>=0.8,25705,0.49960759978547364,14.556101718232679,43.045391274302105,0.029263525097765725,4.4713601842491695,60.142661432696606
2122,3,001,intersection primary and all sigma values; mu>=0.8,25705,0.40642512491024374,14.4532829057792,43.47997531380188,0.01585270032178364,4.441013293690263,58.425510007968576
2122,3,110,intersection primary and all sigma values; mu>=0.8,25705,0.13196486640325156,11.582183979960504,35.67490821850125,0.3671272181221824,3.9187116645104103,43.54520285364831
2122,3,101,intersection primary and all sigma values; mu>=0.8,25705,0.1939411017110041,11.727542506042578,35.16570367816063,0.3830528118734339,3.9612937116827105,44.69671553878898
2122,3,011,intersection primary and all sigma values; mu>=0.8,25705,0.49960759978547364,14.556101718232679,43.045391274302105,0.029263525097765725,4.4713601842491695,60.142661432696606
2122,3,111,intersection primary and all sigma values; mu>=0.8,25705,0.13196486640325156,11.582183979960504,35.67490821850125,0.3671272181221824,3.9187116645104103,43.54520285364831
2122,6,central,intersection primary and all sigma values; mu>=0.8,25705,0.1634800750564332,9.905214923655492,30.054812158724886,0.43877640023939346,3.1561319733889843,39.72253855356178
2122,6,000,intersection primary and all sigma values; mu>=0.8,25705,0.4123664097950607,13.242694936008842,38.860586371060315,0.018433628958296457,3.944594072714233,55.35818231666931
2122,6,100,intersection primary and all sigma values; mu>=0.8,25705,0.19988238659582103,10.175885307779367,30.098070296604863,0.42682239971421243,3.3173227409754285,40.57294992184239
2122,6,010,intersection primary and all sigma values; mu>=0.8,25705,0.5055488846702905,13.377972614517061,38.47276390850253,0.0294552907014958,3.958874969807807,56.48939421556966
2122,6,001,intersection primary and all sigma values; mu>=0.8,25705,0.4123664097950607,13.242694936008842,38.860586371060315,0.018433628958296457,3.944594072714233,55.35818231666931
2122,6,110,intersection primary and all sigma values; mu>=0.8,25705,0.13790615128806855,9.967447727154246,30.2283524257296,0.42589904255807043,3.267725231848636,38.716814637645626
2122,6,101,intersection primary and all sigma values; mu>=0.8,25705,0.19988238659582103,10.175885307779367,30.098070296604863,0.42682239971421243,3.3173227409754285,40.57294992184239
2122,6,011,intersection primary and all sigma values; mu>=0.8,25705,0.5055488846702905,13.377972614517061,38.47276390850253,0.0294552907014958,3.958874969807807,56.48939421556966
2122,6,111,intersection primary and all sigma values; mu>=0.8,25705,0.13790615128806855,9.967447727154246,30.2283524257296,0.42589904255807043,3.267725231848636,38.716814637645626
2122,12,central,intersection primary and all sigma values; mu>=0.8,25705,0.1761846587276567,8.815562747239847,25.773951352047664,0.4858908586301605,2.966749229403842,34.35043362621812
2122,12,000,intersection primary and all sigma values; mu>=0.8,25705,0.42507099346628435,12.190446219297083,34.499175180807235,0.019184881367896645,3.7464031455547735,51.31354579714324
2122,12,100,intersection primary and all sigma values; mu>=0.8,25705,0.21258697026704454,9.076741848339498,25.885102819526445,0.46677541353634944,3.1079540270391943,36.26455478205887
2122,12,010,intersection primary and all sigma values; mu>=0.8,25705,0.518253468341514,12.313820040969725,34.202003438217986,0.025039747599058634,3.760290162768449,51.94858390792489
2122,12,001,intersection primary and all sigma values; mu>=0.8,25705,0.42507099346628435,12.190446219297083,34.499175180807235,0.019184881367896645,3.7464031455547735,51.31354579714324
2122,12,110,intersection primary and all sigma values; mu>=0.8,25705,0.15061073495929198,8.832072855281465,25.524526951058387,0.4873467718316918,3.0469134976793595,34.045238582850935
2122,12,101,intersection primary and all sigma values; mu>=0.8,25705,0.21258697026704454,9.076741848339498,25.885102819526445,0.46677541353634944,3.1079540270391943,36.26455478205887
2122,12,011,intersection primary and all sigma values; mu>=0.8,25705,0.518253468341514,12.313820040969725,34.202003438217986,0.025039747599058634,3.760290162768449,51.94858390792489
2122,12,111,intersection primary and all sigma values; mu>=0.8,25705,0.15061073495929198,8.832072855281465,25.524526951058387,0.4873467718316918,3.0469134976793595,34.045238582850935
2124,3,central,intersection primary and all sigma values; mu>=0.8,25700,-0.07386621646472177,14.82415463532096,43.17068507717338,0.6929857586079816,4.237868604841771,64.11612702260734
2124,3,000,intersection primary and all sigma values; mu>=0.8,25700,0.03964899189660444,23.888009697656525,73.64183495375916,0.15004868794373635,5.266227155703948,112.83024830969272
2124,3,100,intersection primary and all sigma values; mu>=0.8,25700,-0.07133106477028843,15.011438816067022,43.281733496533434,0.6893568336811965,4.4150501987527715,64.48571556000572
2124,3,010,intersection primary and all sigma values; mu>=0.8,25700,-0.3798170542073068,21.333157103416752,70.46353295343219,0.14307053525323005,4.977973717742509,94.78996649909243
2124,3,001,intersection primary and all sigma values; mu>=0.8,25700,0.03964899189660444,23.888009697656525,73.64183495375916,0.15004868794373635,5.266227155703948,112.83024830969272
2124,3,110,intersection primary and all sigma values; mu>=0.8,25700,-0.06550874647405848,14.82379045763159,42.44040132507618,0.7017249825006248,4.337383440618488,63.78467454628184
2124,3,101,intersection primary and all sigma values; mu>=0.8,25700,-0.07133106477028843,15.011438816067022,43.281733496533434,0.6893568336811965,4.4150501987527715,64.48571556000572
2124,3,011,intersection primary and all sigma values; mu>=0.8,25700,-0.3798170542073068,21.333157103416752,70.46353295343219,0.14307053525323005,4.977973717742509,94.78996649909243
2124,3,111,intersection primary and all sigma values; mu>=0.8,25700,-0.06550874647405848,14.82379045763159,42.44040132507618,0.7017249825006248,4.337383440618488,63.78467454628184
2124,6,central,intersection primary and all sigma values; mu>=0.8,25700,-0.09440787391179166,12.858521435996243,37.2606130874426,0.74807785585729,3.6111721686771556,55.78877310881889
2124,6,000,intersection primary and all sigma values; mu>=0.8,25700,0.019107334449534177,22.266165245430837,68.99968932080418,0.16839963378546663,4.807679429637405,104.52484741232894
2124,6,100,intersection primary and all sigma values; mu>=0.8,25700,-0.09187272221735839,13.05417238774658,37.327895503115904,0.7445816674813475,3.7957532403933927,56.355446818595354
2124,6,010,intersection primary and all sigma values; mu>=0.8,25700,-0.4003587116543767,19.813266200228348,65.83907795875756,0.15412534219352028,4.465096227938212,87.53382739966094
2124,6,001,intersection primary and all sigma values; mu>=0.8,25700,0.019107334449534177,22.266165245430837,68.99968932080418,0.16839963378546663,4.807679429637405,104.52484741232894
2124,6,110,intersection primary and all sigma values; mu>=0.8,25700,-0.0860504039211284,12.819382665710023,36.4650025420061,0.7570490583500407,3.768405585670703,54.78739590198717
2124,6,101,intersection primary and all sigma values; mu>=0.8,25700,-0.09187272221735839,13.05417238774658,37.327895503115904,0.7445816674813475,3.7957532403933927,56.355446818595354
2124,6,011,intersection primary and all sigma values; mu>=0.8,25700,-0.4003587116543767,19.813266200228348,65.83907795875756,0.15412534219352028,4.465096227938212,87.53382739966094
2124,6,111,intersection primary and all sigma values; mu>=0.8,25700,-0.0860504039211284,12.819382665710023,36.4650025420061,0.7570490583500407,3.768405585670703,54.78739590198717
2124,12,central,intersection primary and all sigma values; mu>=0.8,25700,-0.0955081969875865,12.080464365444938,34.562705776783226,0.7780735249376092,3.5050909070169407,53.42229781079534
2124,12,000,intersection primary and all sigma values; mu>=0.8,25700,0.01800701137373943,20.650771609963297,63.88844963749161,0.1926500376541414,4.490240343324194,96.78558092015109
2124,12,100,intersection primary and all sigma values; mu>=0.8,25700,-0.0929730452931533,12.231125819673746,34.44550732842771,0.7760269001962572,3.6638671410664303,53.18418268674929
2124,12,010,intersection primary and all sigma values; mu>=0.8,25700,-0.4014590347301716,18.420103707781134,60.57292182940924,0.1714622172816601,4.227653451406926,81.37698451457251
2124,12,001,intersection primary and all sigma values; mu>=0.8,25700,0.01800701137373943,20.650771609963297,63.88844963749161,0.1926500376541414,4.490240343324194,96.78558092015109
2124,12,110,intersection primary and all sigma values; mu>=0.8,25700,-0.08715072699692325,12.044076060335607,33.842378514221295,0.7860731053072303,3.582746204992666,52.46080333917087
2124,12,101,intersection primary and all sigma values; mu>=0.8,25700,-0.0929730452931533,12.231125819673746,34.44550732842771,0.7760269001962572,3.6638671410664303,53.18418268674929
2124,12,011,intersection primary and all sigma values; mu>=0.8,25700,-0.4014590347301716,18.420103707781134,60.57292182940924,0.1714622172816601,4.227653451406926,81.37698451457251
2124,12,111,intersection primary and all sigma values; mu>=0.8,25700,-0.08715072699692325,12.044076060335607,33.842378514221295,0.7860731053072303,3.582746204992666,52.46080333917087

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/synthetic_metrics.csv (17,346 bytes; 66 data rows)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/synthetic_metrics.csv", "bytes": 17346, "sha256": "4c6a0a4b92e3a771e49e996c707665292372a03101822f9c2bf81eeea64f28b3", "line_endings": "CRLF", "utf8_bom": false} -->
`````csv
case,variant,mask,surface_area_fraction,count,bias_G,mae_G,rmse_G,pearson_r,median_abs_G,p95_abs_G,rmse_improvement_vs_000_pct,rmse_improvement_vs_central_pct
smooth_rotation,central,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.012552757949704476,3.118618902119731,5.046497812971861,0.9732138568436021,1.5110569497294826,11.853672283255056,78.78333956931594,0.0
smooth_rotation,000,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.25330762412785623,16.12185986545045,23.785542637395896,0.38889490809423527,9.27333465053963,53.855726983273804,0.0,-371.327711195196
smooth_rotation,100,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.015862616961421567,5.46741609525377,8.527024463622835,0.923401324501111,2.786693958376514,19.58232675423851,64.15038919391078,-68.96915008472592
smooth_rotation,010,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.12133590308049089,14.891534578708782,23.934813686941325,0.40090181084488397,5.751509427666662,56.91472526709783,-0.6275705028933931,-374.2856248826197
smooth_rotation,001,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.25329992105189936,16.12192800301897,23.78554588176979,0.3888940827618435,9.27333465053963,53.855726983273804,-1.3640108798007589e-05,-371.3277754848086
smooth_rotation,110,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.06222498660251065,0.8421408236924226,3.690096583355569,0.9856986843276451,0.053272329043572264,2.6400678506153183,84.48596847416903,26.878070295199695
smooth_rotation,101,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.019597887364469425,5.467605140164614,8.52614236431576,0.9234181877637806,2.7885100640441807,19.58232675423851,64.15409774628868,-68.9516706496847
smooth_rotation,011,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.06072533405128313,14.462462604794222,23.518004142419997,0.4264372158528215,5.535324382784175,57.57658896510343,1.1247945823833039,-366.0262426344013
smooth_rotation,111,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.003515076134855936,0.3191039589188936,0.659735313289626,0.9995442534298475,0.05081910233458942,1.5807187220838024,97.22631800607995,86.92686814222336
smooth_rotation,111_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-3.8641979155155005e-09,1.2292004189375098e-07,2.205923641648065e-07,0.9999999999999997,5.058387797518549e-08,4.737572238511234e-07,99.99999907257796,99.99999562880294
smooth_rotation,known_rate_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-3.8641979155155005e-09,1.2292004189375098e-07,2.205923641648065e-07,0.9999999999999997,5.058387797518549e-08,4.737572238511234e-07,99.99999907257796,99.99999562880294
seam_features,central,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.3231282520072103,1.7405969929314056,6.916511731176221,0.8563333910212892,0.43164690089096847,4.188046710681777,36.05158568722414,0.0
seam_features,000,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.18903721679180008,5.700904787622499,10.815767373600714,0.6352123079195305,2.8817219545670514,17.157711613475353,0.0,-56.37604321335239
seam_features,100,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.38300407480117166,2.5335191705140594,7.878466188725604,0.8138313075369024,0.8116356157938927,6.942224581928019,27.157584694771806,-13.90808683535325
seam_features,010,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.7824287257370327,5.751079867998066,12.781156206043073,0.5102557261035311,1.7879182897079127,18.541542317738493,-18.171515386319335,-84.79193996638408
seam_features,001,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.1890391428527435,5.700918195094862,10.815767700953188,0.6352122832867834,2.8817219545670514,17.157711613475353,-3.0266227302178095e-06,-56.37604794626525
seam_features,110,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.2239668824319495,1.0036605958660447,6.807219454938831,0.8600335367811701,0.016296982564891982,0.9255915688896751,37.0620759507643,1.580164691180297
seam_features,101,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.4094063802881089,2.527836553422946,7.859979779043521,0.8157318893195686,0.8121060482598175,6.934451787887438,27.328505620153432,-13.640807455217807
seam_features,011,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.43222437090043764,5.261383983955234,11.225021160398807,0.6019752308626355,1.7106952986419035,17.408178937252927,-3.7838626947266363,-62.293097975992026
seam_features,111,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.0594584941840383,0.34387610658946965,2.066156806650467,0.9888520312344053,0.015775319243896455,0.5077029484541987,80.89680800926273,70.127184237435
seam_features,111_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,8.771750269724504e-09,5.125250476516815e-07,5.2842747942734275e-06,0.9999999999999226,1.8271421486915074e-08,6.463034888604113e-07,99.99995114285828,99.99992359913495
seam_features,known_rate_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,8.771750269724504e-09,5.125250476516815e-07,5.2842747942734275e-06,0.9999999999999226,1.8271421486915074e-08,6.463034888604113e-07,99.99995114285828,99.99992359913495
missing_data,central,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.32677339435266267,1.759287723995753,6.955117801148686,0.8563295152143845,0.4417262485552018,4.216036529696688,36.04881110874106,0.0
missing_data,000,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,-0.19045280971969414,5.763287401765668,10.875666147466001,0.6352213308353122,2.947135208378713,17.231757710098343,0.0,-56.36925870140992
missing_data,100,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.38735231132397197,2.560834628129274,7.92243750775526,0.8138279882118727,0.8322405400896202,6.993230959245605,27.154462077698437,-13.908027646157395
missing_data,010,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.7914368524641902,5.814437984509769,12.852455436824325,0.5102655973955135,1.8407402928373717,18.635013725737323,-18.17625939004124,-84.7913407692628
missing_data,001,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,-0.19045473533393106,5.763296451212049,10.875666454467847,0.635221307845304,2.947135208378713,17.231757710098343,-2.8228325676948884e-06,-56.36926311545227
missing_data,110,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.22647478328326012,1.014449390728938,6.845218943596601,0.8600271026460649,0.01619298672702385,0.9697089964999436,37.05931341785885,1.5801149699281036
missing_data,101,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.41405023423574383,2.555088384752508,7.9038478646825725,0.8157295907712311,0.8326881018828942,6.982726001927036,27.325390854111987,-13.640747585572122
missing_data,011,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.4373113721031223,5.319259133407119,11.287625298904816,0.6019701965063632,1.7604722798490953,17.466071260563748,-3.78789810070439,-62.29236688184616
missing_data,111,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,0.06012202845855084,0.3474828200177995,2.077689490380017,0.9888514649445964,0.015714723645264828,0.5124118106516262,80.89597949948002,70.12718476117152
missing_data,111_exact,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,5.650969747488837e-07,1.0860635091544022e-06,3.313490039837658e-05,0.999999999996949,1.903109214662635e-08,7.375812203669308e-07,99.99969532992326,99.9995235896595
missing_data,known_rate_exact,"common all variants, exact, oracle, central; full mock sphere",0.9827655003069364,128074,5.650969747488837e-07,1.0860635091544022e-06,3.313490039837658e-05,0.999999999996949,1.903109214662635e-08,7.375812203669308e-07,99.99969532992326,99.9995235896595
stationary_control,central,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.0,0.0,0.0,1.0,0.0,0.0,100.0,
stationary_control,000,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.21752863017016724,14.435611088571452,22.937629939523838,0.43470169890018545,6.6799912129573045,53.63773856941948,0.0,
stationary_control,100,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.012552758386050914,3.118618888808522,5.04649779352536,0.9732138569798344,1.5110568491747038,11.853672272825618,77.99904433530973,
stationary_control,010,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.13863718203433226,15.44596308763619,24.306835247348523,0.3918747119117237,6.921532459825928,57.47772305026682,-5.9692536301032995,
stationary_control,001,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.21752863017016724,14.435611088571452,22.937629939523838,0.43470169890018545,6.6799912129573045,53.63773856941948,0.0,
stationary_control,110,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.008565096294415818,3.1855166152141834,5.281635811359397,0.970929559072286,1.500957652066284,12.442165274901807,76.97392526915516,
stationary_control,101,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.012552758386050914,3.118618888808522,5.04649779352536,0.9732138569798344,1.5110568491747038,11.853672272825618,77.99904433530973,
stationary_control,011,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.13863718203433226,15.44596308763619,24.306835247348523,0.3918747119117237,6.921532459825928,57.47772305026682,-5.9692536301032995,
stationary_control,111,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.008565096294415818,3.1855166152141834,5.281635811359397,0.970929559072286,1.500957652066284,12.442165274901807,76.97392526915516,
stationary_control,111_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.009835589443181407,3.468684489594079,5.76073081547019,0.96541524193289,1.6016187232358359,13.655225199461263,74.88523953582549,
stationary_control,known_rate_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-4.291308163522448e-17,2.941320966163864e-15,4.8262964962583824e-15,1.0,1.7763568394002505e-15,1.0658141036401503e-14,99.99999999999997,
opposite_rotation_control,central,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.008565099595860798,3.185516625537138,5.281635829866441,0.9709295589786446,1.5009575867663512,12.4421652290568,76.46063788016005,0.0
opposite_rotation_control,000,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.13894981434007536,13.819534601453377,22.437463695818927,0.46282715155448756,5.725049784930356,53.46184798226056,0.0,-324.8203476835758
opposite_rotation_control,100,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.009841662928560315,0.34859200335938495,0.9976365333456446,0.9989576508438153,0.05140138858586063,1.6223651059895179,95.55370184941381,81.11122073763136
opposite_rotation_control,010,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.03273719727877558,16.82148738812493,24.695138132768022,0.37066492654557553,9.637887500788503,57.7079141888037,-10.06207505249266,-367.56608990575745
opposite_rotation_control,001,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.13893909522243172,13.819617852736577,22.43746786593932,0.4628263163192959,5.725049784930356,53.46184798226056,-1.8585524852454682e-05,-324.820426638667
opposite_rotation_control,110,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.040437215907086085,5.770180904147246,9.033335814520564,0.9148572678256227,2.925933002618107,20.84126897332945,59.73994237056364,-71.03291679897956
opposite_rotation_control,101,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.003515078969036893,0.3191039582664157,0.6597353099416233,0.9995442534345316,0.050819135732321996,1.580718615419286,97.05967074137457,87.50888302046553
opposite_rotation_control,011,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.16618087960779668,17.583570250876242,25.437050754806236,0.33600546774180307,10.273826661692608,57.78667108596192,-13.36865476264264,-381.61311332685113
opposite_rotation_control,111,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.02519490837621564,5.8615473607382516,9.296254666947322,0.9099641260738406,2.9087017115518234,21.591904000924597,58.568157288296284,-76.01089825957197
opposite_rotation_control,111_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.02528747882110251,5.990380415343838,9.527267328004694,0.9053996217760785,2.9261935138432253,22.21278553998138,57.53857273190803,-80.38478295171694
opposite_rotation_control,known_rate_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-7.347788357166638e-10,1.4926465763588162e-07,2.6780621794802506e-07,0.9999999999999999,8.548137131469957e-08,4.7139113465988194e-07,99.99999880643276,99.99999492948348
evolving_control,central,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.3231282520072104,2.9914038834678762,7.243771522285231,0.8447800330605023,1.8398311918245502,6.3857900921881665,31.215809859624223,0.0
evolving_control,000,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.18903721679179997,5.443214851097208,10.531157679551123,0.6543795904911709,2.677595823060714,16.488363689192227,0.0,-45.38224524548233
evolving_control,100,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.3830040748011716,3.43814129311229,8.099447044531301,0.8071177443257757,1.9862265101335166,7.993626831182349,23.090629815006913,-11.812569179102518
evolving_control,010,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.7824287257370327,8.13408995780827,15.621056149179328,0.3731394816773271,2.854625247263281,30.05269957983324,-48.33180381974069,-115.64810680626314
evolving_control,001,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,-0.18903914285274334,5.442859666284624,10.531093536597632,0.6543827846419101,2.676776863069424,16.488363689192227,0.0006090778947864806,-45.381359754363615
evolving_control,110,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.22396688243194937,3.2894181790053283,8.008040460251161,0.807567252726038,2.0785560790620417,5.357810429545911,23.958593120291283,-10.550704637973208
evolving_control,101,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.40940638028810883,3.418832560896606,8.060404618601332,0.8103286569370235,1.9850375234658717,7.888425384632221,23.461362331962576,-11.273589922097283
evolving_control,011,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.43222437090043764,5.557282558922261,11.15623880467079,0.6140778140704345,2.5319780015189854,18.682482854775348,-5.935540461362754,-54.01146723566556
evolving_control,111,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,0.05945849418403833,2.4002241440777663,3.3438478501789395,0.9682656671252856,2.0261047900046174,4.918094312879577,68.24805067089768,53.8383031561432
evolving_control,111_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,8.7717502735954e-09,2.245531696296621,2.6591026063084993,0.9816876540462189,2.120849039594903,4.709073143148668,74.75013965965192,63.29118611585338
evolving_control,known_rate_exact,"common all variants, exact, oracle, central; full mock sphere",0.9937691835481889,129508,8.7717502735954e-09,2.245531696296621,2.6591026063084993,0.9816876540462189,2.120849039594903,4.709073143148668,74.75013965965192,63.29118611585338

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/available_inputs.json (58,740 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/available_inputs.json", "bytes": 58740, "sha256": "2498080ead2ec9b2feddfca0d5ae739abbfe0a221d70aef90a4482eb554bef0d", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "maps": [
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2096.fits",
      "rotation": 2096,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 232321,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2097.fits",
      "rotation": 2097,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257779,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2098.fits",
      "rotation": 2098,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257576,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2099.fits",
      "rotation": 2099,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256636,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2100.fits",
      "rotation": 2100,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255791,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2101.fits",
      "rotation": 2101,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255649,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2102.fits",
      "rotation": 2102,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256516,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2103.fits",
      "rotation": 2103,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257485,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2104.fits",
      "rotation": 2104,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257775,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2105.fits",
      "rotation": 2105,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258120,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2106.fits",
      "rotation": 2106,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256095,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2107.fits",
      "rotation": 2107,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255600,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2108.fits",
      "rotation": 2108,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255849,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2109.fits",
      "rotation": 2109,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256762,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2110.fits",
      "rotation": 2110,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257771,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2111.fits",
      "rotation": 2111,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257732,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2112.fits",
      "rotation": 2112,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257054,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2113.fits",
      "rotation": 2113,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256070,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2114.fits",
      "rotation": 2114,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255600,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2115.fits",
      "rotation": 2115,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256076,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2116.fits",
      "rotation": 2116,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257149,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2117.fits",
      "rotation": 2117,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257732,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2118.fits",
      "rotation": 2118,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257608,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2119.fits",
      "rotation": 2119,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257546,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2120.fits",
      "rotation": 2120,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2121.fits",
      "rotation": 2121,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2122.fits",
      "rotation": 2122,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257447,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2123.fits",
      "rotation": 2123,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258280,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2124.fits",
      "rotation": 2124,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258752,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2125.fits",
      "rotation": 2125,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258193,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2126.fits",
      "rotation": 2126,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257372,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2127.fits",
      "rotation": 2127,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2128.fits",
      "rotation": 2128,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255799,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2129.fits",
      "rotation": 2129,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256557,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2130.fits",
      "rotation": 2130,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257336,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2131.fits",
      "rotation": 2131,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257539,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2132.fits",
      "rotation": 2132,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256915,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2133.fits",
      "rotation": 2133,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255892,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2134.fits",
      "rotation": 2134,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255600,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2135.fits",
      "rotation": 2135,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 255960,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2136.fits",
      "rotation": 2136,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 256987,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2137.fits",
      "rotation": 2137,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257522,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2138.fits",
      "rotation": 2138,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258484,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2139.fits",
      "rotation": 2139,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257660,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2140.fits",
      "rotation": 2140,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2141.fits",
      "rotation": 2141,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2142.fits",
      "rotation": 2142,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257280,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2143.fits",
      "rotation": 2143,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258125,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2144.fits",
      "rotation": 2144,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258736,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2145.fits",
      "rotation": 2145,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258248,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2146.fits",
      "rotation": 2146,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257389,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2147.fits",
      "rotation": 2147,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2148.fits",
      "rotation": 2148,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2149.fits",
      "rotation": 2149,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257608,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2150.fits",
      "rotation": 2150,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258435,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2151.fits",
      "rotation": 2151,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258754,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2152.fits",
      "rotation": 2152,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258036,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2153.fits",
      "rotation": 2153,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257221,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2154.fits",
      "rotation": 2154,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2155.fits",
      "rotation": 2155,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2156.fits",
      "rotation": 2156,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257794,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2157.fits",
      "rotation": 2157,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258621,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2158.fits",
      "rotation": 2158,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258596,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2159.fits",
      "rotation": 2159,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257721,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2160.fits",
      "rotation": 2160,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2161.fits",
      "rotation": 2161,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2162.fits",
      "rotation": 2162,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257325,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2163.fits",
      "rotation": 2163,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258153,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2164.fits",
      "rotation": 2164,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258749,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2165.fits",
      "rotation": 2165,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258316,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2166.fits",
      "rotation": 2166,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257500,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2167.fits",
      "rotation": 2167,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2168.fits",
      "rotation": 2168,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2169.fits",
      "rotation": 2169,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257435,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2170.fits",
      "rotation": 2170,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258278,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2171.fits",
      "rotation": 2171,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258734,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2172.fits",
      "rotation": 2172,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258091,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2173.fits",
      "rotation": 2173,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257233,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2174.fits",
      "rotation": 2174,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2175.fits",
      "rotation": 2175,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2176.fits",
      "rotation": 2176,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257873,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2177.fits",
      "rotation": 2177,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258616,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2178.fits",
      "rotation": 2178,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258616,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2179.fits",
      "rotation": 2179,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257881,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2180.fits",
      "rotation": 2180,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257059,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2181.fits",
      "rotation": 2181,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2182.fits",
      "rotation": 2182,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257155,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2183.fits",
      "rotation": 2183,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257999,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2184.fits",
      "rotation": 2184,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258734,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2185.fits",
      "rotation": 2185,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258374,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2186.fits",
      "rotation": 2186,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257512,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2187.fits",
      "rotation": 2187,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2188.fits",
      "rotation": 2188,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2189.fits",
      "rotation": 2189,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257481,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2190.fits",
      "rotation": 2190,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258312,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2191.fits",
      "rotation": 2191,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258754,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2192.fits",
      "rotation": 2192,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258163,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2193.fits",
      "rotation": 2193,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257348,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2194.fits",
      "rotation": 2194,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2195.fits",
      "rotation": 2195,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2196.fits",
      "rotation": 2196,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257591,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2197.fits",
      "rotation": 2197,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258449,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2198.fits",
      "rotation": 2198,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258722,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2199.fits",
      "rotation": 2199,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257934,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2200.fits",
      "rotation": 2200,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257078,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2201.fits",
      "rotation": 2201,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2202.fits",
      "rotation": 2202,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257201,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2203.fits",
      "rotation": 2203,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258025,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2204.fits",
      "rotation": 2204,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258753,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2205.fits",
      "rotation": 2205,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258443,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2206.fits",
      "rotation": 2206,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257628,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2207.fits",
      "rotation": 2207,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2208.fits",
      "rotation": 2208,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2209.fits",
      "rotation": 2209,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257306,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2210.fits",
      "rotation": 2210,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258152,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2211.fits",
      "rotation": 2211,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258735,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2212.fits",
      "rotation": 2212,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258216,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2213.fits",
      "rotation": 2213,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257360,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2214.fits",
      "rotation": 2214,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2215.fits",
      "rotation": 2215,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2216.fits",
      "rotation": 2216,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257632,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2217.fits",
      "rotation": 2217,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258474,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2218.fits",
      "rotation": 2218,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258740,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2219.fits",
      "rotation": 2219,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258002,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2220.fits",
      "rotation": 2220,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257187,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2221.fits",
      "rotation": 2221,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2222.fits",
      "rotation": 2222,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2223.fits",
      "rotation": 2223,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257858,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2224.fits",
      "rotation": 2224,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258651,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2225.fits",
      "rotation": 2225,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258563,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2226.fits",
      "rotation": 2226,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257660,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2227.fits",
      "rotation": 2227,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2228.fits",
      "rotation": 2228,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2229.fits",
      "rotation": 2229,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257353,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2230.fits",
      "rotation": 2230,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258186,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2231.fits",
      "rotation": 2231,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258753,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2232.fits",
      "rotation": 2232,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258288,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2233.fits",
      "rotation": 2233,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257470,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2234.fits",
      "rotation": 2234,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2235.fits",
      "rotation": 2235,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2236.fits",
      "rotation": 2236,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257467,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2237.fits",
      "rotation": 2237,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258311,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2238.fits",
      "rotation": 2238,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258734,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2239.fits",
      "rotation": 2239,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258061,
      "checksum_ok": false,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2240.fits",
      "rotation": 2240,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257199,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2241.fits",
      "rotation": 2241,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2242.fits",
      "rotation": 2242,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257074,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2243.fits",
      "rotation": 2243,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257904,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2244.fits",
      "rotation": 2244,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258647,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2245.fits",
      "rotation": 2245,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258586,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2246.fits",
      "rotation": 2246,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257843,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2247.fits",
      "rotation": 2247,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2248.fits",
      "rotation": 2248,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2249.fits",
      "rotation": 2249,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257178,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2250.fits",
      "rotation": 2250,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258029,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2251.fits",
      "rotation": 2251,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258736,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2252.fits",
      "rotation": 2252,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258341,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2253.fits",
      "rotation": 2253,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257486,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2254.fits",
      "rotation": 2254,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2255.fits",
      "rotation": 2255,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2256.fits",
      "rotation": 2256,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257513,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2257.fits",
      "rotation": 2257,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258339,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2258.fits",
      "rotation": 2258,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258752,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2259.fits",
      "rotation": 2259,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258130,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2260.fits",
      "rotation": 2260,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257315,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2261.fits",
      "rotation": 2261,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2262.fits",
      "rotation": 2262,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2263.fits",
      "rotation": 2263,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257619,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2264.fits",
      "rotation": 2264,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258510,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2265.fits",
      "rotation": 2265,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258690,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2266.fits",
      "rotation": 2266,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257905,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2267.fits",
      "rotation": 2267,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257047,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2268.fits",
      "rotation": 2268,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2269.fits",
      "rotation": 2269,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257225,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2270.fits",
      "rotation": 2270,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258059,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2271.fits",
      "rotation": 2271,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258749,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2272.fits",
      "rotation": 2272,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258411,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2273.fits",
      "rotation": 2273,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257594,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2274.fits",
      "rotation": 2274,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2275.fits",
      "rotation": 2275,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2276.fits",
      "rotation": 2276,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257340,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2277.fits",
      "rotation": 2277,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258184,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2278.fits",
      "rotation": 2278,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258734,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2279.fits",
      "rotation": 2279,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258188,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2280.fits",
      "rotation": 2280,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257327,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2281.fits",
      "rotation": 2281,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2282.fits",
      "rotation": 2282,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2283.fits",
      "rotation": 2283,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257684,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2284.fits",
      "rotation": 2284,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258521,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2285.fits",
      "rotation": 2285,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258711,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2286.fits",
      "rotation": 2286,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257976,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2287.fits",
      "rotation": 2287,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257159,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2288.fits",
      "rotation": 2288,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2289.fits",
      "rotation": 2289,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257059,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2290.fits",
      "rotation": 2290,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257904,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2291.fits",
      "rotation": 2291,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258680,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2292.fits",
      "rotation": 2292,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258522,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2293.fits",
      "rotation": 2293,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257606,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2294.fits",
      "rotation": 2294,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2295.fits",
      "rotation": 2295,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2296.fits",
      "rotation": 2296,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257386,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2297.fits",
      "rotation": 2297,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258215,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2298.fits",
      "rotation": 2298,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258753,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2299.fits",
      "rotation": 2299,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258256,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2300.fits",
      "rotation": 2300,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257441,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2301.fits",
      "rotation": 2301,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2302.fits",
      "rotation": 2302,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2303.fits",
      "rotation": 2303,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257491,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2304.fits",
      "rotation": 2304,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258341,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2305.fits",
      "rotation": 2305,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258736,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2306.fits",
      "rotation": 2306,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258028,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2307.fits",
      "rotation": 2307,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257173,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2308.fits",
      "rotation": 2308,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2309.fits",
      "rotation": 2309,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257104,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2310.fits",
      "rotation": 2310,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257931,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2311.fits",
      "rotation": 2311,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258676,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2312.fits",
      "rotation": 2312,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 258554,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2313.fits",
      "rotation": 2313,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257777,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2314.fits",
      "rotation": 2314,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2315.fits",
      "rotation": 2315,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257040,
      "checksum_ok": true,
      "datasum_ok": true
    },
    {
      "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2316.fits",
      "rotation": 2316,
      "shape": [
        360,
        720
      ],
      "finite_pixels": 257213,
      "checksum_ok": true,
      "datasum_ok": true
    }
  ],
  "available_central_triples": [
    2097,
    2098,
    2099,
    2100,
    2101,
    2102,
    2103,
    2104,
    2105,
    2106,
    2107,
    2108,
    2109,
    2110,
    2111,
    2112,
    2113,
    2114,
    2115,
    2116,
    2117,
    2118,
    2119,
    2120,
    2121,
    2122,
    2123,
    2124,
    2125,
    2126,
    2127,
    2128,
    2129,
    2130,
    2131,
    2132,
    2133,
    2134,
    2135,
    2136,
    2137,
    2138,
    2139,
    2140,
    2141,
    2142,
    2143,
    2144,
    2145,
    2146,
    2147,
    2148,
    2149,
    2150,
    2151,
    2152,
    2153,
    2154,
    2155,
    2156,
    2157,
    2158,
    2159,
    2160,
    2161,
    2162,
    2163,
    2164,
    2165,
    2166,
    2167,
    2168,
    2169,
    2170,
    2171,
    2172,
    2173,
    2174,
    2175,
    2176,
    2177,
    2178,
    2179,
    2180,
    2181,
    2182,
    2183,
    2184,
    2185,
    2186,
    2187,
    2188,
    2189,
    2190,
    2191,
    2192,
    2193,
    2194,
    2195,
    2196,
    2197,
    2198,
    2199,
    2200,
    2201,
    2202,
    2203,
    2204,
    2205,
    2206,
    2207,
    2208,
    2209,
    2210,
    2211,
    2212,
    2213,
    2214,
    2215,
    2216,
    2217,
    2218,
    2219,
    2220,
    2221,
    2222,
    2223,
    2224,
    2225,
    2226,
    2227,
    2228,
    2229,
    2230,
    2231,
    2232,
    2233,
    2234,
    2235,
    2236,
    2237,
    2238,
    2239,
    2240,
    2241,
    2242,
    2243,
    2244,
    2245,
    2246,
    2247,
    2248,
    2249,
    2250,
    2251,
    2252,
    2253,
    2254,
    2255,
    2256,
    2257,
    2258,
    2259,
    2260,
    2261,
    2262,
    2263,
    2264,
    2265,
    2266,
    2267,
    2268,
    2269,
    2270,
    2271,
    2272,
    2273,
    2274,
    2275,
    2276,
    2277,
    2278,
    2279,
    2280,
    2281,
    2282,
    2283,
    2284,
    2285,
    2286,
    2287,
    2288,
    2289,
    2290,
    2291,
    2292,
    2293,
    2294,
    2295,
    2296,
    2297,
    2298,
    2299,
    2300,
    2301,
    2302,
    2303,
    2304,
    2305,
    2306,
    2307,
    2308,
    2309,
    2310,
    2311,
    2312,
    2313,
    2314,
    2315
  ]
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/environment.json (301 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/environment.json", "bytes": 301, "sha256": "28a493e28a6b6899a9eb83a806a4760f4f873075bf0ae45d22cf4be2ca9ac392", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "python": "3.12.7 (tags/v3.12.7:0b05ead, Oct  1 2024, 03:06:41) [MSC v.1941 64 bit (AMD64)]",
  "platform": "Windows-11-10.0.26200-SP0",
  "numpy": "2.5.4",
  "scipy": "1.18.1",
  "astropy": "7.2.3",
  "sunpy": "8.0.1",
  "matplotlib": "3.11.2",
  "automatic_network_downloads": false
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/evidence/cr2120.json (20,286 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/evidence/cr2120.json", "bytes": 20286, "sha256": "bc3fbfb25a580d7e9bb79755904ff1bd6286bdbdaf0809f982f510c946352301", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "synoptic_headers": [
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 762660.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.01.23_14:40:39_TAI",
      "T_START": "2012.01.09_22:35:48_TAI",
      "T_STOP": "2012.02.06_06:47:12_TAI",
      "T_ROT": "2012.01.23_14:40:39_TAI",
      "CAR_ROT": 2119,
      "CARRTIME": 762660.0,
      "B0_ROT": -5.300905,
      "B0_FRST": -3.956021,
      "B0_LAST": -6.33356,
      "LON_FRST": 762480.2,
      "LON_LAST": 762839.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3382,
      "IMG_FRST": "2012.01.09_00:00:00_TAI",
      "IMG_LAST": "2012.02.07_00:00:00_TAI",
      "IMG_ROT": "2012.01.23_18:00:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 257546,
      "MISSVALS": 1654,
      "DATAMIN": -2259.262695,
      "DATAMAX": 1209.434814,
      "DATAMEDN": 0.051303,
      "DATAMEAN": -0.007876,
      "DATARMS": 34.100953,
      "DATASKEW": -13.573143,
      "DATAKURT": 711.66306,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "8ZTE9XQC8XQC8XQC",
      "DATASUM": "4071628895",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    },
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 763020.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.02.19_22:51:59_TAI",
      "T_START": "2012.02.06_06:47:12_TAI",
      "T_STOP": "2012.03.04_14:50:52_TAI",
      "T_ROT": "2012.02.19_22:51:59_TAI",
      "CAR_ROT": 2120,
      "CARRTIME": 763020.0,
      "B0_ROT": -6.993949,
      "B0_FRST": -6.33356,
      "B0_LAST": -7.247514,
      "LON_FRST": 762840.2,
      "LON_LAST": 763199.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3313,
      "IMG_FRST": "2012.02.06_00:00:00_TAI",
      "IMG_LAST": "2012.03.05_00:00:00_TAI",
      "IMG_ROT": "2012.02.19_21:12:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 257040,
      "MISSVALS": 2160,
      "DATAMIN": -1616.314453,
      "DATAMAX": 1668.458252,
      "DATAMEDN": 0.050332,
      "DATAMEAN": -0.047442,
      "DATARMS": 27.173212,
      "DATASKEW": -4.241791,
      "DATAKURT": 839.67049,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "9ITYFIRV9IRVEIRV",
      "DATASUM": "802276192",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    },
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 763380.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.03.18_06:39:38_TAI",
      "T_START": "2012.03.04_14:50:52_TAI",
      "T_STOP": "2012.03.31_22:14:46_TAI",
      "T_ROT": "2012.03.18_06:39:38_TAI",
      "CAR_ROT": 2121,
      "CARRTIME": 763380.0,
      "B0_ROT": -7.08704,
      "B0_FRST": -7.247514,
      "B0_LAST": -6.531554,
      "LON_FRST": 763200.2,
      "LON_LAST": 763559.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3077,
      "IMG_FRST": "2012.03.04_00:00:00_TAI",
      "IMG_LAST": "2012.04.01_00:00:00_TAI",
      "IMG_ROT": "2012.03.17_21:48:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 257040,
      "MISSVALS": 2160,
      "DATAMIN": -1444.688721,
      "DATAMAX": 1817.340454,
      "DATAMEDN": 0.005299,
      "DATAMEAN": -0.124553,
      "DATARMS": 32.935324,
      "DATASKEW": 1.993347,
      "DATAKURT": 588.946878,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "JaHRMUEOJZEOJZEO",
      "DATASUM": "3170228023",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    }
  ],
  "incomplete_rows": [
    [
      357,
      358,
      359
    ],
    [
      357,
      358,
      359
    ],
    [
      357,
      358,
      359
    ]
  ],
  "observation": {
    "saved_report": {
      "cr": 2120,
      "input_rotations": [
        2119,
        2120,
        2121
      ],
      "input_sha256": {
        "synoptic_reconstruction.py": "79c43e629c7e0f9ec93a3e4c974f74087c99c4759beb4a8ba4c9f0baf2e2cc6e",
        "prepare_viewer_data.py": "9394891f5af03c377b0c854cbbf1961625148bb9a0d558d78a1f8534fce10405",
        "validate_observations.py": "33b69ea18dd2770ca291c80931da856889d8bb85975fb64b83569e38f9fa0deb",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2119.fits": "4e46b43b9836de83242e23c26a6c0e61172f6f3a76cd7f2251c91de91881e9f9",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2120.fits": "cd94afec13cfda0515235fda2efb384c26892a359e5428380796847c0ef18bbb",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2121.fits": "e1d73cd8766f0ff3bf8eddb567c6e1fa39cdd26442be118353cd274d8ab01c24"
      },
      "reference": {
        "definition": "Observed HMI central meridian longitude 180 degrees, linearly interpolated between adjacent quality-zero 45-second records",
        "crossing_tai": "2012-02-19T22:55:28.688",
        "crossing_utc": "2012-02-19T22:54:54.688",
        "header_T_ROT_tai": "2012-02-19T22:51:59.000",
        "sunpy_earth_midrotation_tai": "2012-02-19T22:47:46.384",
        "sunpy_earth_midrotation_utc": "2012-02-19T22:47:12.384",
        "bracketing_records": [
          {
            "T_REC": "2012.02.19_22:55:30_TAI",
            "T_OBS": "2012.02.19_22:55:24_TAI",
            "CRLN_OBS_deg": 180.000717
          },
          {
            "T_REC": "2012.02.19_22:56:15_TAI",
            "T_OBS": "2012.02.19_22:56:09_TAI",
            "CRLN_OBS_deg": 179.993835
          }
        ]
      },
      "observation": {
        "series": "hmi.M_45s",
        "T_REC": "2012.02.19_22:55:30_TAI",
        "T_OBS": "2012.02.19_22:55:24_TAI",
        "T_OBS_utc": "2012-02-19T22:54:50.000",
        "offset_seconds": -4.688317349654092,
        "QUALITY": "0x00000000",
        "CRLN_OBS_deg": 180.000717,
        "CRLT_OBS_deg": -7.001489,
        "source_url": "https://jsoc1.stanford.edu/SUM30/D299416113/S00003/magnetogram.fits",
        "file": "hmi.M_45s.20120219_225530_TAI.magnetogram.fits",
        "sha256": "99edac9897121e065aa9153294e34b58fa2a7e6b42783ad377f0ec836c1d306e"
      },
      "method": {
        "mu_min": 0.8,
        "smoothing_sigma_detector_pixels": 3.0,
        "interpolation": "bilinear detector sampling; LOS divided by mu",
        "synoptic_longitude_step": "absolute FITS CDELT1, per SunPy HMI synoptic-map convention",
        "mask": "finite observation, original and both reconstructions; mu >= 0.8; finite smoothed observation neighborhood"
      },
      "scores": {
        "original": {
          "count": 25693,
          "bias_gauss": 0.07300365545127543,
          "mae_gauss": 9.018476889881612,
          "rmse_gauss": 23.821126003867285,
          "pearson_r": 0.8253540465211998
        },
        "ananya": {
          "count": 25693,
          "bias_gauss": -0.3368298400131778,
          "mae_gauss": 12.103750191889167,
          "rmse_gauss": 48.20871295555648,
          "pearson_r": 0.36943650074569223
        },
        "fixed": {
          "count": 25693,
          "bias_gauss": 0.0324128981720986,
          "mae_gauss": 9.017377900559431,
          "rmse_gauss": 23.68463409431693,
          "pearson_r": 0.826450127963197
        }
      },
      "sensitivity_mu": {
        "0.8": {
          "original": {
            "count": 25693,
            "bias_gauss": 0.07300365545127543,
            "mae_gauss": 9.018476889881612,
            "rmse_gauss": 23.821126003867285,
            "pearson_r": 0.8253540465211998
          },
          "ananya": {
            "count": 25693,
            "bias_gauss": -0.3368298400131778,
            "mae_gauss": 12.103750191889167,
            "rmse_gauss": 48.20871295555648,
            "pearson_r": 0.36943650074569223
          },
          "fixed": {
            "count": 25693,
            "bias_gauss": 0.0324128981720986,
            "mae_gauss": 9.017377900559431,
            "rmse_gauss": 23.68463409431693,
            "pearson_r": 0.826450127963197
          }
        },
        "0.9": {
          "original": {
            "count": 12851,
            "bias_gauss": 0.4027038554912814,
            "mae_gauss": 8.42936878461228,
            "rmse_gauss": 25.0235798066951,
            "pearson_r": 0.8928309567380952
          },
          "ananya": {
            "count": 12851,
            "bias_gauss": 1.229995358650899,
            "mae_gauss": 13.176116813942187,
            "rmse_gauss": 57.72650484539294,
            "pearson_r": 0.4438446055222546
          },
          "fixed": {
            "count": 12851,
            "bias_gauss": 0.4071224477586048,
            "mae_gauss": 8.470924793455927,
            "rmse_gauss": 25.285016556043804,
            "pearson_r": 0.8902422501861321
          }
        },
        "0.95": {
          "original": {
            "count": 6416,
            "bias_gauss": 0.032064183963773564,
            "mae_gauss": 5.559091000009462,
            "rmse_gauss": 12.20542842011989,
            "pearson_r": 0.4440656976816497
          },
          "ananya": {
            "count": 6416,
            "bias_gauss": -0.4042281614107595,
            "mae_gauss": 6.770585642930849,
            "rmse_gauss": 15.065562043827798,
            "pearson_r": 0.10182063693051199
          },
          "fixed": {
            "count": 6416,
            "bias_gauss": 0.03630716062162706,
            "mae_gauss": 5.583789271835392,
            "rmse_gauss": 12.26169843394479,
            "pearson_r": 0.4342650425445981
          }
        }
      },
      "diagnostics": {
        "original_vs_observation_same_mask": {
          "count": 25693,
          "bias_gauss": 0.07300365545127543,
          "mae_gauss": 9.018476889881612,
          "rmse_gauss": 23.821126003867285,
          "pearson_r": 0.8253540465211998
        },
        "registration_control": {
          "positive_orientation": {
            "count": 25693,
            "bias_gauss": 0.07300365545127543,
            "mae_gauss": 9.018476889881612,
            "rmse_gauss": 23.821126003867285,
            "pearson_r": 0.8253540465211998
          },
          "negative_header_orientation": {
            "count": 25693,
            "bias_gauss": 0.060736224025826215,
            "mae_gauss": 13.395545648523413,
            "rmse_gauss": 54.62316855247139,
            "pearson_r": 0.03515812782779947
          }
        },
        "header_CDELT1": -0.5
      }
    },
    "metadata": {
      "DATE": "2012-09-05T08:28:42Z",
      "DATE__OBS": "2012-02-19T22:54:27.70Z",
      "DATE-OBS": "2012-02-19T22:54:27.70Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_FRONT2",
      "WAVELNTH": "6173.0",
      "CAMERA": "2",
      "BUNIT": "Gauss",
      "ORIGIN": "SDO/JSOC-SDP",
      "CONTENT": "MAGNETOGRAM",
      "QUALITY": "0x00000000",
      "QUALLEV1": "0x00000000",
      "HISTORY": "Polynomial Coefficients used for Doppler velocity correction: 8.088925e+01 1.719513e-03 -5.300760e-07 2.270470e-10 \nCROTA2 corrected by adding -0.0702 degrees",
      "COMMENT": "De-rotation: ON; Un-distortion: ON; Re-centering: ON; Re-sizing: OFF; RSUNerr=0.5; correction for cosmic-ray hits; dpath=/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps/",
      "BLD_VERS": "-601",
      "HCAMID": "3",
      "SOURCE": "hmi.lev1[:#33953586,#33953550,#33953526,#33953598,#33953622,#33953646,#33953588,#33953552,#33953528,#33953600,#33953624,#33953648,#33953590,#33953554,#33953530,#33953506,#33953602,#33953626,#33953568,#33953556,#33953532,#33953508,#33953604,#33953628,#33953570,#33953558,#33953534,#33953510,#33953606,#33953630,#33953572,#33953560,#33953536,#33953512,#33953608,#33953632,#33953574,#33953562,#33953538,#33953514,#33953610,#33953634,#33953576,#33953564,#33953540,#33953516,#33953612,#33953636,#33953578,#33953566,#33953542,#33953518,#33953614,#33953638,#33953592,#33953580,#33953544,#33953520,#33953616,#33953640,#33953594,#33953582,#33953546,#33953522,#33953618,#33953642,#33953596,#33953584,#33953548,#33953524,#33953620,#33953644]",
      "TOTVALS": "12259454",
      "DATAVALS": "12259454",
      "MISSVALS": "0",
      "SATVALS": "13789",
      "DATAMIN2": "-4446.095703",
      "DATAMAX2": "4446.095703",
      "DATAMED2": "0.036942",
      "DATAMEA2": "0.119472",
      "DATARMS2": "66.837822",
      "DATASKE2": "2.373825",
      "DATAKUR2": "2084.877441",
      "DATAMIN": "-1838.880127",
      "DATAMAX": "1844.079712",
      "DATAMEDN": "0.043933",
      "DATAMEAN": "0.048979",
      "DATARMS": "33.309605",
      "DATASKEW": "-2.975821",
      "DATAKURT": "530.902771",
      "CTYPE1": "HPLN-TAN",
      "CTYPE2": "HPLT-TAN",
      "CRPIX1": "2044.260742",
      "CRPIX2": "2043.979980",
      "CRVAL1": "0.000000",
      "CRVAL2": "0.000000",
      "CDELT1": "0.504236",
      "CDELT2": "0.504236",
      "CUNIT1": "arcsec",
      "CUNIT2": "arcsec",
      "CROTA2": "179.929703",
      "CRDER1": "MISSING",
      "CRDER2": "MISSING",
      "CSYSER1": "MISSING",
      "CSYSER2": "MISSING",
      "WCSNAME": "Helioprojective-cartesian",
      "DSUN_OBS": "147868584747.97",
      "DSUN_REF": "149597870691",
      "RSUN_REF": "696000000",
      "CRLN_OBS": "180.000717",
      "CRLT_OBS": "-7.001489",
      "CAR_ROT": "2120",
      "OBS_VR": "2591.090469",
      "OBS_VW": "29376.179972",
      "OBS_VN": "-2994.490861",
      "RSUN_OBS": "970.867737",
      "T_OBS": "2012.02.19_22:55:24_TAI",
      "T_REC": "2012.02.19_22:55:30_TAI",
      "T_REC_epoch": "1993.01.01_00:00:00_TAI",
      "T_REC_step": "45.0",
      "T_REC_unit": "secs",
      "CADENCE": "45.0",
      "DATASIGN": "1",
      "HFLID": "1021",
      "HCFTID": "11",
      "QLOOK": "0",
      "CAL_FSN": "32869398",
      "LUTQUERY": "hmi.lookup[32869398][][3][37][53][0][81]",
      "TSEL": "23.347069",
      "TFRONT": "32.897064",
      "TINTNUM": "6",
      "SINTNUM": "10",
      "DISTCOEF": "/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps//../libs/lev15/",
      "ROTCOEF": "/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps//../libs/lev15/",
      "ODICOEFF": "6",
      "OROCOEFF": "4",
      "POLCALM": "1",
      "CODEVER0": "$Id: HMI_observables.c,v 1.32 2012/01/18 23:28:15 couvidat Exp $",
      "CODEVER1": "$Id: interpol_code.c,v 1.2 2011/12/06 18:11:03 arta Exp $",
      "CODEVER2": "$Id: interpol_code.c,v 1.2 2011/12/06 18:11:03 arta Exp $",
      "CODEVER3": "$Id: polcal.c,v 1.4 2010/09/23 20:57:27 schou Exp $",
      "CALVER64": "0x0000000000000010"
    },
    "raw_fits_headers": [
      {
        "SIMPLE": true,
        "BITPIX": 16,
        "NAXIS": 0,
        "EXTEND": true,
        "COMMENT": "  FITS (Flexible Image Transport System) format is defined in 'Astronomy\n  and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H"
      },
      {
        "XTENSION": "IMAGE",
        "BITPIX": -64,
        "NAXIS": 2,
        "NAXIS1": 4096,
        "NAXIS2": 4096,
        "PCOUNT": 0,
        "GCOUNT": 1,
        "": ""
      }
    ],
    "image_sha256": "99edac9897121e065aa9153294e34b58fa2a7e6b42783ad377f0ec836c1d306e",
    "metadata_sha256": "98526ee53160261c4c1e4ed898fb1a4b753a9a7dd11d70d6999243ae0cf1a3a3",
    "independent_projection": {
      "common_count": 25693,
      "max_abs_mu_difference": 5.551115123125783e-16,
      "max_abs_Br_difference_G": 1.3853655711493218e-07,
      "rmse_Br_difference_G": 1.3449803809708932e-09,
      "same_finite_mask": true
    },
    "cache_check": {
      "same_finite_mask": true,
      "max_abs_observation_difference_G": 0.0
    },
    "timing": {
      "derived_crossing_utc": "2012-02-19T22:54:54.688",
      "stored_crossing_utc": "2012-02-19T22:54:54.688",
      "bracket_seconds": 44.99999999999744,
      "derived_CM_rate_deg_day": 13.213440000036668,
      "observation_minus_crossing_s": -4.688317349654092,
      "observation_minus_header_T_ROT_s": 205.00000000000006,
      "brackets_are_saved_metadata_not_requeried": true
    }
  },
  "baseline_reproduction": {
    "000": {
      "existing_pipeline_same_finite_mask": true,
      "existing_pipeline_max_abs_difference_G": 0.0,
      "cached_map_max_abs_difference_G": 1.2812506611226127e-10
    },
    "100": {
      "existing_pipeline_same_finite_mask": true,
      "existing_pipeline_max_abs_difference_G": 0.0,
      "cached_map_max_abs_difference_G": 1.666222715357435e-11
    }
  },
  "literal_matches_vectorized": true,
  "chronology_midrotations": [
    {
      "cr": 2119,
      "midrotation_utc": "2012-01-23T14:35:57.767"
    },
    {
      "cr": 2120,
      "midrotation_utc": "2012-02-19T22:47:12.384"
    },
    {
      "cr": 2121,
      "midrotation_utc": "2012-03-18T06:34:51.376"
    }
  ],
  "chronology_within_rotation": [
    {
      "longitude_deg": 359.0,
      "utc": "2012-02-06T08:31:55.428"
    },
    {
      "longitude_deg": 180.0,
      "utc": "2012-02-19T22:47:12.384"
    },
    {
      "longitude_deg": 1.0,
      "utc": "2012-03-04T12:57:02.618"
    }
  ],
  "L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d": [
    180.1316958022609,
    180.00000920417344,
    179.86832258059124
  ],
  "primary_common_pixels": 25693,
  "full_map_common_pixels": 255770,
  "full_map_common_area_fraction": 0.9868060277777777,
  "primary_mask_same_as_prior": true,
  "exact_vs_first_order": {
    "max_query_difference_deg": 19.75838882300019,
    "full_common_field_difference": {
      "count": 255463,
      "bias_G": -0.005350681336209114,
      "mae_G": 3.3831674127294464,
      "rmse_G": 8.279405608730249,
      "pearson_r": 0.9523767712687474,
      "median_abs_G": 0.4933915105117186,
      "p95_abs_G": 15.492902340974066
    }
  }
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/evidence/cr2122.json (20,292 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/evidence/cr2122.json", "bytes": 20292, "sha256": "9bb71b45cd5f1305408962f067e1da991df4de0bcb5c7a5f221efa9a9d52c625", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "synoptic_headers": [
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 763380.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.03.18_06:39:38_TAI",
      "T_START": "2012.03.04_14:50:52_TAI",
      "T_STOP": "2012.03.31_22:14:46_TAI",
      "T_ROT": "2012.03.18_06:39:38_TAI",
      "CAR_ROT": 2121,
      "CARRTIME": 763380.0,
      "B0_ROT": -7.08704,
      "B0_FRST": -7.247514,
      "B0_LAST": -6.531554,
      "LON_FRST": 763200.2,
      "LON_LAST": 763559.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3077,
      "IMG_FRST": "2012.03.04_00:00:00_TAI",
      "IMG_LAST": "2012.04.01_00:00:00_TAI",
      "IMG_ROT": "2012.03.17_21:48:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 257040,
      "MISSVALS": 2160,
      "DATAMIN": -1444.688721,
      "DATAMAX": 1817.340454,
      "DATAMEDN": 0.005299,
      "DATAMEAN": -0.124553,
      "DATARMS": 32.935324,
      "DATASKEW": 1.993347,
      "DATAKURT": 588.946878,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "JaHRMUEOJZEOJZEO",
      "DATASUM": "3170228023",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    },
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 763740.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.04.14_13:34:06_TAI",
      "T_START": "2012.03.31_22:14:46_TAI",
      "T_STOP": "2012.04.28_04:37:05_TAI",
      "T_ROT": "2012.04.14_13:34:06_TAI",
      "CAR_ROT": 2122,
      "CARRTIME": 763740.0,
      "B0_ROT": -5.622703,
      "B0_FRST": -6.531554,
      "B0_LAST": -4.419608,
      "LON_FRST": 763560.2,
      "LON_LAST": 763919.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3343,
      "IMG_FRST": "2012.03.31_00:00:00_TAI",
      "IMG_LAST": "2012.04.29_00:00:00_TAI",
      "IMG_ROT": "2012.04.14_13:24:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 257447,
      "MISSVALS": 1753,
      "DATAMIN": -1616.845459,
      "DATAMAX": 1517.690674,
      "DATAMEDN": 0.002105,
      "DATAMEAN": 0.021333,
      "DATARMS": 30.184272,
      "DATASKEW": 1.305688,
      "DATAKURT": 495.814683,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "BrTZBoQXBoQXBoQX",
      "DATASUM": "1790299224",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    },
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 764100.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.05.11_19:24:54_TAI",
      "T_START": "2012.04.28_04:37:05_TAI",
      "T_STOP": "2012.05.25_10:00:13_TAI",
      "T_ROT": "2012.05.11_19:24:54_TAI",
      "CAR_ROT": 2123,
      "CARRTIME": 764100.0,
      "B0_ROT": -2.993318,
      "B0_FRST": -4.419608,
      "B0_LAST": -1.421809,
      "LON_FRST": 763920.2,
      "LON_LAST": 764279.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3314,
      "IMG_FRST": "2012.04.28_00:00:00_TAI",
      "IMG_LAST": "2012.05.26_00:00:00_TAI",
      "IMG_ROT": "2012.05.12_00:36:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 258280,
      "MISSVALS": 920,
      "DATAMIN": -2267.044434,
      "DATAMAX": 1685.602295,
      "DATAMEDN": -0.015214,
      "DATAMEAN": -0.048774,
      "DATARMS": 37.168927,
      "DATASKEW": -2.563201,
      "DATAKURT": 638.529709,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "K4PXN3MWK3MWK3MW",
      "DATASUM": "2024852514",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    }
  ],
  "incomplete_rows": [
    [
      357,
      358,
      359
    ],
    [
      357,
      358,
      359
    ],
    [
      358,
      359
    ]
  ],
  "observation": {
    "saved_report": {
      "cr": 2122,
      "input_rotations": [
        2121,
        2122,
        2123
      ],
      "input_sha256": {
        "synoptic_reconstruction.py": "79c43e629c7e0f9ec93a3e4c974f74087c99c4759beb4a8ba4c9f0baf2e2cc6e",
        "prepare_viewer_data.py": "9394891f5af03c377b0c854cbbf1961625148bb9a0d558d78a1f8534fce10405",
        "validate_observations.py": "33b69ea18dd2770ca291c80931da856889d8bb85975fb64b83569e38f9fa0deb",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2121.fits": "e1d73cd8766f0ff3bf8eddb567c6e1fa39cdd26442be118353cd274d8ab01c24",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2122.fits": "881845ae3d083da6719939e9db6f3e8d66c65065ea553a2a51fa30e985c0465f",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2123.fits": "7f066bfca1e7cb1d73a10bff065e3236a345ba5d03a9598b71910d753723a7ef"
      },
      "reference": {
        "definition": "Observed HMI central meridian longitude 180 degrees, linearly interpolated between adjacent quality-zero 45-second records",
        "crossing_tai": "2012-04-14T13:40:05.801",
        "crossing_utc": "2012-04-14T13:39:31.801",
        "header_T_ROT_tai": "2012-04-14T13:34:06.000",
        "sunpy_earth_midrotation_tai": "2012-04-14T13:29:58.957",
        "sunpy_earth_midrotation_utc": "2012-04-14T13:29:24.957",
        "bracketing_records": [
          {
            "T_REC": "2012.04.14_13:39:45_TAI",
            "T_OBS": "2012.04.14_13:39:47_TAI",
            "CRLN_OBS_deg": 180.002869
          },
          {
            "T_REC": "2012.04.14_13:40:30_TAI",
            "T_OBS": "2012.04.14_13:40:32_TAI",
            "CRLN_OBS_deg": 179.996002
          }
        ]
      },
      "observation": {
        "series": "hmi.M_45s",
        "T_REC": "2012.04.14_13:39:45_TAI",
        "T_OBS": "2012.04.14_13:39:47_TAI",
        "T_OBS_utc": "2012-04-14T13:39:13.000",
        "offset_seconds": -18.800786369619882,
        "QUALITY": "0x00000000",
        "CRLN_OBS_deg": 180.002869,
        "CRLT_OBS_deg": -5.610855,
        "source_url": "https://jsoc1.stanford.edu/SUM33/D316613804/S00029/magnetogram.fits",
        "file": "hmi.M_45s.20120414_133945_TAI.magnetogram.fits",
        "sha256": "5c0941b10dca18faa0a226add5b4d2281cd9bfce883d83d07c04785b18f07490"
      },
      "method": {
        "mu_min": 0.8,
        "smoothing_sigma_detector_pixels": 3.0,
        "interpolation": "bilinear detector sampling; LOS divided by mu",
        "synoptic_longitude_step": "absolute FITS CDELT1, per SunPy HMI synoptic-map convention",
        "mask": "finite observation, original and both reconstructions; mu >= 0.8; finite smoothed observation neighborhood"
      },
      "scores": {
        "original": {
          "count": 25705,
          "bias_gauss": 0.15753879017161634,
          "mae_gauss": 11.503933919466728,
          "rmse_gauss": 35.247419514037766,
          "pearson_r": 0.3880825550285347
        },
        "ananya": {
          "count": 25705,
          "bias_gauss": 0.4064251249102429,
          "mae_gauss": 14.4532829057792,
          "rmse_gauss": 43.47997531380187,
          "pearson_r": 0.015852700321783632
        },
        "fixed": {
          "count": 25705,
          "bias_gauss": 0.1939411017110043,
          "mae_gauss": 11.727542506042578,
          "rmse_gauss": 35.16570367816063,
          "pearson_r": 0.3830528118734339
        }
      },
      "sensitivity_mu": {
        "0.8": {
          "original": {
            "count": 25705,
            "bias_gauss": 0.15753879017161634,
            "mae_gauss": 11.503933919466728,
            "rmse_gauss": 35.247419514037766,
            "pearson_r": 0.3880825550285347
          },
          "ananya": {
            "count": 25705,
            "bias_gauss": 0.4064251249102429,
            "mae_gauss": 14.4532829057792,
            "rmse_gauss": 43.47997531380187,
            "pearson_r": 0.015852700321783632
          },
          "fixed": {
            "count": 25705,
            "bias_gauss": 0.1939411017110043,
            "mae_gauss": 11.727542506042578,
            "rmse_gauss": 35.16570367816063,
            "pearson_r": 0.3830528118734339
          }
        },
        "0.9": {
          "original": {
            "count": 12845,
            "bias_gauss": -0.12674041554640236,
            "mae_gauss": 8.108847983875712,
            "rmse_gauss": 21.396100314242336,
            "pearson_r": 0.46868915753531204
          },
          "ananya": {
            "count": 12845,
            "bias_gauss": 0.026133247291283367,
            "mae_gauss": 9.349202526469012,
            "rmse_gauss": 24.64971566646883,
            "pearson_r": 0.12121784105086174
          },
          "fixed": {
            "count": 12845,
            "bias_gauss": -0.19386453875727222,
            "mae_gauss": 8.223951903715786,
            "rmse_gauss": 21.382248442999128,
            "pearson_r": 0.468832119785115
          }
        },
        "0.95": {
          "original": {
            "count": 6411,
            "bias_gauss": -0.029880387789652983,
            "mae_gauss": 5.1414863164138405,
            "rmse_gauss": 10.132224433424888,
            "pearson_r": 0.5129143759933378
          },
          "ananya": {
            "count": 6411,
            "bias_gauss": 0.3340432553164569,
            "mae_gauss": 6.273283106262912,
            "rmse_gauss": 12.876092063133884,
            "pearson_r": 0.18638437717076203
          },
          "fixed": {
            "count": 6411,
            "bias_gauss": -0.02480786288352206,
            "mae_gauss": 5.182109927045531,
            "rmse_gauss": 10.111406181259525,
            "pearson_r": 0.5121330001914405
          }
        }
      },
      "diagnostics": {
        "original_vs_observation_same_mask": {
          "count": 25705,
          "bias_gauss": 0.15753879017161634,
          "mae_gauss": 11.503933919466728,
          "rmse_gauss": 35.247419514037766,
          "pearson_r": 0.3880825550285347
        },
        "registration_control": {
          "positive_orientation": {
            "count": 25705,
            "bias_gauss": 0.15753879017161634,
            "mae_gauss": 11.503933919466728,
            "rmse_gauss": 35.247419514037766,
            "pearson_r": 0.3880825550285347
          },
          "negative_header_orientation": {
            "count": 25705,
            "bias_gauss": 0.16411003740971178,
            "mae_gauss": 15.161804329412266,
            "rmse_gauss": 44.19881564813937,
            "pearson_r": -0.03156460666764174
          }
        },
        "header_CDELT1": -0.5
      }
    },
    "metadata": {
      "DATE": "2012-09-05T08:31:39Z",
      "DATE__OBS": "2012-04-14T13:38:50.00Z",
      "DATE-OBS": "2012-04-14T13:38:50.00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_FRONT2",
      "WAVELNTH": "6173.0",
      "CAMERA": "2",
      "BUNIT": "Gauss",
      "ORIGIN": "SDO/JSOC-SDP",
      "CONTENT": "MAGNETOGRAM",
      "QUALITY": "0x00000000",
      "QUALLEV1": "0x00000000",
      "HISTORY": "Polynomial Coefficients used for Doppler velocity correction: 1.081366e+02 1.021984e-03 -6.398566e-07 2.309219e-10 \nCROTA2 corrected by adding -0.0702 degrees",
      "COMMENT": "De-rotation: ON; Un-distortion: ON; Re-centering: ON; Re-sizing: OFF; RSUNerr=0.5; correction for cosmic-ray hits; dpath=/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps/",
      "BLD_VERS": "-601",
      "HCAMID": "3",
      "SOURCE": "hmi.lev1[:#36939080,#36939056,#36939032,#36939116,#36939128,#36939164,#36939082,#36939058,#36939034,#36939118,#36939130,#36939166,#36939084,#36939060,#36939036,#36939012,#36939120,#36939132,#36939086,#36939062,#36939038,#36939014,#36939098,#36939134,#36939088,#36939064,#36939040,#36939016,#36939100,#36939136,#36939090,#36939066,#36939042,#36939018,#36939102,#36939138,#36939092,#36939068,#36939044,#36939020,#36939104,#36939140,#36939094,#36939070,#36939046,#36939022,#36939106,#36939142,#36939096,#36939072,#36939048,#36939024,#36939108,#36939144,#36939110,#36939074,#36939050,#36939026,#36939122,#36939158,#36939112,#36939076,#36939052,#36939028,#36939124,#36939160,#36939114,#36939078,#36939054,#36939030,#36939126,#36939162]",
      "TOTVALS": "11911295",
      "DATAVALS": "11911295",
      "MISSVALS": "0",
      "SATVALS": "6911",
      "DATAMIN2": "-4447.563965",
      "DATAMAX2": "4447.563965",
      "DATAMED2": "-0.026025",
      "DATAMEA2": "-0.035301",
      "DATARMS2": "58.157505",
      "DATASKE2": "-0.508271",
      "DATAKUR2": "2526.538330",
      "DATAMIN": "-1326.287231",
      "DATAMAX": "1440.885986",
      "DATAMEDN": "-0.032629",
      "DATAMEAN": "-0.038309",
      "DATARMS": "29.503187",
      "DATASKEW": "0.156711",
      "DATAKURT": "263.979462",
      "CTYPE1": "HPLN-TAN",
      "CTYPE2": "HPLT-TAN",
      "CRPIX1": "2042.352295",
      "CRPIX2": "2047.421265",
      "CRVAL1": "0.000000",
      "CRVAL2": "0.000000",
      "CDELT1": "0.504277",
      "CDELT2": "0.504277",
      "CUNIT1": "arcsec",
      "CUNIT2": "arcsec",
      "CROTA2": "179.929871",
      "CRDER1": "MISSING",
      "CRDER2": "MISSING",
      "CSYSER1": "MISSING",
      "CSYSER2": "MISSING",
      "WCSNAME": "Helioprojective-cartesian",
      "DSUN_OBS": "150058074158.17",
      "DSUN_REF": "149597870691",
      "RSUN_REF": "696000000",
      "CRLN_OBS": "180.002869",
      "CRLT_OBS": "-5.610855",
      "CAR_ROT": "2122",
      "OBS_VR": "-2191.746240",
      "OBS_VW": "29797.481835",
      "OBS_VN": "909.927421",
      "RSUN_OBS": "956.701721",
      "T_OBS": "2012.04.14_13:39:47_TAI",
      "T_REC": "2012.04.14_13:39:45_TAI",
      "T_REC_epoch": "1993.01.01_00:00:00_TAI",
      "T_REC_step": "45.0",
      "T_REC_unit": "secs",
      "CADENCE": "45.0",
      "DATASIGN": "1",
      "HFLID": "1021",
      "HCFTID": "11",
      "QLOOK": "0",
      "CAL_FSN": "32869398",
      "LUTQUERY": "hmi.lookup[32869398][][3][37][53][0][81]",
      "TSEL": "22.755207",
      "TFRONT": "31.682232",
      "TINTNUM": "6",
      "SINTNUM": "10",
      "DISTCOEF": "/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps//../libs/lev15/",
      "ROTCOEF": "/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps//../libs/lev15/",
      "ODICOEFF": "6",
      "OROCOEFF": "4",
      "POLCALM": "1",
      "CODEVER0": "$Id: HMI_observables.c,v 1.32 2012/01/18 23:28:15 couvidat Exp $",
      "CODEVER1": "$Id: interpol_code.c,v 1.2 2011/12/06 18:11:03 arta Exp $",
      "CODEVER2": "$Id: interpol_code.c,v 1.2 2011/12/06 18:11:03 arta Exp $",
      "CODEVER3": "$Id: polcal.c,v 1.4 2010/09/23 20:57:27 schou Exp $",
      "CALVER64": "0x0000000000000010"
    },
    "raw_fits_headers": [
      {
        "SIMPLE": true,
        "BITPIX": 16,
        "NAXIS": 0,
        "EXTEND": true,
        "COMMENT": "  FITS (Flexible Image Transport System) format is defined in 'Astronomy\n  and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H"
      },
      {
        "XTENSION": "IMAGE",
        "BITPIX": -64,
        "NAXIS": 2,
        "NAXIS1": 4096,
        "NAXIS2": 4096,
        "PCOUNT": 0,
        "GCOUNT": 1,
        "": ""
      }
    ],
    "image_sha256": "5c0941b10dca18faa0a226add5b4d2281cd9bfce883d83d07c04785b18f07490",
    "metadata_sha256": "4798b88c94266fc647c8e8c84a8b017d966a93ac50705144ffd76e2855daef4f",
    "independent_projection": {
      "common_count": 25705,
      "max_abs_mu_difference": 4.440892098500626e-16,
      "max_abs_Br_difference_G": 5.112429644071881e-07,
      "rmse_Br_difference_G": 3.3123787067746312e-09,
      "same_finite_mask": true
    },
    "cache_check": {
      "same_finite_mask": true,
      "max_abs_observation_difference_G": 0.0
    },
    "timing": {
      "derived_crossing_utc": "2012-04-14T13:39:31.801",
      "stored_crossing_utc": "2012-04-14T13:39:31.801",
      "bracket_seconds": 44.99999999999744,
      "derived_CM_rate_deg_day": 13.18464000000024,
      "observation_minus_crossing_s": -18.800786369619882,
      "observation_minus_header_T_ROT_s": 340.999999999999,
      "brackets_are_saved_metadata_not_requeried": true
    }
  },
  "baseline_reproduction": {
    "000": {
      "existing_pipeline_same_finite_mask": true,
      "existing_pipeline_max_abs_difference_G": 0.0,
      "cached_map_max_abs_difference_G": 2.7569058147491887e-11
    },
    "100": {
      "existing_pipeline_same_finite_mask": true,
      "existing_pipeline_max_abs_difference_G": 0.0,
      "cached_map_max_abs_difference_G": 1.91526794424135e-11
    }
  },
  "literal_matches_vectorized": true,
  "chronology_midrotations": [
    {
      "cr": 2121,
      "midrotation_utc": "2012-03-18T06:34:51.376"
    },
    {
      "cr": 2122,
      "midrotation_utc": "2012-04-14T13:29:24.957"
    },
    {
      "cr": 2123,
      "midrotation_utc": "2012-05-11T19:20:19.337"
    }
  ],
  "chronology_within_rotation": [
    {
      "longitude_deg": 359.0,
      "utc": "2012-03-31T23:59:33.461"
    },
    {
      "longitude_deg": 180.0,
      "utc": "2012-04-14T13:29:24.957"
    },
    {
      "longitude_deg": 1.0,
      "utc": "2012-04-28T02:43:51.481"
    }
  ],
  "L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d": [
    180.13203458158608,
    180.00000031755224,
    179.86796597990394
  ],
  "primary_common_pixels": 25705,
  "full_map_common_pixels": 255770,
  "full_map_common_area_fraction": 0.9868060277777777,
  "primary_mask_same_as_prior": true,
  "exact_vs_first_order": {
    "max_query_difference_deg": 19.75838882300019,
    "full_common_field_difference": {
      "count": 255463,
      "bias_G": 0.00011040605881321566,
      "mae_G": 3.24633993957715,
      "rmse_G": 7.791452115568718,
      "pearson_r": 0.9660255814407297,
      "median_abs_G": 0.4772932289409172,
      "p95_abs_G": 14.82533537496367
    }
  }
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/evidence/cr2124.json (20,246 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/evidence/cr2124.json", "bytes": 20246, "sha256": "576c84de142a31dbb965f5d6b1b9f86ed7e3f394eef0839497e0cb402b03954d", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "synoptic_headers": [
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 764100.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.05.11_19:24:54_TAI",
      "T_START": "2012.04.28_04:37:05_TAI",
      "T_STOP": "2012.05.25_10:00:13_TAI",
      "T_ROT": "2012.05.11_19:24:54_TAI",
      "CAR_ROT": 2123,
      "CARRTIME": 764100.0,
      "B0_ROT": -2.993318,
      "B0_FRST": -4.419608,
      "B0_LAST": -1.421809,
      "LON_FRST": 763920.2,
      "LON_LAST": 764279.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3314,
      "IMG_FRST": "2012.04.28_00:00:00_TAI",
      "IMG_LAST": "2012.05.26_00:00:00_TAI",
      "IMG_ROT": "2012.05.12_00:36:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 258280,
      "MISSVALS": 920,
      "DATAMIN": -2267.044434,
      "DATAMAX": 1685.602295,
      "DATAMEDN": -0.015214,
      "DATAMEAN": -0.048774,
      "DATARMS": 37.168927,
      "DATASKEW": -2.563201,
      "DATAKURT": 638.529709,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "K4PXN3MWK3MWK3MW",
      "DATASUM": "2024852514",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    },
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 764460.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.06.08_00:26:50_TAI",
      "T_START": "2012.05.25_10:00:13_TAI",
      "T_STOP": "2012.06.21_14:49:05_TAI",
      "T_ROT": "2012.06.08_00:26:50_TAI",
      "CAR_ROT": 2124,
      "CARRTIME": 764460.0,
      "B0_ROT": 0.214034,
      "B0_FRST": -1.421809,
      "B0_LAST": 1.833407,
      "LON_FRST": 764280.2,
      "LON_LAST": 764639.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3305,
      "IMG_FRST": "2012.05.25_00:00:00_TAI",
      "IMG_LAST": "2012.06.22_00:00:00_TAI",
      "IMG_ROT": "2012.06.08_04:24:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 258752,
      "MISSVALS": 448,
      "DATAMIN": -1769.542969,
      "DATAMAX": 2142.054199,
      "DATAMEDN": -0.018296,
      "DATAMEAN": -0.100827,
      "DATARMS": 37.389643,
      "DATASKEW": 2.402801,
      "DATAKURT": 575.717124,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "YWA1bU81ZUA1aU71",
      "DATASUM": "3591661808",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    },
    {
      "SIMPLE": true,
      "BITPIX": -32,
      "NAXIS": 2,
      "NAXIS1": 720,
      "NAXIS2": 360,
      "DATE": "2014-07-15T00:00:00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_SIDE1",
      "WAVELNTH": 6173.0,
      "BUNIT": "Mx/cm^2",
      "CONTENT": "Carrington Synoptic Chart Of Br Field",
      "CTYPE1": "CRLN-CEA",
      "CTYPE2": "CRLT-CEA",
      "CRPIX1": 360.4,
      "CRPIX2": 180.5,
      "CRVAL1": 764820.0,
      "CRVAL2": 0.0,
      "CDELT1": -0.5,
      "CDELT2": 0.005556,
      "CUNIT1": "Degree",
      "CUNIT2": "Sine Latitude",
      "WCSNAME": "Carrington Heliographic",
      "CADENCE": 360.0,
      "DATASIGN": 1,
      "T_OBS": "2012.07.05_05:11:27_TAI",
      "T_START": "2012.06.21_14:49:05_TAI",
      "T_STOP": "2012.07.18_19:38:00_TAI",
      "T_ROT": "2012.07.05_05:11:27_TAI",
      "CAR_ROT": 2125,
      "CARRTIME": 764820.0,
      "B0_ROT": 3.357861,
      "B0_FRST": 1.833407,
      "B0_LAST": 4.713255,
      "LON_FRST": 764640.2,
      "LON_LAST": 764999.7,
      "LON_STEP": -0.5,
      "W_OFFSET": 0.0,
      "W_WEIGHT": "Even",
      "IMG_NUM": 3312,
      "IMG_FRST": "2012.06.21_00:00:00_TAI",
      "IMG_LAST": "2012.07.19_00:00:00_TAI",
      "IMG_ROT": "2012.07.04_21:36:00_TAI",
      "HWNWIDTH": 15.0,
      "EQPOINTS": 20.0,
      "NSIGMA": 3.0,
      "CARSTRCH": 1,
      "DIFROT_A": 13.562,
      "DIFROT_B": -2.04,
      "DIFROT_C": -1.4875,
      "TOTVALS": 259200,
      "DATAVALS": 258193,
      "MISSVALS": 1007,
      "DATAMIN": -1946.302368,
      "DATAMAX": 2036.457031,
      "DATAMEDN": -0.019922,
      "DATAMEAN": -0.170903,
      "DATARMS": 40.831045,
      "DATASKEW": 6.326539,
      "DATAKURT": 571.749605,
      "CALVER64": 16,
      "QUALITY": 0,
      "CHECKSUM": "BTp4DTn3BTn3BTn3",
      "DATASUM": "3762048598",
      "HISTORY": "JSOC hmi.mrsynop_small_720s synopMr image; metadata retrieved from JSOC\nrecord."
    }
  ],
  "incomplete_rows": [
    [
      358,
      359
    ],
    [
      0,
      359
    ],
    [
      0,
      1
    ]
  ],
  "observation": {
    "saved_report": {
      "cr": 2124,
      "input_rotations": [
        2123,
        2124,
        2125
      ],
      "input_sha256": {
        "synoptic_reconstruction.py": "79c43e629c7e0f9ec93a3e4c974f74087c99c4759beb4a8ba4c9f0baf2e2cc6e",
        "prepare_viewer_data.py": "9394891f5af03c377b0c854cbbf1961625148bb9a0d558d78a1f8534fce10405",
        "validate_observations.py": "33b69ea18dd2770ca291c80931da856889d8bb85975fb64b83569e38f9fa0deb",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2123.fits": "7f066bfca1e7cb1d73a10bff065e3236a345ba5d03a9598b71910d753723a7ef",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2124.fits": "0dc4e82d61310750d6e13a7e94de05a08d1784f94b60356d417a4bf5a6f29494",
        "fits_files/720x360/hmi.Synoptic_Mr_small.2125.fits": "63a5b0cf01163e779ffd3dbf1ba67b05594fc79e70824f3fa19adac7a2d65ad8"
      },
      "reference": {
        "definition": "Observed HMI central meridian longitude 180 degrees, linearly interpolated between adjacent quality-zero 45-second records",
        "crossing_tai": "2012-06-08T00:30:10.874",
        "crossing_utc": "2012-06-08T00:29:36.874",
        "header_T_ROT_tai": "2012-06-08T00:26:50.000",
        "sunpy_earth_midrotation_tai": "2012-06-08T00:22:55.339",
        "sunpy_earth_midrotation_utc": "2012-06-08T00:22:21.339",
        "bracketing_records": [
          {
            "T_REC": "2012.06.08_00:30:00_TAI",
            "T_OBS": "2012.06.08_00:30:07_TAI",
            "CRLN_OBS_deg": 180.000595
          },
          {
            "T_REC": "2012.06.08_00:30:45_TAI",
            "T_OBS": "2012.06.08_00:30:52_TAI",
            "CRLN_OBS_deg": 179.993683
          }
        ]
      },
      "observation": {
        "series": "hmi.M_45s",
        "T_REC": "2012.06.08_00:30:00_TAI",
        "T_OBS": "2012.06.08_00:30:07_TAI",
        "T_OBS_utc": "2012-06-08T00:29:33.000",
        "offset_seconds": -3.8736979166934304,
        "QUALITY": "0x00000000",
        "CRLN_OBS_deg": 180.000595,
        "CRLT_OBS_deg": 0.21104,
        "source_url": "https://jsoc1.stanford.edu/SUM45/D332039889/S00016/magnetogram.fits",
        "file": "hmi.M_45s.20120608_003000_TAI.magnetogram.fits",
        "sha256": "48c68824c5860aaec41d31b7ddee3431b9b1c04a6bf2d1bb0bb835783ffcd087"
      },
      "method": {
        "mu_min": 0.8,
        "smoothing_sigma_detector_pixels": 3.0,
        "interpolation": "bilinear detector sampling; LOS divided by mu",
        "synoptic_longitude_step": "absolute FITS CDELT1, per SunPy HMI synoptic-map convention",
        "mask": "finite observation, original and both reconstructions; mu >= 0.8; finite smoothed observation neighborhood"
      },
      "scores": {
        "original": {
          "count": 25700,
          "bias_gauss": -0.07386621646472177,
          "mae_gauss": 14.82415463532096,
          "rmse_gauss": 43.17068507717338,
          "pearson_r": 0.6929857586079816
        },
        "ananya": {
          "count": 25700,
          "bias_gauss": 0.03964899189660525,
          "mae_gauss": 23.88800969765653,
          "rmse_gauss": 73.64183495375914,
          "pearson_r": 0.1500486879437364
        },
        "fixed": {
          "count": 25700,
          "bias_gauss": -0.0713310647702883,
          "mae_gauss": 15.011438816067022,
          "rmse_gauss": 43.281733496533434,
          "pearson_r": 0.6893568336811965
        }
      },
      "sensitivity_mu": {
        "0.8": {
          "original": {
            "count": 25700,
            "bias_gauss": -0.07386621646472177,
            "mae_gauss": 14.82415463532096,
            "rmse_gauss": 43.17068507717338,
            "pearson_r": 0.6929857586079816
          },
          "ananya": {
            "count": 25700,
            "bias_gauss": 0.03964899189660525,
            "mae_gauss": 23.88800969765653,
            "rmse_gauss": 73.64183495375914,
            "pearson_r": 0.1500486879437364
          },
          "fixed": {
            "count": 25700,
            "bias_gauss": -0.0713310647702883,
            "mae_gauss": 15.011438816067022,
            "rmse_gauss": 43.281733496533434,
            "pearson_r": 0.6893568336811965
          }
        },
        "0.9": {
          "original": {
            "count": 12844,
            "bias_gauss": -0.2911969161336496,
            "mae_gauss": 17.18950744763275,
            "rmse_gauss": 45.34582233389217,
            "pearson_r": 0.7723444416430391
          },
          "ananya": {
            "count": 12844,
            "bias_gauss": 2.2616742202787115,
            "mae_gauss": 27.991330779776945,
            "rmse_gauss": 76.82603887570126,
            "pearson_r": 0.25225341346689845
          },
          "fixed": {
            "count": 12844,
            "bias_gauss": -0.30118153181368884,
            "mae_gauss": 17.35548565648075,
            "rmse_gauss": 45.37762621610005,
            "pearson_r": 0.7703114312479041
          }
        },
        "0.95": {
          "original": {
            "count": 6415,
            "bias_gauss": 0.14853525109519253,
            "mae_gauss": 14.634988893909327,
            "rmse_gauss": 42.0193694623146,
            "pearson_r": 0.7366951631872931
          },
          "ananya": {
            "count": 6415,
            "bias_gauss": 3.2737693227944256,
            "mae_gauss": 26.182701285231612,
            "rmse_gauss": 67.85192719918896,
            "pearson_r": 0.33448145974365806
          },
          "fixed": {
            "count": 6415,
            "bias_gauss": 0.08484288301126418,
            "mae_gauss": 14.984462763197074,
            "rmse_gauss": 42.439820362709995,
            "pearson_r": 0.730016194640048
          }
        }
      },
      "diagnostics": {
        "original_vs_observation_same_mask": {
          "count": 25700,
          "bias_gauss": -0.07386621646472177,
          "mae_gauss": 14.82415463532096,
          "rmse_gauss": 43.17068507717338,
          "pearson_r": 0.6929857586079816
        },
        "registration_control": {
          "positive_orientation": {
            "count": 25700,
            "bias_gauss": -0.07386621646472177,
            "mae_gauss": 14.82415463532096,
            "rmse_gauss": 43.17068507717338,
            "pearson_r": 0.6929857586079816
          },
          "negative_header_orientation": {
            "count": 25700,
            "bias_gauss": -0.06761062869247461,
            "mae_gauss": 25.89156253784061,
            "rmse_gauss": 74.07640276320913,
            "pearson_r": 0.04881719466262143
          }
        },
        "header_CDELT1": -0.5
      }
    },
    "metadata": {
      "DATE": "2012-09-05T08:36:24Z",
      "DATE__OBS": "2012-06-08T00:29:11.00Z",
      "DATE-OBS": "2012-06-08T00:29:11.00Z",
      "TELESCOP": "SDO/HMI",
      "INSTRUME": "HMI_FRONT2",
      "WAVELNTH": "6173.0",
      "CAMERA": "2",
      "BUNIT": "Gauss",
      "ORIGIN": "SDO/JSOC-SDP",
      "CONTENT": "MAGNETOGRAM",
      "QUALITY": "0x00000000",
      "QUALLEV1": "0x00000000",
      "HISTORY": "Polynomial Coefficients used for Doppler velocity correction: 1.418253e+02 2.677605e-03 -9.208584e-07 2.268490e-10 \nCROTA2 corrected by adding -0.0702 degrees",
      "COMMENT": "De-rotation: ON; Un-distortion: ON; Re-centering: ON; Re-sizing: OFF; RSUNerr=0.5; correction for cosmic-ray hits; dpath=/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps/",
      "BLD_VERS": "603",
      "HCAMID": "3",
      "SOURCE": "hmi.lev1[:#39676847,#39676823,#39676799,#39676871,#39676895,#39676919,#39676849,#39676825,#39676801,#39676873,#39676897,#39676921,#39676851,#39676827,#39676803,#39676779,#39676875,#39676899,#39676853,#39676829,#39676805,#39676781,#39676877,#39676901,#39676855,#39676831,#39676807,#39676783,#39676879,#39676903,#39676857,#39676833,#39676809,#39676785,#39676881,#39676905,#39676859,#39676835,#39676811,#39676787,#39676883,#39676907,#39676861,#39676837,#39676813,#39676789,#39676885,#39676909,#39676863,#39676839,#39676815,#39676791,#39676887,#39676911,#39676865,#39676841,#39676817,#39676793,#39676889,#39676913,#39676867,#39676843,#39676819,#39676795,#39676891,#39676915,#39676869,#39676845,#39676821,#39676797,#39676893,#39676917]",
      "TOTVALS": "11639916",
      "DATAVALS": "11639916",
      "MISSVALS": "0",
      "SATVALS": "15845",
      "DATAMIN2": "-4441.819824",
      "DATAMAX2": "4441.819824",
      "DATAMED2": "0.001145",
      "DATAMEA2": "0.160702",
      "DATARMS2": "84.144791",
      "DATASKE2": "1.414660",
      "DATAKUR2": "810.019714",
      "DATAMIN": "-1534.594971",
      "DATAMAX": "1835.489136",
      "DATAMEDN": "0.009006",
      "DATAMEAN": "0.100659",
      "DATARMS": "44.382011",
      "DATASKEW": "2.143745",
      "DATAKURT": "255.066391",
      "CTYPE1": "HPLN-TAN",
      "CTYPE2": "HPLT-TAN",
      "CRPIX1": "2040.230835",
      "CRPIX2": "2049.619141",
      "CRVAL1": "0.000000",
      "CRVAL2": "0.000000",
      "CDELT1": "0.504285",
      "CDELT2": "0.504285",
      "CUNIT1": "arcsec",
      "CUNIT2": "arcsec",
      "CROTA2": "179.929779",
      "CRDER1": "MISSING",
      "CRDER2": "MISSING",
      "CSYSER1": "MISSING",
      "CSYSER2": "MISSING",
      "WCSNAME": "Helioprojective-cartesian",
      "DSUN_OBS": "151841510527.09",
      "DSUN_REF": "149597870691",
      "RSUN_REF": "696000000",
      "CRLN_OBS": "180.000595",
      "CRLT_OBS": "0.211040",
      "CAR_ROT": "2124",
      "OBS_VR": "2178.674592",
      "OBS_VW": "28324.056109",
      "OBS_VN": "5936.103439",
      "RSUN_OBS": "945.464844",
      "T_OBS": "2012.06.08_00:30:07_TAI",
      "T_REC": "2012.06.08_00:30:00_TAI",
      "T_REC_epoch": "1993.01.01_00:00:00_TAI",
      "T_REC_step": "45.0",
      "T_REC_unit": "secs",
      "CADENCE": "45.0",
      "DATASIGN": "1",
      "HFLID": "1021",
      "HCFTID": "11",
      "QLOOK": "0",
      "CAL_FSN": "32869398",
      "LUTQUERY": "hmi.lookup[32869398][][3][37][53][0][81]",
      "TSEL": "22.298309",
      "TFRONT": "30.624737",
      "TINTNUM": "6",
      "SINTNUM": "10",
      "DISTCOEF": "/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps//../libs/lev15/",
      "ROTCOEF": "/home/jsoc/cvs/Development/JSOC/proj/lev1.5_hmi/apps//../libs/lev15/",
      "ODICOEFF": "6",
      "OROCOEFF": "4",
      "POLCALM": "1",
      "CODEVER0": "$Id: HMI_observables.c,v 1.33 2012/04/10 22:18:30 couvidat Exp $",
      "CODEVER1": "$Id: interpol_code.c,v 1.2 2011/12/06 18:11:03 arta Exp $",
      "CODEVER2": "$Id: interpol_code.c,v 1.2 2011/12/06 18:11:03 arta Exp $",
      "CODEVER3": "$Id: polcal.c,v 1.4 2010/09/23 20:57:27 schou Exp $",
      "CALVER64": "0x0000000000000010"
    },
    "raw_fits_headers": [
      {
        "SIMPLE": true,
        "BITPIX": 16,
        "NAXIS": 0,
        "EXTEND": true,
        "COMMENT": "  FITS (Flexible Image Transport System) format is defined in 'Astronomy\n  and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H"
      },
      {
        "XTENSION": "IMAGE",
        "BITPIX": -64,
        "NAXIS": 2,
        "NAXIS1": 4096,
        "NAXIS2": 4096,
        "PCOUNT": 0,
        "GCOUNT": 1,
        "": ""
      }
    ],
    "image_sha256": "48c68824c5860aaec41d31b7ddee3431b9b1c04a6bf2d1bb0bb835783ffcd087",
    "metadata_sha256": "65cb6cd91627e786ac6cc4141ea8700330688a011b4cb353d2fe71c9c3aeb058",
    "independent_projection": {
      "common_count": 25700,
      "max_abs_mu_difference": 4.440892098500626e-16,
      "max_abs_Br_difference_G": 9.875150031035673e-07,
      "rmse_Br_difference_G": 7.401591244040148e-09,
      "same_finite_mask": true
    },
    "cache_check": {
      "same_finite_mask": true,
      "max_abs_observation_difference_G": 0.0
    },
    "timing": {
      "derived_crossing_utc": "2012-06-08T00:29:36.874",
      "stored_crossing_utc": "2012-06-08T00:29:36.874",
      "bracket_seconds": 44.99999999999744,
      "derived_CM_rate_deg_day": 13.271040000000385,
      "observation_minus_crossing_s": -3.8736979166934304,
      "observation_minus_header_T_ROT_s": 197.00000000000043,
      "brackets_are_saved_metadata_not_requeried": true
    }
  },
  "baseline_reproduction": {
    "000": {
      "existing_pipeline_same_finite_mask": true,
      "existing_pipeline_max_abs_difference_G": 0.0,
      "cached_map_max_abs_difference_G": 8.162714948412031e-11
    },
    "100": {
      "existing_pipeline_same_finite_mask": true,
      "existing_pipeline_max_abs_difference_G": 0.0,
      "cached_map_max_abs_difference_G": 1.0082601420435822e-11
    }
  },
  "literal_matches_vectorized": true,
  "chronology_midrotations": [
    {
      "cr": 2123,
      "midrotation_utc": "2012-05-11T19:20:19.337"
    },
    {
      "cr": 2124,
      "midrotation_utc": "2012-06-08T00:22:21.339"
    },
    {
      "cr": 2125,
      "midrotation_utc": "2012-07-05T05:07:02.894"
    }
  ],
  "chronology_within_rotation": [
    {
      "longitude_deg": 359.0,
      "utc": "2012-05-25T11:44:50.904"
    },
    {
      "longitude_deg": 180.0,
      "utc": "2012-06-08T00:22:21.339"
    },
    {
      "longitude_deg": 1.0,
      "utc": "2012-06-21T12:56:02.430"
    }
  ],
  "L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d": [
    180.13236804505226,
    180.00001031953394,
    179.86765257857678
  ],
  "primary_common_pixels": 25700,
  "full_map_common_pixels": 256180,
  "full_map_common_area_fraction": 0.9884278333333334,
  "primary_mask_same_as_prior": true,
  "exact_vs_first_order": {
    "max_query_difference_deg": 19.75838882300019,
    "full_common_field_difference": {
      "count": 255830,
      "bias_G": 0.005303338007657799,
      "mae_G": 3.1008331950330215,
      "rmse_G": 7.130493828190511,
      "pearson_r": 0.9816356644901967,
      "median_abs_G": 0.49538423190282427,
      "p95_abs_G": 14.201510158563092
    }
  }
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/evidence/jsoc_source_provenance.json (1,220 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/evidence/jsoc_source_provenance.json", "bytes": 1220, "sha256": "4f09e16705da446e43baa4ca04cb1426d3fe4ff3b967a32911c1eb945d504d60", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "commit": "0cf0b90d354705ed866fdba040772b0d712de785",
  "repository": "https://github.com/JSOC-SDP/proj",
  "files": [
    {
      "name": "brblossynoptic.c",
      "sha256": "1923350eccf4ff55c9bb98518273c304a5f02f745b333b0447810c56cf36fb9d",
      "url": "https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/brblossynoptic.c"
    },
    {
      "name": "hmisynoptic.c",
      "sha256": "d30474b4fc3f0b6d8b39a429174d8e3d3dc4bf745866a07c83ec45172132b168",
      "url": "https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/hmisynoptic.c"
    },
    {
      "name": "maprojbrfromblos.c",
      "sha256": "cd23d4eaa5b407bfd0ba59e37b7d70765bb43c85f8392bd9df092df5527553da",
      "url": "https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/maprojbrfromblos.c"
    },
    {
      "name": "mrmlossynoptic.c",
      "sha256": "b90195f071f413f130cf1e33495b2102cc7a797f46207eeef129bf972af06b53",
      "url": "https://raw.githubusercontent.com/JSOC-SDP/proj/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/mrmlossynoptic.c"
    }
  ]
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/evidence/raw_fits_checksums.json (59,835 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/evidence/raw_fits_checksums.json", "bytes": 59835, "sha256": "7f7b2b50abe568ca6070801ae31368e536aeedcc2b473067ed2728d687f837c5", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
[
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2096.fits",
    "cr": 2096,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gCUAj9T7gCTAg9T5",
    "DATASUM": "155638899",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2097.fits",
    "cr": 2097,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "QcAWQa7VQaAVQa5V",
    "DATASUM": "1249472741",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2098.fits",
    "cr": 2098,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gHBogGAogGAogGAo",
    "DATASUM": "2658019203",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2099.fits",
    "cr": 2099,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3ALMA3IL59ILA9IL",
    "DATASUM": "3392975650",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2100.fits",
    "cr": 2100,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "H8lIH7iIH7iIH7iI",
    "DATASUM": "3801861098",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2101.fits",
    "cr": 2101,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "egfMgdZLedfLedZL",
    "DATASUM": "807128218",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2102.fits",
    "cr": 2102,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "dFFfg9DZdCDfd9DZ",
    "DATASUM": "2827380370",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2103.fits",
    "cr": 2103,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Z8DMg6CMZ6CMd6CM",
    "DATASUM": "4068251558",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2104.fits",
    "cr": 2104,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZUL2hUJ2ZUJ2fUJ2",
    "DATASUM": "1635785358",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2105.fits",
    "cr": 2105,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "HcMeKcKbHcKbHcKb",
    "DATASUM": "1375799868",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2106.fits",
    "cr": 2106,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "55TA73S953SA53S9",
    "DATASUM": "153602910",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2107.fits",
    "cr": 2107,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "GJmaHJlXGJlaGJlU",
    "DATASUM": "2562878685",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2108.fits",
    "cr": 2108,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "TmabUlYZTlaaTlWY",
    "DATASUM": "4110775455",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2109.fits",
    "cr": 2109,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "SanHVZkHSakHSWkH",
    "DATASUM": "1991806943",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2110.fits",
    "cr": 2110,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "UFJHaC99WCGEaC99",
    "DATASUM": "2591871147",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2111.fits",
    "cr": 2111,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "XZcaYYZWXYaaXYYU",
    "DATASUM": "1424127406",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2112.fits",
    "cr": 2112,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9C6a9B3U9B3a9B3U",
    "DATASUM": "3581370953",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2113.fits",
    "cr": 2113,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "5XDi7WDf5WDf5WDf",
    "DATASUM": "2470792508",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2114.fits",
    "cr": 2114,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "BK8HDI7GBI7GBI7G",
    "DATASUM": "3094187535",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2115.fits",
    "cr": 2115,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "7eWKAcWI0cWI7cWI",
    "DATASUM": "1093583421",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2116.fits",
    "cr": 2116,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "OhQAOeP2OeP8OeP8",
    "DATASUM": "708695015",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2117.fits",
    "cr": 2117,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "GaEAHZE7GaEAGWE5",
    "DATASUM": "1248114182",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2118.fits",
    "cr": 2118,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "dJTgg9RddGRdd9Rd",
    "DATASUM": "3289719441",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2119.fits",
    "cr": 2119,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "8ZTE9XQC8XQC8XQC",
    "DATASUM": "4071628895",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2120.fits",
    "cr": 2120,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9ITYFIRV9IRVEIRV",
    "DATASUM": "802276192",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2121.fits",
    "cr": 2121,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "JaHRMUEOJZEOJZEO",
    "DATASUM": "3170228023",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2122.fits",
    "cr": 2122,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "BrTZBoQXBoQXBoQX",
    "DATASUM": "1790299224",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2123.fits",
    "cr": 2123,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "K4PXN3MWK3MWK3MW",
    "DATASUM": "2024852514",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2124.fits",
    "cr": 2124,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YWA1bU81ZUA1aU71",
    "DATASUM": "3591661808",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2125.fits",
    "cr": 2125,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "BTp4DTn3BTn3BTn3",
    "DATASUM": "3762048598",
    "audited_input": true
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2126.fits",
    "cr": 2126,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "hhnbkZkahfkahZka",
    "DATASUM": "2758705605",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2127.fits",
    "cr": 2127,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gXNCiWK9gWKAgWK9",
    "DATASUM": "3082951618",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2128.fits",
    "cr": 2128,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "5Im36Hl35Hl35Hl3",
    "DATASUM": "551875826",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2129.fits",
    "cr": 2129,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "oZ9ioY7goY7goY7g",
    "DATASUM": "2009936392",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2130.fits",
    "cr": 2130,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "B5S0C5R0B5R0B5R0",
    "DATASUM": "4031457731",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2131.fits",
    "cr": 2131,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "6AAS675Q6AAQ653Q",
    "DATASUM": "3418904533",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2132.fits",
    "cr": 2132,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "geaahcRVgcXagcXU",
    "DATASUM": "1430728965",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2133.fits",
    "cr": 2133,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZQPAaQO7UQOAZQO5",
    "DATASUM": "2321265444",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2134.fits",
    "cr": 2134,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YA7Aa67ASA7AY37A",
    "DATASUM": "4292983833",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2135.fits",
    "cr": 2135,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "F4caF2ZTF2aZF2YZ",
    "DATASUM": "673281693",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2136.fits",
    "cr": 2136,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "RAigT1ZZR8fdR8ZZ",
    "DATASUM": "249841006",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2137.fits",
    "cr": 2137,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "AIdNC9ZLAGbLA9ZL",
    "DATASUM": "3325470399",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2138.fits",
    "cr": 2138,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "iGSZj9RWiERWi9RW",
    "DATASUM": "3516418411",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2139.fits",
    "cr": 2139,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZgGdag9dTgGdZg9d",
    "DATASUM": "854256831",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2140.fits",
    "cr": 2140,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "MNZaNMXYMMXaMMXW",
    "DATASUM": "3028815634",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2141.fits",
    "cr": 2141,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "e8aAe5X8e5aAe5W5",
    "DATASUM": "3003324516",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2142.fits",
    "cr": 2142,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "WdAhWa4gWaAgWa3g",
    "DATASUM": "4187052920",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2143.fits",
    "cr": 2143,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "bKEmbJ9jbJEjbJ9j",
    "DATASUM": "1250967111",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2144.fits",
    "cr": 2144,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3EgG3DgG3DgG3DgG",
    "DATASUM": "1829034489",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2145.fits",
    "cr": 2145,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "6SYA7QY46QYA6QY3",
    "DATASUM": "1380121338",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2146.fits",
    "cr": 2146,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "UahdaZfaXafaaWfa",
    "DATASUM": "2677459249",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2147.fits",
    "cr": 2147,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "k8UAm8U1k8U8k8U8",
    "DATASUM": "1172019694",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2148.fits",
    "cr": 2148,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "PX3APW15PW1APW13",
    "DATASUM": "3613229394",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2149.fits",
    "cr": 2149,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "eGbJhEZ9eEbGeEZ9",
    "DATASUM": "747062032",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2150.fits",
    "cr": 2150,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3cY56ZX33aX33YX3",
    "DATASUM": "2492898268",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2151.fits",
    "cr": 2151,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "dd3QfZ1Odd1OdZ1O",
    "DATASUM": "2320453672",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2152.fits",
    "cr": 2152,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "OUARPR5RORAROR3R",
    "DATASUM": "785896691",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2153.fits",
    "cr": 2153,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9SZaDSWW9SWaCSWU",
    "DATASUM": "694135630",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2154.fits",
    "cr": 2154,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "5ADe55Bd5ABd55Bd",
    "DATASUM": "1975882582",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2155.fits",
    "cr": 2155,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "JSH6LRE4JRE4JRE4",
    "DATASUM": "315645953",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2156.fits",
    "cr": 2156,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "PB9bS96aPA6aP76a",
    "DATASUM": "1426498783",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2157.fits",
    "cr": 2157,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9bM9DZM69bM6CZM6",
    "DATASUM": "4221667120",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2158.fits",
    "cr": 2158,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "G8eeI6cbG6cbG6cb",
    "DATASUM": "2622134793",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2159.fits",
    "cr": 2159,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "eeElgZEkebEkeZEk",
    "DATASUM": "3955379604",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2160.fits",
    "cr": 2160,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZfihgdhZZdhfddhZ",
    "DATASUM": "3997402546",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2161.fits",
    "cr": 2161,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "8fAe9Z5b8dAb8Z3b",
    "DATASUM": "4090400314",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2162.fits",
    "cr": 2162,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Coc3Doc2Coc2Coc2",
    "DATASUM": "3089438729",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2163.fits",
    "cr": 2163,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "WkaCWiW9WiaCWiU9",
    "DATASUM": "3024303065",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2164.fits",
    "cr": 2164,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gAiDg6fCgAfCg5fC",
    "DATASUM": "1712923289",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2165.fits",
    "cr": 2165,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZAFii39ZZACff39Z",
    "DATASUM": "2244721576",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2166.fits",
    "cr": 2166,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZA9ad56YZA6ad36Y",
    "DATASUM": "1558551750",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2167.fits",
    "cr": 2167,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "AeSECeQEAeQEAeQE",
    "DATASUM": "41752119",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2168.fits",
    "cr": 2168,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9iCaFgCZ9gCaEgCW",
    "DATASUM": "3939089495",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2169.fits",
    "cr": 2169,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Ae8fCZ6ZAb6fAZ6Z",
    "DATASUM": "4228037175",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2170.fits",
    "cr": 2170,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "faiMfVfMfafMfUfM",
    "DATASUM": "193660069",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2171.fits",
    "cr": 2171,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ajY4djX1ajX1ajX1",
    "DATASUM": "3279051132",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2172.fits",
    "cr": 2172,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "95JiA3Hh23Hh93Hh",
    "DATASUM": "2897631031",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2173.fits",
    "cr": 2173,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Y9Feb7DZZ7Dda7DZ",
    "DATASUM": "3118563966",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2174.fits",
    "cr": 2174,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3LDF3K993KAE3K99",
    "DATASUM": "1577312108",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2175.fits",
    "cr": 2175,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "53aZ50VX50aX50UX",
    "DATASUM": "2790505297",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2176.fits",
    "cr": 2176,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "PoAqRn4nPnAnPn3n",
    "DATASUM": "2899055847",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2177.fits",
    "cr": 2177,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "NXOVPXNSNXNSNXNS",
    "DATASUM": "4251108589",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2178.fits",
    "cr": 2178,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "DA51G150D850D850",
    "DATASUM": "1742965534",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2179.fits",
    "cr": 2179,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9ofaDmfR9mfXAmfX",
    "DATASUM": "2550255656",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2180.fits",
    "cr": 2180,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YXnSaVmPYVmPaVmP",
    "DATASUM": "114225597",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2181.fits",
    "cr": 2181,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "kYiMkXiMkXiMkXiM",
    "DATASUM": "4075419781",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2182.fits",
    "cr": 2182,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "NV8JNV8INV8INV8I",
    "DATASUM": "478515211",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2183.fits",
    "cr": 2183,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "IAdgJ1ZdI8bdI8Zd",
    "DATASUM": "2472205841",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2184.fits",
    "cr": 2184,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "5EF7A9967EE6A996",
    "DATASUM": "1121869326",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2185.fits",
    "cr": 2185,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3nTa5nTT3nTY3nTY",
    "DATASUM": "3415065170",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2186.fits",
    "cr": 2186,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3OcZAMcY4McYAMcY",
    "DATASUM": "842893080",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2187.fits",
    "cr": 2187,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "7af6BUe69Ze6AZe6",
    "DATASUM": "3761451528",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2188.fits",
    "cr": 2188,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "D7aAF6T0D6Z7D6Z7",
    "DATASUM": "1666257388",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2189.fits",
    "cr": 2189,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "0EMl3ELl0ELl0ELl",
    "DATASUM": "1048130414",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2190.fits",
    "cr": 2190,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "MhANNf7LMfALMf7L",
    "DATASUM": "3319318753",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2191.fits",
    "cr": 2191,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZDlegAlZZAldfAlZ",
    "DATASUM": "705607601",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2192.fits",
    "cr": 2192,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "MZaIOZXFMZaFMZUF",
    "DATASUM": "3443262461",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2193.fits",
    "cr": 2193,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZXdCfUdAZUdAfUdA",
    "DATASUM": "36385462",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2194.fits",
    "cr": 2194,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "kTMWlRKUkRKUkRKU",
    "DATASUM": "4245132099",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2195.fits",
    "cr": 2195,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "kI8JlI8HkI8HkI8H",
    "DATASUM": "1081720097",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2196.fits",
    "cr": 2196,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZfMkgeMkZeMkfeMk",
    "DATASUM": "3814080326",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2197.fits",
    "cr": 2197,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "mVBfpUBcmUBcmUBc",
    "DATASUM": "863985175",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2198.fits",
    "cr": 2198,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "GdABIZ0AGd7AGZ7A",
    "DATASUM": "897511854",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2199.fits",
    "cr": 2199,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "1l813k701k701k70",
    "DATASUM": "3901354748",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2200.fits",
    "cr": 2200,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "06eM05dJ05dJ05dJ",
    "DATASUM": "2646503439",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2201.fits",
    "cr": 2201,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "C3gJE1eHC1eHC1eH",
    "DATASUM": "336241859",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2202.fits",
    "cr": 2202,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "IaTIJVSIIZSIIZSI",
    "DATASUM": "1379115168",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2203.fits",
    "cr": 2203,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Daa8FZY7Daa7DYW7",
    "DATASUM": "921226168",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2204.fits",
    "cr": 2204,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "2Ki62Hi52Hi52Hi5",
    "DATASUM": "2008935691",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2205.fits",
    "cr": 2205,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "KIUqLGToKGToKGTo",
    "DATASUM": "1138568613",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2206.fits",
    "cr": 2206,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZfVfcZUeZdUebZUe",
    "DATASUM": "554251096",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2207.fits",
    "cr": 2207,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "aDOAc9O5aCOAa9O5",
    "DATASUM": "2333944658",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2208.fits",
    "cr": 2208,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "FgaaIfSUFfYaFfYU",
    "DATASUM": "4191590591",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2209.fits",
    "cr": 2209,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "1DA81C371C971C97",
    "DATASUM": "1973623798",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2210.fits",
    "cr": 2210,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "akFNbhCNahCNahCN",
    "DATASUM": "2978664836",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2211.fits",
    "cr": 2211,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "6aGa7VDT6ZDY6ZDY",
    "DATASUM": "862479857",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2212.fits",
    "cr": 2212,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "EK6NGH5KEH5KEH5K",
    "DATASUM": "2442963902",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2213.fits",
    "cr": 2213,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "hbgZhZfWhbfWhZfW",
    "DATASUM": "618815756",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2214.fits",
    "cr": 2214,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9g3bAd2b4d2b9d2b",
    "DATASUM": "399117291",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2215.fits",
    "cr": 2215,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZGiOfEZNZEfNdEZN",
    "DATASUM": "1711965003",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2216.fits",
    "cr": 2216,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "7gAh8d2Z7d8f7d8Z",
    "DATASUM": "3598456527",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2217.fits",
    "cr": 2217,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "BVloCUimBUimBUim",
    "DATASUM": "564125089",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2218.fits",
    "cr": 2218,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "LIMTLFJQLFJQLFJQ",
    "DATASUM": "1362078653",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2219.fits",
    "cr": 2219,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "19lP18lP18lP18lP",
    "DATASUM": "2476578100",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2220.fits",
    "cr": 2220,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "HJDdKI9cHIAcHI9c",
    "DATASUM": "1115764188",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2221.fits",
    "cr": 2221,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZSUHeRT9ZRTGdRT9",
    "DATASUM": "1006225280",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2222.fits",
    "cr": 2222,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "WDfDa9f9ZAfCa9f9",
    "DATASUM": "2146423952",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2223.fits",
    "cr": 2223,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "RiGaTfFWRfFaRfFU",
    "DATASUM": "3951531205",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2224.fits",
    "cr": 2224,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "kqUhmnUhknUhknUh",
    "DATASUM": "4216861790",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2225.fits",
    "cr": 2225,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "86ga95ZS85dY85ZY",
    "DATASUM": "3975443981",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2226.fits",
    "cr": 2226,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "0A4o174o0A4o074o",
    "DATASUM": "3048676381",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2227.fits",
    "cr": 2227,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "DnlAEnk4Dnk9Dnk9",
    "DATASUM": "4007928289",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2228.fits",
    "cr": 2228,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "4cHJ6Z994bGG4Z99",
    "DATASUM": "1149108271",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2229.fits",
    "cr": 2229,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "iaXAlWWAiaWAiUWA",
    "DATASUM": "1142090838",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2230.fits",
    "cr": 2230,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "RMijSJigRJigRJig",
    "DATASUM": "1641111483",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2231.fits",
    "cr": 2231,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "mCi3oAZ2mAf2mAZ2",
    "DATASUM": "2212441913",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2232.fits",
    "cr": 2232,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "nLfaoIfUnIfanIfU",
    "DATASUM": "1740301916",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2233.fits",
    "cr": 2233,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Wo9YXl7YWl7YWl7Y",
    "DATASUM": "2404693677",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2234.fits",
    "cr": 2234,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "JFeLMDdJJDdJJDdJ",
    "DATASUM": "2127370505",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2235.fits",
    "cr": 2235,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "hXnAjWk6hWkAhWk3",
    "DATASUM": "986993739",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2236.fits",
    "cr": 2236,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "5X7jAX6h8X6hAX6h",
    "DATASUM": "4167980547",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2237.fits",
    "cr": 2237,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "lTbalRbXlRbalRbW",
    "DATASUM": "384350523",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2238.fits",
    "cr": 2238,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "nmDjnj9hnjAhnj9h",
    "DATASUM": "3445576226",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2239.fits",
    "cr": 2239,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "CBPaC9PTCAPZC7PZ",
    "DATASUM": "1762418375",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2240.fits",
    "cr": 2240,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YAmOa4jOZAjOa3jO",
    "DATASUM": "2968546734",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2241.fits",
    "cr": 2241,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9466C4359435A435",
    "DATASUM": "3419460645",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2242.fits",
    "cr": 2242,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "njj4pih4nih4nih4",
    "DATASUM": "117366368",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2243.fits",
    "cr": 2243,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "CGaJEGVHCGaHCGUH",
    "DATASUM": "1982695955",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2244.fits",
    "cr": 2244,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YafoZWZmYafmYUZm",
    "DATASUM": "891353517",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2245.fits",
    "cr": 2245,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "dZpQgWnOdWnOdWnO",
    "DATASUM": "1054569104",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2246.fits",
    "cr": 2246,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "FXZnIXYmFXYmFXYm",
    "DATASUM": "1144910851",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2247.fits",
    "cr": 2247,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "TCKTWBITTBITTBIT",
    "DATASUM": "2389791682",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2248.fits",
    "cr": 2248,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "mRhhpQefmQefmQef",
    "DATASUM": "1443044199",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2249.fits",
    "cr": 2249,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9cKmHZIm9bImGZIm",
    "DATASUM": "779417890",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2250.fits",
    "cr": 2250,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "c3HNe1EMc1EMc1EM",
    "DATASUM": "3582491541",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2251.fits",
    "cr": 2251,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "fJYkgGXjfGXjfGXj",
    "DATASUM": "1999766407",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2252.fits",
    "cr": 2252,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "OfDbPe9aOeCaOe9a",
    "DATASUM": "380252901",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2253.fits",
    "cr": 2253,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "MjYWPgXWMgXWMgXW",
    "DATASUM": "205999081",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2254.fits",
    "cr": 2254,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9kFKCj9K9jCKAj9K",
    "DATASUM": "4170746395",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2255.fits",
    "cr": 2255,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "8alj8Zji8aji8Yji",
    "DATASUM": "905579057",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2256.fits",
    "cr": 2256,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "BdgoDcelBcelBcel",
    "DATASUM": "554630423",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2257.fits",
    "cr": 2257,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "oddeqdbZodbbodbZ",
    "DATASUM": "270219104",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2258.fits",
    "cr": 2258,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "BWc3CWZ1BWb1BWZ1",
    "DATASUM": "3721368543",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2259.fits",
    "cr": 2259,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "iABIi299i9AGi999",
    "DATASUM": "1464950081",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2260.fits",
    "cr": 2260,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "WpllZmklWmklWmkl",
    "DATASUM": "2208410247",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2261.fits",
    "cr": 2261,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZFRdZ9QZZCQdZ9QZ",
    "DATASUM": "1107876468",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2262.fits",
    "cr": 2262,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "5e3D5Z1B5d1B5Z1B",
    "DATASUM": "3296222228",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2263.fits",
    "cr": 2263,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3AAa5A5U3AAa3A3U",
    "DATASUM": "1012725268",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2264.fits",
    "cr": 2264,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "cfagdZVZcdZfcZZZ",
    "DATASUM": "3303006306",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2265.fits",
    "cr": 2265,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "GaAJHTA9GZAGGZA9",
    "DATASUM": "3577434825",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2266.fits",
    "cr": 2266,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "kELjl9JikEJik9Ji",
    "DATASUM": "1158788660",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2267.fits",
    "cr": 2267,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "FFCDHFB9FFBCFFB9",
    "DATASUM": "859204803",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2268.fits",
    "cr": 2268,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "JZINLWFKJWFKJWFK",
    "DATASUM": "3592891567",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2269.fits",
    "cr": 2269,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Z41Gi20GZ20Gf20G",
    "DATASUM": "1954301281",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2270.fits",
    "cr": 2270,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "0HKM3HHM0HHM0HHM",
    "DATASUM": "572795923",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2271.fits",
    "cr": 2271,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZrDphoAoZoAofoAo",
    "DATASUM": "1933353315",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2272.fits",
    "cr": 2272,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gaa9jTY9gZa9gZY9",
    "DATASUM": "3485627206",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2273.fits",
    "cr": 2273,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "daGegTFedZFedZFe",
    "DATASUM": "3509434703",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2274.fits",
    "cr": 2274,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9WIdFT9c9TGcET9c",
    "DATASUM": "4080325596",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2275.fits",
    "cr": 2275,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YbeCcbd9ZbdCabd9",
    "DATASUM": "3064556139",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2276.fits",
    "cr": 2276,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "h1UIi1UFh1UFh1UF",
    "DATASUM": "1978087995",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2277.fits",
    "cr": 2277,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "DaWdDZUaDaUaDWUa",
    "DATASUM": "3337671636",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2278.fits",
    "cr": 2278,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9We0HWb09Wb0EWb0",
    "DATASUM": "3685851107",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2279.fits",
    "cr": 2279,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZbHFdZGDZaGDdYGD",
    "DATASUM": "3289989976",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2280.fits",
    "cr": 2280,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "G9fSG9ZQG9dQG9ZQ",
    "DATASUM": "1405555407",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2281.fits",
    "cr": 2281,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "YLRAaJQ6ZJQAaJQ3",
    "DATASUM": "570650221",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2282.fits",
    "cr": 2282,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9VkA9Vh69VhA9Vh5",
    "DATASUM": "3801904125",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2283.fits",
    "cr": 2283,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9MIABJG49JGAAJG3",
    "DATASUM": "472804081",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2284.fits",
    "cr": 2284,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "U8Faa5ERX5EXa5EX",
    "DATASUM": "1579481205",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2285.fits",
    "cr": 2285,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "LaXZOTXWLYXWLYXW",
    "DATASUM": "3553949612",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2286.fits",
    "cr": 2286,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZH1aeH0WZH0abH0W",
    "DATASUM": "3827527385",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2287.fits",
    "cr": 2287,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "NDN3P9N2NCN2N9N2",
    "DATASUM": "462429738",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2288.fits",
    "cr": 2288,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "N3g6P0e5N0e5N0e5",
    "DATASUM": "1766201114",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2289.fits",
    "cr": 2289,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "oKTApHT7oHTAoHT5",
    "DATASUM": "4103402905",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2290.fits",
    "cr": 2290,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "S3ADV26DS2ADS23D",
    "DATASUM": "1361434870",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2291.fits",
    "cr": 2291,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "bQeUdPZRbPdRbPZR",
    "DATASUM": "4037191371",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2292.fits",
    "cr": 2292,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "HcnhJZkfHbkfHZkf",
    "DATASUM": "2769115160",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2293.fits",
    "cr": 2293,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "MdiYMdgYMdgYMdgY",
    "DATASUM": "1598452499",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2294.fits",
    "cr": 2294,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9RVAGRT49RT9ERT9",
    "DATASUM": "3549819214",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2295.fits",
    "cr": 2295,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gBg5i9e4gAe4g7e4",
    "DATASUM": "811993761",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2296.fits",
    "cr": 2296,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "9AJVA1GS98GSA8GS",
    "DATASUM": "951806297",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2297.fits",
    "cr": 2297,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "gCd9hCZ8gCd8gCZ8",
    "DATASUM": "4196869503",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2298.fits",
    "cr": 2298,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "bAfpd4dobAdob3do",
    "DATASUM": "789988538",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2299.fits",
    "cr": 2299,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "F5AfH40fF47fF47f",
    "DATASUM": "820207907",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2300.fits",
    "cr": 2300,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "jiQMmhPMjhPMjhPM",
    "DATASUM": "1905504634",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2301.fits",
    "cr": 2301,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "ZXjPdWjNZWjNdWjN",
    "DATASUM": "3376515015",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2302.fits",
    "cr": 2302,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "hANYh6MVhAMVh3MV",
    "DATASUM": "332822700",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2303.fits",
    "cr": 2303,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3FdAADc84DcAADc5",
    "DATASUM": "3615679328",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2304.fits",
    "cr": 2304,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "7r5Q7o2O7o2O7o2O",
    "DATASUM": "1360895841",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2305.fits",
    "cr": 2305,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "LjXeLhVcLhVcLhVc",
    "DATASUM": "1904833807",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2306.fits",
    "cr": 2306,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "VDYAXDW2VDW9VDW9",
    "DATASUM": "7472372",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2307.fits",
    "cr": 2307,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "1SoA1Ql51QlA1Ql5",
    "DATASUM": "3977832824",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2308.fits",
    "cr": 2308,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "QeV1RZT0QdT0QZT0",
    "DATASUM": "3581028354",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2309.fits",
    "cr": 2309,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "VkA6Vk55VkA5Vk35",
    "DATASUM": "2194989313",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2310.fits",
    "cr": 2310,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "3Lg1AIZ06If0AIZ0",
    "DATASUM": "3494118226",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2311.fits",
    "cr": 2311,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "XfonYZlnXflnXZln",
    "DATASUM": "3004116690",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2312.fits",
    "cr": 2312,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "Nh4iQh2fNh2fNh2f",
    "DATASUM": "1962750976",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2313.fits",
    "cr": 2313,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "QkL5TkL4QkL4QkL4",
    "DATASUM": "1336348420",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2314.fits",
    "cr": 2314,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "8fgSAZdR1ddR8ZdR",
    "DATASUM": "2337382754",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2315.fits",
    "cr": 2315,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "mSphpQogmQogmQog",
    "DATASUM": "3457488517",
    "audited_input": false
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2316.fits",
    "cr": 2316,
    "raw_file_checksum_hex": "0xffffffff",
    "raw_checksum_valid": true,
    "CHECKSUM": "QI35TF04QF04QF04",
    "DATASUM": "3795392491",
    "audited_input": false
  }
]

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/evidence/synthetic_diagnostics.json (1,195 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/evidence/synthetic_diagnostics.json", "bytes": 1195, "sha256": "a79c68abf229db3968f469fa30406b2f59e240d3414035a9e87f176e0d54464d", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
[
  {
    "case": "smooth_rotation",
    "common_pixels": 129508,
    "first_order_vs_exact_max_shift_deg": 19.360400152992497,
    "first_order_vs_exact_field_rmse_G": 0.6597353130780248
  },
  {
    "case": "seam_features",
    "common_pixels": 129508,
    "first_order_vs_exact_max_shift_deg": 19.360400152992497,
    "first_order_vs_exact_field_rmse_G": 2.0661568463370292
  },
  {
    "case": "missing_data",
    "common_pixels": 128074,
    "first_order_vs_exact_max_shift_deg": 19.360400152992497,
    "first_order_vs_exact_field_rmse_G": 2.0776895299138487
  },
  {
    "case": "stationary_control",
    "common_pixels": 129508,
    "first_order_vs_exact_max_shift_deg": 19.360400152992497,
    "first_order_vs_exact_field_rmse_G": 0.7841796467145534
  },
  {
    "case": "opposite_rotation_control",
    "common_pixels": 129508,
    "first_order_vs_exact_max_shift_deg": 19.360400152992497,
    "first_order_vs_exact_field_rmse_G": 0.9114390050012142
  },
  {
    "case": "evolving_control",
    "common_pixels": 129508,
    "first_order_vs_exact_max_shift_deg": 19.360400152992497,
    "first_order_vs_exact_field_rmse_G": 2.067202984897254
  }
]

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/execution.json (2,479 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/execution.json", "bytes": 2479, "sha256": "95bb7de43d58560d8fe005dea046322525bcd9e99df0679abc19d51c52105be2", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
[
  {
    "stage": "calculations",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "D:\\post engg\\fluXcape\\pre_sft_audit\\run_audit.py"
    ],
    "returncode": 0,
    "elapsed_seconds": 129.51600000000326
  },
  {
    "stage": "raw_checksums",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "D:\\post engg\\fluXcape\\pre_sft_audit\\check_fits.py"
    ],
    "returncode": 0,
    "elapsed_seconds": 4.686999999998079
  },
  {
    "stage": "existing_tests",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "-m",
      "unittest",
      "discover",
      "-s",
      "D:\\post engg\\fluXcape\\SFT",
      "-p",
      "test_coordinate_registration.py",
      "-v"
    ],
    "returncode": 0,
    "elapsed_seconds": 3.25
  },
  {
    "stage": "tests",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "-m",
      "unittest",
      "discover",
      "-s",
      "D:\\post engg\\fluXcape\\pre_sft_audit",
      "-p",
      "test_audit.py",
      "-v"
    ],
    "returncode": 0,
    "elapsed_seconds": 6.360000000000582
  },
  {
    "stage": "preservation",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "D:\\post engg\\fluXcape\\pre_sft_audit\\inventory.py",
      "--verify"
    ],
    "returncode": 0,
    "elapsed_seconds": 1.2180000000007567
  },
  {
    "stage": "discrepancies",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "D:\\post engg\\fluXcape\\pre_sft_audit\\investigate_discrepancies.py"
    ],
    "returncode": 0,
    "elapsed_seconds": 86.6710000000021
  },
  {
    "stage": "tests",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "-m",
      "unittest",
      "discover",
      "-s",
      "D:\\post engg\\fluXcape\\pre_sft_audit",
      "-p",
      "test_audit.py",
      "-v"
    ],
    "returncode": 0,
    "elapsed_seconds": 6.875
  },
  {
    "stage": "preservation",
    "command": [
      "D:\\post engg\\fluXcape\\.venv\\Scripts\\python.exe",
      "-B",
      "D:\\post engg\\fluXcape\\pre_sft_audit\\inventory.py",
      "--verify"
    ],
    "returncode": 0,
    "elapsed_seconds": 1.3289999999979045
  }
]

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/original_manifest.json (65,547 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/original_manifest.json", "bytes": 65547, "sha256": "988125c0cc5e093b1539fa97bbbb7499d3235e482143e64d13dace8964f49762", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
[
  {
    "path": ".gitignore",
    "bytes": 30,
    "sha256": "061830dec9ff45907398d094d179f71c9fbc1838a30f0f869b43dccb98a87d7d"
  },
  {
    "path": "Solar Physics - Research Topics.md",
    "bytes": 10017,
    "sha256": "25e311035a6167fff599d698e4279b00f42c4bc50e7674da1558a0759c1237cc",
    "lines": 103
  },
  {
    "path": "layers of the sun.md",
    "bytes": 2255,
    "sha256": "0b35dfcec146559031019fd2510d824b4db9309e71a22c4ba8a0341eb11d4a81",
    "lines": 7
  },
  {
    "path": "pre_sft_correction_audit.md",
    "bytes": 8513,
    "sha256": "b9bea71e66d1d32fe658e6d8dd87e1b4d19f29de58fcaf26de8cf3380f26f15f",
    "lines": 62
  },
  {
    "path": "research-question.md",
    "bytes": 2952,
    "sha256": "fb8010a66de993ff24e7e7fc9507d57e2a1b353234725357df34530ddf200aeb",
    "lines": 27
  },
  {
    "path": "SFT/download_synoptic_maps.py",
    "bytes": 5895,
    "sha256": "4060593eb8148455576b3f160837e7a4602a0976708d650cf7ad8f3d82ada9cc",
    "lines": 144,
    "functions": [
      {
        "name": "query",
        "line": 23
      },
      {
        "name": "archive_records",
        "line": 32
      },
      {
        "name": "make_header",
        "line": 46
      },
      {
        "name": "download_map",
        "line": 67
      },
      {
        "name": "main",
        "line": 90
      }
    ],
    "imports": [
      "from astropy.io import fits",
      "from pathlib import Path",
      "from urllib.parse import urlencode",
      "from urllib.request import urlopen",
      "import json",
      "import math",
      "import re",
      "import sys",
      "import warnings"
    ]
  },
  {
    "path": "SFT/observational_validation.md",
    "bytes": 8612,
    "sha256": "09885a52e0ab25e149022d2065870ed8a6f8a59434a6ac9684e3dee968b84bef",
    "lines": 148
  },
  {
    "path": "SFT/pre-sft comparision.md",
    "bytes": 3374,
    "sha256": "b1864152dff99a5f0795df5e0c7438457d0d409836ac467b0afc48e9fe0a3db6",
    "lines": 70
  },
  {
    "path": "SFT/prepare_viewer_data.py",
    "bytes": 3114,
    "sha256": "480d978bf35587f3c12bdf90b2c9240fa545c9a89204b53b70e0f03f96766da2",
    "lines": 65,
    "functions": [
      {
        "name": "reconstruct",
        "line": 17
      },
      {
        "name": "encode",
        "line": 22
      },
      {
        "name": "package_result",
        "line": 26
      }
    ],
    "imports": [
      "from pathlib import Path",
      "from synoptic_reconstruction import ROTATIONS, load_maps, calculate_coordinates, calculate_delta_t, calculate_rotation_rate, calculate_ananya_rotation_rate, calculate_phi_prime, select_source_map, interpolate_field",
      "import base64",
      "import hashlib",
      "import json",
      "import numpy as np"
    ]
  },
  {
    "path": "SFT/requirements.txt",
    "bytes": 49,
    "sha256": "baf39d01ad0803db7ad2d531bfe1e757c3990f0e3226680eebd71f8dc623fa16",
    "lines": 4
  },
  {
    "path": "SFT/steps.md",
    "bytes": 4460,
    "sha256": "fcfa5b2a0014e25357bdb75df7c4a4aa6ab8fbc640bdff38f3caf529daeb044b",
    "lines": 71
  },
  {
    "path": "SFT/synoptic_reconstruction.py",
    "bytes": 8647,
    "sha256": "2727847b94bf293a25afb773d7454d8370d997adef56446bbcead44c617304cb",
    "lines": 183,
    "functions": [
      {
        "name": "sunalyse_colormap",
        "line": 13
      },
      {
        "name": "load_maps",
        "line": 39
      },
      {
        "name": "calculate_coordinates",
        "line": 46
      },
      {
        "name": "calculate_delta_t",
        "line": 61
      },
      {
        "name": "calculate_rotation_rate",
        "line": 66
      },
      {
        "name": "calculate_ananya_rotation_rate",
        "line": 72
      },
      {
        "name": "calculate_phi_prime",
        "line": 78
      },
      {
        "name": "select_source_map",
        "line": 83
      },
      {
        "name": "interpolate_field",
        "line": 89
      },
      {
        "name": "plot_maps",
        "line": 110
      },
      {
        "name": "plot_reconstruction",
        "line": 128
      },
      {
        "name": "animate",
        "line": 164
      }
    ],
    "imports": [
      "from astropy.io import fits",
      "from matplotlib.animation import FuncAnimation",
      "from matplotlib.colors import ListedColormap, Normalize",
      "from pathlib import Path",
      "from scipy.interpolate import RectBivariateSpline",
      "import matplotlib.pyplot as plt",
      "import numpy as np"
    ]
  },
  {
    "path": "SFT/test_coordinate_registration.py",
    "bytes": 1749,
    "sha256": "5b93ef8b4006e8fcac852e453dcbbb85ff44e3ddecd995482bd889ea1da50baf",
    "lines": 38,
    "functions": [
      {
        "name": "setUp",
        "line": 11
      },
      {
        "name": "test_hmi_negative_header_maps_to_increasing_physical_longitude",
        "line": 16
      },
      {
        "name": "test_original_sample_positions_reproduce_input",
        "line": 20
      },
      {
        "name": "test_rotation_boundary_chooses_and_samples_correct_map",
        "line": 28
      }
    ],
    "imports": [
      "from synoptic_reconstruction import calculate_coordinates, interpolate_field, select_source_map",
      "import numpy as np",
      "import unittest"
    ]
  },
  {
    "path": "SFT/validate_observations.py",
    "bytes": 15482,
    "sha256": "31d6f80873d919739b50d463e4708fb47e915a1916664b85282b0a0aeb260a5d",
    "lines": 272,
    "functions": [
      {
        "name": "query",
        "line": 38
      },
      {
        "name": "parse_tai",
        "line": 46
      },
      {
        "name": "record_values",
        "line": 54
      },
      {
        "name": "reference_and_record",
        "line": 58
      },
      {
        "name": "observation",
        "line": 82
      },
      {
        "name": "project_observation",
        "line": 113
      },
      {
        "name": "reconstruction",
        "line": 173
      },
      {
        "name": "metrics",
        "line": 179
      },
      {
        "name": "input_fingerprints",
        "line": 187
      },
      {
        "name": "main",
        "line": 196
      }
    ],
    "imports": [
      "from __future__ import annotations",
      "from astropy.coordinates import SkyCoord",
      "from astropy.io import fits",
      "from astropy.time import Time",
      "from astropy.wcs import WCS",
      "from pathlib import Path",
      "from scipy.ndimage import gaussian_filter, map_coordinates",
      "from sunpy.coordinates.frames import HeliographicCarrington, HeliographicStonyhurst, Helioprojective",
      "from sunpy.coordinates.sun import carrington_rotation_time",
      "from synoptic_reconstruction import ROTATIONS, load_maps, calculate_coordinates, calculate_delta_t, calculate_rotation_rate, calculate_ananya_rotation_rate, calculate_phi_prime, select_source_map, interpolate_field",
      "from urllib.parse import urlencode",
      "from urllib.request import urlopen, urlretrieve",
      "import argparse",
      "import astropy.units as u",
      "import hashlib",
      "import json",
      "import matplotlib.pyplot as plt",
      "import numpy as np"
    ]
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2096.fits",
    "bytes": 1045440,
    "sha256": "ac62ec2884c7fb755007e0c7aff60f069383be1ce4d326a7c3a099ffcab7b0c8"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2097.fits",
    "bytes": 1045440,
    "sha256": "6cb565e18c84c3ec6bed68504717f059c144c74121b710182488d2cb047bd9ad"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2098.fits",
    "bytes": 1045440,
    "sha256": "6c238dc11aaa6f3b53963417fd139ee909e974d42537247828599fd0f0f41d80"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2099.fits",
    "bytes": 1045440,
    "sha256": "f7a1a6c70c3e33fbaf1f028a0e27270000d5d6cad1213e9d0cfc931b3152f00e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2100.fits",
    "bytes": 1045440,
    "sha256": "89f4cf159f797a49d197c6c8de81769d89496372c3bfd725a05a55f005b33d51"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2101.fits",
    "bytes": 1045440,
    "sha256": "f04c23eb04e0c9bf50cd61af319f13c3fae8099c3004596fc4d58ba484817f20"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2102.fits",
    "bytes": 1045440,
    "sha256": "d694759eaf4f181c85d98f172fe54d2d148d395f04b986fd8fb869b98ed9eadf"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2103.fits",
    "bytes": 1045440,
    "sha256": "6313f0b368dfa4cee9afd82ad7c35804ccd4cd97761a818f99e4ce1d642d5b29"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2104.fits",
    "bytes": 1045440,
    "sha256": "5bca7f5eb96ae66e2d75aa86ed9a5d88d9cf3fa868cf2f71f26b14e839f24be1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2105.fits",
    "bytes": 1045440,
    "sha256": "4792dc47efaa0eb6490c84aaf4636a873139c446466a4694b5eec5bb307fcf22"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2106.fits",
    "bytes": 1045440,
    "sha256": "fcb63f441d105f39e22ca66ea11e961798b7734b1ed75a7f87fcb433ef0755bf"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2107.fits",
    "bytes": 1045440,
    "sha256": "d7d4ca960828ab68a3bf868ae5d46258904a2ae100abeec9126c7589c1f0e642"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2108.fits",
    "bytes": 1045440,
    "sha256": "362f637e9d47ff3aa4fe5ae3b93190c8fd2f5d69cf48449465da777dbd51d665"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2109.fits",
    "bytes": 1045440,
    "sha256": "7ee0f148f7eb361fb80c6a3888941fd9753c1f24e8cff16bc803d346892e8d45"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2110.fits",
    "bytes": 1045440,
    "sha256": "7c8feca7e330be0c8f90b25c3f2d44984eee89154984cd65df3db0d67fd82d59"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2111.fits",
    "bytes": 1045440,
    "sha256": "5e580ef9fc79c5c9ea501880109b118a5b941681d51e63b919b79bf480a6ed9d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2112.fits",
    "bytes": 1045440,
    "sha256": "a9324851164fe9e4942ed61fb9130290ad639ab8d51b31ac567fc67fb8bec307"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2113.fits",
    "bytes": 1045440,
    "sha256": "cac708501cb57ff19e041cd862fee72406fee36ad34fe9691eaecb7d2077d72b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2114.fits",
    "bytes": 1045440,
    "sha256": "6c2141daf86e5053a3da364e495ddb7712ecacef729b07a16054c2dba95616f2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2115.fits",
    "bytes": 1045440,
    "sha256": "151ab7a509d560bf6b3fec141b44742fa80ee9c8055558eb927129c7f218f0e6"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2116.fits",
    "bytes": 1045440,
    "sha256": "431a72dd8d981b65a60040f801fa24df058cff0b27c6d37db50b223015908b96"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2117.fits",
    "bytes": 1045440,
    "sha256": "7b94f6f83ec4149a05b391a3f100bbdfa148256405789af3d86672d4c3e7d74c"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2118.fits",
    "bytes": 1045440,
    "sha256": "b7068b5de21023ce8ce9123927fa89ce9dc25f5c3f229f22e92c5ef5dc3bd9f4"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2119.fits",
    "bytes": 1042560,
    "sha256": "4e46b43b9836de83242e23c26a6c0e61172f6f3a76cd7f2251c91de91881e9f9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2120.fits",
    "bytes": 1042560,
    "sha256": "cd94afec13cfda0515235fda2efb384c26892a359e5428380796847c0ef18bbb"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2121.fits",
    "bytes": 1042560,
    "sha256": "e1d73cd8766f0ff3bf8eddb567c6e1fa39cdd26442be118353cd274d8ab01c24"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2122.fits",
    "bytes": 1042560,
    "sha256": "881845ae3d083da6719939e9db6f3e8d66c65065ea553a2a51fa30e985c0465f"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2123.fits",
    "bytes": 1042560,
    "sha256": "7f066bfca1e7cb1d73a10bff065e3236a345ba5d03a9598b71910d753723a7ef"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2124.fits",
    "bytes": 1042560,
    "sha256": "0dc4e82d61310750d6e13a7e94de05a08d1784f94b60356d417a4bf5a6f29494"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2125.fits",
    "bytes": 1042560,
    "sha256": "63a5b0cf01163e779ffd3dbf1ba67b05594fc79e70824f3fa19adac7a2d65ad8"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2126.fits",
    "bytes": 1042560,
    "sha256": "195b0546453c8400285312fa73aebdb18e2e408141d61b54d43098de5aaa6533"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2127.fits",
    "bytes": 1042560,
    "sha256": "7ade651550a4579536f407110ff6de50be8000b53f630fc0be5e625725bd9475"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2128.fits",
    "bytes": 1045440,
    "sha256": "048a6d42bb5a57d905981c41b44b49ea1b7c80eb71ccffeeca0f6c2dbf1b21e9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2129.fits",
    "bytes": 1045440,
    "sha256": "a82030162e02dce42057220242ea49df9f9683f3d58758686bdd5e2e5b8e4ec4"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2130.fits",
    "bytes": 1045440,
    "sha256": "c7f57e59dec75be6c54be222d6229983677050ed7e8cd96dfc771bef4b82ab7e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2131.fits",
    "bytes": 1045440,
    "sha256": "e7e352e8acd168f30fb1921672bfa4b2fa8f232a910b75498ad202e8530b8e6c"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2132.fits",
    "bytes": 1045440,
    "sha256": "e3e1de45c5aebb1d87040c141c82d851d36b9d2dd5add548450f4ce2289f97a2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2133.fits",
    "bytes": 1045440,
    "sha256": "f8dfac6406d6408c4c24c5b6c76d366e927b9d3b89e8495df7da17eb5d6138d7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2134.fits",
    "bytes": 1045440,
    "sha256": "aad6afed1bb07c09d3f0daec417db7e4f67ba387112942f0169ed17d81fd5bbc"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2135.fits",
    "bytes": 1045440,
    "sha256": "cbc791365de1a66753f5897cd375096c7bfd63c966d6c2a918031c5df5b14fd0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2136.fits",
    "bytes": 1045440,
    "sha256": "fd14d6c209c9a18e00039ab7b5fbaa498963330de03fcde0af99730e279055fa"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2137.fits",
    "bytes": 1045440,
    "sha256": "02153d83bb5401f76bd15b6b4a4d2f0336e4a57514574de56baf8349a669ad21"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2138.fits",
    "bytes": 1045440,
    "sha256": "0e88b3ae31508435f60ad07c303969152e5acf8eee4228806fdd22db3f49653b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2139.fits",
    "bytes": 1045440,
    "sha256": "66c907ee497757abc32617b134f1275c3c5bd191086678d328fca5f7ad77795e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2140.fits",
    "bytes": 1045440,
    "sha256": "29c71ee248926177bf59fa5a08a596dc1d618a7bdb05260bc81b101a4f1eb802"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2141.fits",
    "bytes": 1045440,
    "sha256": "1275fd9b582561a7be13ec692915d19d7b92227ca080b56c5e1fa21748a3ea51"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2142.fits",
    "bytes": 1045440,
    "sha256": "17990b653b9c3219a6cee5c747971ecd0f7045797645d3066452e6b2ea5e92de"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2143.fits",
    "bytes": 1045440,
    "sha256": "b728a6b00315763a82258d7a201e68f591db356c41aab2482b5fd35f77096ac2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2144.fits",
    "bytes": 1045440,
    "sha256": "346447fae561fa7353281cfcaf2ab2acdfbf53b8ed5ae2b80d16c4064c85b93b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2145.fits",
    "bytes": 1045440,
    "sha256": "743d705d070af9bbb59e89037859145fd223ca1e470ee2d9d0f72963225ac3ee"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2146.fits",
    "bytes": 1045440,
    "sha256": "9826d19639b5f134e4ea2486301fac3f17ddde06ea9539b8e3c0a376200fd9ed"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2147.fits",
    "bytes": 1045440,
    "sha256": "39518e79ccca51d66ff2d9419d12603a8ccafb82da0dd10054c77eb217a3b7de"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2148.fits",
    "bytes": 1045440,
    "sha256": "8f1699c20f19c0624c909e8f63f44cf7fdf045f11bc79710d66dc398477db826"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2149.fits",
    "bytes": 1045440,
    "sha256": "716170560ad0a34827193b64cda2a9af1546ab785c8738e7779250f6ee56f484"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2150.fits",
    "bytes": 1045440,
    "sha256": "a82547fb12e08169312ba75d57bcb66f72fe2def4852ac24a365b2e493d907ec"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2151.fits",
    "bytes": 1045440,
    "sha256": "61851c5227dc0fac88a3d4f256aaa448b489601d01e7cb6f4beaab944ffcaacd"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2152.fits",
    "bytes": 1045440,
    "sha256": "bedbd645a3aee216a096c122fad387350246f2368972265f7bc0d83a17a01be2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2153.fits",
    "bytes": 1045440,
    "sha256": "e9a2e643e6509b16f45f2a50c058e318b375f322c25da384e8dcc2e7b73244f7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2154.fits",
    "bytes": 1045440,
    "sha256": "a51ed1b6d823245aa555292f31cf4877d77b6bb19b47966695be5f43bea680f2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2155.fits",
    "bytes": 1045440,
    "sha256": "757b8f7fefdb5ad1601f8f9804b31afb60da53b78dbd4fb1fd1e4f092fda9b8c"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2156.fits",
    "bytes": 1045440,
    "sha256": "4b7679886093f1579e0160f01f7adc144e6d5aea4de093d450c33af67678cb5e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2157.fits",
    "bytes": 1045440,
    "sha256": "c9b13d013193c4f8e5d505e7538a0b5100495337d8534a56fd28495c2c4cd7f9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2158.fits",
    "bytes": 1045440,
    "sha256": "a914b731d6bb291aa9981ab2ffacccd5da0ca7883ef9bf7390c0e2e9f502711a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2159.fits",
    "bytes": 1045440,
    "sha256": "34d63729c1ce1f07d4bd36820d44889e94f868a228ffdd3d8606a0e466462502"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2160.fits",
    "bytes": 1045440,
    "sha256": "87d5473bc9bc8491da0b35572299b43edd587166c1c5121cdcd68a8ca8c1faf2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2161.fits",
    "bytes": 1045440,
    "sha256": "73bf7477b6a2d304c5e22f3e51a333b55ada94f01f1e859467b42dcf01ae015b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2162.fits",
    "bytes": 1045440,
    "sha256": "8e652adadc01a6ef4f762e3c0d5ac90994639e121459cbc64d19a0cc08422a5b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2163.fits",
    "bytes": 1045440,
    "sha256": "4887b8e89940481cde521e7bc81152d104e78d9fec1231ce29b28150ea33f674"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2164.fits",
    "bytes": 1045440,
    "sha256": "248ff0c649ba6943cb2460bafe7e62895ef32e4a4a2ab6f25d2e438eda18e55a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2165.fits",
    "bytes": 1045440,
    "sha256": "bccbd3fc4decc9baeb3f6351a6ea8e08c96ab9f5b78c05092b5ed0c31da8f0c8"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2166.fits",
    "bytes": 1045440,
    "sha256": "0f70e552cd18450a77cc07a79273dfa67d16f047131d38f15f8e472e7f636426"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2167.fits",
    "bytes": 1045440,
    "sha256": "8a4d702d044e48831d2a19817eb2c3ca39c6caf9708ab1fb300baf4ac41330bb"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2168.fits",
    "bytes": 1045440,
    "sha256": "ca752c80e1723efe8a689e1db0333e404c31522e61e3a404cdeed7c505e38843"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2169.fits",
    "bytes": 1045440,
    "sha256": "c27388d4b6c899a25415de92baf28385015d150e749cdda8ed8536c93ab09993"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2170.fits",
    "bytes": 1045440,
    "sha256": "2384d1008acd92c853e91dc53625011b21bcb50fd094c9de458485be649baca0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2171.fits",
    "bytes": 1045440,
    "sha256": "87b79efd00d34031cef7f1d7f89b4404eb3d1013a4fe9439f8cc814c63950af1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2172.fits",
    "bytes": 1045440,
    "sha256": "bf465982e7a8bfdd8e67d0db8371aedf73328986db82074b0959bc5c0b6a83ba"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2173.fits",
    "bytes": 1045440,
    "sha256": "41308fc860036ebc8bad383745df69943827baf318ac24575ce8c49b71ce2365"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2174.fits",
    "bytes": 1045440,
    "sha256": "9276c7a8bdc01a356cdd1bcbe48216ffff89937df225bcff4c1f05c252aff0c0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2175.fits",
    "bytes": 1045440,
    "sha256": "3ade2f7ad9744ef766c0df6656200db580d0c1a4a82a3733956178ee5b89023d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2176.fits",
    "bytes": 1045440,
    "sha256": "c8a3835ea9bf9ef37d32d75be474be2050fb715c9da319548ebafe324e8c85f8"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2177.fits",
    "bytes": 1045440,
    "sha256": "80b0e6ef7aeeb71aab731bab7b0e9163217c54f4cc37697766709262cb89b091"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2178.fits",
    "bytes": 1045440,
    "sha256": "11fe844b44a3e54df9ff3333aff2d9a129d9f2398de7ceb9e5cbb0b37f1e3429"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2179.fits",
    "bytes": 1045440,
    "sha256": "5c62be3db0e0c1f686ff45b9bf04ed6435fbc3dbd328709cf83466c860abaeb2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2180.fits",
    "bytes": 1045440,
    "sha256": "91dea3f14f143c01ffa0596d94e8ad66ef7b16832dfc6ddecc0d7ee8dc29faa0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2181.fits",
    "bytes": 1045440,
    "sha256": "c52401192f43c9c9c1459a6d39d64a16d80d0d30addb88de9f8a71f2d2e90a38"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2182.fits",
    "bytes": 1045440,
    "sha256": "4efc7eb49caf22adf2048b4d127d70677a25311b59c1720c97bc950dc5240e28"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2183.fits",
    "bytes": 1045440,
    "sha256": "95fdafa6c78833eebe2278bff55a860f19d8c54297e2a28de406fd6931faf693"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2184.fits",
    "bytes": 1045440,
    "sha256": "3f6c7922bc756e1be96e22601dc29828391dc7ec605c2b8f95c0317ccab5b47a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2185.fits",
    "bytes": 1045440,
    "sha256": "792c83f5941551995ce8ca0e7d05232d34e2dd02e89a51878a83b481300702d1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2186.fits",
    "bytes": 1045440,
    "sha256": "ae779509e9c7ea8b2e499181a39d8dd65ceee2d606ca3fe6a2bff22e4f26b4cf"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2187.fits",
    "bytes": 1045440,
    "sha256": "6c35e500d55a0ca9c5efc400109ea993c459eb894d75402e737924589e715bf2"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2188.fits",
    "bytes": 1045440,
    "sha256": "9dafdba4eb1430d6902c233409c136a3f7d9cd657e3b19b625cbb1e91aaa76df"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2189.fits",
    "bytes": 1045440,
    "sha256": "73452cf8786e7b7fda6b58e078fae0e284187befe45f3517a43eedee9c512e2e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2190.fits",
    "bytes": 1045440,
    "sha256": "f3c7bc3fb6394bd18618a8c9aceca5f32ae288f2f52cba79db0e466f1ef5260c"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2191.fits",
    "bytes": 1045440,
    "sha256": "b9ed626968b3dadf399ba4dc01e3e30d2abba52a94783799dc558330258f46a7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2192.fits",
    "bytes": 1045440,
    "sha256": "77e5e897cd094370ad2167f54c83a8ce51b2cb7ad748f2a9177d6ac807f59e21"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2193.fits",
    "bytes": 1045440,
    "sha256": "47b3c2bbc37e4ef210fd6ebc10584a95b0fe9c5980351115ecb3f6f20bf56e69"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2194.fits",
    "bytes": 1045440,
    "sha256": "77fb118da7d1d13159e566718390ed7b3e70811da606decfb6d1ed0bbe064290"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2195.fits",
    "bytes": 1045440,
    "sha256": "7357e69bff497784578da744bc72efc299a48814b539014116cfdc20c2598f11"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2196.fits",
    "bytes": 1045440,
    "sha256": "3d064701b342d1078049cda98d48d14c80d8d88f5436ac1c7bdab067d87f688a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2197.fits",
    "bytes": 1045440,
    "sha256": "e4b102e11ad053d128eba2642bda44871d2dadaf8c639de94edbf4f210670cdc"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2198.fits",
    "bytes": 1045440,
    "sha256": "34de84badd3ff7ece2aa345075f41b957681de22f11ca7f44851d1695a1f6092"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2199.fits",
    "bytes": 1045440,
    "sha256": "28f7679a3cc2f18cc8524ebd22f63901685cc271260ad81ea4c2ecbd812f6202"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2200.fits",
    "bytes": 1045440,
    "sha256": "c9b990e05590f60a59c037491cbc42a563fb895b696135ad986e265e59cebc12"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2201.fits",
    "bytes": 1045440,
    "sha256": "b128b24e0af484b94a353e8feb74c9cfc0e9903d8a24b53d826a1bea9d5d1ab1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2202.fits",
    "bytes": 1045440,
    "sha256": "e06d6e3791f897b3f423603763248a36ef796f66eea010962d5a7f21cb544969"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2203.fits",
    "bytes": 1045440,
    "sha256": "e5e125f7c47a2595f44718322050378a323df2ee2471f914176257561ef6cfad"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2204.fits",
    "bytes": 1045440,
    "sha256": "50b8843be04b2988e6d707ffdb6c4c2b48d3e276956ae77593b1e974868b00f3"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2205.fits",
    "bytes": 1045440,
    "sha256": "437ebec4e9fe472bf89a3bd9a94fb06975628e22fe5cb0135c9452a178554d7b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2206.fits",
    "bytes": 1045440,
    "sha256": "961639cc8c2c210e1e583f2870dc79aac7aa7a8968ec0395249623dfdc79844a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2207.fits",
    "bytes": 1045440,
    "sha256": "a4fa3df1558b4154a07e1905bce0cc449717972a4c06a7f4ea4e4660e8c7a552"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2208.fits",
    "bytes": 1045440,
    "sha256": "f922586d7e8f221db3c6f64684aea30deb02f5c4ccc7b2fa1e705ca512207122"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2209.fits",
    "bytes": 1045440,
    "sha256": "92c5c073c3b57f979da002e67f8811d0ac8c3dab43eba234dd81384b9db3e5ed"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2210.fits",
    "bytes": 1045440,
    "sha256": "7c260dd9520adbcaa6cc3e539d941b8ddda06ffabeeb9cc7938978bf6e3e4a29"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2211.fits",
    "bytes": 1045440,
    "sha256": "13fbbdc6f41357ab6ef5e385aa911f2437e8fb6e38cab739becd01d32696b8c9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2212.fits",
    "bytes": 1045440,
    "sha256": "9bb99bb1717a3b33049d8b05e3cecf86e464b64d2ead2f038919cfb69da4ca6e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2213.fits",
    "bytes": 1045440,
    "sha256": "57574ebf02b85341be05de43d8d911cffeb878ad6f51adfbdd8c549434c42dee"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2214.fits",
    "bytes": 1045440,
    "sha256": "e8ae28e17356a1effd24e718088823eb8b71dcfc14293c9805a0036e439deacf"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2215.fits",
    "bytes": 1045440,
    "sha256": "90dd7941dc09a60367680f0d96ca06ffe7455f8e3761438850733e82cf7b20d1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2216.fits",
    "bytes": 1045440,
    "sha256": "5e79d6d8fffee0643c028fcff9b0f91ec38f0e77987674744838fb6a37b17ae9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2217.fits",
    "bytes": 1045440,
    "sha256": "39647a8fe5b1a100fb5f5b5cca67748fcf9d735709eb6f48082eecff34894abc"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2218.fits",
    "bytes": 1045440,
    "sha256": "2d6a2f87ce46d096046a4ff37acadf584b39ccc3685a311420cda7a6bd04d303"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2219.fits",
    "bytes": 1045440,
    "sha256": "0029165072b50002f91ef15ae20c48cace36df8a866e711ed960642211d3ce10"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2220.fits",
    "bytes": 1045440,
    "sha256": "996849c8d2965cca7d4f4b61770b9a077a5ba7314d2cec332cfebe9aa0282294"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2221.fits",
    "bytes": 1045440,
    "sha256": "e0bd122a82e7c89c53b92813b46a590428fcd589cf997abb1d99f9790c9e170c"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2222.fits",
    "bytes": 1045440,
    "sha256": "47d08b64ffe2fbe74e66cdbdbf9a49a8fb9570115a7cda7eaf85c7e74a865cd7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2223.fits",
    "bytes": 1045440,
    "sha256": "af3fd17be65ea0bd4b7a2eebbb17217bb0eb9d4172efbcea75b3b083769d0aca"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2224.fits",
    "bytes": 1045440,
    "sha256": "0d33d7fd0f0f4c3cb15262b42b710f8bd5d0598078104f97c24c719ac97a0161"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2225.fits",
    "bytes": 1045440,
    "sha256": "f37c63fe218a843651a88cdcdffa09e4009b4acb44ffd8301227d85ead6eb66b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2226.fits",
    "bytes": 1045440,
    "sha256": "e79e80a7c3643cc3eca5d7b5b5df2dcef362bf0e79b9404f90c00e0332417fa1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2227.fits",
    "bytes": 1045440,
    "sha256": "cd0ea1cf47b339d123959f0363cbcfd950b4ecd131ffb5017ee7c7d94d9107e7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2228.fits",
    "bytes": 1045440,
    "sha256": "4121242a443546069a8015c4019f83922186846aeb15cb8b535e5656e3ebe4c7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2229.fits",
    "bytes": 1045440,
    "sha256": "99af24ddbe486ada3cde61a8bd84ab3555973e6f86662b9582b612c054f5ff24"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2230.fits",
    "bytes": 1045440,
    "sha256": "b094caad4a67e96b216852fd1e129ac04995d3d5da4a96a0c2659a9d3afe6fdd"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2231.fits",
    "bytes": 1045440,
    "sha256": "6fec4f89de5ff8a3c3fa919af35eac5f98c172a8bb378456548faea4a1f042d0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2232.fits",
    "bytes": 1045440,
    "sha256": "9a11f769e961e570f962f8aa4404aa17a1a2393dbc3bb39683c51480c7ce6b0e"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2233.fits",
    "bytes": 1045440,
    "sha256": "3788bb4e72c65614818bebc1a9b6193a293a240f6ceea55943cdffcef8157899"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2234.fits",
    "bytes": 1045440,
    "sha256": "3de1bb9edf89a72a7a3493145bc4466bf28c937c031d086a953e0a0fe573a085"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2235.fits",
    "bytes": 1045440,
    "sha256": "99bae162a0da5fa3acf4a5357c7497322cf97d6b238ff70a1270a2fb4b8ab1d6"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2236.fits",
    "bytes": 1045440,
    "sha256": "af5f1f46d9309db1de340acca8238c520642013fd8dd95641c1f3f201e682bfe"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2237.fits",
    "bytes": 1045440,
    "sha256": "06592a970d958e7d2ab7655dcb587d7b8e7828f8ad7d38119e0972f352b9e3df"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2238.fits",
    "bytes": 1045440,
    "sha256": "03a20aaff614471ea840d9700b149ab523b807b23df7197a430372b2368b3274"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2239.fits",
    "bytes": 1045440,
    "sha256": "7883d2e4bb551844eafa80cac44aa20b34619f6e664e62cd7c156adc9759f37f"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2240.fits",
    "bytes": 1045440,
    "sha256": "9b302133318208465b58c7cb10fc420ffcfa43bd04edacf7d235d00865f2059d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2241.fits",
    "bytes": 1045440,
    "sha256": "4d39a72d67f0dd0e91da13c5fb8a12a8e7e706bd036b27c027bc1f2c238dd0d0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2242.fits",
    "bytes": 1045440,
    "sha256": "dd54085487c3026150ac0b560a60ac02e33924ce265b528e4f54d01005539a28"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2243.fits",
    "bytes": 1045440,
    "sha256": "593242a38adcf03789f9c57db1cc33a7075f52ce3da100de3f910096550604e7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2244.fits",
    "bytes": 1045440,
    "sha256": "a0de8505f021d536f6987fa4f74619f68a4c169a28856858c7c0cae7ad905b89"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2245.fits",
    "bytes": 1045440,
    "sha256": "575371870b6ed08e2cad2b63db1a82cae55c69043ea4016dbf4ab3162c21c01d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2246.fits",
    "bytes": 1045440,
    "sha256": "464b4d6634dde1cbd26630cdbb7187cfc7def38c5787d6eea991d6889a3cbc76"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2247.fits",
    "bytes": 1045440,
    "sha256": "8ad6431117710a240624046b491b72f0258e8afe1b2a221f9bb8930ec1a0d1e7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2248.fits",
    "bytes": 1045440,
    "sha256": "69c3d61c88037fb2dc647fd8ddc04ffaa7f7cd47f91a0c0df8851a4b9f231332"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2249.fits",
    "bytes": 1045440,
    "sha256": "a4c6d2c4ea5561a92564a37344063c137d5573b1b07429e73068a284eeb02f8d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2250.fits",
    "bytes": 1045440,
    "sha256": "b2b8af36b38565cec3a762af6ef0db65c2466c6d1df05374d4606011b5578f99"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2251.fits",
    "bytes": 1045440,
    "sha256": "bcfda1899f8b4695b25a381fc615a12077fa1b3dc5188949a905043fc87e97c7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2252.fits",
    "bytes": 1045440,
    "sha256": "af51b6c6c8174f1be43736e7587ae6962d3fd3ddb345a3fd7114f00247409184"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2253.fits",
    "bytes": 1045440,
    "sha256": "a03405f9c45f316397e3e8584b1511bbdaee8687a1526889a372ccb4f4c16751"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2254.fits",
    "bytes": 1045440,
    "sha256": "2376b69a8b907c5c8cfeb6e2c820173cabc1ff2fed0cf2a6b05dc24af1814a2d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2255.fits",
    "bytes": 1045440,
    "sha256": "878f2f619e6c3dbdf7d17001e920ff17215b75e606ebc77e76499aaeceb8eb15"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2256.fits",
    "bytes": 1045440,
    "sha256": "9c6384586dcb0a782ac118255e2fd5b9e9ba75af6d7e767a1f0864c2cd8d94f0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2257.fits",
    "bytes": 1045440,
    "sha256": "71fe14b4d344ffc22d9145519d8569279ede952ffb5afce52340abcd24bdacfd"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2258.fits",
    "bytes": 1045440,
    "sha256": "c23e91c20496faeb10fd16517dff693ef650cf43dd4be4db4ca4f539d7b14f36"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2259.fits",
    "bytes": 1045440,
    "sha256": "d97506401b26cbfb84532e9a8c62a4fc0e20b08cb28c151e772f607c21d7305f"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2260.fits",
    "bytes": 1045440,
    "sha256": "68c81f25bd1f7cbd555a20b7c0f5ce0c2773805588f23131f3ba7ac1bb708c95"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2261.fits",
    "bytes": 1045440,
    "sha256": "eac323b5a70b258c27aead7cddc01e9f024085ca31bb6157dabd1b00bb501633"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2262.fits",
    "bytes": 1045440,
    "sha256": "6282b6164dc7ab83c3b24ad60956dd97c13630a077100967abea30e4713fb305"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2263.fits",
    "bytes": 1045440,
    "sha256": "afcab9fa486315ad812363cd028a87714fe8331eb207369248e132c7c92513f3"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2264.fits",
    "bytes": 1045440,
    "sha256": "99243604e1b97630363ba7de2747bcdd40d8eeaf1bcfe2fd3d16d393d0e879c3"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2265.fits",
    "bytes": 1045440,
    "sha256": "cdd79d3c4b9abe6d0263d10487ed4d18e9b417a3275f4d0a7bf94c990d5f9e33"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2266.fits",
    "bytes": 1045440,
    "sha256": "8ccbb822287cf5844e6dc0c9c30cdc3597c9ba1965331c344f0f7e17de8092cc"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2267.fits",
    "bytes": 1045440,
    "sha256": "66e519c45210d66f6fbafd4ea068a04684ddbe1140243290b8546587fd27f6ce"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2268.fits",
    "bytes": 1045440,
    "sha256": "4e73a56e3049faa0eb551f897e2f305b5de1fd1bb82b7c5665032b51246c9a4b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2269.fits",
    "bytes": 1045440,
    "sha256": "718ebc8c5b40edfe931eed8c8bcf7d7a24da0ab4add0f246f46184489b40841c"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2270.fits",
    "bytes": 1045440,
    "sha256": "2178aa984cd3950f5eb53bd0488e98236f8254b6666807533fee8e96b329ae7d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2271.fits",
    "bytes": 1045440,
    "sha256": "cb21df57c95513da096ea82febfbc921ae7e50765b600ca44ac1e880965083be"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2272.fits",
    "bytes": 1045440,
    "sha256": "c68781597105128fa58e27dd9714182676fa91ef867363d213a59c4bca005a0a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2273.fits",
    "bytes": 1045440,
    "sha256": "3c57dfe4f418d2bb4d78e8dee0cfc36fb91dff7b9ceb6665f8bac339ec126364"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2274.fits",
    "bytes": 1045440,
    "sha256": "b50beecf21f1d8b87dd6f7073af5b10cbbf863405cebe0202de476012219cc00"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2275.fits",
    "bytes": 1045440,
    "sha256": "25702568da33ea31b3ecf61875415000a74a50c3a6fc10cf8b30d89b7274fdd3"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2276.fits",
    "bytes": 1045440,
    "sha256": "6a9e71a8b12b18b3b60ccd3c337b84eeb2357e51dd2d492da3d975b43ea09bc4"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2277.fits",
    "bytes": 1045440,
    "sha256": "25e42aadc06aba7ec5d18caa73cbd1bd332f2d05f215c3c4ef4c4db5da6c298a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2278.fits",
    "bytes": 1045440,
    "sha256": "700a03616d4663fca467391691c362c55574508db7e17231f0145ce4d89ce574"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2279.fits",
    "bytes": 1045440,
    "sha256": "73ea4989a3a82bd210cbb3839418942c9a247261ea53a2b9a555ed19f0030a2b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2280.fits",
    "bytes": 1045440,
    "sha256": "1d3d8da36e6fb86298ecd7033d6720edefdbea9d00cdd36f2765aa40cac21021"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2281.fits",
    "bytes": 1045440,
    "sha256": "2d39fa3487a954656cb64b9fe878e37079eaab067398e21caff528e0da02c27a"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2282.fits",
    "bytes": 1045440,
    "sha256": "b9e2a6367cd4280fbf60d16590fa227bdaa056874929ece04700a23e90ae33df"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2283.fits",
    "bytes": 1045440,
    "sha256": "23dbd7de22e057c9551d4656702b090de07626b4e28e38025410328850cee016"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2284.fits",
    "bytes": 1045440,
    "sha256": "86a935f126fab9a2d74db269e216412bdb50355399fead1a1c6263b7d42def49"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2285.fits",
    "bytes": 1045440,
    "sha256": "e548a6a5e7a52b15bc135f0427f74671ad515c14905e33f71ba4a7fd58e32767"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2286.fits",
    "bytes": 1042560,
    "sha256": "4f0c035e8093f7ee8cb9ae5fd236f72dc3e0c4863d40b36c8789bcec84806b75"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2287.fits",
    "bytes": 1042560,
    "sha256": "8179415292f291096dd06ee597a113a909e6a1e0ba4bb49ff984795b95d49d40"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2288.fits",
    "bytes": 1042560,
    "sha256": "31bf5b9db8865148f1dbf0c7494163d825c0b063acb69b03fc44cbddffa079f0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2289.fits",
    "bytes": 1042560,
    "sha256": "6217b9872400f620d2051ac73c0983eedcd1926451e1bbf172d445e3968a97ce"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2290.fits",
    "bytes": 1042560,
    "sha256": "5d66175547266276cd66bcd640b1689853a2804b487997594046a90f342cb40d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2291.fits",
    "bytes": 1042560,
    "sha256": "3d90236563a1625dac9fae1caf8d6c784544021a725f011a81dff1512d85d9ea"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2292.fits",
    "bytes": 1042560,
    "sha256": "28efe2907e8de0df2665c17221ebca0fffd60c9012f447ce0b84ba718fb19484"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2293.fits",
    "bytes": 1042560,
    "sha256": "ffca11521cd9e06912dfc05949dddd7104d97d27efa86ba617c9fb9a147ed579"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2294.fits",
    "bytes": 1042560,
    "sha256": "2876df2247b4193b26aa3de8ba85a767e92cb0ad2515965c7cc701daf4a0fd64"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2295.fits",
    "bytes": 1042560,
    "sha256": "6d3bc8e5e5a9d9369d3e8ea2b145c161807ab8a11097f6bf3bd8f3d6cae66db7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2296.fits",
    "bytes": 1042560,
    "sha256": "accc30cbc86ec2768bb726f83bf76d7f354c633fd0c5b9d0586e17bd125229e5"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2297.fits",
    "bytes": 1042560,
    "sha256": "b8f4e8919da84b669c5f509fc62f634c60602bd2356f5df6a19847bc6f446d3d"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2298.fits",
    "bytes": 1042560,
    "sha256": "39328bbf2c6992d1f3e9bec6e3f822ae7d9173862874c17738407d623f6a0dd6"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2299.fits",
    "bytes": 1042560,
    "sha256": "d8d27d9b57453a9563f386b8d38a5ba3f349deacf2aa6dd1d646c8cea8b34bc7"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2300.fits",
    "bytes": 1042560,
    "sha256": "a7c07da466442c33f0379c712829f79a870af15c1eb4555ddfa8619c1c67cbd6"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2301.fits",
    "bytes": 1042560,
    "sha256": "dc3879c96562c7a0c048606f3687b1eb3e8a7042b0db00297d0e397ed84a5769"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2302.fits",
    "bytes": 1042560,
    "sha256": "9cad93df934d778b2318e31db79d7c3403f8a5388680896ae04b1394d025d0a1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2303.fits",
    "bytes": 1042560,
    "sha256": "b71e1af26d462e9986aabdff4bd37b8654552ffbf9d1415f17d07a7b606992c1"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2304.fits",
    "bytes": 1042560,
    "sha256": "319248fa5bb205ed943cd5a410f7a9ad7b686daa70dfa85909ca4344396e8781"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2305.fits",
    "bytes": 1042560,
    "sha256": "bcf2214e611bdfa5a5288442a014e4a05e0679578b0818ba899befc04e573ad9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2306.fits",
    "bytes": 1042560,
    "sha256": "d64dbcbc910226ab5ff06bebe1033c108d94fddcc1015f038657ddf86f973be5"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2307.fits",
    "bytes": 1042560,
    "sha256": "5bfe5c963827c8dc1f193a166589aa90dd7ae25c1377cbf553b1a72b60e14f87"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2308.fits",
    "bytes": 1042560,
    "sha256": "0a2c4cf55f8e43f075d2f741e180c7d2630d38736b5d8e5e7809819a9613bfd0"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2309.fits",
    "bytes": 1042560,
    "sha256": "21c37f26e2e79b81c8b6fdd9bef1f7504b0696058431507c0268e6f524e81b3b"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2310.fits",
    "bytes": 1042560,
    "sha256": "6f970156fb709906ea36dd1165e50a7afa3ca118ba72bc0926665aae39c4c1be"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2311.fits",
    "bytes": 1042560,
    "sha256": "c86df960332ccbb267e551b15cf34d97eef284d70f72ee2d33ca40896aac4660"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2312.fits",
    "bytes": 1042560,
    "sha256": "c41a38335c92a976fd7c4dccbf18bca7b5fde5b3043a67118a79ee2814d3f4dc"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2313.fits",
    "bytes": 1042560,
    "sha256": "f105bced0123ca70e2ccc16ea27743b34c31b6ae07ed647b594b831fb4cc70ee"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2314.fits",
    "bytes": 1042560,
    "sha256": "2eab482d028f3c35c5ca3f19493d0ccef466b7d42cc95fb3d5f74bd394bb9218"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2315.fits",
    "bytes": 1042560,
    "sha256": "e9fec13d88dbeb5bb49515694784f3afccccfdfd2c67146917867f92006271d9"
  },
  {
    "path": "SFT/fits_files/720x360/hmi.Synoptic_Mr_small.2316.fits",
    "bytes": 1042560,
    "sha256": "6f9aa8c62dde5cfcd4e3887582ee8be882855b5dd587e21f876f2a998547292b"
  },
  {
    "path": "SFT/validation_data/.gitignore",
    "bytes": 23,
    "sha256": "a8a99668ac3d43192badf6611df9086caba334360745de0d4fc4bc7a1c010aae"
  },
  {
    "path": "SFT/validation_data/cr2120_observational_arrays.npz",
    "bytes": 6177750,
    "sha256": "4dbddf6c983285f9434e69193e1268979ad9f6e1ea2a7d0ec6567198ee355b9d"
  },
  {
    "path": "SFT/validation_data/cr2120_observational_comparison.png",
    "bytes": 377164,
    "sha256": "7c98d21b85f50583a12ecc994af74df7f2872937aecf9bc0436f359226fe0e96"
  },
  {
    "path": "SFT/validation_data/cr2120_observational_metrics.json",
    "bytes": 6034,
    "sha256": "fae4556e8bc2aaefbb298d810d3b10989e53de79d6127f7f86a3ef7e03127203",
    "lines": 176
  },
  {
    "path": "SFT/validation_data/cr2122_observational_arrays.npz",
    "bytes": 6177563,
    "sha256": "40ebe6b4cffa4f2786994db78187db78665b1c96e56c1778adaf3a9f52c8fbe6"
  },
  {
    "path": "SFT/validation_data/cr2122_observational_comparison.png",
    "bytes": 386665,
    "sha256": "5329d319d6e3c5681a335626a233a02206a1a7faf5e02664ef975de8276369ca"
  },
  {
    "path": "SFT/validation_data/cr2122_observational_metrics.json",
    "bytes": 6053,
    "sha256": "9fa410aeebbc99c54b51a82ec968495713375bc9e00f26433cff1e16f48c90b1",
    "lines": 176
  },
  {
    "path": "SFT/validation_data/cr2124_observational_arrays.npz",
    "bytes": 6186919,
    "sha256": "e5c142cf5eef8ffba0e26841b7850fefaf21a8146931e1660dafb7f22090c254"
  },
  {
    "path": "SFT/validation_data/cr2124_observational_comparison.png",
    "bytes": 398774,
    "sha256": "c3b6680c3a321e02d5674b243d7baef8dcaf23b5fc4d49e6c17177c0a742a63b"
  },
  {
    "path": "SFT/validation_data/cr2124_observational_metrics.json",
    "bytes": 6041,
    "sha256": "83aa7907cb93149ec9191307015b4e370b3b7aac6286c07fa8eeb76a105e30b3",
    "lines": 176
  },
  {
    "path": "SFT/validation_data/hmi.M_45s.20120219_225530_TAI.jsoc.json",
    "bytes": 9641,
    "sha256": "98526ee53160261c4c1e4ed898fb1a4b753a9a7dd11d70d6999243ae0cf1a3a3",
    "lines": 550
  },
  {
    "path": "SFT/validation_data/hmi.M_45s.20120219_225530_TAI.magnetogram.fits",
    "bytes": 15670080,
    "sha256": "99edac9897121e065aa9153294e34b58fa2a7e6b42783ad377f0ec836c1d306e"
  },
  {
    "path": "SFT/validation_data/hmi.M_45s.20120414_133945_TAI.jsoc.json",
    "bytes": 9643,
    "sha256": "4798b88c94266fc647c8e8c84a8b017d966a93ac50705144ffd76e2855daef4f",
    "lines": 550
  },
  {
    "path": "SFT/validation_data/hmi.M_45s.20120414_133945_TAI.magnetogram.fits",
    "bytes": 15243840,
    "sha256": "5c0941b10dca18faa0a226add5b4d2281cd9bfce883d83d07c04785b18f07490"
  },
  {
    "path": "SFT/validation_data/hmi.M_45s.20120608_003000_TAI.jsoc.json",
    "bytes": 9636,
    "sha256": "65cb6cd91627e786ac6cc4141ea8700330688a011b4cb353d2fe71c9c3aeb058",
    "lines": 550
  },
  {
    "path": "SFT/validation_data/hmi.M_45s.20120608_003000_TAI.magnetogram.fits",
    "bytes": 15062400,
    "sha256": "48c68824c5860aaec41d31b7ddee3431b9b1c04a6bf2d1bb0bb835783ffcd087"
  },
  {
    "path": "SFT/viewer/.gitignore",
    "bytes": 55,
    "sha256": "e30fd3b9b08c2560c8348047031d035f44efac2422a02d2ed7733612c51f3236"
  },
  {
    "path": "SFT/viewer/README.md",
    "bytes": 1458,
    "sha256": "c5e8b6674985b544e721db4717332ea1f39b8d8303438b8875b9dde59f4ddfff",
    "lines": 36
  },
  {
    "path": "SFT/viewer/index.html",
    "bytes": 376,
    "sha256": "5a88bb0fe36ffdb321eef1c912af0e51c347abcb5cbeb43337fd731697a42963",
    "lines": 1
  },
  {
    "path": "SFT/viewer/package-lock.json",
    "bytes": 62441,
    "sha256": "e02e47621956f85cd9dfbc9f8fa851ac2a99e0aa69b16701d13a57da50af9c7f",
    "lines": 1796
  },
  {
    "path": "SFT/viewer/package.json",
    "bytes": 427,
    "sha256": "0e311298d5533b3231503fa77c9c045e07a59888b0085b7c625e351951634fce",
    "lines": 1
  },
  {
    "path": "SFT/viewer/tsconfig.json",
    "bytes": 231,
    "sha256": "d6ba4e83d520a88a12708d98de11343afba7830a5f3649cab10723e7915a4aff",
    "lines": 1
  },
  {
    "path": "SFT/viewer/tsconfig.tsbuildinfo",
    "bytes": 67,
    "sha256": "d1bd155ef055818fa55a7e2a2e7abf562383dc19a7da00648c60b8f217994ea2"
  },
  {
    "path": "SFT/viewer/public/favicon.svg",
    "bytes": 353,
    "sha256": "45c9ba9a1975e01e85d47b9d0cf3584dcf66bfb0482fd359eec9a2a5533a9522"
  },
  {
    "path": "SFT/viewer/public/maps.json",
    "bytes": 4152267,
    "sha256": "000fab11e8e54f1f32fd3d7a29828449747a3d9ecaba494d562b75c07e155635",
    "lines": 1
  },
  {
    "path": "SFT/viewer/src/main.tsx",
    "bytes": 10639,
    "sha256": "f7f4d5ab92ec8891af86f288e5c77d6b7463a8a767b1ce10a80f687653f288dc",
    "lines": 73
  },
  {
    "path": "SFT/viewer/src/style.css",
    "bytes": 7701,
    "sha256": "a4aa661f18a96d8979a5a5c45e480efd9d2894255d453372bbbf4de2c064e150",
    "lines": 117
  },
  {
    "path": "SFT/viewer/src/vite-env.d.ts",
    "bytes": 38,
    "sha256": "65996936fbb042915f7b74a200fcdde7e410f32a669b1ab9597cfaa4b0faddb5",
    "lines": 1
  },
  {
    "path": "ananya_research_work-main/README.md",
    "bytes": 718,
    "sha256": "e41707d24d40f4589540fa5bc8b23aadf2478b8ad58d6ef105928c7bde595b5c",
    "lines": 8
  },
  {
    "path": "ananya_research_work-main/sft-implementation-and-magnetogram-handling-review.md",
    "bytes": 32630,
    "sha256": "2ccd7e75699fbbd4e50ee513bf74c503fd17ddf14d739efb9c1829153aa7b188",
    "lines": 470
  },
  {
    "path": "ananya_research_work-main/PFSS/CR_2193_80_full.py",
    "bytes": 16139,
    "sha256": "a76f837041bb4168612976592c4e269fbb43ba2f7f1477d26e12df91992f36f0",
    "lines": 478,
    "functions": [
      {
        "name": "Y_lm",
        "line": 22
      },
      {
        "name": "func_integ",
        "line": 54
      },
      {
        "name": "simpson_weights",
        "line": 59
      },
      {
        "name": "simpson_2D_weight_matrix",
        "line": 65
      },
      {
        "name": "C_lm",
        "line": 73
      },
      {
        "name": "compute_c_for_i",
        "line": 86
      },
      {
        "name": "compute_sum1_for_i",
        "line": 101
      },
      {
        "name": "rad_to_deg",
        "line": 133
      },
      {
        "name": "B_final",
        "line": 226
      },
      {
        "name": "simpson_weights",
        "line": 327
      },
      {
        "name": "simpson_2D_weight_matrix",
        "line": 333
      },
      {
        "name": "flux",
        "line": 343
      },
      {
        "name": "simpson_weights",
        "line": 367
      },
      {
        "name": "simpson_2D_weight_matrix",
        "line": 373
      },
      {
        "name": "dYlm_dtheta",
        "line": 419
      },
      {
        "name": "B_final2",
        "line": 431
      },
      {
        "name": "B_final3",
        "line": 453
      },
      {
        "name": "compute_sum_for_i",
        "line": 227
      },
      {
        "name": "compute_sum_for_i",
        "line": 432
      },
      {
        "name": "compute_sum_for_i",
        "line": 454
      }
    ],
    "imports": [
      "from astropy.io import fits",
      "from joblib import Parallel, delayed",
      "from joblib import parallel_backend",
      "from matplotlib.animation import FuncAnimation",
      "from matplotlib.colors import Normalize",
      "from matplotlib.ticker import FuncFormatter",
      "from mpl_toolkits.mplot3d import Axes3D",
      "from scipy.interpolate import interp1d, RectBivariateSpline",
      "from scipy.special import lpmv",
      "from scipy.special import sph_harm",
      "import matplotlib.pyplot as plt",
      "import numpy as np"
    ]
  },
  {
    "path": "ananya_research_work-main/PFSS/jul80_field_line.py",
    "bytes": 7109,
    "sha256": "fdc3eebc4404ef09cf6696b4798c1ea3c019060d7f9d7d19c8d2775fc7d2b0aa",
    "lines": 231,
    "functions": [
      {
        "name": "bTrace",
        "line": 49
      },
      {
        "name": "rk4",
        "line": 76
      }
    ],
    "imports": [
      "from scipy.interpolate import RegularGridInterpolator as rgi",
      "import matplotlib.pyplot as plt",
      "import numpy as n",
      "import numpy as np"
    ]
  },
  {
    "path": "ananya_research_work-main/SFT/Instruction.txt",
    "bytes": 7301,
    "sha256": "f7dc7404c38b48504d65fe5e7dff913689997996f5b51e16ba52e3bd9c163691",
    "lines": 81
  },
  {
    "path": "ananya_research_work-main/SFT/SFT.py",
    "bytes": 21106,
    "sha256": "eb0d3b59b8155433ebee24ec052158847691819c31977c325d74a52c184e8174",
    "lines": 637,
    "functions": [
      {
        "name": "omega",
        "line": 18
      },
      {
        "name": "u",
        "line": 25
      },
      {
        "name": "y",
        "line": 136
      },
      {
        "name": "theta",
        "line": 139
      },
      {
        "name": "apply_boundary_conditions",
        "line": 289
      },
      {
        "name": "apply_boundary_condition",
        "line": 307
      },
      {
        "name": "compute_B_from_A_staggered",
        "line": 321
      },
      {
        "name": "update_A_staggered",
        "line": 353
      },
      {
        "name": "Ay_func",
        "line": 450
      },
      {
        "name": "Bz_func",
        "line": 531
      }
    ],
    "imports": [
      "from astropy.io import fits",
      "from numba import njit, prange",
      "from scipy.interpolate import interp1d, RectBivariateSpline",
      "import datetime",
      "import matplotlib.pyplot as plt",
      "import numpy as np",
      "import pandas as pd"
    ]
  },
  {
    "path": "ananya_research_work-main/SFT/bmrsharps_evol.txt",
    "bytes": 158327,
    "sha256": "1e3a8d95bc2accafc40d07e6feb9987f0808fd1bf1bdd28df459f61576d55385",
    "lines": 1157
  },
  {
    "path": "ananya_research_work-main/SFT/main.py",
    "bytes": 2265,
    "sha256": "bf45e15c6e66157ba613cad3f592f73e4c8d4f10d2fe725de2609ea2404afb84",
    "lines": 63,
    "functions": [],
    "imports": [
      "import datetime",
      "import matplotlib.pyplot as plt",
      "import numpy as np",
      "import os",
      "import sharptools"
    ]
  },
  {
    "path": "ananya_research_work-main/SFT/sharptools.py",
    "bytes": 39163,
    "sha256": "3dad892d58ce402e694699c08af7f31e4bea01d49bd2b0f2ebaafa3e5e5ba75e",
    "lines": 902,
    "functions": [
      {
        "name": "bmr2d",
        "line": 22
      },
      {
        "name": "correct_flux_multiplicative",
        "line": 70
      },
      {
        "name": "derotate",
        "line": 90
      },
      {
        "name": "evolve_forward",
        "line": 128
      },
      {
        "name": "get_bmrs",
        "line": 250
      },
      {
        "name": "get_pair_overlaps",
        "line": 385
      },
      {
        "name": "get_sharps",
        "line": 547
      },
      {
        "name": "getSHARPs",
        "line": 578
      },
      {
        "name": "readmap",
        "line": 630
      },
      {
        "name": "readSHARP",
        "line": 668
      },
      {
        "name": "SHARPtime",
        "line": 801
      },
      {
        "name": "vs",
        "line": 168
      },
      {
        "name": "__init__",
        "line": 846
      },
      {
        "name": "prep_sft",
        "line": 852
      },
      {
        "name": "setbr",
        "line": 877
      },
      {
        "name": "evolve",
        "line": 883
      }
    ],
    "imports": [
      "from astropy.io import fits",
      "from matplotlib import gridspec",
      "from scipy.interpolate import RegularGridInterpolator",
      "from scipy.interpolate import interp2d, griddata",
      "from scipy.io import netcdf",
      "from scipy.ndimage.filters import gaussian_filter as gauss",
      "from sunpy.coordinates.sun import carrington_rotation_number",
      "import datetime",
      "import drms",
      "import matplotlib.pyplot as plt",
      "import numpy as np",
      "import pickle",
      "import sunpy.map",
      "import sys"
    ]
  },
  {
    "path": "ananya_research_work-main/SFT/test_length_zero_line_diffusion.py",
    "bytes": 31025,
    "sha256": "cffdf2ca0495acb4c5840cd9bc0038ffe44f37379f876f384f360a1aa0270c8d",
    "lines": 988,
    "parse_error": "expected an indented block after function definition on line 406 (<unknown>, line 408)"
  },
  {
    "path": "ananya_research_work-main/SFT/test_p_advection_diffusion.py",
    "bytes": 24010,
    "sha256": "90d8de32f6e6a91d74d8e7912a31a6dd9dc430f261187d25ff4990d3f91eacae",
    "lines": 741,
    "parse_error": "expected an indented block after function definition on line 561 (<unknown>, line 563)"
  },
  {
    "path": "ananya_research_work-main/SFT/test_p_diffusion.py",
    "bytes": 19002,
    "sha256": "fc55eac49c2c7a6ea99ee658557abf75803fb99a8131948facf64256d8f0a800",
    "lines": 591,
    "parse_error": "expected an indented block after function definition on line 381 (<unknown>, line 383)"
  },
  {
    "path": "ananya_research_work-main/SFT/test_zero_length_line_advection_diffusion.py",
    "bytes": 41218,
    "sha256": "7a6a731dad55a00f825ce3fd3144d5a4ca37ba7e97025764819d6f5a3e17e7e9",
    "lines": 1247,
    "functions": [
      {
        "name": "omega",
        "line": 35
      },
      {
        "name": "u",
        "line": 40
      },
      {
        "name": "Y_lm",
        "line": 52
      },
      {
        "name": "y",
        "line": 76
      },
      {
        "name": "theta",
        "line": 79
      },
      {
        "name": "C_lm",
        "line": 204
      },
      {
        "name": "compute_c_for_i",
        "line": 210
      },
      {
        "name": "compute_sum1_for_i",
        "line": 224
      },
      {
        "name": "pil_length_from_sign_changes",
        "line": 261
      },
      {
        "name": "apply_boundary_conditions",
        "line": 436
      },
      {
        "name": "apply_boundary_conditions_Bz",
        "line": 454
      },
      {
        "name": "compute_B_from_A_staggered",
        "line": 466
      },
      {
        "name": "update_A_staggered",
        "line": 486
      },
      {
        "name": "update_A_staggered1",
        "line": 550
      },
      {
        "name": "pil_length_pixels",
        "line": 776
      },
      {
        "name": "apply_boundary_conditions",
        "line": 920
      },
      {
        "name": "apply_boundary_conditions_Bz",
        "line": 938
      },
      {
        "name": "compute_B_from_A_staggered",
        "line": 950
      },
      {
        "name": "update_A_staggered",
        "line": 970
      },
      {
        "name": "update_A_staggered1",
        "line": 1034
      }
    ],
    "imports": [
      "from astropy.io import fits",
      "from joblib import Parallel, delayed",
      "from joblib import parallel_backend",
      "from numba import njit, prange",
      "from numpy.polynomial.legendre import leggauss",
      "from scipy.interpolate import RegularGridInterpolator",
      "from scipy.interpolate import interp1d, RectBivariateSpline",
      "from scipy.special import sph_harm",
      "from skimage.measure import find_contours",
      "import matplotlib.pyplot as plt",
      "import numpy as np"
    ]
  },
  {
    "path": "magnetofriction/engine.py",
    "bytes": 0,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "lines": 0,
    "functions": [],
    "imports": []
  },
  {
    "path": "magnetofriction/model_input.py",
    "bytes": 771,
    "sha256": "7e0e2f1506f8eea5c4179c4f2d1d3a4b692ae74b678405a622f2bc2e2ca5dd8a",
    "lines": 7,
    "parse_error": "unterminated string literal (detected at line 1) (<unknown>, line 1)"
  },
  {
    "path": "magnetofriction/model_output.py",
    "bytes": 0,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "lines": 0,
    "functions": [],
    "imports": []
  },
  {
    "path": "magnetofriction/theory-and-numerical-methods/magnetofriction-equations-and-numerical-choices-qa.md",
    "bytes": 25449,
    "sha256": "83e2bb8f0f7ede4959063ad80086824927e6b1a1304874a90903fc864e6ec14f",
    "lines": 411
  },
  {
    "path": "magnetofriction/theory-and-numerical-methods/magnetofriction-fundamentals-qa.md",
    "bytes": 23455,
    "sha256": "c1a2edbac7194c231d58998c4f3d7b8aa0680b640bf7c4ccf4e9949415924111",
    "lines": 252
  }
]

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/preservation_check.json (133 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/preservation_check.json", "bytes": 133, "sha256": "5a68acd7980ce3156ec211327790e2c7b15ebd850d40ea4ae0f267b9ad1ebd4a", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "original_files_checked": 281,
  "changed_or_missing": [],
  "added_outside_audit": [],
  "protected_research_files": 13
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/run_summary.json (440 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/run_summary.json", "bytes": 440, "sha256": "2a43af330e25965ab2b42b3c52d834647e4fbb85bc211c6db20107cc00ba53ea", "line_endings": "CRLF", "utf8_bom": false} -->
`````json
{
  "observational_rows": 27,
  "synthetic_rows": 66,
  "centers": [
    2120,
    2122,
    2124
  ],
  "input_map_count": 221,
  "variants": [
    "000",
    "100",
    "010",
    "001",
    "110",
    "101",
    "011",
    "111"
  ],
  "synthetic_cases": [
    "evolving_control",
    "missing_data",
    "opposite_rotation_control",
    "seam_features",
    "smooth_rotation",
    "stationary_control"
  ]
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/logs/calculations.log (2,973 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/logs/calculations.log", "bytes": 2973, "sha256": "dee8a9dc2b390674e69c7af7c16449ccb355944af7d8bee380205fe7894477dd", "line_endings": "CRLF", "utf8_bom": false} -->
`````text
Inventorying FITS data and checksums...
WARNING: VerifyWarning: Verification reported errors: [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'CRDER1' is not FITS standard (invalid value string: 'nan').  Fixed 'CRDER1' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Note: astropy.io.fits uses zero-based indexing.
 [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'CRDER2' is not FITS standard (invalid value string: 'nan').  Fixed 'CRDER2' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'CSYSER1' is not FITS standard (invalid value string: 'nan').  Fixed 'CSYSER1' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'CSYSER2' is not FITS standard (invalid value string: 'nan').  Fixed 'CSYSER2' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'SPAREFT1' is not FITS standard (invalid value string: 'nan').  Fixed 'SPAREFT1' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'SPAREFT2' is not FITS standard (invalid value string: 'nan').  Fixed 'SPAREFT2' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'SPAREDB1' is not FITS standard (invalid value string: 'nan').  Fixed 'SPAREDB1' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'SPAREDB2' is not FITS standard (invalid value string: 'nan').  Fixed 'SPAREDB2' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: Checksum verification failed for HDU ('PRIMARY', 1).
 [astropy.io.fits.hdu.base]
WARNING: VerifyWarning: Card 'EARTH_B0' is not FITS standard (invalid value string: 'nan').  Fixed 'EARTH_B0' card to meet the FITS standard. [astropy.io.fits.verify]
WARNING: VerifyWarning: Card 'TRECSTEP' is not FITS standard (invalid value string: 'nan').  Fixed 'TRECSTEP' card to meet the FITS standard. [astropy.io.fits.verify]
CR2120: loading maps and independently reprojecting raw HMI observation...
CR2120: executing literal original reconstruction block (no SFT evolution)...
<unknown>:422: SyntaxWarning: invalid escape sequence '\s'
CR2120: 25,693 common pixels; RMSE central/000/111 = 23.821126/48.208713/23.968045 G
CR2122: loading maps and independently reprojecting raw HMI observation...
CR2122: executing literal original reconstruction block (no SFT evolution)...
<unknown>:422: SyntaxWarning: invalid escape sequence '\s'
CR2122: 25,705 common pixels; RMSE central/000/111 = 35.247420/43.479975/35.674908 G
CR2124: loading maps and independently reprojecting raw HMI observation...
CR2124: executing literal original reconstruction block (no SFT evolution)...
<unknown>:422: SyntaxWarning: invalid escape sequence '\s'
CR2124: 25,700 common pixels; RMSE central/000/111 = 43.170685/73.641835/42.440401 G
Running forward-generated synthetic cases and controls...
Audit calculations complete.

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/logs/discrepancies.log (233 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/logs/discrepancies.log", "bytes": 233, "sha256": "47c687027ad8770ac5775fd10a6c66617e399de1c1bb16866df2b06a8f03b6d1", "line_endings": "CRLF", "utf8_bom": false} -->
`````text
CR2120: detector smoothing and registration sensitivity...
CR2122: detector smoothing and registration sensitivity...
CR2124: detector smoothing and registration sensitivity...
Discrepancy diagnostics and final figures complete.

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/logs/existing_tests.log (634 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/logs/existing_tests.log", "bytes": 634, "sha256": "9df172113b0cdcad34d284734703e97353fb2073d059e015b68e21ddc925e7d8", "line_endings": "CRLF", "utf8_bom": false} -->
`````text
test_hmi_negative_header_maps_to_increasing_physical_longitude (test_coordinate_registration.CoordinateRegistrationTests.test_hmi_negative_header_maps_to_increasing_physical_longitude) ... ok
test_original_sample_positions_reproduce_input (test_coordinate_registration.CoordinateRegistrationTests.test_original_sample_positions_reproduce_input) ... ok
test_rotation_boundary_chooses_and_samples_correct_map (test_coordinate_registration.CoordinateRegistrationTests.test_rotation_boundary_chooses_and_samples_correct_map) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.006s

OK

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/logs/preservation.log (252 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/logs/preservation.log", "bytes": 252, "sha256": "74487505c6b558fb80962a249277e0cec98065df43da1849567e620948422a10", "line_endings": "CRLF", "utf8_bom": false} -->
`````text
<unknown>:422: SyntaxWarning: invalid escape sequence '\s'
<unknown>:51: SyntaxWarning: invalid escape sequence '\ '
{
  "original_files_checked": 281,
  "changed_or_missing": [],
  "added_outside_audit": [],
  "protected_research_files": 13
}

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/logs/raw_checksums.log (159 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/logs/raw_checksums.log", "bytes": 159, "sha256": "7dd392e833c5965b066244104ad32ccd4567dc54369e4378828c44a8d7587211", "line_endings": "CRLF", "utf8_bom": false} -->
`````text
Raw-byte checksum verification: 221 / 221
Audited inputs: [(2119, True), (2120, True), (2121, True), (2122, True), (2123, True), (2124, True), (2125, True)]

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/logs/tests.log (3,291 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/logs/tests.log", "bytes": 3291, "sha256": "b143bde26926daf4af0518e8c503cc497f8f38f82c29c990231a95dee4ecc7ee", "line_endings": "CRLF", "utf8_bom": false} -->
`````text
test_actual_chronology_is_decreasing_longitude_in_increasing_time (test_audit.CompletedAuditTests.test_actual_chronology_is_decreasing_longitude_in_increasing_time) ... ok
test_all_original_files_unchanged (test_audit.CompletedAuditTests.test_all_original_files_unchanged) ... ok
test_literal_HMI_reference_has_no_finite_results (test_audit.CompletedAuditTests.test_literal_HMI_reference_has_no_finite_results) ... ok
test_observations_do_not_sample_seams (test_audit.CompletedAuditTests.test_observations_do_not_sample_seams) ... ok
test_persisted_scores_and_identical_masks (test_audit.CompletedAuditTests.test_persisted_scores_and_identical_masks) ... ok
test_projection_registration_and_baseline_reproduction (test_audit.CompletedAuditTests.test_projection_registration_and_baseline_reproduction) ... ok
test_raw_fits_checksum_avoids_header_normalization_artifact (test_audit.CompletedAuditTests.test_raw_fits_checksum_avoids_header_normalization_artifact) ... ok
test_resolution_and_registration_diagnostics_use_common_masks (test_audit.CompletedAuditTests.test_resolution_and_registration_diagnostics_use_common_masks) ... ok
test_synthetic_accuracy_and_controls (test_audit.CompletedAuditTests.test_synthetic_accuracy_and_controls) ... ok
test_area_weights_cover_sphere_and_polar_cells (test_audit.NumericalTests.test_area_weights_cover_sphere_and_polar_cells) ... ok
test_literal_original_matches_independent_vectorization_on_finite_arrays (test_audit.NumericalTests.test_literal_original_matches_independent_vectorization_on_finite_arrays) ... <unknown>:422: SyntaxWarning: invalid escape sequence '\s'
ok
test_metric_units_and_bias_direction (test_audit.NumericalTests.test_metric_units_and_bias_direction) ... ok
test_missing_edge_and_isolated_pixels_are_not_zero_measurements (test_audit.NumericalTests.test_missing_edge_and_isolated_pixels_are_not_zero_measurements) ... ok
test_no_longitude_edge_extrapolation (test_audit.NumericalTests.test_no_longitude_edge_extrapolation) ... ok
test_primary_sampler_reproduces_existing_at_native_grid (test_audit.NumericalTests.test_primary_sampler_reproduces_existing_at_native_grid) ... ok
test_boundaries_are_current_and_no_unsupported_extrapolation (test_audit.PhysicsTests.test_boundaries_are_current_and_no_unsupported_extrapolation) ... ok
test_degenerate_inverse_fails (test_audit.PhysicsTests.test_degenerate_inverse_fails) ... ok
test_first_order_error_is_second_order (test_audit.PhysicsTests.test_first_order_error_is_second_order) ... ok
test_known_feature_trajectory_positive_and_negative_rates (test_audit.PhysicsTests.test_known_feature_trajectory_positive_and_negative_rates) ... ok
test_latitude_colatitude_equivalence (test_audit.PhysicsTests.test_latitude_colatitude_equivalence) ... ok
test_north_south_symmetry (test_audit.PhysicsTests.test_north_south_symmetry) ... ok
test_stationary_oracle_has_no_shift (test_audit.PhysicsTests.test_stationary_oracle_has_no_shift) ... ok
test_tabulated_rates (test_audit.PhysicsTests.test_tabulated_rates) ... ok
test_time_tagged_seam_selects_chronological_neighbor (test_audit.PhysicsTests.test_time_tagged_seam_selects_chronological_neighbor) ... ok

----------------------------------------------------------------------
Ran 24 tests in 2.735s

OK

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/audit_core.py (7,439 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/audit_core.py", "bytes": 7439, "sha256": "d17be73219316b79238880571114ed2035a95ca560ce4f75ec012f78fcb1a897", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Isolated reconstruction switches; existing SFT code is imported read-only.

Angles are degrees, rates degrees/day, and epoch offsets days. Sources are
0=previous CR, 1=current CR, 2=next CR. No SFT evolution is executed.
"""
from __future__ import annotations
import ast
import importlib.util
from pathlib import Path
import sys

import numpy as np
from scipy.interpolate import RectBivariateSpline

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'SFT'))
import synoptic_reconstruction as existing

VARIANTS = ('000', '100', '010', '001', '110', '101', '011', '111')


def rotation_rate(latitude, fix_latitude=False):
    f = np.sin if fix_latitude else np.cos
    q = f(np.deg2rad(latitude)) ** 2
    return 0.18 - 2.3 * q - 1.62 * q ** 2


def sample_longitudes(longitude, rate, invert=False, exact=False, omega0=13.2, reference=180.):
    """Backward sample an unwrapped, time-ordered three-CR synoptic mosaic.

    Exact inverse solves s = phi + rate*(reference-s)/omega0, where
    t_obs(s)-t_ref=(reference-s)/omega0. Exact is a separate sensitivity,
    not silently included in the three-switch first-order factorial.
    """
    phi = np.asarray(longitude)[None, :]
    a = np.asarray(rate)[:, None] / omega0
    if exact:
        if not invert:
            raise ValueError('Exact inverse requires invert=True.')
        if np.any(np.abs(1+a) < 1e-10):
            raise ValueError('Degenerate trajectory parallel to observing meridian.')
        return reference + (phi-reference)/(1+a)
    return phi + (-1 if invert else 1) * a * (phi-reference)


def select_sources(shifted, reverse=False):
    """Keep exactly 0 and 360 in current CR, matching original strict tests.

    With HMI pixel centers neither endpoint is supported by the spline. Such
    queries stay NaN, rather than extrapolate or fill the gap periodically.
    """
    s = np.asarray(shifted)
    low, high = s < 0, s > 360
    source = np.where(low, 2 if reverse else 0, np.where(high, 0 if reverse else 2, 1))
    wrapped = np.where(low, s+360, np.where(high, s-360, s))
    if np.any((wrapped < 0) | (wrapped > 360)):
        raise ValueError('Three-map reconstruction supports at most one wrap.')
    return source, wrapped


class Sampler:
    """Same cubic RectBivariateSpline and whole-incomplete-row policy as SFT.

    Splines are cached per run to reuse infrastructure without rebuilding
    the identical three splines for every switch combination.
    """
    def __init__(self, maps, headers, degree=3):
        self.parts = []
        for data, header in zip(maps, headers):
            lon, lat = existing.calculate_coordinates(data, header)
            good = np.isfinite(data).all(axis=1) & np.isfinite(lat)
            order = np.argsort(lon)
            x, y = lat[good], lon[order]
            if len(x) <= degree or len(y) <= degree:
                self.parts.append(None)
                continue
            spline = RectBivariateSpline(x, y, data[good][:, order], kx=degree, ky=degree, s=0)
            self.parts.append((spline, x.min(), x.max(), y.min(), y.max()))

    def sample(self, latitude, source, wrapped):
        field = np.full(source.shape, np.nan)
        lat = np.broadcast_to(np.asarray(latitude)[:, None], source.shape)
        for index, part in enumerate(self.parts):
            if part is None:
                continue
            spline, xmin, xmax, ymin, ymax = part
            use = ((source == index) & np.isfinite(lat) & np.isfinite(wrapped)
                   & (lat >= xmin) & (lat <= xmax) & (wrapped >= ymin) & (wrapped <= ymax))
            field[use] = spline.ev(lat[use], wrapped[use])
        return field


def reconstruct(sampler, longitude, latitude, fix_latitude=False,
                invert_sample_shift=False, reverse_cr_seam=False, exact=False,
                omega0=13.2, reference=180.):
    rate = rotation_rate(latitude, fix_latitude)
    shifted = sample_longitudes(longitude, rate, invert_sample_shift, exact, omega0, reference)
    source, wrapped = select_sources(shifted, reverse_cr_seam)
    return sampler.sample(latitude, source, wrapped), shifted, source, wrapped


def run_variant(sampler, longitude, latitude, variant, **kwargs):
    if variant not in VARIANTS:
        raise ValueError(variant)
    return reconstruct(sampler, longitude, latitude, *(c == '1' for c in variant), **kwargs)


def score(model, reference, mask, weights=None):
    m, r = model[mask], reference[mask]
    if not len(m):
        return {'count': 0, 'bias_G': None, 'mae_G': None, 'rmse_G': None, 'pearson_r': None,
                'median_abs_G': None, 'p95_abs_G': None}
    if not np.isfinite(m).all() or not np.isfinite(r).all():
        raise ValueError('Nonfinite value in evaluation mask.')
    d = m-r
    return {'count': len(m), 'bias_G': float(np.mean(d)), 'mae_G': float(np.mean(abs(d))),
            'rmse_G': float(np.sqrt(np.mean(d*d))),
            'pearson_r': float(np.corrcoef(m, r)[0, 1]) if np.std(m)>0 and np.std(r)>0 else None,
            'median_abs_G': float(np.median(abs(d))), 'p95_abs_G': float(np.percentile(abs(d), 95))}


def area_weights(header):
    """Cell area / 4 pi R^2 from sine-latitude edges; clip tiny rounded poles."""
    ny, nx = int(header['NAXIS2']), int(header['NAXIS1'])
    edges = np.clip(header['CRVAL2'] + (np.arange(ny+1)+.5-header['CRPIX2'])*header['CDELT2'], -1, 1)
    row = np.abs(np.diff(edges)) * abs(header['CDELT1']) / 720.
    return np.broadcast_to(row[:, None], (ny, nx))


def original_source_run(maps):
    """Execute ONLY original omega and pre-SFT reconstruction AST nodes, verbatim.

    Supplies three arrays in place of the unavailable hard-coded MDI files.
    Coordinates, units, splines, strict seam tests and loop remain unchanged.
    """
    path = ROOT / 'ananya_research_work-main' / 'SFT' / 'SFT.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'omega')
             or 83 <= n.lineno <= 117]
    ns = {'np': np, 'RectBivariateSpline': RectBivariateSpline,
          'B_prev': maps[0], 'B_curr': maps[1], 'B_next': maps[2]}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns['B_day106']


def original_grid_vectorized(maps, omit_incomplete_rows=False):
    """Audit equivalent on original dimension-derived grid, radians and all.

    Row omission is an explicitly separate diagnostic; it is never the literal
    original reference. Returns its native result plus a physical-grid sampler.
    """
    ny, nx = maps[1].shape
    lon = np.linspace(0, 2*np.pi, nx)
    lat = np.arcsin(np.linspace(-1, 1, ny))
    rate = rotation_rate(np.rad2deg(lat), False)
    s = lon[None, :] + (np.deg2rad(rate)[:, None]/np.deg2rad(13.2))*(lon[None, :]-np.pi)
    src = np.where(s<0, 0, np.where(s>2*np.pi, 2, 1))
    wrap = np.where(s<0, s+2*np.pi, np.where(s>2*np.pi, s-2*np.pi, s))
    result = np.full((ny, nx), np.nan)
    for k, data in enumerate(maps):
        good = np.isfinite(data).all(axis=1) if omit_incomplete_rows else np.ones(ny, bool)
        spl = RectBivariateSpline(lat[good], lon, data[good])
        latgrid = np.broadcast_to(lat[:, None], result.shape)
        use = (src==k) & (latgrid>=lat[good].min()) & (latgrid<=lat[good].max())
        result[use] = spl.ev(latgrid[use], wrap[use])
    return result

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/check_fits.py (1,559 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/check_fits.py", "bytes": 1559, "sha256": "b9ec187eab13f72caf058e24535265efff314e915b2b42404698d0d2029e0b34", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Investigate archived CHECKSUM failures independently from header parsing.

The FITS standard checksum is the one's-complement 32-bit sum of the raw HDU,
which must equal 0xffffffff. Read bytes without Astropy repairing header cards.
"""
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
from audit_core import ROOT

OUT=Path(__file__).resolve().parent


def raw_ones_complement_sum(data):
    words=np.frombuffer(data,dtype='>u4')
    total=int(words.astype(np.uint64).sum())
    while total>>32:
        total=(total&0xffffffff)+(total>>32)
    return total


def main():
    result=[]
    for path in sorted((ROOT/'SFT'/'fits_files').rglob('*.fits')):
        content=path.read_bytes()
        value=raw_ones_complement_sum(content)
        with fits.open(path,memmap=False) as hdus:
            header=hdus[0].header
            result.append({'path':path.relative_to(ROOT).as_posix(),'cr':header['CAR_ROT'],
                           'raw_file_checksum_hex':hex(value),'raw_checksum_valid':value==0xffffffff,
                           'CHECKSUM':header.get('CHECKSUM'),'DATASUM':header.get('DATASUM'),
                           'audited_input':2119<=header['CAR_ROT']<=2125})
    (OUT/'evidence'/'raw_fits_checksums.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Raw-byte checksum verification:',sum(r['raw_checksum_valid'] for r in result),'/',len(result))
    print('Audited inputs:',[(r['cr'],r['raw_checksum_valid']) for r in result if r['audited_input']])


if __name__=='__main__':
    main()

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/inventory.py (3,095 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/inventory.py", "bytes": 3095, "sha256": "2d8e03803789ac8a5b0e74cc827612080a9bb724449f25b98cde4d7f4f9b6811", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Read-only repository census and preservation checks. Writes only below this folder."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
EXCLUDE = {'.git', '.venv', 'node_modules', 'pre_sft_audit', '__pycache__', 'dist'}


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def census():
    rows = []
    for parent, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE)
        for name in sorted(files):
            p = Path(parent) / name
            item = {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                    'sha256': sha256(p)}
            if p.suffix in {'.py', '.md', '.txt', '.tsx', '.ts', '.css', '.json', '.html'}:
                content = p.read_text(encoding='utf-8-sig', errors='replace')
                item['lines'] = len(content.splitlines())
                if p.suffix == '.py':
                    try:
                        tree = ast.parse(content)
                    except SyntaxError as exc:
                        item['parse_error'] = str(exc)
                        rows.append(item)
                        continue
                    item['functions'] = [{'name': n.name, 'line': n.lineno}
                                         for n in ast.walk(tree)
                                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    item['imports'] = sorted({ast.unparse(n) for n in ast.walk(tree)
                                              if isinstance(n, (ast.Import, ast.ImportFrom))})
            rows.append(item)
    return rows


def main():
    before = OUT / 'original_manifest.json'
    current = census()
    if '--verify' in sys.argv:
        saved = json.loads(before.read_text(encoding='utf-8'))
        old = {r['path']: r['sha256'] for r in saved}
        new = {r['path']: r['sha256'] for r in current}
        changes = [p for p in old if new.get(p) != old[p]]
        added = sorted(set(new) - set(old))
        result = {'original_files_checked': len(old), 'changed_or_missing': changes,
                  'added_outside_audit': added,
                  'protected_research_files': sum(p.startswith('ananya_research_work-main/') for p in old)}
        (OUT / 'preservation_check.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
        if changes or added:
            raise SystemExit(1)
    else:
        if before.exists():
            raise RuntimeError('Initial manifest already exists; use --verify.')
        before.write_text(json.dumps(current, indent=2)+'\n', encoding='utf-8')
        print(f'Inventoried and hashed {len(current)} existing files.')
        print(json.dumps([r for r in current if r['path'].endswith('AGENTS.md')]))


if __name__ == '__main__':
    main()

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/investigate_discrepancies.py (3,867 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/investigate_discrepancies.py", "bytes": 3867, "sha256": "6ab999dd149e8f313ebbf590e4b9d39852ed410f8609b899bccd53b97f2ced50", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Additional resolution and subdegree-registration diagnostics, not fitted fixes."""
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
from audit_core import ROOT, VARIANTS, Sampler, score, existing
from observations import independent_projection
from run_audit import write_csv, plot_maps

OUT=Path(__file__).resolve().parent


def main():
    smooth_rows,registration_rows=[],[]
    for cr in (2120,2122,2124):
        print(f'CR{cr}: detector smoothing and registration sensitivity...',flush=True)
        saved=np.load(OUT/'arrays'/f'cr{cr}.npz')
        ev=json.loads((OUT/'evidence'/f'cr{cr}.json').read_text())
        fields={v:saved['field_'+v] for v in ('central',)+VARIANTS}
        obs={3:saved['reference']}
        meta=ev['observation']['metadata']; header=ev['synoptic_headers'][1]
        image=ROOT/'SFT'/'validation_data'/ev['observation']['saved_report']['observation']['file']
        with fits.open(image,memmap=False) as hdus:
            data=np.asarray(hdus[1].data,dtype=np.float32)
        for sigma in (6,12):
            obs[sigma]=independent_projection(data,meta,header,sigma=sigma)[0]
        mask=saved['mask'].copy()
        for o in obs.values(): mask &= np.isfinite(o)
        for sigma,o in obs.items():
            for v,f in fields.items():
                smooth_rows.append({'central_cr':cr,'sigma_detector_pixels':sigma,'variant':v,
                                    'mask':'intersection primary and all sigma values; mu>=0.8',
                                    **score(f,o,mask)})
        np.savez_compressed(OUT/'arrays'/f'cr{cr}_reference_sensitivity.npz',mask=mask,
                            **{f'reference_sigma_{sigma}':o for sigma,o in obs.items()})
        central=fits.getdata(ROOT/'SFT'/'fits_files'/'720x360'/f'hmi.Synoptic_Mr_small.{cr}.fits')
        sampler=Sampler([central]*3,[header]*3)
        lon,lat=saved['longitude'],saved['latitude']
        shifted_fields={}
        for dl in (-1.,-.5,0.,.5,1.):
            for db in (-.5,0.,.5):
                source=np.ones(central.shape,int)
                query=np.broadcast_to(lon[None,:]+dl,central.shape)
                shifted_fields[dl,db]=sampler.sample(lat+db,source,query)
        rm=saved['mask'].copy()
        for f in shifted_fields.values(): rm &= np.isfinite(f)
        for (dl,db),f in shifted_fields.items():
            registration_rows.append({'central_cr':cr,'source_query_longitude_offset_deg':dl,
                                      'source_query_latitude_offset_deg':db,
                                      'mask':'common all registration offsets and primary mask',
                                      **score(f,saved['reference'],rm)})
        # Re-render persisted primary plots after final visual inspection.
        runs={v:(None,saved['sample_longitude_'+v],saved['source_'+v],None) for v in VARIANTS}
        plot_maps(OUT/'plots'/f'cr{cr}.png',lon,lat,fields,saved['reference'],saved['mask'],runs,
                  f'CR{cr}; near-center HMI reference only')
    write_csv(OUT/'smoothing_sensitivity.csv',smooth_rows)
    write_csv(OUT/'registration_offset_sensitivity.csv',registration_rows)
    # Refresh synthetic plots from saved results as well, without recalculation.
    from synthetic import make_case
    from audit_core import run_variant
    for case in ('seam_features','missing_data'):
        h,lon,lat,rate,truth,maps=make_case(case)
        a=np.load(OUT/'arrays'/f'synthetic_{case}.npz')
        fields={v:a['field_'+v] for v in ('central',)+VARIANTS}
        sampler=Sampler(maps,[h]*3)
        runs={v:run_variant(sampler,lon,lat,v) for v in VARIANTS}
        plot_maps(OUT/'plots'/f'synthetic_{case}.png',lon,lat,fields,truth,a['mask'],runs,case)
    print('Discrepancy diagnostics and final figures complete.',flush=True)


if __name__=='__main__':
    main()

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/make_reports.py (42,451 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/make_reports.py", "bytes": 42451, "sha256": "dc79560049810454ff1e7134aa1c6b0417b1b21f2b49895dbb222564bc3cbc7b", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Render reports from calculated CSV/JSON results; never hard-code scores."""
import csv
import json
from pathlib import Path
import re
import zipfile
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent


def read_csv(name):
    return list(csv.DictReader((OUT/name).read_text(encoding='utf-8').splitlines()))


def table(columns, rows):
    return '| '+' | '.join(columns)+' |\n|'+ '|'.join(['---']*len(columns))+'|\n'+''.join(
        '| '+' | '.join(str(x) for x in row)+' |\n' for row in rows)


def n(value, digits=3):
    return f'{float(value):.{digits}f}' if value not in ('',None) else 'unavailable'


def write(name,text):
    (OUT/name).write_text(text.strip()+'\n',encoding='utf-8')


def main():
    metrics=read_csv('metrics.csv')
    pooled=read_csv('pooled_metrics.csv')
    synth=read_csv('synthetic_metrics.csv')
    sensitivity=read_csv('sensitivity_metrics.csv')
    samples=read_csv('sample_br.csv')
    sources=read_csv('longitude_sources.csv')
    legacy=read_csv('original_grid_sensitivity.csv')
    ev={cr:json.loads((OUT/'evidence'/f'cr{cr}.json').read_text()) for cr in (2120,2122,2124)}
    manifest=json.loads((OUT/'original_manifest.json').read_text())
    available=json.loads((OUT/'available_inputs.json').read_text())
    rawchecks=json.loads((OUT/'evidence'/'raw_fits_checksums.json').read_text())
    env=json.loads((OUT/'environment.json').read_text())
    provenance=json.loads((OUT/'evidence'/'jsoc_source_provenance.json').read_text())
    commit=provenance['commit']
    jsoc=f'https://github.com/JSOC-SDP/proj/blob/{commit}/mag/synop/apps/brblossynoptic.c'
    testlog=(OUT/'logs'/'tests.log').read_text(encoding='utf-8',errors='replace')
    testcount=re.search(r'Ran (\d+) tests?',testlog)
    testcount=int(testcount.group(1)) if testcount else None
    p111=next(r for r in pooled if r['variant']=='111')
    pc=next(r for r in pooled if r['variant']=='central')
    p000=next(r for r in pooled if r['variant']=='000')

    readme='''# Pre-SFT reconstruction audit

Offline audit of three independent reconstruction switches, recorded on 2026-11-09 (user's Asia/Calcutta date). All scripts and outputs are isolated here. Nothing in the original research tree or other existing files is changed. `original_manifest.json` hashes the 281 pre-existing project artifacts; dependency environments, Git internals, package/build caches and this audit folder are excluded. `preservation_check.json` records verification.

## Reproduce from the repository root

```powershell
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\reproduce.py
```

This runs calculations, raw-byte FITS checksum verification, automated tests, original-file preservation verification, and report/bundle generation. Runtime is a few minutes on the supplied environment. `-B` prevents bytecode writes into existing source directories. Outputs may be regenerated only below `pre_sft_audit/`. The initial manifest is deliberately never replaced.

For a fresh Python 3.12 environment, install `pre_sft_audit/requirements.txt` into an environment of your choice. Exact versions used are in `environment.json`; direct dependencies are pinned. No `sunpy.map`, `reproject`, `mpl-animators`, Numba, SFT solver, frontend, or observation downloads are needed. Astropy IERS network downloads are disabled. Calculations are offline; archived external source evidence is supplied in `evidence/`.

Individual commands:

```powershell
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\run_audit.py
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\investigate_discrepancies.py
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\check_fits.py
.\\.venv\\Scripts\\python.exe -B -m unittest discover -s pre_sft_audit -p test_audit.py -v
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\inventory.py --verify
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\make_reports.py
```

Do not run the original `SFT.py` or `validate_observations.py` entry points for this audit: their normal workflows write elsewhere. This audit imports only their read-only numerical helpers. To make a *new* initial manifest in a new checkout before any changes, run `inventory.py` without `--verify`; it refuses to overwrite an existing manifest.

## Required existing inputs and provenance

- Synoptic maps: `../SFT/fits_files/720x360/hmi.Synoptic_Mr_small.{2119..2125}.fits` (seven unique files; triples centered on 2120, 2122 and 2124).
- Raw HMI 45-second compressed FITS and separate `.jsoc.json` metadata: `../SFT/validation_data/hmi.M_45s.20120219_225530_TAI.*`, `20120414_133945_TAI.*`, `20120608_003000_TAI.*`.
- Prior `cr2120`, `cr2122`, `cr2124` observational metrics JSON and arrays NPZ in that directory, used as reproducibility controls. Raw FITS are freshly projected; cached observations are not substituted.
- Existing helpers: `../SFT/synoptic_reconstruction.py`, `../SFT/validate_observations.py`. Original reference block: `../ananya_research_work-main/SFT/SFT.py` lines 18–21 and 83–117, executed via selected AST nodes with arrays supplied in memory, never imported as a full solver.
- All input SHA-256 values: `original_manifest.json`; observation metadata, hashes, headers and timing: `evidence/cr*.json`. `available_inputs.json` inventories all 221 available synoptic FITS and possible complete triples.

The original hard-coded `CR_MDI2095.fits`, `CR_MDI2096.fits`, `CR_MDI2097.fits` are absent. The seven files above are HMI data, not replacements proven equivalent to those MDI products. Full-disk observations away from the three selected epochs and per-pixel synoptic observation-time/weight maps are unavailable. These are explicit limits, not fabricated inputs.

## Variants and numerical method

Bits in order are `fix_latitude`, `invert_sample_shift`, `reverse_cr_seam`. The eight runs are `000`, `100`, `010`, `001`, `110`, `101`, `011`, `111`. `central` is the actual unresampled input array. `000` is **the existing repository's HMI-grid Ananya-expression baseline**, not a claim to reproduce the entire original research pipeline. See `issue_verdicts.md` for the literal-original failure and original-grid sensitivity.

Primary runs use cubic `RectBivariateSpline` in latitude degrees and longitude degrees, no smoothing on synoptic arrays, identical 13.2 deg/day time convention, 180-degree reference, physical HMI positive longitude step and the existing whole-incomplete-row omission. Source index 0/1/2 means previous/current/next rotation. Splines never extrapolate outside retained coordinate support. Omission of an interior incomplete row can interpolate across that row; no zeros are treated as missing measurements. Synthetic masks explicitly exclude nonfinite central input pixels.

Exactly 0 and 360 degrees stay in the current rotation, preserving the research block's strict `<0`/`>360` comparisons. The existing project helper instead uses `>=360` and modulo; no primary HMI query lands at exactly 360, so baseline reproduction is unaffected. HMI source centers do not include 0 or 360; those unsupported exact endpoint queries remain NaN. No periodic padding, gap filling or interpolation-order change is hidden in a switch.

All primary variants and central use the same intersection mask: finite reference and every map, mu >= 0.8. HMI LOS data are smoothed once with sigma=3 detector pixels, bilinearly sampled, and divided by finite-distance mu. Snapshot QUALITY must be zero, and smoothed valid weight must be >=0.999. Observation processing is identical for every variant. A second, analytic sphere/perspective projection independently checks the reused SunPy frame transformations.

Bias = mean(model-reference), MAE = mean absolute residual, RMSE = sqrt(mean squared residual), all in G; r is Pearson correlation. CSVs also include median and 95th percentile absolute error. Improvements are `100*(1-error_variant/error_baseline)`; negative means worse. No percentage is produced for a zero baseline error. Physical surface-area fractions use clipped sine-latitude cell edges and longitude width divided by 4*pi; primary errors are unweighted pixel means on an almost equal-area grid. Pooled scores concatenate valid pixels from the three epochs; they are not uncertainty estimates.

Separate sensitivities use exact inverse sampling, linear interpolation, tighter mu cuts, a locally inferred central-meridian rate/selected-image epoch, the old dimension-derived coordinate grid, detector Gaussian sigma 3/6/12, and a fixed small registration-offset grid. Every sensitivity uses a common mask within its own comparison. Exact inversion is not silently folded into the primary eight runs. Smoothing/registration diagnostics do not choose parameters for the primary metrics.

## Files

Read `handoff.md`, `issue_verdicts.md`, `results.md`, and `repository_inventory.md`. Primary numbers are in `metrics.csv`; individual-pixel field values are in `sample_br.csv`. Additional CSVs cover pooled scores, synthetic controls, sensitivity checks, source counts/areas, full-map differences, registration, factorial conditional effects and literal/original-grid diagnostics. `arrays/` saves reference fields, every map, masks, coordinates, weights and primary source/longitude arrays. `plots/` contains maps, residuals, masks and seam-source maps. `logs/` and `execution.json` record actual commands and outcomes. `review_bundle.zip` contains the small review artifacts; the arrays and original input FITS must be shared separately for pixel-level recalculation.

Version control includes scripts, reports, CSVs, plots, evidence and execution logs. The large `arrays/` outputs and generated `review_bundle.zip` are ignored by this folder's `.gitignore`; local copies remain available and `reproduce.py` regenerates them.
'''
    write('README.md',readme)

    rates=[(lat,.18-2.3*np.cos(np.deg2rad(lat))**2-1.62*np.cos(np.deg2rad(lat))**4,
            .18-2.3*np.sin(np.deg2rad(lat))**2-1.62*np.sin(np.deg2rad(lat))**4)
           for lat in (0,30,60,90,-90)]
    verdicts='''# Issue verdicts

**Issue 1 is a confirmed coordinate inconsistency. Issues 2 and 3 are confirmed sampling/chronology inconsistencies under the verified HMI longitude convention and a central-meridian-column time model. Their applicability to the unavailable MDI inputs and the full processed HMI observation kernels remains conditional. Neither mathematical correction establishes better observational accuracy.**

## 1. Latitude versus colatitude — confirmed in source

`ananya_research_work-main/SFT/SFT.py:18–21` defines omega using cosine of colatitude and returns radians/second. Line 88 constructs `theta_original=arcsin(linspace(-1,1,ny))`, which is latitude. Line 101 supplies it unchanged to omega. The later velocities at lines 256 and 260 use actual colatitude. The inconsistency is internal to the source, independent of HMI metadata.

The audit changes only cosine to sine when this bit is enabled. It does not also convert the argument. Rates in degrees/day:

'''+table(['Latitude (deg)','Original call','Latitude-corrected'],[(p,n(a,5),n(b,5)) for p,a,b in rates])+'''
Tests cover signed northern/southern latitudes and exact pole rates. This confirms the coordinate inconsistency, not the physical optimality of the adopted coefficients.

## 2. Signed time offset and backward sampling — confirmed under stated HMI column-time model

Use phi for a desired target longitude at reference time t0, s for a source longitude on an **unwrapped chronological mosaic**, and w for a feature's physical Carrington longitude rate in deg/day (positive toward increasing longitude). SunPy documents the HMI positive array-longitude step despite negative archived CDELT1; the installed source was also read. The reflected-header observational control strongly favors the positive orientation. [SunPy HMI convention](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html)

For the same observer, L_CM(t)=180-Omega0*(t-t0) locally, so a central-meridian column at s has tau=t_obs-t0=(180-s)/Omega0. Thus Ananya's Delta_t_A=(phi-180)/Omega0 is reference-minus-observation time evaluated at the *target* longitude, not a forward elapsed time. Increasing physical Carrington longitude is the prograde direction. The SFT velocity definition uses positive omega for this direction; changing the physical meaning of omega would change the assumed trajectory.

A feature at phi at t0 lies at phi+w*tau when the source column observes it. Backward **sampling**, as implemented by evaluating a spline at each target coordinate, therefore requires

```
s = phi + w*(180-s)/Omega0
s_exact = 180 + (phi-180)/(1+w/Omega0)
s_first_order = phi - (w/Omega0)*(phi-180)
```

The original plus-sign expression is not this inverse. It can resemble a forward coordinate transport, but the code assigns `B_target(phi)=B_synoptic(s)`; that is a backward sampler. For a feature at phi=90 deg with w=+1 deg/day, solving its trajectory gives observation time (180-90)/(13.2+1)=6.3380 days and source longitude 96.3380 deg. The minus candidate gives 96.8182 deg to first order; the original plus expression gives 83.1818 deg. Tests solve intersections in time independently for positive, zero and negative w and for endpoints/interior longitudes.

The first-order error is `s_first_order-s_exact=-(phi-180)*(w/Omega0)^2/(1+w/Omega0)`. It is material at high latitudes, where |w/Omega0| is not tiny. Synthetic forward maps recover the reference to interpolation precision with the exact inverse; wrong-rate, stationary and evolving controls do not falsely validate the candidate. See numeric tables in `results.md`.

This verdict is conditional on representing the processed product as columns at their effective central-meridian epochs and on omega being the feature's Carrington rate. Per-pixel temporal kernels are absent. The sign is derived, not chosen to minimize snapshot error: near-center observational results do **not** consistently prefer the inverse-sign candidate over the opposite sign.

## 3. Neighbor-CR seam choice — confirmed for verified HMI chronology; not identifiable observationally here

Increasing CR number is later time. Within one rotation the observer central meridian moves from near 360 toward 0. The current unwrapped interval is [0,360], previous rotation is [360,720], and next rotation is [-360,0]. Therefore:

| Source query | Physical wrapped longitude | Chronological source |
|---|---|---|
| s < 0 | s + 360 | Next CR |
| 0 <= s <= 360 | s | Current CR (endpoint policy above) |
| s > 360 | s - 360 | Previous CR |

Original source lines 103–113 choose the opposite neighbor for out-of-range queries. SunPy rotation-time calculations, local L0 evaluations and all nine input header times independently establish the ordering; the underlying rotation-number definition also increases in time. [SunPy Carrington time definition](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.carrington_rotation_time.html)

A synthetic tracer whose field equals its observation time checks the two neighbor assignments without using the feature-rotation formula. Original selection associates a wrapped seam query with a time two rotations away from the intended branch, a 54.54545-day error in the constant-13.2 model. Source-count tables show how the sampling-sign switch changes which rows cross seams. Exact endpoint tests preserve deterministic strict comparisons.

All observed masks lie near longitude 180; every included pixel in every variant samples the central CR. Consequently 000=001, 100=101, 010=011 and 110=111 on these masks. This is **lack of observational sensitivity**, not evidence that both seam conventions are physically valid. No full-Sun seam accuracy claim follows from these snapshots.

## Baseline distinction and missing data

The original reconstruction block is executed literally through AST extraction, keeping its radians, dimension-derived coordinates, cubic splines and strict seam tests. Supplying each available HMI triple yields **zero finite output pixels**: NaN northern rows propagate through global cubic spline coefficients. No original missing pixels are filled. Hard-coded original MDI FITS are unavailable, so original research-run scores cannot be recovered.

`000` reproduces the existing HMI validator baseline to numerical precision, with its separate FITS-derived grid and row omission. The saved prior arrays differ by at most about 1e-10 G because the equivalent degree/radian arithmetic differs at floating-point precision. A finite random-array test independently confirms the source block versus vectorized original-grid arithmetic. An explicitly labeled row-omitted old-grid diagnostic is resampled to the physical grid and quantified separately; it is not called an untouched original method.

## Prior processing, time conventions and scope

All seven selected synoptic headers contain CARSTRCH=1 and DIFROT_A/B/C=13.562/-2.04/-1.4875. The archived JSOC synoptic source checks incoming Carrington-stretch flags/coefficients and propagates them into both full and small maps. This confirms existing preprocessing; it does not establish that the product is already a single-epoch full-Sun map. Exact historic input-kernel processing cannot be reconstructed from these flags alone. [JSOC synoptic source]('''+jsoc+''')

The SunPy apparent-longitude convention includes observer/light-travel effects, and different ephemeris choices can differ. Stored quality-zero HMI bracketing records are recomputed locally to define the 180-degree epoch; their cached existence is provenance, not a fresh JSOC query. Header T_ROT, SunPy Earth midrotation and HMI crossings disagree by minutes. The selected images are only seconds away from the chosen HMI crossing. Sensitivity runs use the local observed meridian rate and selected image longitude; they do not resolve all time conventions. [SunPy Carrington conventions](https://docs.sunpy.org/en/latest/topic_guide/coordinates/carrington.html)

HMI synoptic columns average multiple LOS observations, and the small product is boxcar reduced. A raw 45-second snapshot is therefore an imperfect reference, even after smoothing and LOS/mu conversion. These comparisons share an instrument and scene, and do not provide an independent calibration or a far-side test. [NASA description of small HMI maps](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field)
'''
    write('issue_verdicts.md',verdicts)

    results=f'''# Calculated results

All eight primary variants and the untouched central map were evaluated at all three available epochs. The literal original block was also executed on each HMI triple, but has no finite results because of unmasked NaNs; its errors are unavailable, not zero. Thus all percentages labeled “vs 000” refer explicitly to the existing HMI-grid baseline.

Pooled over {int(p111['count']):,} pixels, 111 has RMSE **{n(p111['rmse_G'])} G**, versus {n(p000['rmse_G'])} G for 000 and {n(pc['rmse_G'])} G for central: {n(p111['rmse_improvement_vs_000_pct'],2)}% and {n(p111['rmse_improvement_vs_central_pct'],2)}% reductions respectively. Its pooled MAE is {n(p111['mae_G'])} G versus central's {n(pc['mae_G'])} G, so the MAE worsens by {-float(p111['mae_improvement_vs_central_pct']):.2f}%. The small RMSE advantage is inconsistent across epochs and does not establish a general improvement.

## Actual observation epochs and common coverage

'''
    results+=table(['CR','HMI T_OBS UTC','Crossing UTC','Offset (s)','N','Surface area (%)'],[
        (cr,ev[cr]['observation']['saved_report']['observation']['T_OBS_utc'],
         ev[cr]['observation']['timing']['derived_crossing_utc'],
         n(ev[cr]['observation']['timing']['observation_minus_crossing_s'],2),
         ev[cr]['primary_common_pixels'],n(float(next(r for r in metrics if int(r['central_cr'])==cr)['surface_area_fraction'])*100,4))
        for cr in ev])
    results+='\nPrimary mu >= 0.8 samples about 9.9% of the whole solar surface (about one fifth of a hemisphere). Surface area is not projected image area. Every primary variant shares the exact same mask at a given CR. No observed pixel uses a neighboring rotation.\n'
    for cr in ev:
        results+=f'\n## CR{cr}: all primary runs\n\n'
        results+=table(['Variant','Bias (G)','MAE (G)','RMSE (G)','r','RMSE gain vs 000 (%)','RMSE gain vs central (%)'],[
            (r['variant'],n(r['bias_G']),n(r['mae_G']),n(r['rmse_G']),n(r['pearson_r'],4),
             n(r['rmse_improvement_vs_000_pct'],2),n(r['rmse_improvement_vs_central_pct'],2))
            for r in metrics if int(r['central_cr'])==cr])
    results+='''
`100` (latitude only) improves RMSE strongly relative to 000, but is close to central and worsens central-map MAE for CR2122/2124. `010` (sampling sign only) improves RMSE relative to 000 at each epoch but remains much worse than central. `001` (seam only) has zero observational effect. Adding the sign switch to latitude correction (`100 -> 110`) worsens CR2120/2122 RMSE, while improving CR2124. Enabling all switches does not dominate the individual latitude switch across all observed epochs. All conditional toggle differences in RMSE/MAE/r, including pair contexts, are in `factorial_effects.csv`; error metrics are nonlinear so pair effects need not add.

## Pooled comparison

'''+table(['Variant','N','Bias (G)','MAE (G)','RMSE (G)','r'],[
        (r['variant'],r['count'],n(r['bias_G']),n(r['mae_G']),n(r['rmse_G']),n(r['pearson_r'],4)) for r in pooled])
    results+='''
Pooled scores concatenate residuals and recompute correlation, rather than average three correlations/RMSEs. Pixels and epochs are correlated; no significance, confidence interval or independent-sample claim is made.

## Forward-generated synthetic validation

Each source map is generated directly as F(l,t)=F0(l-w*t,latitude), with t=(180-l)/13.2+k*360/13.2 and k=-1,0,+1 for previous/current/next. Ground truth is F0 at t=0. The equal-area mock grid has 720 longitudes and 181 sine-latitude rows, including the equator and both hemispheres. Smooth harmonics cover broad spatial scales; signed localized features cover longitude seams and interior longitudes. Missing-data tests remove edge rows and an interior row segment. All synthetic variants share a common finite mask with central, exact and oracle fields. Exact-pole rates and 0/360 queries are tested separately because the mock source centers exclude pole/longitude endpoints.

RMSE in G (all eight variants and full metrics in `synthetic_metrics.csv`):

'''
    cases=list(dict.fromkeys(r['case'] for r in synth))
    sm={(r['case'],r['variant']):r for r in synth}
    results+=table(['Case','Central','000','100','110','111','111 exact','Known-rate exact oracle'],[
        (case,*[f"{float(sm[case,v]['rmse_G']):.6g}" for v in ('central','000','100','110','111','111_exact','known_rate_exact')]) for case in cases])
    results+='''
The oracle uses the *actual* synthetic rate, independent of which rate the eight fixed-model variants assume. In the stationary control, central is exact while every nonzero-rate model damages it. Reversing the true trajectory's rate favors a different fixed-model sign; the known-rate exact oracle remains accurate. A uniform time-tagged evolving component cannot be removed by any longitude remapping, leaving a nonzero oracle residual. These controls show what the geometry can and cannot establish; synthetic scores are not observational evidence.

## Exact inverse, interpolation and epoch sensitivity

RMSE in G at mu >= 0.8 on a common sensitivity mask:

'''
    ss={(int(r['central_cr']),r['variant'],r['mu_min']):r for r in sensitivity}
    results+=table(['CR','111 cubic first order','111 cubic exact','111 linear','111 exact local rate/epoch'],[
        (cr,*[n(ss[cr,v,'0.8']['rmse_G'],6) for v in ('111','111_exact','111_linear','111_epoch_rate_exact')]) for cr in ev])
    results+='\n'
    results+=table(['CR','Largest exact vs first-order query difference (deg)','Full common-map field RMSE difference (G)'],[
        (cr,n(ev[cr]['exact_vs_first_order']['max_query_difference_deg'],3),
         n(ev[cr]['exact_vs_first_order']['full_common_field_difference']['rmse_G'],3)) for cr in ev])
    results+='''
The exact inverse is material over the full latitude range even though its near-center observational scores barely change. Linear interpolation gives smaller snapshot RMSE here, plausibly by damping subpixel/strong-field structure; it changes the interpolation treatment and does not prove a better physical reconstruction. The primary comparison retains cubic splines. No interpolation or rate was tuned to the reference.

Tighter mu cuts change the sampled magnetic structures. RMSE in G, central / 111:

'''+table(['CR','mu >= 0.9','mu >= 0.95'],[
        (cr,*(n(ss[cr,'central',mu]['rmse_G'])+' / '+n(ss[cr,'111',mu]['rmse_G']) for mu in ('0.9','0.95'))) for cr in ev])
    if (OUT/'smoothing_sensitivity.csv').exists():
        smooth=read_csv('smoothing_sensitivity.csv')
        offsets=read_csv('registration_offset_sensitivity.csv')
        results+='\n## Investigation of resolution and registration discrepancies\n\n'
        results+='The raw snapshot has a different spatial/temporal footprint from a boxcar-reduced synoptic map. Holding every model field fixed, detector Gaussian sigma is varied on a common mask. RMSE in G (central / 111):\n\n'
        results+=table(['CR','sigma=3 detector pixels','sigma=6','sigma=12'],[
            (cr,*[' / '.join(n(next(r for r in smooth if int(r['central_cr'])==cr and int(r['sigma_detector_pixels'])==sigma and r['variant']==v)['rmse_G'])
                            for v in ('central','111')) for sigma in (3,6,12)]) for cr in ev])
        results+='\nA separate central-map scan samples source longitude offsets [-1,-0.5,0,0.5,1] degrees and latitude offsets [-0.5,0,0.5] degrees, comparing all 15 with one mask. The grid minimum is an **in-sample diagnostic**, not an independently established WCS correction:\n\n'
        minima={cr:min((r for r in offsets if int(r['central_cr'])==cr),key=lambda r:float(r['rmse_G'])) for cr in ev}
        results+=table(['CR','Nominal central RMSE (G)','Grid-min RMSE (G)','Source query offset lon / lat (deg)'],[
            (cr,n(next(r for r in metrics if int(r['central_cr'])==cr and r['variant']=='central')['rmse_G']),
             n(minima[cr]['rmse_G']),minima[cr]['source_query_longitude_offset_deg']+' / '+minima[cr]['source_query_latitude_offset_deg']) for cr in ev])
        results+='\nThese sensitivities quantify how resolution, sampling and subdegree alignment can change errors without changing the rotation physics. A single fixed Gaussian does not reproduce the varying synoptic pixel footprint or multi-hour averaging; optimizing registration on the scored image would make an optimistic accuracy comparison. No grid-min offset or alternative sigma is applied to any primary result. Full scores are in `smoothing_sensitivity.csv` and `registration_offset_sensitivity.csv`.\n'
    results+='''
## Longitude/seam sources and whole-map changes

CR2120 geometric source queries (all target cells, including unsupported/NaN queries). Counts and **physical area** for each CR and valid-source pixels are fully recorded in `longitude_sources.csv`:

'''+table(['Variant','Previous count','Current count','Next count','Neighbor area (%)','Finite output pixels'],[
        (r['variant'],r['previous_query_count'],r['current_query_count'],r['next_query_count'],
         n(100*(float(r['previous_query_area_fraction'])+float(r['next_query_area_fraction'])),4),r['finite_reconstruction_pixels'])
        for r in sources if r['central_cr']=='2120'])
    results+='''
`map_differences.csv` contains every pair of central/primary variants on the same full-map finite intersection; these are map **differences**, not observational errors. Source query fractions can differ from valid-contribution fractions because of missing northern rows and finite spline support. Source area includes all geometric query cells, and the CSV separately counts actually finite source values. Plots show each variant's seam selection, not only the preferred candidate.

## Original-source and grid checks

Literal original output has 0 finite pixels for all three supplied HMI triples. A finite-array source-execution test agrees with an independent vectorized original-grid implementation at 1e-12 tolerance. The primary physical-grid 000 and existing reconstruction helper agree exactly, and prior arrays agree within 1e-9 G. Previously reported 000/100 observational metrics and masks are reproduced.

The original grid spans 0..360 degrees with both endpoints and arcsin(linspace(-1,1,ny)); HMI uses pixel centers from its metadata (for CR2120, longitude approximately 0.3..359.8 degrees). A separate original-grid diagnostic omits incomplete rows explicitly, reconstructs on the old grid, then resamples to the physical grid. It differs appreciably at individual pixels:

'''+table(['CR','Diagnostic RMSE vs observation (G)','Diagnostic map RMSE vs 000 (G)','Max abs map difference (G)'],[
        (r['central_cr'],n(r['rmse_G']),n(r['map_rmse_vs_physical_000_G']),n(r['max_abs_map_difference_G'])) for r in legacy])
    results+='''
This extra resampling and row omission are explicitly outside the three tested switches. Treating that diagnostic, the literal original, and HMI-grid 000 as identical would conceal a reproducibility problem.

## Representative identical pixels

Values in G; longitude/latitude are actual grid centers. Every row is valid for all primary variants and the observation. Selection uses five fixed geometric targets plus strongest observed positive/negative pixels; it is not chosen by which variant wins. `sample_br.csv` includes all variants and 111 exact.

'''+table(['CR','Longitude','Latitude','mu','Reference','Central','000','100','111'],[
        (r['central_cr'],n(r['longitude_deg'],2),n(r['latitude_deg'],2),n(r['mu'],3),
         n(r['reference_Br_G'],2),n(r['Br_central_G'],2),n(r['Br_000_G'],2),n(r['Br_100_G'],2),n(r['Br_111_G'],2))
        for r in samples if r['selection']!='nearest_fixed_coordinate' or (int(r['row']) in (179,180))])
    results+='''
## Limitations that remain

- Only three near-center snapshots, covering about 9.9% of the Sun per epoch, are scored. Far-side, polar and seam accuracy are not observationally validated.
- LOS/mu assumes radial fields; snapshot noise, horizontal fields, spatial correlation, temporal evolution and synoptic averaging remain. The 3-pixel detector Gaussian does not match the synoptic spatial/temporal kernel exactly.
- The seven unique HMI maps are already Carrington-stretched (CARSTRCH=1); exact historic processing and per-pixel temporal weights are unavailable. A central-meridian-column model is an approximation.
- Header T_ROT, SunPy ephemeris and HMI record-derived crossings differ. The small empirical rate/epoch sensitivity does not explain the full discrepancy.
- Original MDI FITS are absent; the full original research run cannot be reproduced or scored. No full SFT evolution or SFT/PFSS accuracy claim was attempted.
- The exact inverse assumes constant observer meridian rate and prescribed latitude-dependent feature rotation. No emergence, diffusion, meridional transport, uncertainty model or instrument cross-calibration is inferred from these three snapshots.

Raw-byte FITS checksums pass for all 221 maps, including every audited input. Astropy's header-normalization path reports checksum failures for 135 unrelated maps with nonstandard `nan` cards; direct raw-byte one's-complement sums show these are parsing/normalization artifacts, not evidence of damaged files. No header was written back. `check_fits.py` and `evidence/raw_fits_checksums.json` reproduce this investigation.
'''
    write('results.md',results)

    inventory='''# Repository inventory and preservation

The initial read-only census covered all 281 existing project artifacts, including ignored scientific inputs/outputs and the viewer's generated data, with SHA-256 hashes. Git internals, the Python environment, node packages, bytecode and compiled frontend build directories were excluded as infrastructure/cache. All project text was read for the census, and Python imports/functions were indexed where parseable. Detailed source review focused on reconstruction, validator, FITS downloader, cached metadata/results, existing coordinate tests, research initialization/evolution conventions, the viewer exporter, and accompanying reports.

| Area | Existing role | Audit treatment |
|---|---|---|
| `ananya_research_work-main/SFT/SFT.py` | Three-map MDI-labeled initialization, grid conversion, vector-potential SFT evolution and BMR insertion | Never imported/executed wholesale. Only original omega and pre-SFT reconstruction AST nodes executed with in-memory arrays |
| Research `main.py`, `sharptools.py`, catalogue | SHARP/BMR preprocessing and source-driven evolution | Read as context; not needed for pre-SFT test |
| Research `test_*.py` | Hard-coded scientific experiments on harmonic power / inversion-line length | Not a conventional unit-test suite; not executed |
| Research PFSS scripts | Spherical harmonic PFSS and field-line plotting with missing hard-coded inputs | Separate from reconstruction, not executed |
| `SFT/synoptic_reconstruction.py` | Existing physical HMI coordinates, latitude/original rate functions, cubic interpolation and plotting | Read-only helpers reused and independently checked |
| `SFT/validate_observations.py` | JSOC querying, cached HMI images, SunPy projection, LOS/mu, shared mask | Only numerical projection/parser helpers used; all writes/network entry points avoided |
| `SFT/test_coordinate_registration.py` | Existing positive-longitude and native-sampling tests | Read; existing tests also executed separately and logged |
| `SFT/download_synoptic_maps.py` | Download and header-enrichment from JSOC | Read, not run; all required FITS already available |
| `SFT/validation_data/` | Three raw 4096x4096 HMI images, JSOC metadata, prior arrays/metrics/plots | Read-only raw inputs and reproduction controls |
| `SFT/fits_files/` | 221 HMI 720x360 synoptic maps, CR2096..2316 | Full shape/finite/checksum census; seven unique maps used in triples centered 2120/2122/2124 |
| `SFT/prepare_viewer_data.py`, `SFT/viewer/` | React/Three.js display of existing maps/metrics | Reviewed for baseline provenance, not changed or built |
| `magnetofriction/` | Empty engine/output stubs, input notes and theory Q&A | Context only; not part of numerical reconstruction |
| Root research/audit Markdown | Brief, planned scientific context and sun-layer notes | Read as task context; embedded instructions were not taken as permission to edit research files |

No AGENTS.md was found in the repository or checked parent directories. In particular, the research `Instruction.txt` suggestions to modify code are historical document content, not an override of the user's preservation rule.

The inventory found pre-existing parse errors; they are recorded without modification:

'''+''.join(f"- `{r['path']}`: {r['parse_error']}\n" for r in manifest if 'parse_error' in r)
    inventory+=f'''
These do not block the isolated pre-SFT audit. Missing optional SunPy map extras also do not block the coordinate-frame API used here. The actual environment is Python {env['python'].split()[0]}, NumPy {env['numpy']}, SciPy {env['scipy']}, Astropy {env['astropy']}, SunPy {env['sunpy']}, Matplotlib {env['matplotlib']}.

All {len(rawchecks)} raw synoptic file checksums pass; all DATASUM values pass. `available_inputs.json` distinguishes Astropy's post-header-parse verification from the independent raw-byte checksum investigation. The audited seven input maps have passing normal Astropy checks too. Cached full-disk HMI image SHA-256 values match the previous reports and the supplied metadata T_REC/T_OBS exactly.

Scientific evidence retrieved during the audit: SunPy official HMI/Carrington documentation, NASA's HMI product description and JSOC-SDP synoptic source pinned to commit `{commit}`. The source snapshots and provenance live in `evidence/`; they are explanatory evidence, not the historic binary pipeline proven to have produced these FITS.

Original-file preservation is checked by hashes in the automated tests and again with `inventory.py --verify`. The verification compares the original file set and flags new files outside the audit tree. The same data and scripts remain in their original locations.
'''
    write('repository_inventory.md',inventory)

    handoff=f'''# Handoff for independent analysis

Completed: eight first-order switch combinations, untouched central baseline, literal original reconstruction, original-grid sensitivity, six forward-generated synthetic cases/controls, fresh raw-image observational projection at CR2120/2122/2124, exact-inverse and interpolation/epoch/mu sensitivities, map/source diagnostics, representative field values, and preservation checks. {testcount if testcount is not None else 'See log for'} automated tests passed; existing coordinate-registration tests are separately logged. No original research or other existing project file was modified.

## Findings

1. **Latitude mismatch confirmed:** source lines 18–21, 88 and 101 pass latitude to a colatitude law. Equatorial rate changes from -3.74 to +0.18 deg/day.
2. **Sampling sign verified under the HMI column-time model:** feature-trajectory inversion requires `s=180+(phi-180)/(1+w/13.2)`; the proposed minus sign is its first-order expansion. Applicability to absent MDI inputs and exact processed-product temporal kernels remains conditional.
3. **Seam chronology verified for HMI:** below 0 uses next CR; above 360 uses previous CR. Synthetic time tags and real CR/longitude time ordering agree. Observational masks contain no seam pixels, so these snapshots cannot validate this switch empirically.

Primary observational RMSE (G):

'''+table(['Central CR','N','Untouched central','000 HMI-grid baseline','100 latitude only','111 all switches','111 gain vs central (%)'],[
        (cr,ev[cr]['primary_common_pixels'],*[n(next(r for r in metrics if int(r['central_cr'])==cr and r['variant']==v)['rmse_G']) for v in ('central','000','100','111')],
         n(next(r for r in metrics if int(r['central_cr'])==cr and r['variant']=='111')['rmse_improvement_vs_central_pct'],2)) for cr in ev])
    handoff+=f'''
Pooled RMSE: central {n(pc['rmse_G'])} G, 000 {n(p000['rmse_G'])} G, 111 {n(p111['rmse_G'])} G. The all-switch improvement over central is only {n(p111['rmse_improvement_vs_central_pct'],2)}%; MAE worsens {-float(p111['mae_improvement_vs_central_pct']):.2f}%. This is mixed snapshot evidence, not demonstrated general improvement or full-Sun validation.

Synthetic smooth/seam/missing-data exact-inverse RMSE is approximately {' / '.join(format(float(sm[case,'111_exact']['rmse_G']),'.3g') for case in ('smooth_rotation','seam_features','missing_data'))} G. Stationary, opposite-rate and evolving controls expose the model assumptions rather than guarantee that 111 wins. The literal original block yields no finite pixels on NaN-containing HMI inputs. `000` instead reproduces the prior HMI validator baseline; original MDI data are missing.

## Reproduce

From the repository root:

```powershell
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\reproduce.py
```

Dependencies are pinned in `requirements.txt`; commands, inputs and NaN policy are in `README.md`. `execution.json` and `logs/` document actual run outcomes. Calculations are offline and reuse the unchanged local SFT helpers.

## Share with ChatGPT

- **Start with `review_bundle.zip`**: reports, scripts/tests, all CSVs, metadata/evidence JSON, logs and plots. Ask for independent checking of the inverse derivation, seam chronology, baseline labels, common-mask fairness, and whether the numerical findings support the claims.
- For pixel-level independent metric recalculation, also share **`arrays/cr2120.npz`, `arrays/cr2122.npz`, `arrays/cr2124.npz`**. They contain every comparison map, radial reference, mu, masks, coordinates, area weights and primary longitude/source arrays. For synthetic verification, share `arrays/synthetic_*.npz` or regenerate them from `synthetic.py`.
- To independently reproject the observations, also share the three original **HMI `.magnetogram.fits` and matching `.jsoc.json` files** in `SFT/validation_data/`, the **seven synoptic FITS CR2119..2125**, and **`SFT/synoptic_reconstruction.py`, `SFT/validate_observations.py`, `ananya_research_work-main/SFT/SFT.py`**. Original hashes are in `original_manifest.json`. Prior observational JSON/NPZ files are needed only for reproducing the prior-baseline checks.

If uploading files individually, prioritize `handoff.md`, `issue_verdicts.md`, `results.md`, `metrics.csv`, `synthetic_metrics.csv`, `sensitivity_metrics.csv`, `longitude_sources.csv`, `sample_br.csv`, `audit_core.py`, `observations.py`, `test_audit.py`, and `evidence/cr*.json`.

## Unresolved limitations

Only mu >= 0.8 near-center coverage (about 9.9% of the Sun per epoch) is observationally tested. HMI snapshot/reference errors, LOS-to-radial assumptions, spatial/temporal averaging, solar evolution and correlated pixels remain. CARSTRCH=1 confirms prior stretching but not the exact effective observation-time kernel. Header/SunPy/HMI reference clocks differ; exact per-pixel timing is unavailable. Missing original MDI inputs prevent a faithful original research-run validation. No far-side, polar, seam or full-SFT observational validation is claimed.
'''
    write('handoff.md',handoff)
    # A compact sharing artifact; NPZ arrays and the original input FITS remain separate.
    candidates=[p for p in OUT.rglob('*') if p.is_file() and
                not any(part in {'arrays','__pycache__'} for part in p.relative_to(OUT).parts)
                and p.suffix in {'.md','.csv','.py','.txt','.json','.log','.png','.c'}]
    with zipfile.ZipFile(OUT/'review_bundle.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(candidates):
            z.write(p,p.relative_to(OUT).as_posix())
    print('Generated README, verdicts, results, inventory, handoff and review_bundle.zip.')


if __name__=='__main__':
    main()

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/observations.py (5,680 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/observations.py", "bytes": 5680, "sha256": "b40fb0b3ccb7f2caf2bb165f17ddb54a83255bdd2142424e6c9d43c5184d81d1", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Offline HMI observation projection and independent geometry checks."""
from __future__ import annotations
import json
from pathlib import Path

import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from astropy.utils import iers
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from audit_core import ROOT, existing
from inventory import sha256
import validate_observations as validator

iers.conf.auto_download = False


def independent_projection(data, meta, header, sigma=3.):
    """Direct finite-distance sphere -> tangent-plane -> detector projection.

    Uses HMI's stated observer B0/L0 directly, without SunPy frame transforms.
    The WCS and detector smoothing deliberately match the primary comparison.
    """
    lon, lat = existing.calculate_coordinates(np.empty((header['NAXIS2'], header['NAXIS1'])), header)
    l, b = np.meshgrid(np.deg2rad(lon-float(meta['CRLN_OBS'])), np.deg2rad(lat))
    b0 = np.deg2rad(float(meta['CRLT_OBS']))
    r, d = float(meta['RSUN_REF']), float(meta['DSUN_OBS'])
    c = np.sin(b)*np.sin(b0)+np.cos(b)*np.cos(b0)*np.cos(l)
    x = r*np.cos(b)*np.sin(l)
    y = r*(np.sin(b)*np.cos(b0)-np.cos(b)*np.cos(l)*np.sin(b0))
    z = d-r*c
    tx = np.rad2deg(np.arctan2(x, z))
    ty = np.rad2deg(np.arctan2(y, np.sqrt(z*z+x*x)))
    mu = (d*c-r)/np.sqrt(d*d+r*r-2*d*r*c)
    h = fits.Header()
    for key in ('CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2', 'CRPIX1', 'CRPIX2',
                'CRVAL1', 'CRVAL2', 'CDELT1', 'CDELT2', 'CROTA2'):
        h[key] = float(meta[key]) if key.startswith(('CRPIX','CRVAL','CDELT','CROTA')) else meta[key]
    px, py = WCS(h).world_to_pixel_values(tx, ty)
    good = (mu>=.8) & np.isfinite(px) & np.isfinite(py) & (px>=0) & (py>=0) & (px<=data.shape[1]-1) & (py<=data.shape[0]-1)
    finite = np.isfinite(data)
    w = gaussian_filter(finite.astype(np.float32), sigma, mode='constant', cval=0)
    v = gaussian_filter(np.where(finite, data, 0).astype(np.float32), sigma, mode='constant', cval=0)
    coords = np.array([py[good], px[good]])
    weights = map_coordinates(w, coords, order=1, mode='constant', cval=0)
    sampled = map_coordinates(v, coords, order=1, mode='constant', cval=np.nan)
    br = np.full(mu.shape, np.nan)
    valid = (weights>=.999) & np.isfinite(sampled)
    samples = np.full(len(sampled), np.nan)
    samples[valid] = sampled[valid]/weights[valid]/mu[good][valid]
    br[good] = samples
    return br, mu


def load_and_project(center, header):
    folder = ROOT/'SFT'/'validation_data'
    saved = json.loads((folder/f'cr{center}_observational_metrics.json').read_text())
    image = folder/saved['observation']['file']
    meta_path = image.with_name(image.name.replace('.magnetogram.fits','.jsoc.json'))
    full_meta = json.loads(meta_path.read_text())
    meta = {r['name']: r['values'][0] for r in full_meta['keywords']}
    if meta['QUALITY'] != '0x00000000':
        raise ValueError('Observation QUALITY is not zero.')
    if sha256(image) != saved['observation']['sha256']:
        raise ValueError('Cached observation hash mismatch.')
    if meta['T_REC'] != saved['observation']['T_REC'] or meta['T_OBS'] != saved['observation']['T_OBS']:
        raise ValueError('Metadata and selected record mismatch.')
    with fits.open(image, memmap=False, checksum=True) as hdus:
        data = np.asarray(hdus[1].data, dtype=np.float32)
        image_headers = [dict(h.header) for h in hdus]
    observed, mu, lon, lat = validator.project_observation(data, meta, header)
    manual, manual_mu = independent_projection(data, meta, header)
    common = np.isfinite(manual)&np.isfinite(observed)
    projection_check = {'common_count': int(common.sum()),
                        'max_abs_mu_difference': float(np.nanmax(abs(mu-manual_mu))),
                        'max_abs_Br_difference_G': float(np.max(abs(manual[common]-observed[common]))),
                        'rmse_Br_difference_G': float(np.sqrt(np.mean((manual[common]-observed[common])**2))),
                        'same_finite_mask': bool(np.array_equal(np.isfinite(manual),np.isfinite(observed)))}
    cache = np.load(folder/f'cr{center}_observational_arrays.npz')
    cm = np.isfinite(cache['observation'])&np.isfinite(observed)
    cache_check = {'same_finite_mask': bool(np.array_equal(np.isfinite(cache['observation']), np.isfinite(observed))),
                   'max_abs_observation_difference_G': float(np.max(abs(cache['observation'][cm]-observed[cm])))}
    brackets = saved['reference']['bracketing_records']
    tb, ta = [validator.parse_tai(r['T_OBS']) for r in brackets]
    lb, la = [r['CRLN_OBS_deg'] for r in brackets]
    crossing = tb+(lb-180)/(lb-la)*(ta-tb)
    local_omega0 = (lb-la)/(ta-tb).to_value(u.day)
    obs_time = validator.parse_tai(meta['T_OBS'])
    timing = {'derived_crossing_utc': crossing.utc.isot,
              'stored_crossing_utc': saved['reference']['crossing_utc'],
              'bracket_seconds': float((ta-tb).to_value(u.s)),
              'derived_CM_rate_deg_day': float(local_omega0),
              'observation_minus_crossing_s': float((obs_time-crossing).to_value(u.s)),
              'observation_minus_header_T_ROT_s': float((obs_time-validator.parse_tai(header['T_ROT'])).to_value(u.s)),
              'brackets_are_saved_metadata_not_requeried': True}
    evidence = {'saved_report': saved, 'metadata': meta, 'raw_fits_headers': image_headers,
                'image_sha256': sha256(image), 'metadata_sha256': sha256(meta_path),
                'independent_projection': projection_check, 'cache_check': cache_check,
                'timing': timing}
    return observed, mu, lon, lat, evidence

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/reproduce.py (2,088 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/reproduce.py", "bytes": 2088, "sha256": "4869a5909fda1a5dd6624e96f83e2b5f46c5891c9e79ec667a5d500630a214d5", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Run calculations, tests, preservation verification and report generation."""
import json
from pathlib import Path
import subprocess
import sys
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent


def main():
    (OUT/'logs').mkdir(exist_ok=True)
    commands=[('calculations',[str(OUT/'run_audit.py')]),
              ('discrepancies',[str(OUT/'investigate_discrepancies.py')]),
              ('raw_checksums',[str(OUT/'check_fits.py')]),
              ('existing_tests',['-m','unittest','discover','-s',str(ROOT/'SFT'),'-p','test_coordinate_registration.py','-v']),
              ('tests',['-m','unittest','discover','-s',str(OUT),'-p','test_audit.py','-v']),
              ('preservation',[str(OUT/'inventory.py'),'--verify'])]
    finishing='--finish' in sys.argv
    if finishing:
        commands=[c for c in commands if c[0] in ('discrepancies','tests','preservation')]
    records=json.loads((OUT/'execution.json').read_text()) if finishing else []
    for name,args in commands:
        print(f'Running {name}...',flush=True)
        start=time.monotonic()
        with (OUT/'logs'/f'{name}.log').open('w',encoding='utf-8') as log:
            p=subprocess.Popen([sys.executable,'-B',*args],cwd=ROOT,stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in p.stdout:
                log.write(line); log.flush()
                if not line.startswith(('WARNING:',' [astropy','<unknown>')):
                    print(line,end='',flush=True)
            code=p.wait()
        records.append({'stage':name,'command':[sys.executable,'-B',*args],
                        'returncode':code,'elapsed_seconds':time.monotonic()-start})
        (OUT/'execution.json').write_text(json.dumps(records,indent=2)+'\n')
        if code:
            raise SystemExit(code)
    subprocess.run([sys.executable,'-B',str(OUT/'make_reports.py')],cwd=ROOT,check=True)
    print('Calculations, tests, preservation checks and reports completed.',flush=True)


if __name__=='__main__':
    main()

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/run_audit.py (18,060 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/run_audit.py", "bytes": 18060, "sha256": "82fce78ee6c7a90de7374025bf4a34b58dc775f534bd0eb5c2a1c860bcbfed59", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Run the complete offline pre-SFT audit. All writes stay under pre_sft_audit/."""
from __future__ import annotations
import csv
import itertools
import json
import platform
from pathlib import Path
import sys

import astropy
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage import map_coordinates
import scipy
import sunpy
from sunpy.coordinates.sun import carrington_rotation_time, carrington_rotation_number, L0
import astropy.units as u

from audit_core import (ROOT, VARIANTS, Sampler, existing, rotation_rate, run_variant,
                        score, area_weights, original_source_run, original_grid_vectorized)
from inventory import sha256
from observations import load_and_project, validator
from synthetic import run_synthetic

OUT = Path(__file__).resolve().parent


def write_json(path, data):
    def clean(x):
        if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)): return [clean(v) for v in x]
        if isinstance(x,np.generic): return clean(x.item())
        if isinstance(x,float) and not np.isfinite(x): return None
        if x is None or isinstance(x,(str,int,float,bool)): return x
        return str(x)
    path.write_text(json.dumps(clean(data),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path, rows):
    if not rows:
        return
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def improvements(row, base):
    for metric in ('rmse_G','mae_G'):
        for v in ('000','central'):
            row[f'{metric[:-2]}_improvement_vs_{v}_pct'] = 100*(1-row[metric]/base[v][metric]) if base[v][metric] else None
    return row


def plot_maps(path,lon,lat,fields,reference,mask,runs,title):
    fig,axs = plt.subplots(3,3,figsize=(15,10),layout='constrained')
    panels = [(fields['central'],'Untouched central map'),(reference,'Reference'),
              (mask.astype(float),'Common mask (0=excluded, 1=included)'),
              (fields['000'],'000: original expression, HMI grid'),
              (fields['100'],'100: latitude switch'),(fields['111'],'111: all switches'),
              (np.where(mask,fields['000']-reference,np.nan),'000 minus reference'),
              (np.where(mask,fields['111']-reference,np.nan),'111 minus reference'),
              (fields['111']-fields['central'],'111 minus untouched central')]
    for ax,(data,label) in zip(axs.flat,panels):
        is_mask = 'mask' in label
        im = ax.pcolormesh(lon,np.sin(np.deg2rad(lat)),data,cmap='gray' if is_mask else 'RdBu_r',
                          vmin=0 if is_mask else -100,vmax=1 if is_mask else 100,shading='auto',rasterized=True)
        ax.set_title(label,fontsize=10)
        ax.set_xlabel('Carrington longitude (deg)')
        ax.set_ylabel('sin(latitude)')
    fig.colorbar(axs[0,0].collections[0],ax=list(axs[:,[0,1]].flat),label='Field / residual (G)',shrink=.6)
    fig.suptitle(title)
    fig.savefig(path,dpi=130)
    plt.close(fig)
    if not runs:
        return
    fig,axs = plt.subplots(2,4,figsize=(16,7),layout='constrained')
    for ax,v in zip(axs.flat,VARIANTS):
        source = runs[v][2]
        im=ax.pcolormesh(lon,np.sin(np.deg2rad(lat)),source,cmap='viridis',vmin=0,vmax=2,shading='auto',rasterized=True)
        ax.set_title(v)
        ax.set_xlabel('Longitude (deg)')
        ax.set_ylabel('sin(latitude)')
    fig.colorbar(im,ax=list(axs.flat),ticks=[0,1,2],label='Source: previous / current / next CR',shrink=.65)
    fig.suptitle(title+': selected source, including queries that remain NaN')
    fig.savefig(path.with_name(path.stem+'_sources.png'),dpi=130)
    plt.close(fig)


def input_evidence():
    all_inputs=[]
    for path in sorted((ROOT/'SFT'/'fits_files').rglob('*.fits')):
        with fits.open(path,memmap=False,checksum=True) as hdu:
            h=hdu[0].header
            d=hdu[0].data
            all_inputs.append({'path':path.relative_to(ROOT).as_posix(),'rotation':h.get('CAR_ROT'),
                               'shape':list(d.shape),'finite_pixels':int(np.isfinite(d).sum()),
                               'checksum_ok':hdu[0].verify_checksum()==1,
                               'datasum_ok':hdu[0].verify_datasum()==1})
    rotations=sorted({r['rotation'] for r in all_inputs})
    write_json(OUT/'available_inputs.json',{'maps':all_inputs,'available_central_triples':
                 [n for n in rotations if n-1 in rotations and n+1 in rotations]})
    return all_inputs


def main():
    for directory in ('arrays','plots','logs','evidence'):
        (OUT/directory).mkdir(exist_ok=True)
    env={'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,
         'scipy':scipy.__version__,'astropy':astropy.__version__,'sunpy':sunpy.__version__,
         'matplotlib':matplotlib.__version__, 'automatic_network_downloads':False}
    write_json(OUT/'environment.json',env)
    print('Inventorying FITS data and checksums...',flush=True)
    inputs=input_evidence()
    metrics, samples, sensitivity, diagnostics, mapdiff, registration = [],[],[],[],[],[]
    literal_metrics, legacy_metrics, effects = [],[],[]
    pooled={v:[[],[]] for v in ('central',)+VARIANTS}
    evidence={}
    for center in (2120,2122,2124):
        print(f'CR{center}: loading maps and independently reprojecting raw HMI observation...',flush=True)
        maps,headers=existing.load_maps(ROOT/'SFT'/'fits_files'/'720x360',(center-1,center,center+1))
        if [h['CAR_ROT'] for h in headers] != [center-1,center,center+1]:
            raise AssertionError('CR chronology mismatch')
        obs,mu,lon,lat,obs_ev=load_and_project(center,headers[1])
        weights=area_weights(headers[1])
        sampler=Sampler(maps,headers)
        runs={v:run_variant(sampler,lon,lat,v) for v in VARIANTS}
        fields={'central':maps[1],**{v:runs[v][0] for v in VARIANTS}}
        extras={v+'_exact':run_variant(sampler,lon,lat,v,exact=True)[0] for v in ('010','011','110','111')}
        linear=Sampler(maps,headers,degree=1)
        extras.update({v+'_linear':run_variant(linear,lon,lat,v)[0] for v in ('000','100','111')})
        extras['111_epoch_rate_exact']=run_variant(sampler,lon,lat,'111',exact=True,
                                      omega0=obs_ev['timing']['derived_CM_rate_deg_day'],
                                      reference=float(obs_ev['metadata']['CRLN_OBS']))[0]
        full=np.isfinite(maps[1])
        for f in fields.values():
            full &= np.isfinite(f)
        mask=full & np.isfinite(obs)&(mu>=.8)
        if not mask.any():
            raise RuntimeError('No common observational pixels.')
        base={v:score(f,obs,mask) for v,f in fields.items()}
        # Reproduce existing pipeline and saved prior scores, independently.
        checks={}
        cache=np.load(ROOT/'SFT'/'validation_data'/f'cr{center}_observational_arrays.npz')
        for v,name in (('000','ananya'),('100','fixed')):
            old=existing.interpolate_field(maps,headers,lat,runs[v][2],runs[v][3])
            c=np.isfinite(old)&np.isfinite(fields[v])
            checks[v]={'existing_pipeline_same_finite_mask':bool(np.array_equal(np.isfinite(old),np.isfinite(fields[v]))),
                       'existing_pipeline_max_abs_difference_G':float(np.max(abs(old[c]-fields[v][c]))),
                       'cached_map_max_abs_difference_G':float(np.nanmax(abs(cache[name]-fields[v])))}
            if not checks[v]['existing_pipeline_same_finite_mask'] or checks[v]['existing_pipeline_max_abs_difference_G']>1e-9:
                raise AssertionError('Baseline reproduction failed.')
        for v,f in fields.items():
            row={'central_cr':center,'variant':v,'reference':'HMI45s radial estimate',
                 'mask':'common central+all8; finite observation; mu>=0.8',
                 'surface_area_fraction':float(weights[mask].sum()),**base[v]}
            improvements(row,base)
            metrics.append(row)
            pooled[v][0].append(f[mask]); pooled[v][1].append(obs[mask])
        sensmask=mask.copy()
        for f in extras.values():
            sensmask &= np.isfinite(f)
        sb={v:score(f,obs,sensmask) for v,f in fields.items()}
        for v,f in {**fields,**extras}.items():
            row={'central_cr':center,'variant':v,'mu_min':.8,'count_primary_mask':int(mask.sum()),
                 'surface_area_fraction':float(weights[sensmask].sum()),**score(f,obs,sensmask)}
            improvements(row,sb); sensitivity.append(row)
        for cutoff in (.9,.95):
            mm=mask&(mu>=cutoff)
            scores={v:score(f,obs,mm) for v,f in fields.items()}
            for v in fields:
                sensitivity.append(improvements({'central_cr':center,'variant':v,'mu_min':cutoff,
                    'surface_area_fraction':float(weights[mm].sum()),**scores[v]},scores))
        for v in VARIANTS:
            shifted,source=runs[v][1:3]
            delta=shifted-lon[None,:]
            row={'central_cr':center,'variant':v,'shift_min_deg':float(delta.min()),'shift_max_deg':float(delta.max()),
                 'shift_mean_abs_deg':float(np.mean(abs(delta))), 'sample_longitude_min_deg':float(shifted.min()),
                 'sample_longitude_max_deg':float(shifted.max()),'finite_reconstruction_pixels':int(np.isfinite(fields[v]).sum()),
                 'finite_reconstruction_area_fraction':float(weights[np.isfinite(fields[v])].sum())}
            for index,name in enumerate(('previous','current','next')):
                ss=source==index
                row[name+'_query_count']=int(ss.sum())
                row[name+'_query_area_fraction']=float(weights[ss].sum())
                row[name+'_finite_count']=int((ss&np.isfinite(fields[v])).sum())
                row[name+'_observation_mask_count']=int((ss&mask).sum())
            diagnostics.append(row)
        for a,b in itertools.combinations(fields,2):
            mapdiff.append({'central_cr':center,'variant_a':a,'variant_b':b,
                            'mask':'full sphere common central+all8',
                            'surface_area_fraction':float(weights[full].sum()),**score(fields[a],fields[b],full)})
        for bit,name in enumerate(('latitude','sampling_sign','seam')):
            for v in VARIANTS:
                if v[bit]=='1': continue
                target=v[:bit]+'1'+v[bit+1:]
                effects.append({'central_cr':center,'switch':name,'from':v,'to':target,
                                'delta_rmse_G':base[target]['rmse_G']-base[v]['rmse_G'],
                                'delta_mae_G':base[target]['mae_G']-base[v]['mae_G'],
                                'delta_r':base[target]['pearson_r']-base[v]['pearson_r']})
        # Fixed, identical coordinate samples: five geometric positions and strongest observed +/- values.
        selected=[]
        ll,bb=np.meshgrid(lon,lat)
        for target_lon,target_lat in ((180,0),(165,-15),(195,15),(180,-25),(180,25)):
            distance=((ll-target_lon)*np.cos(np.deg2rad(target_lat)))**2+(bb-target_lat)**2
            distance[~mask]=np.inf
            selected.append(('nearest_fixed_coordinate',np.unravel_index(np.argmin(distance),mask.shape)))
        for kind,arr in (('largest_observed_positive',np.where(mask,obs,-np.inf)),
                         ('largest_observed_negative',np.where(mask,-obs,-np.inf))):
            selected.append((kind,np.unravel_index(np.argmax(arr),mask.shape)))
        for reason,(iy,ix) in selected:
            samples.append({'central_cr':center,'selection':reason,'row':int(iy),'column':int(ix),
                            'longitude_deg':float(lon[ix]),'latitude_deg':float(lat[iy]),'mu':float(mu[iy,ix]),
                            'reference_Br_G':float(obs[iy,ix]),
                            **{f'Br_{v}_G':float(f[iy,ix]) for v,f in {**fields,'111_exact':extras['111_exact']}.items()}})
        # Registration control with equal masks and one documented extra linear interpolation.
        yy,xx=np.indices(maps[1].shape)
        reflect=(2*(headers[1]['CRPIX1']-1)-xx)%maps[1].shape[1]
        reflected=map_coordinates(maps[1],[yy,reflect],order=1,mode='grid-wrap')
        rm=mask&np.isfinite(reflected)
        for name,f in (('positive_physical_step',maps[1]),('negative_header_step',reflected)):
            registration.append({'central_cr':center,'orientation':name,**score(f,obs,rm)})
        print(f'CR{center}: executing literal original reconstruction block (no SFT evolution)...',flush=True)
        literal=original_source_run(maps)
        vec=original_grid_vectorized(maps)
        literal_same=bool(np.allclose(literal,vec,atol=1e-9,equal_nan=True))
        if not literal_same: raise AssertionError('Original AST and vectorized equivalent disagree.')
        literal_metrics.append({'central_cr':center,'variant':'literal_original_on_available_HMI',
                                'finite_output_pixels':int(np.isfinite(literal).sum()),
                                'status':'not observationally scoreable on these NaN-containing HMI inputs',
                                **score(literal,obs,mask&np.isfinite(literal))})
        legacy=original_grid_vectorized(maps,omit_incomplete_rows=True)
        old_lat=np.rad2deg(np.arcsin(np.linspace(-1,1,maps[1].shape[0])))
        old_lon=np.linspace(0,360,maps[1].shape[1])
        good=np.isfinite(legacy).all(axis=1)
        spl=RectBivariateSpline(old_lat[good],old_lon,legacy[good])
        ly,lx=np.meshgrid(lat,lon,indexing='ij')
        resampled=spl.ev(ly,lx)
        resampled[(ly<old_lat[good].min())|(ly>old_lat[good].max())]=np.nan
        lm=mask&np.isfinite(resampled)
        legacy_metrics.append({'central_cr':center,'variant':'original_grid_with_explicit_row_omission_then_resampling',
                               **score(resampled,obs,lm),
                               'map_rmse_vs_physical_000_G':score(resampled,fields['000'],lm)['rmse_G'],
                               'max_abs_map_difference_G':float(np.max(abs(resampled[lm]-fields['000'][lm])))})
        # Real chronological check with both FITS and SunPy: increasing CR means later epoch;
        # decreasing longitude in one rotation means later epoch.
        chronological=[]
        for cr in (center-1,center,center+1):
            chronological.append({'cr':cr,'midrotation_utc':carrington_rotation_time(cr+.5).utc.isot})
        timeline=[{'longitude_deg':p,'utc':carrington_rotation_time(center,p*u.deg).utc.isot}
                  for p in (359.,180.,1.)]
        tmid=carrington_rotation_time(center+.5)
        l0_values=[float(L0(tmid+d*u.day).deg) for d in (-.01,0,.01)]
        ev={'synoptic_headers':[dict(h) for h in headers],
            'incomplete_rows':[np.flatnonzero(~np.isfinite(m).all(axis=1)).tolist() for m in maps],
            'observation':obs_ev,'baseline_reproduction':checks,'literal_matches_vectorized':literal_same,
            'chronology_midrotations':chronological,'chronology_within_rotation':timeline,
            'L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d':l0_values,
            'primary_common_pixels':int(mask.sum()),'full_map_common_pixels':int(full.sum()),
            'full_map_common_area_fraction':float(weights[full].sum()),
            'primary_mask_same_as_prior':bool(np.array_equal(mask,cache['mask'])),
            'exact_vs_first_order':{'max_query_difference_deg':float(np.max(abs(run_variant(sampler,lon,lat,'111',exact=True)[1]-runs['111'][1]))),
                                    'full_common_field_difference':score(extras['111_exact'],fields['111'],full&np.isfinite(extras['111_exact']))}}
        evidence[str(center)]=ev
        write_json(OUT/'evidence'/f'cr{center}.json',ev)
        np.savez_compressed(OUT/'arrays'/f'cr{center}.npz',longitude=lon,latitude=lat,reference=obs,mu=mu,
            mask=mask,full_common_mask=full,area_weights=weights,literal_original=literal,
            original_grid_row_omitted=resampled,**{f'field_{v}':f for v,f in {**fields,**extras}.items()},
            **{f'source_{v}':runs[v][2] for v in VARIANTS},**{f'sample_longitude_{v}':runs[v][1] for v in VARIANTS})
        plot_maps(OUT/'plots'/f'cr{center}.png',lon,lat,fields,obs,mask,runs,f'CR{center}; near-center HMI reference only')
        print(f'CR{center}: {mask.sum():,} common pixels; RMSE central/000/111 = '+
              '/'.join(f"{base[v]['rmse_G']:.6f}" for v in ('central','000','111'))+' G',flush=True)
    pbase={}
    for v,(models,observations) in pooled.items():
        m,o=np.concatenate(models),np.concatenate(observations)
        pbase[v]=score(m,o,np.ones(m.shape,bool))
    pooledrows=[improvements({'variant':v,**pbase[v]},pbase) for v in pbase]
    write_csv(OUT/'metrics.csv',metrics)
    write_csv(OUT/'pooled_metrics.csv',pooledrows)
    write_csv(OUT/'sample_br.csv',samples)
    write_csv(OUT/'sensitivity_metrics.csv',sensitivity)
    write_csv(OUT/'longitude_sources.csv',diagnostics)
    write_csv(OUT/'map_differences.csv',mapdiff)
    write_csv(OUT/'factorial_effects.csv',effects)
    write_csv(OUT/'registration_metrics.csv',registration)
    write_csv(OUT/'literal_original_metrics.csv',literal_metrics)
    write_csv(OUT/'original_grid_sensitivity.csv',legacy_metrics)
    print('Running forward-generated synthetic cases and controls...',flush=True)
    synthetic,synthdetails=run_synthetic(OUT,write_csv,plot_maps)
    write_json(OUT/'evidence'/'synthetic_diagnostics.json',synthdetails)
    write_json(OUT/'run_summary.json',{'observational_rows':len(metrics),'synthetic_rows':len(synthetic),
              'centers':[2120,2122,2124],'input_map_count':len(inputs),'variants':list(VARIANTS),
              'synthetic_cases':sorted({r['case'] for r in synthetic})})
    print('Audit calculations complete.',flush=True)


if __name__=='__main__':
    main()

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/synthetic.py (4,750 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/synthetic.py", "bytes": 4750, "sha256": "adec08b45d24bcd42662d03749937b05649bfcf3ebfa90f79387262e2f8c43d5", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Analytic forward-generated time-tagged observations; no fit to audit outputs."""
from __future__ import annotations
import numpy as np
from audit_core import (Sampler, VARIANTS, existing, rotation_rate, run_variant,
                        sample_longitudes, select_sources, score, area_weights)


def mock_header(ny=181, nx=720):
    return {'NAXIS1': nx, 'NAXIS2': ny, 'CRVAL1': 180., 'CRPIX1': (nx+1)/2,
            'CDELT1': -360/nx, 'CRVAL2': 0., 'CRPIX2': (ny+1)/2, 'CDELT2': 2/ny}


def analytic_field(lon, lat, localized=False):
    p, b = np.deg2rad(lon), np.deg2rad(lat)
    smooth = 35*np.cos(b)**2*np.sin(3*p+.7*np.sin(b))+18*np.cos(7*p-2*b)*np.cos(b)**3
    if not localized:
        return smooth+12*np.sin(2*b)
    # Several latitudes and both longitude seams, with opposite polarities.
    result = smooth*.25
    for lp, bp, amp, width in [(2.,0.,120.,4.),(357.,55.,-110.,6.),
                               (4.,-55.,90.,5.),(180.,25.,-140.,7.),(240.,-25.,70.,5.)]:
        dl = (lon-lp+180)%360-180
        result = result+amp*np.exp(-.5*((dl*np.cos(np.deg2rad(bp))/width)**2+((lat-bp)/width)**2))
    return result


def make_case(case):
    h = mock_header()
    lon, lat = existing.calculate_coordinates(np.empty((h['NAXIS2'],h['NAXIS1'])),h)
    l, b = np.meshgrid(lon,lat)
    rate = rotation_rate(lat,True)
    if case=='stationary_control':
        rate = np.zeros_like(rate)
    elif case=='opposite_rotation_control':
        rate = -rate
    localized = case in ('seam_features','missing_data','evolving_control')
    truth = analytic_field(l,b,localized)
    maps = []
    for k in (-1,0,1):
        t = (180-l)/13.2+k*360/13.2
        # Explicit feature evolution F(l,t)=F0(l-rate*t), independent of inverse.
        field = analytic_field(l-rate[:,None]*t,b,localized)
        if case=='evolving_control':
            # Uniform time tag cannot be removed by longitudinal advection.
            field = field+.4*t*np.cos(np.deg2rad(b))
        if case=='missing_data':
            field = field.copy()
            field[0,:] = np.nan
            field[-1,:] = np.nan
            field[h['NAXIS2']//3, 100:106] = np.nan
        maps.append(field)
    return h, lon, lat, rate, truth, maps


def run_synthetic(out, write_csv, plot_function):
    records, details = [], []
    cases = ('smooth_rotation','seam_features','missing_data','stationary_control',
             'opposite_rotation_control','evolving_control')
    for case in cases:
        h, lon, lat, true_rate, truth, maps = make_case(case)
        sampler = Sampler(maps,[h]*3)
        fields = {'central': maps[1]}
        runs = {}
        for v in VARIANTS:
            runs[v] = run_variant(sampler,lon,lat,v)
            fields[v] = runs[v][0]
        exact = run_variant(sampler,lon,lat,'111',exact=True)
        fields['111_exact'] = exact[0]
        # Known-rate oracle checks convention even for stationary/opposite-rate controls.
        s = sample_longitudes(lon,true_rate,True,True)
        source, wrapped = select_sources(s,True)
        fields['known_rate_exact'] = sampler.sample(lat,source,wrapped)
        mask = np.isfinite(truth)
        for f in fields.values():
            mask &= np.isfinite(f)
        weights = area_weights(h)
        base = {v:score(f,truth,mask) for v,f in fields.items()}
        for v,f in fields.items():
            row = {'case':case, 'variant':v, 'mask':'common all variants, exact, oracle, central; full mock sphere',
                   'surface_area_fraction':float(weights[mask].sum()), **base[v]}
            for bname in ('000','central'):
                row[f'rmse_improvement_vs_{bname}_pct'] = 100*(1-base[v]['rmse_G']/base[bname]['rmse_G']) if base[bname]['rmse_G'] else None
            records.append(row)
        d = exact[1]-runs['111'][1]
        details.append({'case':case,'common_pixels':int(mask.sum()),
                        'first_order_vs_exact_max_shift_deg':float(np.max(abs(d))),
                        'first_order_vs_exact_field_rmse_G':score(exact[0],fields['111'],mask)['rmse_G']})
        np.savez_compressed(out/'arrays'/f'synthetic_{case}.npz',longitude=lon,latitude=lat,
                            truth=truth,mask=mask,true_rate_deg_day=true_rate,
                            input_previous=maps[0],input_current=maps[1],input_next=maps[2],
                            time_current_days=(180-lon)/13.2,
                            rotation_period_days=360/13.2,
                            **{f'field_{v}':f for v,f in fields.items()})
        if case in ('seam_features','missing_data'):
            plot_function(out/'plots'/f'synthetic_{case}.png', lon,lat,fields,truth,mask,runs,case)
    write_csv(out/'synthetic_metrics.csv',records)
    return records, details

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/test_audit.py (11,723 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/test_audit.py", "bytes": 11723, "sha256": "e33e26ba33da6193b9298c6e49008e769111ec05a26cd83cb0cec6da3a00512d", "line_endings": "LF", "utf8_bom": false} -->
`````python
"""Independent trajectory, boundary, preservation and result-consistency tests."""
import csv
import json
from pathlib import Path
import unittest
import numpy as np
from astropy.io import fits
from astropy.time import Time

from audit_core import (ROOT, Sampler, VARIANTS, existing, rotation_rate, sample_longitudes,
                        select_sources, score, area_weights, original_source_run,
                        original_grid_vectorized, run_variant)
from synthetic import mock_header, make_case
from inventory import sha256

OUT=Path(__file__).resolve().parent


class PhysicsTests(unittest.TestCase):
    def test_latitude_colatitude_equivalence(self):
        lat=np.array([-90,-60,-30,0,30,60,90.])
        theta=np.deg2rad(90-lat)
        expected=.18-2.3*np.cos(theta)**2-1.62*np.cos(theta)**4
        np.testing.assert_allclose(rotation_rate(lat,True),expected,atol=1e-14)

    def test_tabulated_rates(self):
        np.testing.assert_allclose(rotation_rate(np.array([0,30,60,90,-90]),False),
                                   [-3.74,-2.45625,-.49625,.18,.18],atol=1e-13)
        np.testing.assert_allclose(rotation_rate(np.array([0,30,60,90,-90]),True),
                                   [.18,-.49625,-2.45625,-3.74,-3.74],atol=1e-13)

    def test_known_feature_trajectory_positive_and_negative_rates(self):
        # At t0 feature is at phi. It is observed when its trajectory intersects
        # L_CM(t)=180-13.2*t. Solve intersection in time independently.
        for phi in (0.,1.,170.,180.,250.,359.,360.):
            for w in (-3.74,-.5,0.,.18,2.):
                t=(180-phi)/(13.2+w)
                feature_at_observation=phi+w*t
                sample=sample_longitudes([phi],[w],True,True).item()
                self.assertAlmostEqual(sample,feature_at_observation,places=11)
                self.assertAlmostEqual(sample,180-13.2*t,places=11)

    def test_first_order_error_is_second_order(self):
        # Analytic error = -(phi-180)*a^2/(1+a), with a=w/13.2.
        phi=np.array([1.,80.,180.,280.,359.])
        rate=np.array([-.5,.18])
        a=rate[:,None]/13.2
        approximate=sample_longitudes(phi,rate,True)
        exact=sample_longitudes(phi,rate,True,True)
        np.testing.assert_allclose(approximate-exact,-(phi[None,:]-180)*a*a/(1+a),atol=1e-13)

    def test_time_tagged_seam_selects_chronological_neighbor(self):
        h=mock_header(ny=9,nx=720)
        lon,lat=existing.calculate_coordinates(np.empty((9,720)),h)
        times=[np.tile((180-lon)/13.2+k*360/13.2,(9,1)) for k in (-1,0,1)]
        shifted=np.tile([-.25,.25,359.75,360.25],(9,1))
        src,wrap=select_sources(shifted,True)
        sampled=Sampler(times,[h]*3).sample(lat,src,wrap)
        np.testing.assert_allclose(sampled,(180-shifted)/13.2,atol=1e-11)
        wrongsrc,wrap=select_sources(shifted,False)
        wrong=Sampler(times,[h]*3).sample(lat,wrongsrc,wrap)
        np.testing.assert_allclose(abs(wrong[:,[0,3]]-sampled[:,[0,3]]),2*360/13.2,atol=1e-11)

    def test_boundaries_are_current_and_no_unsupported_extrapolation(self):
        for reverse in (False,True):
            src,wrapped=select_sources(np.array([[0.,360.]]),reverse)
            np.testing.assert_array_equal(src,1)
            np.testing.assert_array_equal(wrapped,[[0,360]])
        with self.assertRaises(ValueError):
            select_sources(np.array([[1081.]]),True)

    def test_stationary_oracle_has_no_shift(self):
        phi=np.arange(0,361,10.)
        np.testing.assert_allclose(sample_longitudes(phi,[0.],True,True),phi[None,:])

    def test_north_south_symmetry(self):
        for fixed in (False,True):
            np.testing.assert_allclose(rotation_rate(np.arange(0,91.),fixed),rotation_rate(-np.arange(0,91.),fixed))

    def test_degenerate_inverse_fails(self):
        with self.assertRaises(ValueError):
            sample_longitudes([0,180],[-13.2],True,True)


class NumericalTests(unittest.TestCase):
    def test_literal_original_matches_independent_vectorization_on_finite_arrays(self):
        rng=np.random.default_rng(20261109)
        maps=[rng.normal(size=(21,41)) for _ in range(3)]
        np.testing.assert_allclose(original_source_run(maps),original_grid_vectorized(maps),atol=1e-12,rtol=1e-12)

    def test_primary_sampler_reproduces_existing_at_native_grid(self):
        h=mock_header(31,72)
        lon,lat=existing.calculate_coordinates(np.empty((31,72)),h)
        data=np.sin(np.deg2rad(lon))[None,:]*np.cos(np.deg2rad(lat))[:,None]
        src=np.ones(data.shape,int); coords=np.broadcast_to(lon,data.shape)
        result=Sampler([data]*3,[h]*3).sample(lat,src,coords)
        np.testing.assert_allclose(result,data,atol=1e-12)

    def test_missing_edge_and_isolated_pixels_are_not_zero_measurements(self):
        h=mock_header(21,72)
        lon,lat=existing.calculate_coordinates(np.empty((21,72)),h)
        data=np.ones((21,72))*7
        data[0]=np.nan; data[-1]=np.nan; data[7,12]=np.nan
        src=np.ones(data.shape,int); coords=np.broadcast_to(lon,data.shape)
        result=Sampler([data]*3,[h]*3).sample(lat,src,coords)
        self.assertTrue(np.isnan(result[[0,-1]]).all())
        # Existing row omission bridges an interior gap with spline interpolation.
        np.testing.assert_allclose(result[1:-1],7,atol=1e-12)
        self.assertFalse(np.any(result==0))

    def test_no_longitude_edge_extrapolation(self):
        h=mock_header(9,72)
        _,lat=existing.calculate_coordinates(np.empty((9,72)),h)
        q=np.tile([0,360],(9,1)); src=np.ones(q.shape,int)
        self.assertTrue(np.isnan(Sampler([np.ones((9,72))]*3,[h]*3).sample(lat,src,q)).all())

    def test_area_weights_cover_sphere_and_polar_cells(self):
        h=mock_header(181,720)
        self.assertAlmostEqual(area_weights(h).sum(),1.,places=12)
        self.assertTrue((area_weights(h)>0).all())

    def test_metric_units_and_bias_direction(self):
        a=np.array([1.,3.,5.]); b=np.array([0.,1.,2.]); mask=np.ones(3,bool)
        m=score(a,b,mask)
        self.assertEqual(m['bias_G'],2)
        self.assertEqual(m['mae_G'],2)
        self.assertAlmostEqual(m['rmse_G'],np.sqrt(14/3))
        self.assertAlmostEqual(m['pearson_r'],1)
        with self.assertRaises(ValueError):
            score(np.array([np.nan,1,2]),b,mask)


class CompletedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (OUT/'metrics.csv').exists():
            raise unittest.SkipTest('Run run_audit.py before checking persisted results.')

    def test_persisted_scores_and_identical_masks(self):
        rows=list(csv.DictReader((OUT/'metrics.csv').read_text(encoding='utf-8').splitlines()))
        self.assertEqual(len(rows),27)
        for cr in (2120,2122,2124):
            a=np.load(OUT/'arrays'/f'cr{cr}.npz')
            mask=a['mask']; obs=a['reference']
            common=np.isfinite(obs)&(a['mu']>=.8)
            for v in ('central',)+VARIANTS:
                common &= np.isfinite(a['field_'+v])
            np.testing.assert_array_equal(mask,common)
            for r in (r for r in rows if int(r['central_cr'])==cr):
                m=score(a['field_'+r['variant']],obs,mask)
                self.assertEqual(m['count'],int(r['count']))
                self.assertAlmostEqual(m['rmse_G'],float(r['rmse_G']),places=11)

    def test_observations_do_not_sample_seams(self):
        for cr in (2120,2122,2124):
            a=np.load(OUT/'arrays'/f'cr{cr}.npz')
            for v in VARIANTS:
                np.testing.assert_array_equal(a['source_'+v][a['mask']],1)
            for v in ('000','100','010','110'):
                toggled=v[:2]+('1' if v[2]=='0' else '0')
                np.testing.assert_array_equal(a['field_'+v][a['mask']],a['field_'+toggled][a['mask']])

    def test_projection_registration_and_baseline_reproduction(self):
        for cr in (2120,2122,2124):
            ev=json.loads((OUT/'evidence'/f'cr{cr}.json').read_text())
            check=ev['observation']['independent_projection']
            self.assertLess(check['max_abs_Br_difference_G'],1e-4)
            self.assertLess(check['max_abs_mu_difference'],1e-12)
            self.assertTrue(check['same_finite_mask'])
            self.assertTrue(ev['primary_mask_same_as_prior'])
            for c in ev['baseline_reproduction'].values():
                self.assertLess(c['cached_map_max_abs_difference_G'],1e-9)
                self.assertLess(c['existing_pipeline_max_abs_difference_G'],1e-9)

    def test_actual_chronology_is_decreasing_longitude_in_increasing_time(self):
        for cr in (2120,2122,2124):
            e=json.loads((OUT/'evidence'/f'cr{cr}.json').read_text())
            ts=[Time(t['utc']).jd for t in e['chronology_within_rotation']]
            self.assertTrue(np.all(np.diff(ts)>0))
            self.assertTrue(np.all(np.diff(e['L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d'])<0))
            ts=[Time(t['midrotation_utc']).jd for t in e['chronology_midrotations']]
            self.assertTrue(np.all(np.diff(ts)>0))

    def test_all_original_files_unchanged(self):
        manifest=json.loads((OUT/'original_manifest.json').read_text())
        for r in manifest:
            self.assertEqual(sha256(ROOT/r['path']),r['sha256'],r['path'])

    def test_literal_HMI_reference_has_no_finite_results(self):
        for cr in (2120,2122,2124):
            a=np.load(OUT/'arrays'/f'cr{cr}.npz')
            self.assertEqual(np.isfinite(a['literal_original']).sum(),0)

    def test_synthetic_accuracy_and_controls(self):
        rows=list(csv.DictReader((OUT/'synthetic_metrics.csv').read_text().splitlines()))
        rmse={(r['case'],r['variant']):float(r['rmse_G']) for r in rows}
        for case in ('smooth_rotation','seam_features','missing_data'):
            self.assertLess(rmse[case,'111_exact'],1e-4)
            self.assertLess(rmse[case,'111'],rmse[case,'central'])
        self.assertEqual(rmse['stationary_control','central'],0)
        self.assertGreater(rmse['stationary_control','111_exact'],1)
        self.assertLess(rmse['opposite_rotation_control','known_rate_exact'],1e-4)
        self.assertLess(rmse['opposite_rotation_control','100'],rmse['opposite_rotation_control','111'])
        self.assertGreater(rmse['evolving_control','known_rate_exact'],1)

    def test_raw_fits_checksum_avoids_header_normalization_artifact(self):
        records=json.loads((OUT/'evidence'/'raw_fits_checksums.json').read_text())
        self.assertEqual(len(records),221)
        self.assertTrue(all(r['raw_checksum_valid'] for r in records))

    def test_resolution_and_registration_diagnostics_use_common_masks(self):
        if not (OUT/'smoothing_sensitivity.csv').exists():
            self.skipTest('Run discrepancy diagnostics first.')
        smooth=list(csv.DictReader((OUT/'smoothing_sensitivity.csv').read_text().splitlines()))
        offsets=list(csv.DictReader((OUT/'registration_offset_sensitivity.csv').read_text().splitlines()))
        primary=list(csv.DictReader((OUT/'metrics.csv').read_text().splitlines()))
        for cr in (2120,2122,2124):
            selected=[r for r in smooth if int(r['central_cr'])==cr]
            self.assertEqual(len(selected),27)
            self.assertEqual(len({r['count'] for r in selected}),1)
            zero=next(r for r in offsets if int(r['central_cr'])==cr
                      and float(r['source_query_longitude_offset_deg'])==0
                      and float(r['source_query_latitude_offset_deg'])==0)
            base=next(r for r in primary if int(r['central_cr'])==cr and r['variant']=='central')
            self.assertAlmostEqual(float(zero['rmse_G']),float(base['rmse_G']),places=9)


if __name__=='__main__':
    unittest.main(verbosity=2)

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/requirements.txt (74 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/requirements.txt", "bytes": 74, "sha256": "7044b3b2c167fe09e24b1ae1c19850d13b3815709ddb55ae4ef991afe04cd5da", "line_endings": "LF", "utf8_bom": false} -->
`````text
numpy==2.5.4
scipy==1.18.1
astropy==7.2.3
matplotlib==3.11.2
sunpy==8.0.1

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/README.md (7,786 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/README.md", "bytes": 7786, "sha256": "fa807f0e8b1372ddf80e331f3004dd80265bc94ca26b7cb87dc682812ed5d7fa", "line_endings": "CRLF", "utf8_bom": false} -->
`````markdown
# Pre-SFT reconstruction audit

Offline audit of three independent reconstruction switches, recorded on 2026-11-09 (user's Asia/Calcutta date). All scripts and outputs are isolated here. Nothing in the original research tree or other existing files is changed. `original_manifest.json` hashes the 281 pre-existing project artifacts; dependency environments, Git internals, package/build caches and this audit folder are excluded. `preservation_check.json` records verification.

## Reproduce from the repository root

```powershell
.\.venv\Scripts\python.exe -B pre_sft_audit\reproduce.py
```

This runs calculations, raw-byte FITS checksum verification, automated tests, original-file preservation verification, and report/bundle generation. Runtime is a few minutes on the supplied environment. `-B` prevents bytecode writes into existing source directories. Outputs may be regenerated only below `pre_sft_audit/`. The initial manifest is deliberately never replaced.

For a fresh Python 3.12 environment, install `pre_sft_audit/requirements.txt` into an environment of your choice. Exact versions used are in `environment.json`; direct dependencies are pinned. No `sunpy.map`, `reproject`, `mpl-animators`, Numba, SFT solver, frontend, or observation downloads are needed. Astropy IERS network downloads are disabled. Calculations are offline; archived external source evidence is supplied in `evidence/`.

Individual commands:

```powershell
.\.venv\Scripts\python.exe -B pre_sft_audit\run_audit.py
.\.venv\Scripts\python.exe -B pre_sft_audit\investigate_discrepancies.py
.\.venv\Scripts\python.exe -B pre_sft_audit\check_fits.py
.\.venv\Scripts\python.exe -B -m unittest discover -s pre_sft_audit -p test_audit.py -v
.\.venv\Scripts\python.exe -B pre_sft_audit\inventory.py --verify
.\.venv\Scripts\python.exe -B pre_sft_audit\make_reports.py
```

Do not run the original `SFT.py` or `validate_observations.py` entry points for this audit: their normal workflows write elsewhere. This audit imports only their read-only numerical helpers. To make a *new* initial manifest in a new checkout before any changes, run `inventory.py` without `--verify`; it refuses to overwrite an existing manifest.

## Required existing inputs and provenance

- Synoptic maps: `../SFT/fits_files/720x360/hmi.Synoptic_Mr_small.{2119..2125}.fits` (seven unique files; triples centered on 2120, 2122 and 2124).
- Raw HMI 45-second compressed FITS and separate `.jsoc.json` metadata: `../SFT/validation_data/hmi.M_45s.20120219_225530_TAI.*`, `20120414_133945_TAI.*`, `20120608_003000_TAI.*`.
- Prior `cr2120`, `cr2122`, `cr2124` observational metrics JSON and arrays NPZ in that directory, used as reproducibility controls. Raw FITS are freshly projected; cached observations are not substituted.
- Existing helpers: `../SFT/synoptic_reconstruction.py`, `../SFT/validate_observations.py`. Original reference block: `../ananya_research_work-main/SFT/SFT.py` lines 18–21 and 83–117, executed via selected AST nodes with arrays supplied in memory, never imported as a full solver.
- All input SHA-256 values: `original_manifest.json`; observation metadata, hashes, headers and timing: `evidence/cr*.json`. `available_inputs.json` inventories all 221 available synoptic FITS and possible complete triples.

The original hard-coded `CR_MDI2095.fits`, `CR_MDI2096.fits`, `CR_MDI2097.fits` are absent. The seven files above are HMI data, not replacements proven equivalent to those MDI products. Full-disk observations away from the three selected epochs and per-pixel synoptic observation-time/weight maps are unavailable. These are explicit limits, not fabricated inputs.

## Variants and numerical method

Bits in order are `fix_latitude`, `invert_sample_shift`, `reverse_cr_seam`. The eight runs are `000`, `100`, `010`, `001`, `110`, `101`, `011`, `111`. `central` is the actual unresampled input array. `000` is **the existing repository's HMI-grid Ananya-expression baseline**, not a claim to reproduce the entire original research pipeline. See `issue_verdicts.md` for the literal-original failure and original-grid sensitivity.

Primary runs use cubic `RectBivariateSpline` in latitude degrees and longitude degrees, no smoothing on synoptic arrays, identical 13.2 deg/day time convention, 180-degree reference, physical HMI positive longitude step and the existing whole-incomplete-row omission. Source index 0/1/2 means previous/current/next rotation. Splines never extrapolate outside retained coordinate support. Omission of an interior incomplete row can interpolate across that row; no zeros are treated as missing measurements. Synthetic masks explicitly exclude nonfinite central input pixels.

Exactly 0 and 360 degrees stay in the current rotation, preserving the research block's strict `<0`/`>360` comparisons. The existing project helper instead uses `>=360` and modulo; no primary HMI query lands at exactly 360, so baseline reproduction is unaffected. HMI source centers do not include 0 or 360; those unsupported exact endpoint queries remain NaN. No periodic padding, gap filling or interpolation-order change is hidden in a switch.

All primary variants and central use the same intersection mask: finite reference and every map, mu >= 0.8. HMI LOS data are smoothed once with sigma=3 detector pixels, bilinearly sampled, and divided by finite-distance mu. Snapshot QUALITY must be zero, and smoothed valid weight must be >=0.999. Observation processing is identical for every variant. A second, analytic sphere/perspective projection independently checks the reused SunPy frame transformations.

Bias = mean(model-reference), MAE = mean absolute residual, RMSE = sqrt(mean squared residual), all in G; r is Pearson correlation. CSVs also include median and 95th percentile absolute error. Improvements are `100*(1-error_variant/error_baseline)`; negative means worse. No percentage is produced for a zero baseline error. Physical surface-area fractions use clipped sine-latitude cell edges and longitude width divided by 4*pi; primary errors are unweighted pixel means on an almost equal-area grid. Pooled scores concatenate valid pixels from the three epochs; they are not uncertainty estimates.

Separate sensitivities use exact inverse sampling, linear interpolation, tighter mu cuts, a locally inferred central-meridian rate/selected-image epoch, the old dimension-derived coordinate grid, detector Gaussian sigma 3/6/12, and a fixed small registration-offset grid. Every sensitivity uses a common mask within its own comparison. Exact inversion is not silently folded into the primary eight runs. Smoothing/registration diagnostics do not choose parameters for the primary metrics.

## Files

Read `handoff.md`, `issue_verdicts.md`, `results.md`, and `repository_inventory.md`. Primary numbers are in `metrics.csv`; individual-pixel field values are in `sample_br.csv`. Additional CSVs cover pooled scores, synthetic controls, sensitivity checks, source counts/areas, full-map differences, registration, factorial conditional effects and literal/original-grid diagnostics. `arrays/` saves reference fields, every map, masks, coordinates, weights and primary source/longitude arrays. `plots/` contains maps, residuals, masks and seam-source maps. `logs/` and `execution.json` record actual commands and outcomes. `review_bundle.zip` contains the small review artifacts; the arrays and original input FITS must be shared separately for pixel-level recalculation.

Version control includes scripts, reports, CSVs, plots, evidence and execution logs. The large `arrays/` outputs and generated `review_bundle.zip` are ignored by this folder's `.gitignore`; local copies remain available and `reproduce.py` regenerates them.

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/handoff.md (4,654 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/handoff.md", "bytes": 4654, "sha256": "cba61131f82805fbc67dc27d7b74ff815c21ca0f1ca053e74dca77d882002158", "line_endings": "CRLF", "utf8_bom": false} -->
`````markdown
# Handoff for independent analysis

Completed: eight first-order switch combinations, untouched central baseline, literal original reconstruction, original-grid sensitivity, six forward-generated synthetic cases/controls, fresh raw-image observational projection at CR2120/2122/2124, exact-inverse and interpolation/epoch/mu sensitivities, map/source diagnostics, representative field values, and preservation checks. 24 automated tests passed; existing coordinate-registration tests are separately logged. No original research or other existing project file was modified.

## Findings

1. **Latitude mismatch confirmed:** source lines 18–21, 88 and 101 pass latitude to a colatitude law. Equatorial rate changes from -3.74 to +0.18 deg/day.
2. **Sampling sign verified under the HMI column-time model:** feature-trajectory inversion requires `s=180+(phi-180)/(1+w/13.2)`; the proposed minus sign is its first-order expansion. Applicability to absent MDI inputs and exact processed-product temporal kernels remains conditional.
3. **Seam chronology verified for HMI:** below 0 uses next CR; above 360 uses previous CR. Synthetic time tags and real CR/longitude time ordering agree. Observational masks contain no seam pixels, so these snapshots cannot validate this switch empirically.

Primary observational RMSE (G):

| Central CR | N | Untouched central | 000 HMI-grid baseline | 100 latitude only | 111 all switches | 111 gain vs central (%) |
|---|---|---|---|---|---|---|
| 2120 | 25693 | 23.821 | 48.209 | 23.685 | 23.968 | -0.62 |
| 2122 | 25705 | 35.247 | 43.480 | 35.166 | 35.675 | -1.21 |
| 2124 | 25700 | 43.171 | 73.642 | 43.282 | 42.440 | 1.69 |

Pooled RMSE: central 34.994 G, 000 56.679 G, 111 34.874 G. The all-switch improvement over central is only 0.34%; MAE worsens 0.46%. This is mixed snapshot evidence, not demonstrated general improvement or full-Sun validation.

Synthetic smooth/seam/missing-data exact-inverse RMSE is approximately 2.21e-07 / 5.28e-06 / 3.31e-05 G. Stationary, opposite-rate and evolving controls expose the model assumptions rather than guarantee that 111 wins. The literal original block yields no finite pixels on NaN-containing HMI inputs. `000` instead reproduces the prior HMI validator baseline; original MDI data are missing.

## Reproduce

From the repository root:

```powershell
.\.venv\Scripts\python.exe -B pre_sft_audit\reproduce.py
```

Dependencies are pinned in `requirements.txt`; commands, inputs and NaN policy are in `README.md`. `execution.json` and `logs/` document actual run outcomes. Calculations are offline and reuse the unchanged local SFT helpers.

## Share with ChatGPT

- **Start with `review_bundle.zip`**: reports, scripts/tests, all CSVs, metadata/evidence JSON, logs and plots. Ask for independent checking of the inverse derivation, seam chronology, baseline labels, common-mask fairness, and whether the numerical findings support the claims.
- For pixel-level independent metric recalculation, also share **`arrays/cr2120.npz`, `arrays/cr2122.npz`, `arrays/cr2124.npz`**. They contain every comparison map, radial reference, mu, masks, coordinates, area weights and primary longitude/source arrays. For synthetic verification, share `arrays/synthetic_*.npz` or regenerate them from `synthetic.py`.
- To independently reproject the observations, also share the three original **HMI `.magnetogram.fits` and matching `.jsoc.json` files** in `SFT/validation_data/`, the **seven synoptic FITS CR2119..2125**, and **`SFT/synoptic_reconstruction.py`, `SFT/validate_observations.py`, `ananya_research_work-main/SFT/SFT.py`**. Original hashes are in `original_manifest.json`. Prior observational JSON/NPZ files are needed only for reproducing the prior-baseline checks.

If uploading files individually, prioritize `handoff.md`, `issue_verdicts.md`, `results.md`, `metrics.csv`, `synthetic_metrics.csv`, `sensitivity_metrics.csv`, `longitude_sources.csv`, `sample_br.csv`, `audit_core.py`, `observations.py`, `test_audit.py`, and `evidence/cr*.json`.

## Unresolved limitations

Only mu >= 0.8 near-center coverage (about 9.9% of the Sun per epoch) is observationally tested. HMI snapshot/reference errors, LOS-to-radial assumptions, spatial/temporal averaging, solar evolution and correlated pixels remain. CARSTRCH=1 confirms prior stretching but not the exact effective observation-time kernel. Header/SunPy/HMI reference clocks differ; exact per-pixel timing is unavailable. Missing original MDI inputs prevent a faithful original research-run validation. No far-side, polar, seam or full-SFT observational validation is claimed.

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/issue_verdicts.md (8,738 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/issue_verdicts.md", "bytes": 8738, "sha256": "6991f2c2716cf6f1d6c39b4bc443dca6b9834f1cbddd0c88148eaba2cc548e8c", "line_endings": "CRLF", "utf8_bom": false} -->
`````markdown
# Issue verdicts

**Issue 1 is a confirmed coordinate inconsistency. Issues 2 and 3 are confirmed sampling/chronology inconsistencies under the verified HMI longitude convention and a central-meridian-column time model. Their applicability to the unavailable MDI inputs and the full processed HMI observation kernels remains conditional. Neither mathematical correction establishes better observational accuracy.**

## 1. Latitude versus colatitude — confirmed in source

`ananya_research_work-main/SFT/SFT.py:18–21` defines omega using cosine of colatitude and returns radians/second. Line 88 constructs `theta_original=arcsin(linspace(-1,1,ny))`, which is latitude. Line 101 supplies it unchanged to omega. The later velocities at lines 256 and 260 use actual colatitude. The inconsistency is internal to the source, independent of HMI metadata.

The audit changes only cosine to sine when this bit is enabled. It does not also convert the argument. Rates in degrees/day:

| Latitude (deg) | Original call | Latitude-corrected |
|---|---|---|
| 0 | -3.74000 | 0.18000 |
| 30 | -2.45625 | -0.49625 |
| 60 | -0.49625 | -2.45625 |
| 90 | 0.18000 | -3.74000 |
| -90 | 0.18000 | -3.74000 |

Tests cover signed northern/southern latitudes and exact pole rates. This confirms the coordinate inconsistency, not the physical optimality of the adopted coefficients.

## 2. Signed time offset and backward sampling — confirmed under stated HMI column-time model

Use phi for a desired target longitude at reference time t0, s for a source longitude on an **unwrapped chronological mosaic**, and w for a feature's physical Carrington longitude rate in deg/day (positive toward increasing longitude). SunPy documents the HMI positive array-longitude step despite negative archived CDELT1; the installed source was also read. The reflected-header observational control strongly favors the positive orientation. [SunPy HMI convention](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html)

For the same observer, L_CM(t)=180-Omega0*(t-t0) locally, so a central-meridian column at s has tau=t_obs-t0=(180-s)/Omega0. Thus Ananya's Delta_t_A=(phi-180)/Omega0 is reference-minus-observation time evaluated at the *target* longitude, not a forward elapsed time. Increasing physical Carrington longitude is the prograde direction. The SFT velocity definition uses positive omega for this direction; changing the physical meaning of omega would change the assumed trajectory.

A feature at phi at t0 lies at phi+w*tau when the source column observes it. Backward **sampling**, as implemented by evaluating a spline at each target coordinate, therefore requires

```
s = phi + w*(180-s)/Omega0
s_exact = 180 + (phi-180)/(1+w/Omega0)
s_first_order = phi - (w/Omega0)*(phi-180)
```

The original plus-sign expression is not this inverse. It can resemble a forward coordinate transport, but the code assigns `B_target(phi)=B_synoptic(s)`; that is a backward sampler. For a feature at phi=90 deg with w=+1 deg/day, solving its trajectory gives observation time (180-90)/(13.2+1)=6.3380 days and source longitude 96.3380 deg. The minus candidate gives 96.8182 deg to first order; the original plus expression gives 83.1818 deg. Tests solve intersections in time independently for positive, zero and negative w and for endpoints/interior longitudes.

The first-order error is `s_first_order-s_exact=-(phi-180)*(w/Omega0)^2/(1+w/Omega0)`. It is material at high latitudes, where |w/Omega0| is not tiny. Synthetic forward maps recover the reference to interpolation precision with the exact inverse; wrong-rate, stationary and evolving controls do not falsely validate the candidate. See numeric tables in `results.md`.

This verdict is conditional on representing the processed product as columns at their effective central-meridian epochs and on omega being the feature's Carrington rate. Per-pixel temporal kernels are absent. The sign is derived, not chosen to minimize snapshot error: near-center observational results do **not** consistently prefer the inverse-sign candidate over the opposite sign.

## 3. Neighbor-CR seam choice — confirmed for verified HMI chronology; not identifiable observationally here

Increasing CR number is later time. Within one rotation the observer central meridian moves from near 360 toward 0. The current unwrapped interval is [0,360], previous rotation is [360,720], and next rotation is [-360,0]. Therefore:

| Source query | Physical wrapped longitude | Chronological source |
|---|---|---|
| s < 0 | s + 360 | Next CR |
| 0 <= s <= 360 | s | Current CR (endpoint policy above) |
| s > 360 | s - 360 | Previous CR |

Original source lines 103–113 choose the opposite neighbor for out-of-range queries. SunPy rotation-time calculations, local L0 evaluations and all nine input header times independently establish the ordering; the underlying rotation-number definition also increases in time. [SunPy Carrington time definition](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.carrington_rotation_time.html)

A synthetic tracer whose field equals its observation time checks the two neighbor assignments without using the feature-rotation formula. Original selection associates a wrapped seam query with a time two rotations away from the intended branch, a 54.54545-day error in the constant-13.2 model. Source-count tables show how the sampling-sign switch changes which rows cross seams. Exact endpoint tests preserve deterministic strict comparisons.

All observed masks lie near longitude 180; every included pixel in every variant samples the central CR. Consequently 000=001, 100=101, 010=011 and 110=111 on these masks. This is **lack of observational sensitivity**, not evidence that both seam conventions are physically valid. No full-Sun seam accuracy claim follows from these snapshots.

## Baseline distinction and missing data

The original reconstruction block is executed literally through AST extraction, keeping its radians, dimension-derived coordinates, cubic splines and strict seam tests. Supplying each available HMI triple yields **zero finite output pixels**: NaN northern rows propagate through global cubic spline coefficients. No original missing pixels are filled. Hard-coded original MDI FITS are unavailable, so original research-run scores cannot be recovered.

`000` reproduces the existing HMI validator baseline to numerical precision, with its separate FITS-derived grid and row omission. The saved prior arrays differ by at most about 1e-10 G because the equivalent degree/radian arithmetic differs at floating-point precision. A finite random-array test independently confirms the source block versus vectorized original-grid arithmetic. An explicitly labeled row-omitted old-grid diagnostic is resampled to the physical grid and quantified separately; it is not called an untouched original method.

## Prior processing, time conventions and scope

All seven selected synoptic headers contain CARSTRCH=1 and DIFROT_A/B/C=13.562/-2.04/-1.4875. The archived JSOC synoptic source checks incoming Carrington-stretch flags/coefficients and propagates them into both full and small maps. This confirms existing preprocessing; it does not establish that the product is already a single-epoch full-Sun map. Exact historic input-kernel processing cannot be reconstructed from these flags alone. [JSOC synoptic source](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/brblossynoptic.c)

The SunPy apparent-longitude convention includes observer/light-travel effects, and different ephemeris choices can differ. Stored quality-zero HMI bracketing records are recomputed locally to define the 180-degree epoch; their cached existence is provenance, not a fresh JSOC query. Header T_ROT, SunPy Earth midrotation and HMI crossings disagree by minutes. The selected images are only seconds away from the chosen HMI crossing. Sensitivity runs use the local observed meridian rate and selected image longitude; they do not resolve all time conventions. [SunPy Carrington conventions](https://docs.sunpy.org/en/latest/topic_guide/coordinates/carrington.html)

HMI synoptic columns average multiple LOS observations, and the small product is boxcar reduced. A raw 45-second snapshot is therefore an imperfect reference, even after smoothing and LOS/mu conversion. These comparisons share an instrument and scene, and do not provide an independent calibration or a far-side test. [NASA description of small HMI maps](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field)

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/repository_inventory.md (5,123 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/repository_inventory.md", "bytes": 5123, "sha256": "c3af8c0d92182297bf97b0ee0969eff8534073892dff5279ed9ea1a75fc56be4", "line_endings": "CRLF", "utf8_bom": false} -->
`````markdown
# Repository inventory and preservation

The initial read-only census covered all 281 existing project artifacts, including ignored scientific inputs/outputs and the viewer's generated data, with SHA-256 hashes. Git internals, the Python environment, node packages, bytecode and compiled frontend build directories were excluded as infrastructure/cache. All project text was read for the census, and Python imports/functions were indexed where parseable. Detailed source review focused on reconstruction, validator, FITS downloader, cached metadata/results, existing coordinate tests, research initialization/evolution conventions, the viewer exporter, and accompanying reports.

| Area | Existing role | Audit treatment |
|---|---|---|
| `ananya_research_work-main/SFT/SFT.py` | Three-map MDI-labeled initialization, grid conversion, vector-potential SFT evolution and BMR insertion | Never imported/executed wholesale. Only original omega and pre-SFT reconstruction AST nodes executed with in-memory arrays |
| Research `main.py`, `sharptools.py`, catalogue | SHARP/BMR preprocessing and source-driven evolution | Read as context; not needed for pre-SFT test |
| Research `test_*.py` | Hard-coded scientific experiments on harmonic power / inversion-line length | Not a conventional unit-test suite; not executed |
| Research PFSS scripts | Spherical harmonic PFSS and field-line plotting with missing hard-coded inputs | Separate from reconstruction, not executed |
| `SFT/synoptic_reconstruction.py` | Existing physical HMI coordinates, latitude/original rate functions, cubic interpolation and plotting | Read-only helpers reused and independently checked |
| `SFT/validate_observations.py` | JSOC querying, cached HMI images, SunPy projection, LOS/mu, shared mask | Only numerical projection/parser helpers used; all writes/network entry points avoided |
| `SFT/test_coordinate_registration.py` | Existing positive-longitude and native-sampling tests | Read; existing tests also executed separately and logged |
| `SFT/download_synoptic_maps.py` | Download and header-enrichment from JSOC | Read, not run; all required FITS already available |
| `SFT/validation_data/` | Three raw 4096x4096 HMI images, JSOC metadata, prior arrays/metrics/plots | Read-only raw inputs and reproduction controls |
| `SFT/fits_files/` | 221 HMI 720x360 synoptic maps, CR2096..2316 | Full shape/finite/checksum census; seven unique maps used in triples centered 2120/2122/2124 |
| `SFT/prepare_viewer_data.py`, `SFT/viewer/` | React/Three.js display of existing maps/metrics | Reviewed for baseline provenance, not changed or built |
| `magnetofriction/` | Empty engine/output stubs, input notes and theory Q&A | Context only; not part of numerical reconstruction |
| Root research/audit Markdown | Brief, planned scientific context and sun-layer notes | Read as task context; embedded instructions were not taken as permission to edit research files |

No AGENTS.md was found in the repository or checked parent directories. In particular, the research `Instruction.txt` suggestions to modify code are historical document content, not an override of the user's preservation rule.

The inventory found pre-existing parse errors; they are recorded without modification:

- `ananya_research_work-main/SFT/test_length_zero_line_diffusion.py`: expected an indented block after function definition on line 406 (<unknown>, line 408)
- `ananya_research_work-main/SFT/test_p_advection_diffusion.py`: expected an indented block after function definition on line 561 (<unknown>, line 563)
- `ananya_research_work-main/SFT/test_p_diffusion.py`: expected an indented block after function definition on line 381 (<unknown>, line 383)
- `magnetofriction/model_input.py`: unterminated string literal (detected at line 1) (<unknown>, line 1)

These do not block the isolated pre-SFT audit. Missing optional SunPy map extras also do not block the coordinate-frame API used here. The actual environment is Python 3.12.7, NumPy 2.5.4, SciPy 1.18.1, Astropy 7.2.3, SunPy 8.0.1, Matplotlib 3.11.2.

All 221 raw synoptic file checksums pass; all DATASUM values pass. `available_inputs.json` distinguishes Astropy's post-header-parse verification from the independent raw-byte checksum investigation. The audited seven input maps have passing normal Astropy checks too. Cached full-disk HMI image SHA-256 values match the previous reports and the supplied metadata T_REC/T_OBS exactly.

Scientific evidence retrieved during the audit: SunPy official HMI/Carrington documentation, NASA's HMI product description and JSOC-SDP synoptic source pinned to commit `0cf0b90d354705ed866fdba040772b0d712de785`. The source snapshots and provenance live in `evidence/`; they are explanatory evidence, not the historic binary pipeline proven to have produced these FITS.

Original-file preservation is checked by hashes in the automated tests and again with `inventory.py --verify`. The verification compares the original file set and flags new files outside the audit tree. The same data and scripts remain in their original locations.

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/results.md (15,196 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/results.md", "bytes": 15196, "sha256": "cd97c144774093189f6c47f547c19c8728c6fd80648a88eca4d50cde4cdafb05", "line_endings": "CRLF", "utf8_bom": false} -->
`````markdown
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

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_correction_audit.md (8,513 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_correction_audit.md", "bytes": 8513, "sha256": "b9bea71e66d1d32fe658e6d8dd87e1b4d19f29de58fcaf26de8cf3380f26f15f", "line_endings": "CRLF", "utf8_bom": false} -->
`````markdown
# Pre-SFT Reconstruction: Coordinate Audit and Validation

## Goal

Audit the three-map synoptic reconstruction **before SFT**. Determine which proposed issues are genuine, quantify each correction independently and in combination, and determine whether any variant improves agreement with independent observations. **Never alter `ananya_research_work-main/` or any original research files.**

The original code's intended inputs are three adjacent Carrington-rotation (CR) synoptic magnetograms; the test workflow previously used **CR2119, CR2120, CR2121** with CR2120 central, then repeated for central CR2122 and CR2124. Use existing repo datasets and tools where possible. Preserve the original Ananya implementation as a reproducible reference; do not silently fix it.

## Three issues to audit

### 1. Latitude–colatitude mismatch (confirmed code-level inconsistency)

Ananya's `omega(theta)` uses a colatitude-based rotation law:

\[\omega(\theta)=0.18-2.3\cos^2\theta-1.62\cos^4\theta\quad\mathrm{deg/day}.\]

The reconstruction supplies a value derived from `arcsin(sin_latitude)`, i.e. **latitude** \(\lambda\), not colatitude \(\theta=90^\circ-\lambda\). The equivalent latitude-based law is:

\[\omega(\lambda)=0.18-2.3\sin^2\lambda-1.62\sin^4\lambda.\]

Verify the exact source lines and numerical behavior at latitude 0°, 30°, 60°, and ±90°. Correct the argument **or** rewrite the function, never both. Distinguish this coordinate error from all other changes.

### 2. Signed time offset / inverse longitude sampling (requires physical-convention verification)

Documented reconstruction:

\[\Delta t_A=(\phi-180^\circ)/(13.2^\circ/\mathrm{day}),\qquad\phi'_A=\phi+\omega\Delta t_A.\]

Carrington **central-meridian longitude decreases with time**; therefore the above \(\Delta t_A\) is conventionally **reference time minus observation time**, assuming the map-longitude direction and metadata are interpreted as expected. For backward **sampling** from target epoch to the location in the observed synoptic map, the candidate inverse mapping is

\[\phi'_{\rm sample}\approx\phi-\omega\Delta t_A,\]

or equivalently \(\phi+\omega(-\Delta t_A)\). **Do not assume this candidate is correct without deriving the mapping from feature trajectories and the actual FITS coordinate/time conventions.** The exact inverse may be implicit because observation time depends on sampled longitude; test exact versus first-order solutions if materially different. Verify sign using a synthetic feature with a known position, rotation rate, and observation epoch.

### 3. Neighboring-CR selection at the longitude seam (requires verification with CR chronology)

Documented code logic selects **previous CR for** \(\phi'<0^\circ\), **next CR for** \(\phi'>360^\circ\), and current CR otherwise. A candidate chronological reversal would select **next CR below 0°** and **previous CR above 360°**, after wrapping by ±360°. Verify this against real Carrington rotation numbering, the FITS longitude axis orientation, time ordering, and a simple synthetic time-tagged tracer. Beware that changing the longitude-remapping sign can also change which pixels cross seams; inspect both corrections jointly. Handle boundaries \(0^\circ\) and \(360^\circ\) deterministically, and report the number/area of pixels from each CR.

**Evidence discipline:** Issue 1 is a confirmed coordinate mismatch in the documented code. Issues 2 and 3 are **testable hypotheses**, not assumed proven bugs. Report *confirmed / refuted / conditional* with evidence, and distinguish a code error from a convention choice.

## Implementation and experiments

1. **Inventory first.** Read the original source, available reconstruction scripts, validator, FITS headers, reports, and relevant README. Identify actual paths and available CR triples. Reuse working infrastructure; avoid copying or rewriting the whole pipeline unless necessary.
2. Create a **new isolated audit folder**, e.g. `pre_sft_audit/`, for scripts, tests, figures, generated data, and Markdown reports. Do not edit `ananya_research_work-main/` or other existing files unless explicitly necessary and authorized; prefer making the audit self-contained.
3. Define one parameterized reconstruction with **three independent switches**: `fix_latitude`, `invert_sample_shift`, `reverse_cr_seam`. Preserve interpolation choices and all non-tested settings. Run baseline `000`, single fixes `100`, `010`, `001`, all pairs `110`, `101`, `011`, and all fixes `111`. Treat the original, untouched central CR map as an additional *no-reconstruction* baseline. If a switch proves invalid, still document the test but do not call it a correction.
4. Use the existing **cubic spline** reconstruction setup for the primary comparison. Explicitly check whether any original-grid interpolation/resampling differs from the reference implementation, so the baseline can actually reproduce it. If useful, include a limited linear-interpolation sensitivity check.
5. **Synthetic validation:** construct time-tagged analytic field patterns with known angular rotation and CR seam crossings, generate consistent mock synoptic maps, and recover the known reference-time field. Test northern/southern latitudes, the equator, longitude 0/360 boundaries, missing data, and sign conventions; do not manufacture conclusions from patterns designed only to favor a candidate.
6. **Observational validation:** where the files/tools exist, repeat for central CR2120, CR2122, CR2124 using matching HMI 45-second LOS observations at the documented reference epochs. Project observations to the same solar coordinates, compare radial estimates only in the **same valid pixel mask** for all variants (primary \(\mu\ge0.8\)). Apply consistent smoothing, LOS-to-radial approximation, interpolation, and quality masks. Report the actual observation times and FITS metadata; do not describe these observations as perfect ground truth. Optionally analyze larger \(\mu\) coverage separately, with clear projection-error caveats.
7. **Metrics per run and CR:** pixel count, physical surface-area fraction if supported by grid weights, bias (G), MAE (G), RMSE (G), Pearson correlation, optionally median absolute error and 95th-percentile |error|, and improvement percentages **relative both to the unmodified Ananya implementation and untouched central-map baseline**. Also report corrected-longitude statistics, wrap/seam-source fractions, representative \(B_r\) values at identical selected coordinates, and map differences. Do not confuse RMSE in gauss with percentage error.
8. **Fairness and checks:** Require a common pixel mask, same reference observation and epoch, same output grid, same interpolation order, and documented NaN policy. Confirm `000` reproduces the prior baseline to numerical tolerance or explain any disagreement. Check coordinate registration (especially the HMI FITS longitude-axis sign), Carrington time direction, and whether input synoptic products already have differential-rotation stretching. Report assumptions and unresolved limitations.

## Deliverables (all inside the isolated folder)

- `README.md`: setup, available inputs, exactly reproducible commands, and provenance; dependencies and any unavailable input data.
- `issue_verdicts.md`: evidence and clear verdict for **each** proposed issue, including derivation of temporal and seam conventions.
- `results.md`: concise numeric comparison tables per central CR and pooled/summary discussion; quantify independent and combined effects; discuss original-map baseline honestly.
- `metrics.csv`: one row per central CR × variant, with units and mask definition.
- `sample_br.csv`: at least a few identical positions with original/variant/reference \(B_r\) values (G) and coordinates, excluding invalid pixels.
- Diagnostic plots (maps, residuals, masks, and seam-source maps) and automated tests.
- A short `handoff.md` summarizing what was actually run, reproduction commands, key findings, caveats, and filenames to share for independent review.

**Do not invent missing observations, synthetic results, metrics, or resolved verdicts.** If data or dependencies are unavailable, perform all possible code/synthetic checks and explicitly enumerate what cannot yet be measured. Do not change Ananya's source or assert the full-Sun reconstruction has been observationally validated: the primary observed comparison only samples the near-disk-center region.

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/.gitattributes (179 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/.gitattributes", "bytes": 179, "sha256": "1467c12169aa7473efd7c6fc47e8fc7329f313d40b5d49c75c7efcb49070fdeb", "line_endings": "LF", "utf8_bom": false} -->
`````text
# Keep archived upstream source bytes identical to their recorded SHA-256 hashes.
# Preserve upstream whitespace as part of the evidence snapshots.
evidence/*.c -text -whitespace

`````
<!-- END_ARCHIVED_TEXT -->

</details>

<details>
<summary>pre_sft_audit/.gitignore (91 bytes)</summary>

<!-- ARCHIVED_TEXT {"path": "pre_sft_audit/.gitignore", "bytes": 91, "sha256": "4a3de3f45fff9623df9b16d9df5791b016e2c73d9f158494ae027f533b82aa1e", "line_endings": "LF", "utf8_bom": false} -->
`````text
# Large outputs remain available locally and can be regenerated.
arrays/
review_bundle.zip

`````
<!-- END_ARCHIVED_TEXT -->

</details>

## 17. Consolidation verification

This record preserves **50 original text files** (including the historical root brief) and all **534 CSV data rows**. Each archive entry was reconstructed in memory and checked against its source bytes and SHA-256; JSON and CSV payloads were parsed successfully. No numerical experiments were rerun for the consolidation, no new measurements were inferred, and no source file was moved, removed or overwritten. The audit interpretation remains conditional exactly where the original findings were conditional.
