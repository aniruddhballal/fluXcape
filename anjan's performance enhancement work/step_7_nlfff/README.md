# Step 7: NLFFF reconstruction (WSR)

This step measures the reconstruction part of Main.py only. It minimises the original weighted L objective using the existing accepted/rejected-step and timestep rules. No earlier stage is rerun and no scientific or performance changes are made.

## Inputs

Seven generated input arrays:

- From **step 6**: three resampled 3D field components in `PFSSmagneticfield_for_uniform_grid/Bfield_full/{Bx_full,By_full,Bz_full}.npy`.
- From **step 6**: three resampled surface components in `Preprocessedmagneticfield_interpolated/{Bx,By,Bz}.npy`.
- From **step 5**: `weight_function/W.npy`.

The first, unresampled 3D field saved in step 6 is not needed here. Use compatible grid settings and a completed step 6 run. The measurement requires NumPy, SciPy, Matplotlib and psutil from the existing requirements file.

## Preflight and run

From `step_7_nlfff/`, with the virtual environment activated, check the currently available saved inputs:

```bash
python measure_nlfff.py --input-dir "../step_6_potential/runs/20261116_103848_750500" --weights-dir "../step_5_weights/runs/20261113_163255_483855" --check-only
```

To actually start a **600-second** measurement, remove `--check-only`:

```bash
python measure_nlfff.py --input-dir "../step_6_potential/runs/20261116_103848_750500" --weights-dir "../step_5_weights/runs/20261113_163255_483855" --max-seconds 600
```

Options: `--source-dir PATH` selects the current original/candidate Main.py and helpers; `--label original` labels the report. `--max-seconds 0` disables the limit. No automatic search for a different input run occurs.

Each execution copies/hashes the seven inputs and Main.py/laplace.py/vectormath.py into an ignored `runs/<timestamp>/`. The runner extracts the original reconstruction suffix starting at its grid setup and prepends its original imports. An AST comparison verifies that the retained statements are unchanged. The original source files stay untouched. The initial potential solve is not executed; importing its helper functions does not run it.

## Logs and measurements

The run directory contains `nlfff.log`, which captures the original per-attempt messages: accepted steps include L and dt, and rejected attempts report timestep reduction. The text logs are preserved. New runs also produce convergence.csv with initial L, every accepted/rejected attempt and normal completion; a dedicated viewer is available below. Watch with `tail -f "PATH_TO_RUN/nlfff.log"` in another terminal.

A timestamped `nlfff_*.md` report is written after execution stops, with machine-readable measurements.json in the run directory. It records elapsed/CPU time, peak RSS, sampled counters, source/input/output hashes, checkpoint count and generated storage. Copying and hashing are excluded from timing; field loading, reconstruction and checkpoint/figure writes are included. Agg avoids interactive window waiting.

GNU time peak RSS is the largest individual process peak; psutil additionally samples process-tree RSS and cumulative CPU at 100 ms, including on timeout. Sampling may miss short peaks or double-count shared pages. Match backends/settings for later comparisons. One invocation is one trial, not a repeated median.

## Outputs and completion

The original code saves under `Optimizedmagneticfield/step_N/`:

- `Bx.npy`, `By.npy`, `Bz.npy`: reconstructed 3D field components.
- `L_values.npy`: accepted-objective history.
- At periodic checkpoints, `L_functional_semilogy.png`: objective-history plot.

There is an initial checkpoint, periodic checkpoints every **200 accepted steps**, and a final save when the program exits normally. A timeout can leave only earlier checkpoints or an incomplete checkpoint write. `highest_saved_step` describes stored checkpoint labels, not necessarily the last accepted step reached before interruption. Existing checkpoints are not assumed to be complete restart records.

The unchanged configuration permits **2,000,001 accepted steps** and can stop earlier when its existing timestep floor triggers. Exit code zero means the original program finished, not necessarily that it reached that step budget or L=0. Report the actual workload shown in the logs. A time-capped run is partial. At the configured maximum, three-component checkpoint fields alone can total approximately **3.24 TB**; a bounded first run is appropriate to measure the actual cost.

## Current status

Real-observation runs and resumed continuations have been executed. The retained finalized runs below all ended at their time limits; none establishes full reconstruction completion. Small synthetic smoke/resume tests verify the tooling rather than physical accuracy or full-scale speedup.

| Run | Start state | Time limit | Highest saved field step | Retained report |
| --- | --- | ---: | ---: | --- |
| 16 November, 11:52 | Fresh step 6 inputs | 600 s | 0 | [Initial bounded trial](nlfff_20261116_115212_374166.md) |
| 16 November, 12:19 | Fresh step 6 inputs | 14,400 s | 3600 | [Four-hour trial](nlfff_20261116_121943_573055.md) |
| 17 November, 11:50 | Restart package step 3600 | 14,400 s | 7000 | [Resumed trial](nlfff_20261117_115008_927724.md) |
| 17 November, 15:56 | Restart package step 7000 | 2,700 s | 7600 | [Resumed trial with automatic preservation](nlfff_20261117_155657_781931.md) |

Saved field steps are not the exact terminal accepted-step counts. For example, the four-hour run progressed beyond its saved step 3600; unsaved progress must be repeated on resume. Reports distinguish ordinary field checkpoints from complete restart packages and record each invocation's measurements separately.

A further run, `runs/20261118_102825_170239/`, was observed active during the **18 November 2026** documentation review. It was launched from the step 7600 restart package with `--max-seconds 0` (no time cap). At the read-only inspection around 15:13 IST, its CSV recorded accepted step 11761 and `restart_checkpoints/latest.json` identified a complete step 11600 package. No finalized `measurements.json` or timestamped report existed then. These are dated observations, not completed baseline values or a promise of current process status. The documentation update did not touch the worker, its CSV or checkpoints.

Historical experiment entries remain in [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md); earlier preparation statements there predate these runs.

## CSV progress and four-hour run

From this folder, with the venv active, run in terminal 1:

```bash
python measure_nlfff.py --input-dir "../step_6_potential/runs/20261116_103848_750500" --weights-dir "../step_5_weights/runs/20261113_163255_483855" --max-seconds 14400
```

This is a new run from the saved step 6 field, not a continuation of the previous 10-minute run. It stops at four hours or earlier if the original stopping condition triggers. The limit covers measured execution; input copying and final output hashing are outside that period. No checkpoint-policy or numerical settings are changed.

After its run directory and convergence.csv exist, terminal 2 (also in this folder):

```bash
python live_viewer/serve.py
```

Open **http://127.0.0.1:8766/**. The server prints the selected CSV path; use --csv runs/RUN_ID/convergence.csv to pin a particular run. See [live_viewer/README.md](live_viewer/README.md).

The CSV contains timestamp, elapsed_seconds, event, attempts, accepted_steps, rejected_attempts, full-precision L, L_normalised, trial_L, next_dt, relaxation_time, interval_seconds and seconds_per_attempt. Initial/final rows have no attempt timing. All rejected attempts are included; their L column remains the last accepted L and trial_L records the rejected trial. Each row is closed immediately for live reading.

Instrumentation affects only the isolated script: _step7_original.py preserves the uninstrumented suffix, and AST checks verify that removing logging statements restores the original statements exactly. Original Main.py and helper source files stay unchanged. Logging overhead is included in measured runtime and has not been benchmarked separately.

A tiny real-equation fixture produced identical field and L-history arrays with and without logging. A stand-in decision-loop test covered accepted/rejected counts. Firefox checks covered charts, dt and counters, axis switching, automatic CSV updates and compact layout. These tests did not start a real observation reconstruction.

## Automatic restart preservation

Every fresh or resumed `measure_nlfff.py` run automatically starts its restart-preservation companion. No second command is needed. Keep using this runner for WSR runs rather than launching Main.py or the isolated worker directly. Complete restart packages are captured every **200 accepted steps** (not attempts); the runner also waits for a final capture on timeout or Ctrl+C. Resume from the latest complete package, repeating any unsaved steps. An abrupt shutdown can interrupt the newest write, so use the preceding fully published package. Before the first complete checkpoint, a fresh run has no saved progress to restore.

The runner prints the latest restart state path when stopping. See `restart_preservation.log` and `restart_checkpoints/latest.json` in the run folder. A preservation process that exits unexpectedly while the solver is running stops the run with an error rather than silently continuing without preservation. Check the log if preservation fails. Companion CPU/RAM are separate from solver metrics; final preservation cleanup is included in reported wall time.

### Attach preservation to an older already-running run

`preserve_restart.py` can package a complete accepted-step restart snapshot using existing periodic field checkpoints and the new CSV. It does not edit, stop, attach to, or change the live solver. From this folder:

```bash
python preserve_restart.py --run-dir runs/RUN_ID --watch
```

Without `--watch` it packages the latest complete periodic checkpoint once. With `--watch` it checks every five seconds, captures newer complete periodic checkpoints and stops when the original worker stops. Use only one watcher per run; do not start this manual watcher for a run already managed automatically. Snapshots are saved atomically under the ignored run's `restart_checkpoints/step_N/`; `latest.json` points to the newest complete package. Each package currently occupies roughly 0.8 GiB, including copied fields and fixed references.

Packages contain the accepted field, original step-0 boundary reference, weight volume, coordinates, L and relaxation-time histories, next adaptive timestep, accepted step/attempt/rejection counts, source/settings and file hashes. At an accepted checkpoint, divB is recomputed from the saved accepted field with the run's copied original helper and saved as an array. This reconstructs the state at that accepted checkpoint, not the later state of an in-progress rejected trial. Only complete periodic accepted checkpoints are selected; partial writes are skipped and retried.

The initial four-hour run already writes the CSV information needed to recover dt and time history. That is why useful restart data can be preserved without injecting new code into its live process. Unsaved attempts after the selected checkpoint must be repeated; the preservation cannot recover the exact state at an arbitrary timeout instant. Identical continuation requires the same numerical environment and copied equations. An isolated tiny test verified that continuing one step from a preserved checkpoint exactly matches uninterrupted fields, L, dt and time history.

This tool preserves restart data. The measurement runner now supports --resume as described below. The small implementation tests did not restart a real observation; the subsequent real resumes are recorded in the status table above.

## Resume a preserved checkpoint

From this folder with the original virtual environment activated, check the preserved step 3600 package:

```bash
python measure_nlfff.py --resume "runs/20261116_121943_573055/restart_checkpoints/step_3600" --check-only
```

To continue for up to another four hours:

```bash
python measure_nlfff.py --resume "runs/20261116_121943_573055/restart_checkpoints/step_3600" --max-seconds 14400
```

Do not combine --resume with --input-dir/--weights-dir. The package supplies the saved inputs, copied original sources, settings and solver state; --source-dir does not select new code during a resume. A state.json path can also be passed. Hashes, shapes, history consistency and recorded Python/package versions are checked before launch.

A new run directory is created; the preserved package and old run are not modified. It restores Bx/By/Bz, original fixed boundary references, divB, weights, coordinates, dt/current_dt, step count and L/time histories. Only original imports, the checkpoint-save block, reconstruction loop and final-save block run; initial field construction and original WSR setup calculations are skipped. The next accepted step will be 3601, while the original log labels its attempt from step 3600 before incrementing. The original total accepted-step budget remains 2,000,001, not 2,000,001 extra steps.

The time cap and reported wall/CPU time apply to this new invocation. Its CSV keeps all history through the preserved checkpoint, appends a resumed event, continues attempt/rejection counts and L/initial-L normalisation, and offsets elapsed_seconds by the previous checkpoint's active elapsed time. Overnight downtime is excluded; timestamps are actual clock times. Fields loaded at startup are included in this invocation's measurements. No field/L state is recomputed during restoration.

Unsaved attempts after the checkpoint are repeated. For the original four-hour run this means replaying the last 41 accepted steps after step 3600, rather than repeating the first 3600. Initial checkpoint files in the new run use the restored step label rather than step 0.

The same live viewer works: restart its server to select the newest CSV, or explicitly select the new run with --csv. Restart preservation starts automatically for resumed runs too; no manual watcher command is needed.

Tests (small synthetic workload only):

```bash
python -m unittest discover -s . -p test_resume.py -v
```

The integration test compares uninterrupted versus resumed fields and L arrays bit-for-bit, dt/time history and progress counts; it tests a second preservation/resume and rejects a damaged package. The original Main.py/equations remain unchanged. No real observation reconstruction is launched by these tests; the real run reports above are separate execution evidence.

## Tool and evidence map

| File/location | Role |
| --- | --- |
| [measure_nlfff.py](measure_nlfff.py) | Fresh/resume preflight, isolated execution, timing, reports, and automatic preservation supervision. |
| [progress_log.py](progress_log.py) | CSV progress instrumentation and resumed-history handling. |
| [preserve_restart.py](preserve_restart.py) | Captures complete periodic accepted-step packages; supports a read-only watcher for older runs. |
| [restart_state.py](restart_state.py) | Validates saved files, hashes, shapes, history and environment, restores runtime state, and generates the original-loop continuation. |
| [test_resume.py](test_resume.py) | Tiny synthetic uninterrupted-versus-resumed equivalence and damaged-package tests. |
| [live_viewer/](live_viewer/README.md) | Read-only CSV charts with zoom, fullscreen and moving sample markers. |
| [Timestep-curve comparison, 18 November](analysis/dt_curve_comparison_from_minute_240_20261118.png) | Retained diagnostic plot. It is not an additional solver run, a convergence proof or a performance benchmark. |

`runs/` holds ignored local inputs, copied source, arrays, CSVs and complete restart packages. A clone supplies the tools and retained reports, not those run products. A raw `Optimizedmagneticfield/step_N/` field directory is not interchangeable with a validated `restart_checkpoints/step_N/` package. For an existing local run, read `restart_checkpoints/latest.json` rather than assuming the illustrative step 3600 path is the newest package. A new viewer process is needed to select a newly created resumed CSV; already-open viewers stay attached to their selected file.
