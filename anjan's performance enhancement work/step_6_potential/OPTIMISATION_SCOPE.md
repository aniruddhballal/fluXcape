# Current optimisation scope

User-confirmed scope, recorded 18 November 2026. Read this before continuing performance work in step 6. This narrows the broader project brief; it does not authorise work on other stages.

## Objective and priority

Optimise execution time for only the first output group within step 6: the iterative potential solve, magnetic-field gradients and scaling. Time is the current priority. The user does not currently consider memory usage a problem; memory optimisation is deferred until later.

Anjan supplied the scientific code. The user has spent time understanding its mathematics and measuring stage runtimes and is now beginning performance enhancement. Preserve the existing mathematics, numerical settings, boundary treatment, scaling conventions and output behaviour. Scientific corrections are outside this task.

Accuracy is a strict user priority: performance improvements must involve zero or very close to zero accuracy tradeoff relative to the original implementation. Aim for bit-identical results where feasible. If a candidate differs numerically, quantify the differences and establish that they satisfy this requirement before accepting it; do not assume a small difference is acceptable or sacrifice accuracy for speed.

## Exact boundary

Relevant original source directory:

`../hmi.sharp_cea_720s.4698.20141022_000000_TAI/`

The scope starts with the initial grid/potential setup in `Main.py` and ends immediately after saving:

1. `PFSSmagneticfield/Bfield_full/Bx_full.npy`
2. `PFSSmagneticfield/Bfield_full/By_full.npy`
3. `PFSSmagneticfield/Bfield_full/Bz_full.npy`

Included operations:

- Load the existing `Preprocessedmagneticfield/Bz.npy` input; do not regenerate it.
- Set up the 300 x 300 x 150 potential grid and existing boundary values.
- Execute `laplace.py::solve_pfss_cartesian_vectorized`, the Jacobi Laplace solver actually called by `Main.py`, with the existing tolerance (1e-3) and iteration limit (100000).
- Calculate the three components with the existing negative gradients and `edge_order=2`.
- Apply the existing scaling and save the first three arrays.
- Inspect or change only files, functions, variables and data relevant to these operations, including necessary isolated measurement/candidate tooling.

Excluded operations:

- The subsequent 3D interpolation and its three outputs under `PFSSmagneticfield_for_uniform_grid/`.
- The subsequent 2D boundary interpolation and its three outputs under `Preprocessedmagneticfield_interpolated/`.
- Every other pipeline stage, including reconstruction, convergence behaviour and restart work in step 7. Runs on another device are outside this task.
- Unused solver implementations and unrelated analysis or visualisation work.

The second output group derives from the first group; the third derives separately from the supplied 2D boundary inputs. Neither is part of the present optimisation workload.

## Measurement and validation

- The recorded 2273.691901564 seconds (37 min 53.69 s) measures the whole of step 6, including both excluded interpolation groups. It is not a measured runtime for this narrower workload.
- The Windows original first-field-only baseline completed on 18 November 2026: run `20261118_194031_937624`, report `potential_20261118_194031_937624.md`, wall time 6930.6786912 s (1 h 55 min 30.68 s), sampled peak RSS 747954176 bytes, exit code 0, all three outputs present. Its log reports convergence at zero-based label 16975 (16976 updates). It used the saved inputs from `../step_4_package/runs/20261118_192252_109811`. The optimised comparison used exactly these inputs; their hashes differ from the historical Ubuntu inputs. See the completed full-input comparison below.
- No separate timing for the three output groups has been established. The earlier conversational estimate of approximately 99% / 1% / less than 0.1% was speculative, not measured evidence; do not use it to claim a bottleneck or speedup.
- Measure the scoped original workload before claiming improvements. Compare candidates on matching inputs, hardware, numerical settings and execution boundaries.
- Preserve original source and fixed inputs; develop candidates separately. Check candidate numerical outputs against the original before accepting an improvement, including layouts and finite/NaN behaviour. Do not silently relax tolerances or change precision, boundaries or stopping rules to obtain a speedup.

## Communication and next action

The user requests answers as short as possible, accurate, and explicit about uncertainty; avoid unsupported assumptions or invented timings.

Commit completed changes whenever files are created or modified. Finish the requested task, including its commit, before handing back to the user.

The user subsequently authorised implementation using the same entry point (`measure_potential.py`), an original default path, and a selectable separate optimised implementation with minimal runner changes. The implementation now exists as `optimised_laplace.py`; use `--implementation original|optimised` and `--first-field-only` for this narrowed workload. Existing commands retain the complete step 6 behaviour. Full-input output equivalence has now been verified for one matched Windows run pair, with an observed speedup; repeated-trial performance validation remains outstanding. See README.md and the comparison report for limits.

## First optimisation implementation

Implemented in commit `e17895f`, with the intent of reducing time per Jacobi iteration while retaining the original equations and numerical behaviour:

- `measure_potential.py` remains the entry point. `--implementation original` is the default; `--implementation optimised` selects the separate candidate. `--first-field-only` stops either path immediately after the first three saves. Without it, the existing complete step 6 workload remains available.
- The runner copies source and inputs into an isolated run directory. For the optimised path, it inserts a solver import override into the generated script. Anjan's original source files are unchanged.
- `optimised_laplace.py` uses a Numba-compiled CPU kernel (`njit`, `parallel=True`, `fastmath=False`). It parallelises independent x planes within each Jacobi update; successive iterations remain sequential.
- Two potential buffers are allocated and swapped between iterations, avoiding a full potential copy every iteration. The cell update and maximum-change scan share one traversal, avoiding the original full-volume arithmetic temporaries and separate difference array. Per-plane errors are reduced using NumPy's maximum.
- The candidate retains float64, the original expression order, fixed boundary values, convergence tolerance and iteration limit. Unsupported layouts/types or nonfinite initial values fall back to the original solver. Gradients, scaling and file saves remain the original code.
- Numba is an optional dependency listed in `requirements-optimised.txt`. Compilation and CSV logging are included in measured runtime. `NUMBA_NUM_THREADS` controls the candidate's worker count when set before launch.
- Reports identify the implementation and workload boundary and retain source hashes, dependency versions, output hashes and timing information.

Five tests in `test_implementations.py` passed locally. They cover bit-identical potential values over fixed iteration counts, matching convergence iteration and logged maximum changes, unchanged inputs, nonfinite fallback, overflow behaviour, one/two-thread execution, and runner dispatch. The first three saved files were byte-identical between original and optimised paths on a small fixture; the original default full-step path also produced its nine expected files. The full-input comparison below was completed subsequently.

## Completed Windows full-input comparison

The optimised run `20261118_214427_942015` completed successfully in 540.392198 s (9 min 0.39 s), including any JIT compilation. Compared with the matched original run, this is an observed 12.8253x wall-time speedup (92.2029% reduction). Both used the same inputs, original source snapshots, workload boundary and Windows system. Both stopped at zero-based iteration label 16975.

All three output files were independently rehashed and compared: byte-identical SHA-256 hashes, float64 shape `(300, 300, 150)`, 40,500,000 total finite values, zero maximum absolute difference, and bit-identical elements. All 340 logged convergence samples match in iteration label and full-precision maximum change. The exact final stopping-update error and scalar potential were not saved; do not claim direct comparisons of those unsaved quantities. Sampled peak RSS fell from 713.30 to 659.18 MiB. CPU time fell from 6895.20 to 5460.59 sampled CPU seconds; parallel CPU seconds sum work across cores.

See [comparison_windows_20261118.md](comparison_windows_20261118.md) for full metrics, component ranges/hashes, progress samples, environment and limitations. This is one run per implementation, not a repeated-trial median. The actual Numba worker count was not recorded; `OMP_NUM_THREADS=8` alone does not establish it. The question below remains unanswered.

## Second optimisation after device inspection

The user requested inspection of this device and a separate second optimised implementation (third solver overall) if further gains could be demonstrated. The relevant device is an HP Victus with Ryzen 5 5600H (6 cores/12 logical processors), one 8 GiB RAM module configured at 3200 MT/s, GTX 1650 with 4 GiB VRAM and Windows 11. See [device_and_v2_windows_20261118.md](device_and_v2_windows_20261118.md) for the inventory, raw benchmark link and limitations. Numba's CUDA compiler runtime is unavailable locally; no GPU performance claim is made.

`optimised_laplace_v2.py` is selected through the same runner with `--implementation optimised-v2 --first-field-only`. Original remains the default; the original code and version 1 module are unchanged. V2 preserves the float64 field expression, arithmetic order, gradients, scaling, boundary values and stopping rule. It replaces the floating maximum recurrence with an exact unsigned ordering of the nonnegative float64 error bit patterns, viewed back as float64 for the stopping comparison. This allows SIMD with fast-math disabled; it does not lower precision. NaN handling and exceptional-input fallbacks are covered by tests.

Three 60-update full-grid trials per implementation at 1, 2, 4, 6, 8 and 12 workers all produced bit-identical potentials and error histories. Four workers gave the lowest v2 median in this sweep, so v2 defaults to up to four workers. An explicit `NUMBA_NUM_THREADS` overrides this choice. Actual worker count and threading layer are recorded in `solver_runtime.json` and the run report. Seven unit/integration tests passed, covering all three selectors.

The full v2 observation run `20261118_221042_587814` subsequently completed successfully in 408.8075312 s (6 min 48.81 s), with four workers and threading layer `omp`. Compared with the recorded v1 run, it was 1.3219x faster (24.3498% less wall time); compared with the original it was 16.9534x faster. Sampled CPU time was 1581.125 s and sampled peak RSS 656.18 MiB. Independent file hashes and array-bit comparisons confirmed all three files are byte-identical across original, v1 and v2: all 40,500,000 field values finite and identical, maximum absolute difference zero. All 340 logged iteration/error pairs match, and all three runs stop at zero-based label 16975 (16976 updates). The scalar potential and exact stopping-update error were not saved. The full-run measurements are single trials, not repeated medians or proof of a global optimum. Detailed results are in the device/v2 report linked above. V2 code was committed as `04b550b` and its successful run report as `a541874`.

## User's question after the first implementation

Record only; the user explicitly requested that this question remain unanswered here and in chat for this documentation task.

Could this optimised version be further optimised using OpenMP (OMP), MPI or CUDA, and would that improve performance even more dramatically?
