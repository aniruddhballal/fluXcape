# Performance improvement log

Append results here as each stage is improved. The methodology and project context are in [README.md](README.md). No stage has a completed before/after comparison yet; blank values mean unmeasured, not zero.

## Reporting scope

Original behaviour is the reference; preserve the existing mathematics and physics. Before any candidate exists, report the baseline measurements and execution outcome without demanding output-equivalence testing or scientific validation. After a change, check equivalence to the original. Flag execution failures, relevant measurement issues and regressions caused by our changes; do not elevate inherited warnings or conventions into performance blockers. See README.md for the full scope.

## Seven-stage tracker

| Step | Work | Files | Status |
| --- | --- | --- | --- |
| 1 | Compile preprocessor | `preproc.c` and C compiler | Original baseline measured on Linux; no candidate yet |
| 2 | Extract and resample FITS data | `fitsdataextraction.py` | Source reviewed; baseline tool ready; scientific dependencies needed |
| 3 | Preprocess surface field | Compiled `preproc` executable | Original baseline measured (one trial); no candidate yet |
| 4 | Package bottom-boundary arrays | `plot.py` | Original baseline measured (one trial); no candidate yet |
| 5 | Generate spatial weights | `weightfunction.py` | Original baseline measured (one trial); no candidate yet |
| 6 | Initial potential-field solve and grid/boundary preparation | First part of `Main.py`, `laplace.py` | 600-second partial baseline; no outputs yet |
| 7 | WSR reconstruction | Remaining `Main.py`, `vectormath.py` | Not started |

## Results summary

Use seconds for runtime, MiB for sampled peak RAM and generated storage. Report median runtime over repeated comparable trials, with trial count and sampling method in the detailed entry. Keep original and candidate measurements on the same machine with the same inputs and scientific settings.

| Step | Before time (s) | After time (s) | Time reduction (%) | Before peak RAM (MiB) | After peak RAM (MiB) | Output validation | Entry |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | 2.54995 (one trial) | | | 15.921875 | | Original outputs recorded | [Baseline](step_3_preprocess/preprocess_20261113_154914_817499.md) |
| 4 | 1.165231 (one trial) | | | 212.480469 | | Original arrays recorded | [Baseline](step_4_package/package_20261113_160555_320989.md) |
| 5 | 23.271376 (one trial) | | | 193.046875 | | Original weights recorded | [Baseline](step_5_weights/weights_20261113_163255_483855.md) |
| 6 | | | | | | | |
| 7 | | | | | | | |

Time reduction = `100 × (before − after) / before`; speedup = `before / after`. Negative reduction means slower. RAM reduction uses the same percentage formula, but RAM peaks are never added together.

Sum comparable, completed stage runtimes for an **estimated serial total**. Report the highest stage RAM peak separately. Until all stages have comparable measurements, label totals as partial. Short WSR trials estimate fixed-workload performance, not full convergence runtime. Splitting Main.py changes memory lifetimes and adds I/O; document the measured execution boundaries. Track storage separately and avoid counting reused inputs twice.

## Entry template

Copy this section below for each experiment. Retain unsuccessful or mixed results as well as accepted improvements. Update the tracker and summary only when the measurements and validation support the result.

### Step N — experiment title — YYYY-MM-DD

- **Status:** planned / measured / validated / accepted / rejected.
- **Purpose and change:** what was slow or memory intensive, what changed, and why it should help.
- **Code:** original and candidate commit IDs or source hashes; modified files and execution commands.
- **Machine/environment:** CPU, RAM, OS, Python/package/compiler versions, compiler flags and thread settings.
- **Fixed inputs:** observation, filenames/hashes, array shapes, grid and scientific parameters. Identify saved prerequisites reused in both versions.
- **Measurement scope:** exactly what is timed, included/excluded I/O, warm-up/cache treatment, repetition count and memory sampling method. Separate compilation from execution.
- **Workload completion:** completed / partial / early stop. For WSR, record requested and actual accepted steps, rejected attempts, stopping reason, checkpoint interval and objective behaviour.

| Metric | Original | Candidate | Change |
| --- | --- | --- | --- |
| Median wall time (s), trials and range | | | |
| Peak sampled process-tree RAM (MiB) | | | |
| CPU time (s), if measured | | | |
| Generated scientific output (MiB) | | | |
| Monitoring/log storage (MiB), if applicable | | | |

- **Candidate equivalence (only after a change):** compare with original outputs, including shapes, layout, finite/NaN masks and numerical differences/tolerances. For an unchanged baseline, write “not applicable; no candidate yet.” Preserve the existing scientific behaviour.
- **Decision:** accept/reject/defer, with tradeoffs and limitations.
- **Evidence:** paths to retained reports/results or commit references; do not commit large generated data.
- **Next action:** remaining checks or the next experiment.

## Completed experiments

### Step 1 — original compilation baseline — 2026-11-13

- **Status:** baseline measured; no performance change or candidate comparison.
- **Command:** `python3 "anjan's performance enhancement work/step_1_compile/measure_compile.py"`.
- **Environment:** local Linux host, GCC 13.3.0, `-O3`, no OpenMP. Full platform and source hash are in the report; this is not the earlier Windows host.
- **Scope:** three consecutive compilations, GNU time backend; source copying/hash/report overhead excluded. Source unchanged; executable was not run.
- **Median wall time:** 0.142465 s (range 0.139224–0.189277 s).
- **Median CPU time:** 0.13 s.
- **Maximum recorded RSS:** 42.49 MiB, largest individual process peak across compilation tree, not simultaneous tree total.
- **Executable size:** 28,912 bytes in each trial.
- **Build outcome:** all three succeeded. Warnings flag unchecked `fscanf` return values at preproc.c lines 350 and 361; not fixed in this experiment.
- **Validation:** successful compilation and unchanged source hash; executable behaviour/numerical results remain for step 3.
- **Evidence:** [full report](step_1_compile/compile_20261113_113407_004146.md); raw logs and measurements remain locally under the ignored runs directory.
- **Next:** measure on the target machine if needed; prioritise expensive execution stages rather than spending substantial effort accelerating this one-time build.

The earlier 300-second end-to-end attempt stopped during extraction and is not a completed stage timing or a before/after comparison.

## Step 2 preparation — 2026-11-13

[step_2_extract/](step_2_extract/) contains the original-stage description and extraction-only measurement script. The original scientific source is unchanged. Lightweight fixture smoke checks covered isolated output/report generation and timeout cleanup. Scientific execution is pending: the current system Python lacks NumPy, SciPy, Matplotlib and Astropy. No runtime, RAM baseline or speedup is claimed yet.

### Step 3 — original preprocessing baseline — 2026-11-13

- **Status:** one successful original trial; no optimisation or before/after comparison.
- **Inputs:** existing step 1 trial-1 executable, GCC 13.3.0 with -O3 and no OpenMP; step 2 resampled maps from run 20261113_120212_837984. Executable/input hashes verified against saved originals.
- **Scope:** execution only; compilation, extraction, copying and hashing excluded. GNU time on the local Linux host.
- **Wall time:** 2.549950 s. **CPU time:** 2.53 s. **Peak RSS:** 15.921875 MiB.
- **Generated scientific outputs:** two files, 8,631,434 bytes (8.231577 MiB); copied input files excluded.
- **Validation:** expected 90,000 points, finite field values and preserved output coordinates. Bpre.dat and Bfield_processed.dat use transposed axis orders; after alignment their differences are consistent with text rounding (max 0.0005000000001 G). The existing output conventions are retained as baseline behaviour, not a blocker or a proposed scientific correction.
- **Limitations:** iteration count and objective history are not printed at the original verbosity. One trial is not a repeated median baseline.
- **Evidence:** [full baseline report](step_3_preprocess/preprocess_20261113_154914_817499.md), logs and raw measurements under its ignored run directory.

### Step 4 — original boundary packaging baseline — 2026-11-13

- **Status:** one completed original trial; no optimisation or candidate comparison.
- **Scope:** plot.py only, using saved step 2 interpolated maps and step 3 Bfield_processed.dat. No prior or subsequent stages ran.
- **Wall time:** 1.165231 s. **CPU time:** 3.05 s. **Peak RSS:** 212.480469 MiB (GNU time).
- **Outputs:** three 300×300 NumPy component arrays, 2,160,384 bytes (2.060303 MiB). Copied inputs excluded.
- **Plotting:** contour construction and layout included; Agg disables interactive display/wait. No plot files are saved by the original script.
- **Baseline checks:** all three arrays are finite and exactly match the reshape/transpose operations in unchanged plot.py; source/input hashes recorded. No candidate equivalence check is needed yet.
- **Evidence:** [full report](step_4_package/package_20261113_160555_320989.md); logs and measurements in its ignored run directory.

### Step 5 — original weight generation baseline — 2026-11-13

- **Status:** one successful original trial; no candidate or performance changes yet.
- **Processor:** unchanged weightfunction.py. No data-file inputs; grid/taper settings are in source. No earlier or later stages ran.
- **Wall time:** 23.271376 s. **CPU time:** 25.18 s. **Peak RSS:** 193.046875 MiB (GNU time).
- **Output:** weight_function/W.npy, 108,000,128 bytes (102.996948 MiB), float64 shape 300×300×150 (13.5 million weights). All values finite; observed range 0.0–1.0.
- **Scope:** weight calculation, saving and original contour/layout work included; Agg disables interactive window display/wait. Source copying and output hashing excluded.
- **Baseline provenance:** original source hash verified unchanged; output hash and environment in report. No candidate equivalence check is due yet.
- **Evidence:** [full report](step_5_weights/weights_20261113_163255_483855.md); raw measurements/log/output in the ignored run directory.

### Step 6 — time-limited original baseline — 2026-11-13

- **Status:** partial; stopped at the requested 600-second execution limit during the initial Laplace solve. No WSR or earlier steps ran.
- **Input:** saved step 4 boundary arrays, run 20261113_160555_320989. Main.py, laplace.py and vectormath.py copied unchanged; exact Main.py prefix ends before line 154.
- **Measured elapsed time:** 600.045567 s; not a completed stage runtime. **Peak sampled process-tree RSS:** 638.625000 MiB (100-ms psutil sampling). **Sampled cumulative CPU:** 603.64 s. GNU time final counters are unavailable after process-group termination.
- **Last logged iteration:** 4350 (zero-based solver label); max update/error 0.0157, versus stopping tolerance 0.001 (15.7 times the threshold). Progress prints every 50 iterations, so this is the last reported label, not the exact iteration reached at termination.
- **Generated field outputs:** none; the solve had not returned to the output-writing code. No unfinished potential checkpoint exists. Step 7 needs a completed compatible set of step 6 outputs before it can run.
- **Evidence:** [partial run report](step_6_potential/potential_20261113_164206_525807.md); original progress log and sampled counters in its ignored run directory. No extrapolated completion time or speedup is claimed.
