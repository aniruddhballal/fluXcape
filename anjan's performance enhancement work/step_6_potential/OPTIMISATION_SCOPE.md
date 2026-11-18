# Current optimisation scope

User-confirmed scope, recorded 18 November 2026. Read this before continuing performance work in step 6. This narrows the broader project brief; it does not authorise work on other stages.

## Objective and priority

Optimise execution time for only the first output group within step 6: the iterative potential solve, magnetic-field gradients and scaling. Time is the current priority. The user does not currently consider memory usage a problem; memory optimisation is deferred until later.

Anjan supplied the scientific code. The user has spent time understanding its mathematics and measuring stage runtimes and is now beginning performance enhancement. Preserve the existing mathematics, numerical settings, boundary treatment, scaling conventions and output behaviour. Scientific corrections are outside this task.

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

The immediate request was to document this scope before starting optimisation work. At the time of writing, no optimisation has been implemented for this narrowed task. The pending discussion is where time-based performance enhancement has the most scope within the included operations.
