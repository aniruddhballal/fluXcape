# Step 4: boundary packaging baseline

Run the original `plot.py` in isolation using saved outputs. It reads `Bfield_processed.dat` from step 3 and the three `interpolated_dataB*.dat` files from step 2. No earlier stage is repeated; steps 5–7 do not run.

From the repository root, with the Python environment activated:

```bash
python "anjan's performance enhancement work/step_4_package/measure_package.py" --resampled-dir "PATH_TO_STEP_2_RUN" --processed-dir "PATH_TO_STEP_3_RUN"
```

Requires NumPy and Matplotlib; Windows/non-GNU platforms also need psutil. Options: `--check-only`, `--source PATH` (default: the original observation folder's current plot.py), `--label original`, and `--max-seconds 600` (default; 0 means unlimited).

Each invocation copies/hashes the source and four input files into ignored `runs/<timestamp>/`, executes the unchanged script there and writes `package_<timestamp>.md`. Logs and measurements.json stay in the run directory. The three generated scientific files are `Preprocessedmagneticfield/Bx.npy`, `By.npy` and `Bz.npy`, each a 300×300 array. Copied input files are excluded from output size. Original source and earlier results are not overwritten.

Timing includes reading, reshaping, NumPy saves, six contour plots and layout calculation. Agg disables interactive window display/wait; the original script does not save those plots to files. This is a baseline of the entire existing step, not just the array-writing section. Source/input copying and hashing are outside timing.

Reports record wall/CPU time, peak RSS, source/input hashes, versions and output bytes/hashes. GNU time RSS is the largest individual process peak; psutil samples simultaneous process-tree RSS at 20 ms and may double-count shared pages or miss brief peaks. Match backend, inputs, plotting mode and workload for candidate comparisons. One run is one trial; collect repeated completed runs for a median comparison when testing improvements.

The original behaviour is the reference. No candidate has been implemented. Record measurements in [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md).

## Retained baseline

The [13 November completed trial](package_20261113_160555_320989.md) records **1.165231 s** wall time, 3.05 s CPU time and 212.480469 MiB GNU time peak RSS. Three 300×300 component arrays total 2,160,384 bytes. This is a single unchanged-source baseline; no optimized candidate or speedup is established. Its outputs are explicitly reused by step 6. The report is retained in Git, while copied inputs and generated arrays are local ignored run products. Documentation reviewed 18 November 2026; no packaging run was started for this update.
