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
