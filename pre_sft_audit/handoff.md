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
