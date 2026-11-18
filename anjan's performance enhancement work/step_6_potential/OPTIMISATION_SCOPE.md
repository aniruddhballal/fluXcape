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
- No separate timing for the three output groups has been established. The earlier conversational estimate of approximately 99% / 1% / less than 0.1% was speculative, not measured evidence; do not use it to claim a bottleneck or speedup.
- Measure the scoped original workload before claiming improvements. Compare candidates on matching inputs, hardware, numerical settings and execution boundaries.
- Preserve original source and fixed inputs; develop candidates separately. Check candidate numerical outputs against the original before accepting an improvement, including layouts and finite/NaN behaviour. Do not silently relax tolerances or change precision, boundaries or stopping rules to obtain a speedup.

## Communication and next action

The user requests answers as short as possible, accurate, and explicit about uncertainty; avoid unsupported assumptions or invented timings.

Commit completed changes whenever files are created or modified. Finish the requested task, including its commit, before handing back to the user.

The user subsequently authorised implementation using the same entry point (`measure_potential.py`), an original default path, and a selectable separate optimised implementation with minimal runner changes. The candidate now exists as `optimised_laplace.py`; use `--implementation original|optimised` and `--first-field-only` for this narrowed workload. Existing commands retain the complete step 6 behaviour. See README.md for usage and validation limits. Full-observation equivalence and performance acceptance remain pending; do not treat the candidate as an accepted speedup.

## First optimisation implementation

Implemented in commit `e17895f`, with the intent of reducing time per Jacobi iteration while retaining the original equations and numerical behaviour:

- `measure_potential.py` remains the entry point. `--implementation original` is the default; `--implementation optimised` selects the separate candidate. `--first-field-only` stops either path immediately after the first three saves. Without it, the existing complete step 6 workload remains available.
- The runner copies source and inputs into an isolated run directory. For the optimised path, it inserts a solver import override into the generated script. Anjan's original source files are unchanged.
- `optimised_laplace.py` uses a Numba-compiled CPU kernel (`njit`, `parallel=True`, `fastmath=False`). It parallelises independent x planes within each Jacobi update; successive iterations remain sequential.
- Two potential buffers are allocated and swapped between iterations, avoiding a full potential copy every iteration. The cell update and maximum-change scan share one traversal, avoiding the original full-volume arithmetic temporaries and separate difference array. Per-plane errors are reduced using NumPy's maximum.
- The candidate retains float64, the original expression order, fixed boundary values, convergence tolerance and iteration limit. Unsupported layouts/types or nonfinite initial values fall back to the original solver. Gradients, scaling and file saves remain the original code.
- Numba is an optional dependency listed in `requirements-optimised.txt`. Compilation and CSV logging are included in measured runtime. `NUMBA_NUM_THREADS` controls the candidate's worker count when set before launch.
- Reports identify the implementation and workload boundary and retain source hashes, dependency versions, output hashes and timing information.

Five tests in `test_implementations.py` passed locally. They cover bit-identical potential values over fixed iteration counts, matching convergence iteration and logged maximum changes, unchanged inputs, nonfinite fallback, overflow behaviour, one/two-thread execution, and runner dispatch. The first three saved files were byte-identical between original and optimised paths on a small fixture; the original default full-step path also produced its nine expected files. These are fixture results, not full-observation validation. No full-input speedup has been measured.

## User's question after the first implementation

Record only; the user explicitly requested that this question remain unanswered here and in chat for this documentation task.

Could this optimised version be further optimised using OpenMP (OMP), MPI or CUDA, and would that improve performance even more dramatically?
