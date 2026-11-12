# Pre-SFT reconstruction changes: quantitative justification

**Study date:** 12 November 2026 (Asia/Kolkata)  
**Compared implementations:** Ananya's reconstruction in `ananya's research work/SFT/SFT.py` versus my pre-SFT reconstruction, historically `my work/pre-sft/main.py` and currently retained as `my work/pre_sft_reconstruction/reconstruct_synoptic_map.py`.

This is the source of truth for the stepwise ablation. The original implementation files were not modified; the superseded accuracy-comparison archive was removed after its purpose was consolidated here.

## Executive conclusion

The complete reconstruction (V6, mine) is substantially better than Ananya's V0 under the controlled synthetic ground truth:

- RMSE fell from **17.7057 G to 7.1335 G**, a cumulative **59.71% reduction**.
- MAE fell from **8.9584 G to 2.2526 G**, a cumulative **74.86% reduction**.
- Pearson correlation increased from **0.2857 to 0.8845**.

The result supports the overall claim that the complete set of changes materially improves the reconstruction. It does **not** support the stronger claim that every individual change improves every metric monotonically. Neighbor selection was neutral/slightly worse in the pooled synthetic score, and the exact denominator reduced RMSE by 0.22% while improving MAE by 4.71%. Those negative or mixed effects are retained here rather than hidden.

For observations, literal V0–V5 are not numerically comparable because Ananya's global tensor spline receives NaNs from the FITS maps and produces no finite scored output. A separate nearest-filled diagnostic makes the stepwise observational trend measurable, but it is explicitly not the literal Ananya implementation.

## What changed relative to Ananya's code

The versions are cumulative: each version retains all earlier changes and introduces one additional change.

| Version | Cumulative implementation |
|---|---|
| V0 | Ananya's original latitude interpretation, neighboring-CR branch order, source-longitude sign, denominator, idealized coordinate arrays, and `RectBivariateSpline`. |
| V1 | Correct the differential-rotation argument from latitude to colatitude. |
| V2 | Correct neighboring Carrington-rotation selection: negative unwrapped source longitudes use the next CR; values above 360° use the previous CR. |
| V3 | Correct the source-longitude sign: `phi_src = phi_dest - omega * delta_t`. |
| V4 | Use the exact denominator `delta_t = (phi_dest - 180°) / (omega_0 + omega)`. |
| V5 | Use longitude and latitude centers read from the FITS WCS/header rather than `linspace`/idealized grids. |
| V6 | Use the mine's gap-preserving longitude `CubicSpline` construction over the three neighboring maps. This is the final mine implementation. |

### Logical rationale

1. **Latitude → colatitude.** The differential-rotation law is defined with `cos(theta)` where `theta` is colatitude. Passing latitude changes the rotation rate, especially away from the equator, so the backward sample is taken from the wrong longitude.

2. **Neighboring CR selection.** The three maps occupy consecutive unwrapped longitude intervals. The original branch labels the previous rotation as the negative-longitude source and the next rotation as the greater-than-360° source, reversing the temporal neighbor identity.

3. **Source-longitude sign.** Backward sampling must undo the rotation between the source observation time and the reference time. The original plus sign moves the sample in the wrong direction; the corrected expression subtracts the differential-rotation displacement.

4. **Exact denominator.** The source-time relation contains the reference-frame rate and the latitude-dependent differential rate, so the denominator is `omega_0 + omega(theta)`, not only `omega_0`. This is a small correction numerically but is the consistent solution of the time/longitude relation.

5. **FITS coordinate grids.** The actual FITS header defines the pixel centers and the sin(latitude) sampling. Replacing these with idealized endpoint-inclusive arrays introduces coordinate offsets and treats the longitude axis as if it had a different sampling geometry.

6. **Interpolation method.** The mine's longitude-only, gap-preserving splines avoid global contamination by missing pixels and preserve the correct map identity across the unwrapped longitude axis. This is also why V6 remains valid on raw FITS inputs where Ananya's global spline does not.

## Stepwise quantitative results

Error reduction is defined as:

`100 × (previous RMSE or MAE − current RMSE or MAE) / previous RMSE or MAE`.

Positive values mean lower error; negative values mean worse error. Correlation is reported as the absolute change in Pearson *r* rather than as a percentage error reduction.

### Pooled synthetic validation

The synthetic pool contains 12 existing analytic cases: constant, smooth, fine-structure, and bipolar fields, each at rotation factors 0, 1, and 0.7. Every version is evaluated against the same analytic truth on the same full 360×720 grid; total pooled sample count is 3,110,400.

| Change | RMSE change | MAE change | correlation change | Interpretation |
|---|---:|---:|---:|---|
| V0 → V1: colatitude | **+37.02%** | **+44.79%** | +0.4261 | Major improvement; fixes the rotation-law coordinate. |
| V1 → V2: neighboring CR selection | **−0.22%** | **−0.20%** | −0.0012 | Slight pooled degradation; logically correct, but not independently beneficial for every synthetic case/metric. |
| V2 → V3: source-longitude sign | **+35.84%** | **+50.77%** | +0.1725 | Major improvement; fixes the direction of backward sampling. |
| V3 → V4: exact denominator | **−0.22%** | **+4.71%** | −0.00025 | Mixed: slightly worse RMSE but meaningfully better MAE. |
| V4 → V5: FITS grids | **+0.74%** | **+3.11%** | +0.0017 | Small but consistent improvement from physical pixel coordinates. |
| V5 → V6: interpolation method | **+0.00014%** | **+0.0064%** | +0.0000003 | Numerically negligible on finite synthetic data; important for missing-data robustness. |

| Version | RMSE (G) | MAE (G) | Pearson r | Cumulative RMSE reduction | Cumulative MAE reduction |
|---|---:|---:|---:|---:|---:|
| V0 Ananya | 17.7057 | 8.9584 | 0.2857 | 0.00% | 0.00% |
| V1 | 11.1518 | 4.9461 | 0.7118 | 37.02% | 44.79% |
| V2 | 11.1763 | 4.9560 | 0.7105 | 36.88% | 44.68% |
| V3 | 7.1711 | 2.4400 | 0.8830 | 59.50% | 72.76% |
| V4 | 7.1869 | 2.3250 | 0.8828 | 59.41% | 74.05% |
| V5 | 7.1335 | 2.2527 | 0.8845 | 59.71% | 74.85% |
| V6 Mine | 7.1335 | 2.2526 | 0.8845 | **59.71%** | **74.86%** |

### Observational validation

The observational set uses the three existing 2017-06-09 HMI times and both validated reference constructions at each time: LOS radial proxy and vector radial reference. The same stored `mu > 0.7` mask is used for every version and every reference; the pooled scored count is 231,218.

#### Literal raw-FITS result

V0–V5 have zero finite scored pixels on the raw FITS maps because Ananya's global `RectBivariateSpline` is contaminated by NaNs. They are **invalid**, not zero-error results and not comparable baselines. V6 is valid:

| Version | RMSE (G) | MAE (G) | Pearson r | Status |
|---|---:|---:|---:|---|
| V0–V5 | — | — | — | Invalid on raw FITS inputs: no finite output |
| V6 Mine | 23.4898 | 11.3425 | 0.4064 | Valid |

#### Nearest-filled diagnostic

For attribution only, each source map was nearest-filled before running all seven versions. This removes the NaN failure mode but is an external input adaptation and must not be interpreted as literal V0 behavior.

| Change | RMSE change | MAE change | correlation change |
|---|---:|---:|---:|
| V0 → V1: colatitude | **+22.98%** | **+12.23%** | +0.4291 |
| V1 → V2: neighboring CR selection | 0.00% | 0.00% | 0.0000 |
| V2 → V3: source-longitude sign | **+2.24%** | **+1.58%** | +0.0326 |
| V3 → V4: exact denominator | **+0.02%** | **−0.02%** | +0.0001 |
| V4 → V5: FITS grids | −0.00% | +0.00% | +0.000004 |
| V5 → V6: interpolation method | −0.00% | 0.00% | approximately 0 |

The filled diagnostic changes from V0 RMSE **31.2039 G**, MAE **13.1288 G**, *r* **−0.0554** to V6 RMSE **23.4898 G**, MAE **11.3425 G**, *r* **0.4064**: **24.72% lower RMSE**, **13.61% lower MAE**, and a +0.4618 increase in correlation. The raw-FITS V6 result agrees with the finite V6 diagnostic because the scored mask excludes V6's missing output cells.

## How the test was performed

- **Endpoint tested:** the reconstructed central synoptic map before Ananya's later SFT grid initialization, vector potential construction, flow evolution, diffusion, or time stepping. No full SFT simulation was run.
- **Source maps:** CR2190, CR2191, and CR2192 HMI radial synoptic FITS maps, 360×720 pixels, with CR2191 as the target/reference rotation.
- **Synthetic truth:** analytic magnetic fields were generated independently of either implementation, then sampled into the three neighboring rotations using the existing validation acquisition-time model. The same truth was used for all V0–V6 versions.
- **Observational truth:** the existing validated LOS-radial-proxy and vector-radial reference arrays for 10:48, 11:00, and 11:12 TAI on 9 June 2017. The same stored mask was reused for all versions.
- **Metrics:** RMSE and MAE are in gauss; correlation is Pearson *r*. Percentage changes compare adjacent cumulative versions. No version was allowed to choose a more favorable mask.
- **Scope:** exactly seven cumulative versions, V0–V6. No 64-combination factorial study was run.
- **Execution date:** 12 November 2026, using the local project virtual environment. The ablation runner evaluated the reconstruction functions directly and did not execute the SFT time-evolution code.

## Final justification

The strongest evidence is the controlled synthetic comparison: the final mine implementation reduces RMSE by 59.71%, reduces MAE by 74.86%, and raises correlation from 0.2857 to 0.8845 relative to Ananya's V0. The largest gains come from the colatitude interpretation and source-longitude sign, exactly where the physical mapping is otherwise wrong. FITS-grid handling provides a smaller additional gain, while the interpolation change is primarily a robustness correction for missing data rather than a large finite-data accuracy change.

The evidence does **not** justify saying that every individual change is independently better on every metric. The correct statement is: **the complete set of changes is substantially better overall, the major physical corrections produce the dominant gains, and the few neutral or negative individual deltas are documented and understood rather than omitted.**

