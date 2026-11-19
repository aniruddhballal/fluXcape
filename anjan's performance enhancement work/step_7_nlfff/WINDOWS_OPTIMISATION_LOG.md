# Windows step 7 optimisation log

This is the continuing record of local WSR/NLFFF performance work on the Windows laptop. Keep the individual run reports as immutable measurement evidence and append experiments here. No step 7 optimisation has been implemented or accepted yet.

## Scope and comparison rules

- Prioritise useful elapsed-time improvements under this laptop's memory limits, while retaining the original mathematics, precision, boundaries, timestep/acceptance rules and numerical output behaviour. Zero or near-zero accuracy tradeoff is the user requirement; seek bit-identical results and quantify differences before accepting a candidate.
- Use short bounded trials (the present request was 10?20 attempts). A complete multi-hour Windows reconstruction is not requested. Record any explicit attempt/time cap; do not infer a new hard runtime or RAM budget.
- An attempt is one complete proposed update, accepted or rejected. An accepted step can require multiple attempts. Report both counts and distinguish per-attempt intervals from total wall time divided by accepted steps.
- Fix input files, initial state, grid, scientific settings and workload. Preserve the original source and use separate candidates. Record memory pressure, watcher activity, thread environment and measurement boundaries. Use repeated comparable trials before a general speedup claim.
- Commit completed code, reports and log updates. Retain failed/partial measurements and their limitations. Short-trial timing is not full-convergence timing or scientific validation.

## Laptop and measurement context

| Item | Value |
| --- | --- |
| System | HP Victus 16-e0xxx; Windows 11 build 26200 |
| CPU | AMD Ryzen 5 5600H; 6 physical cores, 12 logical processors |
| Installed RAM | 8 GiB; one reported module configured at 3200 MT/s |
| OS-visible RAM | 7887097856 bytes / 7.345432281 GiB |
| Storage | SK hynix PC711 HFS512GDE9X073N; 512,105,932,800 bytes |
| Python | 3.12.7 |
| NumPy / SciPy | 2.5.4 / 1.18.1 |
| Matplotlib / psutil | 3.11.2 / 7.2.2 |
| Captured thread environment | `{}` |
| Measurement backend | psutil; process-tree memory/CPU sampled every 100 ms |

Hardware details originate from the earlier [laptop audit](../step_6_potential/reports/device_and_v2_windows_20261118.md); this trial's measurements and software versions are recorded in its own report. No CPU/GPU/power/driver optimisation was applied for this trial. The earlier battery-saver-off statement belonged to a step 6 run; power/battery/thermal state was not established for this step 7 sample.

## Experiment W001 ? original full-grid ten-attempt sample ? 19 November 2026

- **Run:** `20261119_192609_356822`; label `windows_10_attempt_timing_trial`; started `2026-11-19T19:26:10.630367+05:30`.
- **Evidence:** [individual report and original hashes](nlfff_20261119_192609_356822.md). Local ignored run files: `measurements.json`, `convergence.csv`, `nlfff.log`, `restart_preservation.log` and `memory_pressure_snapshot.json`.
- **Workload:** fresh original Main.py reconstruction suffix; grid 300 x 300 x 150 = 13,500,000 cells; three float64 field components; no scientific/performance changes. Instrumentation adds only the requested session-relative attempt cap plus logging.
- **Bounds:** `--max-attempts 10`; `--max-seconds 0` (no wall-time timeout). Original accepted-step budget stays 2,000,001, initial dt 0.0001, small-dt threshold 0.0000001, periodic checkpoint interval 200 accepted steps.
- **Outcome:** 10 attempts, 10 accepted, 0 rejected. Solver exit code 0; final field saved at step 10; no convergence/completion claim for the full reconstruction. Restart-preservation companion exited 2 and did not establish a restart package.

### Individual iteration timings

| Attempt | Accepted-step count | Event | Interval seconds | Within 10% of sample mean? |
| ---: | ---: | --- | ---: | --- |
| 1 | 1 | accepted | 54.348008900 | yes |
| 2 | 2 | accepted | 60.116550000 | no |
| 3 | 3 | accepted | 46.029721100 | yes |
| 4 | 4 | accepted | 60.171661700 | no |
| 5 | 5 | accepted | 52.177140000 | yes |
| 6 | 6 | accepted | 39.731030200 | no |
| 7 | 7 | accepted | 53.381364900 | yes |
| 8 | 8 | accepted | 35.383115500 | no |
| 9 | 9 | accepted | 51.157530800 | yes |
| 10 | 10 | accepted | 51.301631600 | yes |

### Timing and resource summary

| Metric | Value |
| --- | ---: |
| Mean seconds/attempt | 50.379775470 |
| Median seconds/attempt | 51.739385800 |
| Minimum seconds | 35.383115500 |
| Maximum seconds | 60.171661700 |
| Range width (s) | 24.788546200 |
| Sample standard deviation (s) | 8.009341978 |
| Coefficient of variation (%) | 15.897931071 |
| Mean excluding first attempt (s) | 49.938860644 |
| Sum of ten attempt intervals (s) | 503.797754700 |
| Whole-session wall time (s) | 525.772106100 |
| Whole-session seconds / accepted step | 52.577210610 |
| Sampled cumulative CPU time (s) | 394.296875000 |
| Sampled peak resident process-tree RAM (MiB) | 2804.523437500 |
| Within +/-10% of mean (45.341797923 to 55.417753017 s) | 6/10 = 60% |
| Within +/-20% of mean (40.303820376 to 60.455730564 s) | 8/10 = 80% |
| Generated output bytes (initial + final saves) | 648001120 |
| Saved output files / step directories | 8 / 2 |

Intervals are event-to-event times from the CSV, not isolated kernel timings. The first includes initial checkpoint I/O. Initial loading/objective setup and final saves/cleanup lie outside the ten intervals but inside the session wall time. There is no 200-step periodic checkpoint in this sample. CPU seconds sum process-tree CPU activity and are not elapsed time. Input preparation, copying and post-run hashing are outside measured step 7 execution.

### Per-attempt numerical state (diagnostic, not scientific validation)

| Accepted step | L | Next dt | Numerical relaxation time |
| ---: | ---: | ---: | ---: |
| 0 | 20027337925.198563 | 0.0001 | 0.0 |
| 1 | 20027223104.57604 | 0.000101 | 0.0001 |
| 2 | 20027107136.713867 | 0.00010201000000000001 | 0.000201 |
| 3 | 20026990010.159023 | 0.00010303010000000001 | 0.00030301000000000004 |
| 4 | 20026871713.344334 | 0.00010406040100000001 | 0.00040604010000000007 |
| 5 | 20026752234.587357 | 0.00010510100501000002 | 0.000510100501 |
| 6 | 20026631562.089226 | 0.00010615201506010001 | 0.0006152015060100001 |
| 7 | 20026509683.933495 | 0.00010721353521070101 | 0.0007213535210701001 |
| 8 | 20026386588.084965 | 0.00010828567056280802 | 0.0008285670562808012 |
| 9 | 20026262262.388542 | 0.00010936852726843611 | 0.0009368527268436092 |
| 10 | 20026136694.567978 | 0.00011046221254112047 | 0.0010462212541120454 |

Final three fields were checked to have shape `(300, 300, 150)` with all finite values; 40,500,000 final field values total. Each field file is 108,000,128 bytes. Objective history has 11 values (initial plus ten accepted updates). Output/source/input SHA-256 hashes are retained in the linked individual report; no candidate-equivalence claim is due before a step 7 candidate exists.

### Input provenance

The original interpolation and boundary-preparation suffix of step 6 was run separately from the saved Windows V3 first fields (`20261118_224124_147720`) and Windows step 4 boundary arrays (`20261118_192252_109811`), without rerunning the Laplace solve. The generated step 7 input directory is `../step_6_potential/runs/from_v3_for_step7_trial`. Its local preparation script and `preparation.json` record the source/input hashes. Weights came from `../step_5_weights/runs/20261118_192501_152805`. This preparation is excluded from step 7 timing. These input hashes differ from the historical Ubuntu run.

Reproduce from the step 7 folder with the environment activated (runs another bounded trial, not the full reconstruction):

```powershell
python .\measure_nlfff.py --input-dir "..\step_6_potential\runs\from_v3_for_step7_trial" --weights-dir "..\step_5_weights\runs\20261118_192501_152805" --max-attempts 10 --max-seconds 0 --label windows_10_attempt_timing_trial
```

The same default watcher is enabled in that reproduction command; the failure below remains unresolved. Do not present a repeat with that failure as a clean benchmark.

### Memory constraints observed

Available memory was approximately 1.36 GiB before preparation and fell to roughly 50 MiB during execution. One later snapshot records the following exact counts; snapshots are not continuous monitoring:

| Snapshot metric | Bytes / count | GiB where applicable |
| --- | ---: | ---: |
| System physical RAM | 7887097856 | 7.345432281 |
| System available RAM | 523653120 | 0.487689972 |
| System used RAM | 7363444736 | 6.857742310 |
| System pagefile/swap used | 3602235392 | 3.354843140 |
| System pagefile/swap total | 13958643712 | 13.000000000 |
| Largest worker private committed memory | 6486700032 | 6.041210175 |
| Largest worker resident memory | 2023038976 | 1.884101868 |
| Largest worker peak private committed memory | 7351717888 | 6.846820831 |
| Largest worker peak working set | 2966024192 | 2.762325287 |
| Largest worker cumulative page faults | 72732252 | not applicable |
| Snapshot system RAM used | 93.4% | not applicable |

Page-fault count includes soft/hard faults and is not a direct disk-paging count. System pagefile use is not solely attributable to the worker. The worker's resident memory is much smaller than its private committed allocation. A low sampled RSS here must not be interpreted as an algorithmic memory improvement over Ubuntu. No memory cap was imposed or application forcibly closed.

### Restart-watcher failure and benchmark quality

The solver succeeded, but the companion watcher repeatedly encountered `WinError 32` on `restart_checkpoints/step_0.building/field/Bx.npy` and exited with code 2. It did not establish a restart package. Its retries may have added memory/disk activity; that contribution was not isolated. Full original-grid timings therefore reflect substantial memory pressure plus a failing background companion. **W001 is a diagnostic measurement with limitations, not a clean accepted performance baseline.** These issues should be resolved or explicitly controlled before attributing a candidate speedup. No claim is made that Windows itself or memory pressure alone explains the observed runtime.

### Ubuntu context and comparison limits

The completed Ubuntu report records 20,064 accepted steps and an approximate cumulative active-time estimate of 81,131.502868121 s (checkpoint offset plus final invocation), about 22.53653 h. Dividing gives a coarse approximately 4.0436 s/accepted step, including rejected work and overhead. It is not a distribution of individual iterations. The user estimates 90?95% of Ubuntu iterations were near 4 s; the Ubuntu CSV is absent locally, so that frequency was not verified.

Using the user's approximate 4 s reference, this laptop sample's mean / 4 is 12.594944x. The conversational 52/4 = 13x was a rounded illustration; the observed mean is 50.379775470 s. This compares a memory-constrained laptop sample with a Ryzen 9 9950X Ubuntu desktop (16 cores/32 logical CPUs, approximately 30.46 GiB OS-visible RAM), different input hashes and measurement circumstances. It is not an isolated Windows-versus-Ubuntu slowdown or a valid full-run extrapolation.

### Verification and commits

- Two focused attempt-limit tests passed, covering exact accepted/rejected counts and unchanged natural termination before the cap.
- Default unbounded generated instrumentation was compared with the preceding instrumenter and is byte-identical. Original scientific source files are untouched.
- Tooling commit: `1f42473`. Raw run report/analysis commit: `d824e12`. Restart preservation failure remains documented rather than silently treated as success.

## Template for the next experiment

- Experiment ID, date, implementation commit and change being investigated.
- Same input hashes and initial state or a clearly stated different workload; source/scientific settings and thread environment.
- Attempt/time limits, actual accepted/rejected counts, stopping reason and output completeness.
- All per-attempt times; mean/median/min/max/sample deviation; total wall and CPU; sampling method; peak resident and private memory where available.
- Background/watcher state, memory pressure, power/thermal context and any failures affecting measurements.
- Candidate field/history/layout/finite-value equivalence versus the original on matching inputs and workload.
- Repeated matched timings, absolute changes and percentage improvements with the exact numerator/denominator; distinguish diagnostic results from accepted gains.
- Links to immutable run reports, logs/artifacts, validation commands and conclusion.
