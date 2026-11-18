# Step 6: initial potential field and grid preparation

For current optimisation work, read [OPTIMISATION_SCOPE.md](OPTIMISATION_SCOPE.md) first: the user has narrowed the task to the initial solve, gradients and scaling that produce the first three field files, with execution time as the priority.

## Selecting the implementation

The existing entry point and original default remain available. Existing commands still run the complete step 6 and produce nine arrays. To measure only the first three arrays, use `--first-field-only` with either implementation:

```bash
python "anjan's performance enhancement work/step_6_potential/measure_potential.py" --input-dir "PATH_TO_EXISTING_INPUT_RUN" --implementation original --first-field-only --max-seconds 0
python "anjan's performance enhancement work/step_6_potential/measure_potential.py" --input-dir "PATH_TO_EXISTING_INPUT_RUN" --implementation optimised --first-field-only --max-seconds 0
```

Install the optional dependency in the active environment before selecting `optimised`:

```bash
python -m pip install -r "anjan's performance enhancement work/step_6_potential/requirements-optimised.txt"
```

Version 2 is selected with `--implementation optimised-v2`, using the same entry point, optional dependency and input directory. It lives separately in `optimised_laplace_v2.py`. The original and version 1 selectors retain their behaviour. V2 changes the error-maximum reduction to an exact ordering of nonnegative float64 bit patterns, enabling SIMD with fast-math disabled; the field update expression is unchanged. On the inspected Ryzen 5 5600H laptop, four workers gave the best v2 median in a six-configuration sweep. V2 therefore defaults to up to four workers; set `NUMBA_NUM_THREADS` explicitly to override it. Its `solver_runtime.json` and measurement report record actual worker count and threading layer. See [device inspection and v2 experiments](device_and_v2_windows_20261118.md) for measurements and validation limits.

The full Windows v2 run finished in 6 min 48.81 s versus v1's 9 min 0.39 s: 24.35% less wall time in these single completed runs. All three saved field files are byte-identical to both v1 and the original, with identical logged convergence and stopping label. V2's full report is [potential_20261118_221042_587814.md](potential_20261118_221042_587814.md).

Each optimised path copies its separate solver module into the isolated run and overrides only the active solver import. Anjan's source is unchanged. The kernels reuse two potential buffers, parallelise independent x planes, and combine the Jacobi update and maximum-change scan. They use float64, the original field expression order, and disabled fast-math. Gradients, scaling, saving and any requested interpolation remain the original code. Unsupported array layouts/types and nonfinite inputs fall back to the original solver.

Numba compilation is included in wall time. Each isolated run has its own copy/cache, so do not assume compilation is free. Set `NUMBA_NUM_THREADS` before launching to control the worker count; version 1 uses Numba's default, while v2 uses the default described above. More threads do not guarantee a faster solve. Reports record the implementation, workload boundary, solver hash, dependency versions and thread environment. `--check-only` checks prerequisites without running or compiling the kernel.

Small-fixture tests check bit-identical potential values, matching stopping iterations/progress, unchanged inputs, nonfinite fallback, and matching first-three output files through the runner. Run them with:

```bash
python -m unittest discover -s "anjan's performance enhancement work/step_6_potential" -p test_implementations.py -v
```

The subsequent [matched Windows full-input comparison](comparison_windows_20261118.md) verified byte-identical output files and matching logged convergence, with an observed 12.83x wall-time speedup (one completed run per implementation, not repeated medians). The historical 37 min 53.69 s Ubuntu report includes all nine outputs and is not a scoped baseline.

Runs only the initial-field/preparation section of the current Main.py. Step 7's WSR reconstruction is excluded; step 5's weights are not needed. Earlier stages do not rerun.

With the Python environment activated, from the repository root:

```bash
python "anjan's performance enhancement work/step_6_potential/measure_potential.py" --input-dir "PATH_TO_STEP_4_RUN" --max-seconds 600
```

The input directory must contain `Preprocessedmagneticfield/Bx.npy`, `By.npy`, `Bz.npy`. Dependencies: NumPy, SciPy, Matplotlib and psutil (already in this folder's requirements.txt). Options: `--check-only`, `--source-dir PATH`, `--label original`, and `--max-seconds` (default 600; zero means unlimited).

The runner copies Main.py, laplace.py, vectormath.py and the three surface arrays into an isolated ignored `runs/<timestamp>/`. It extracts the exact source prefix before the reconstruction grid setup: the final top-level Nx assignment before BxC is loaded. An AST check verifies this is an unchanged prefix and contains no WSR while loop. A substantially reorganised Main.py may require updating that interface; the runner does not alter original files or mathematical expressions.

The original grid remains 300×300×150; Laplace tolerance 1e-3 and limit 100,000 iterations are unchanged. The script constructs the initial field, resamples it into the reconstruction box, and resamples the surface boundary. A completed run writes nine arrays:

- `PFSSmagneticfield/Bfield_full/{Bx_full,By_full,Bz_full}.npy`: three initial 3D components.
- `PFSSmagneticfield_for_uniform_grid/Bfield_full/{Bx_full,By_full,Bz_full}.npy`: three resampled 3D components.
- `Preprocessedmagneticfield_interpolated/{Bx,By,Bz}.npy`: three resampled surface components.

Reports are `potential_<timestamp>.md`. Raw measurements.json, potential.log, copied files and generated arrays remain in the run directory. The log captures the solver's existing iteration progress. Output size excludes copied inputs and monitoring files. Copying/hash time is outside measured execution. GNU time reports largest individual process RSS on completion. A separate 100-ms psutil sample records tree RSS and CPU counters, including partial runs; shared pages can be double-counted and short-lived activity/peaks can be missed. These are distinctly named metrics in the report.

## Timestamped convergence data

New runs also write `convergence.csv` in their run directory. It records iteration labels **0, 50, 100, ...** at the solver's existing progress-print location:

| Column | Meaning |
| --- | --- |
| `timestamp` | Local timestamp including timezone offset. |
| `solver_elapsed_seconds` | Monotonic elapsed time since entry into the solver, including solver setup; excludes preceding script imports/setup. |
| `iteration` | Original zero-based iteration label. Label 0 is recorded after the first update, not before any work. |
| `max_change` | Full-precision maximum change between successive potential arrays (the existing logged error). |
| `interval_seconds` | Wall time since the previous logged entry; blank on the first row. |
| `iterations_since_previous` | Number of iteration updates between entries, normally 50; blank on the first row. |
| `mean_seconds_per_iteration` | Interval time divided by the iteration count; a block average, not individual iteration timings. Blank on the first row. |

Each row is written and closed immediately so it remains available while running and after interruption. Monitor with `tail -f "PATH_TO_RUN/convergence.csv"`, or open the CSV later to plot error against time/iteration. If convergence occurs between scheduled entries, the normal potential.log records the stopping message; the CSV contains only the scheduled entries. A killed run may end after the last logged label.

Only the isolated laplace.py copy receives logging instrumentation; an unmodified copy remains as laplace_original.py and the observation-folder source stays unchanged. AST checks verify the original solver statements are retained, and a small 101-iteration test produced bit-identical solver output with CSV rows at 0/50/100. Measurement provenance records helper and instrumented-source hashes. CSV timestamps, formatting and writes introduce some logging overhead; this has not been measured separately. Use matching logging settings for comparisons.

Already-running processes and historical runs are unchanged; start a new run to collect the CSV. This change does not start another solve automatically.

A timeout is recorded as partial, not a completed runtime; no outputs may exist if the initial solve has not finished. Progress is diagnostic and is not extrapolated into a guaranteed completion time. Use the same workload, backend and settings when later comparing a candidate. The existing implementation is the reference; no scientific changes are made.

## Live HTML charts

A local viewer is available in [live_viewer/](live_viewer/). From this step's directory, run `python live_viewer/serve.py` in a second terminal, then open **http://127.0.0.1:8765/** in Firefox. It selects the newest CSV at startup and refreshes every two seconds. Pass `--csv runs/RUN_ID/convergence.csv` to select a particular run. The viewer only reads data and does not affect or restart the solver.

## Executed baselines and available outputs

Reviewed on 18 November 2026:

| Run | Recorded outcome |
| --- | --- |
| [13 November, 600-second limit](potential_20261113_164206_525807.md) | Timed out during the initial solve; wall time 600.045567 s; no generated field arrays. This is not a completed runtime. |
| [16 November, completed](potential_20261116_103848_750500.md) | Wall time **2,273.691902 s**, CPU time 2,277.05 s; nine generated arrays totaling **650,161,152 bytes**. |

The completed run's GNU time peak RSS is **3,027.722656 MiB**; independently sampled process-tree peak RSS is **3,017.359375 MiB**. These are distinct measurements and must not be interchanged or added. Values are from a single original trial with CSV instrumentation, not a repeated-median optimization comparison.

The completed local run is `runs/20261116_103848_750500/`. Its resampled field and boundary arrays supply the recorded step 7 runs; earlier steps need not be repeated while those saved inputs remain available. Ignored run arrays/CSV are not distributed by a clone. [The live viewer guide](live_viewer/README.md) explains read-only plotting; the viewer does not start the potential solver. No solve was run during this documentation update.
