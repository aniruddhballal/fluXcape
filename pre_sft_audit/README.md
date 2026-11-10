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
