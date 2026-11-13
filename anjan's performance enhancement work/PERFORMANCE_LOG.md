# Performance improvement log

Append results here as each stage is improved. The methodology and project context are in [README.md](README.md). No stage has a completed before/after comparison yet; blank values mean unmeasured, not zero.

## Seven-stage tracker

| Step | Work | Files | Status |
| --- | --- | --- | --- |
| 1 | Compile preprocessor | `preproc.c` and C compiler | Not started |
| 2 | Extract and resample FITS data | `fitsdataextraction.py` | Not started |
| 3 | Preprocess surface field | Compiled `preproc` executable | Not started |
| 4 | Package bottom-boundary arrays | `plot.py` | Not started |
| 5 | Generate spatial weights | `weightfunction.py` | Not started |
| 6 | Initial potential-field solve and grid/boundary preparation | First part of `Main.py`, `laplace.py` | Not started |
| 7 | WSR reconstruction | Remaining `Main.py`, `vectormath.py` | Not started |

## Results summary

Use seconds for runtime, MiB for sampled peak RAM and generated storage. Report median runtime over repeated comparable trials, with trial count and sampling method in the detailed entry. Keep original and candidate measurements on the same machine with the same inputs and scientific settings.

| Step | Before time (s) | After time (s) | Time reduction (%) | Before peak RAM (MiB) | After peak RAM (MiB) | Output validation | Entry |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |
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

- **Numerical validation:** reference outputs, shapes, finite/NaN masks, maximum/relative differences, tolerances and relevant physical diagnostics. Explain any scientific changes separately; lower runtime alone is not sufficient.
- **Decision:** accept/reject/defer, with tradeoffs and limitations.
- **Evidence:** paths to retained reports/results or commit references; do not commit large generated data.
- **Next action:** remaining checks or the next experiment.

## Completed experiments

None recorded yet. The earlier 300-second end-to-end attempt stopped during extraction and is not a completed stage timing or a before/after comparison.
