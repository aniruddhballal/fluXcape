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

Files prepared; preflight passes for the saved step 5/6 inputs. The real reconstruction has **not** been started. An isolated tiny 4×4×4 synthetic smoke test verified suffix execution, initial/final checkpoint writing and report generation; it is a tooling test, not a measured baseline for the real observation. Record actual runs in [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md).

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

## Preserve restart data from an already-running run

`preserve_restart.py` can package a complete accepted-step restart snapshot using existing periodic field checkpoints and the new CSV. It does not edit, stop, attach to, or change the live solver. From this folder:

```bash
python preserve_restart.py --run-dir runs/RUN_ID --watch
```

Without `--watch` it packages the latest complete periodic checkpoint once. With `--watch` it checks every five seconds, captures newer complete periodic checkpoints and stops when the original worker stops. Use only one watcher per run. Snapshots are saved atomically under the ignored run's `restart_checkpoints/step_N/`; `latest.json` points to the newest complete package. Each package currently occupies roughly 0.8 GiB, including copied fields and fixed references.

Packages contain the accepted field, original step-0 boundary reference, weight volume, coordinates, L and relaxation-time histories, next adaptive timestep, accepted step/attempt/rejection counts, source/settings and file hashes. At an accepted checkpoint, divB is recomputed from the saved accepted field with the run's copied original helper and saved as an array. This reconstructs the state at that accepted checkpoint, not the later state of an in-progress rejected trial. Only complete periodic accepted checkpoints are selected; partial writes are skipped and retried.

The initial four-hour run already writes the CSV information needed to recover dt and time history. That is why useful restart data can be preserved without injecting new code into its live process. Unsaved attempts after the selected checkpoint must be repeated; the preservation cannot recover the exact state at an arbitrary timeout instant. Identical continuation requires the same numerical environment and copied equations. An isolated tiny test verified that continuing one step from a preserved checkpoint exactly matches uninterrupted fields, L, dt and time history.

This tool preserves restart **data**. A user-facing resume runner still needs to be implemented and tested before using it for tomorrow's reconstruction. No real observation was restarted during this preservation work.
