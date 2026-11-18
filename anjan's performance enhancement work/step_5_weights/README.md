# Step 5: generate weights

Run the original `weightfunction.py` alone. It needs no FITS files or outputs from earlier stages: its inputs are the grid and taper parameters defined in the source.

From the repository root, in the Python environment:

```bash
python "anjan's performance enhancement work/step_5_weights/measure_weights.py"
```

Requires NumPy and Matplotlib; Windows/non-GNU platforms also need psutil. Options: `--check-only`, `--label original`, `--source PATH` (defaults to the current weightfunction.py in the original observation folder), and `--max-seconds 600` (default; 0 means unlimited).

The original loops compute one weight at each of 300×300×150 grid points. The resulting `weight_function/W.npy` is used later by Main.py to weight its reconstruction objective. It is not a magnetic-field component.

Each invocation copies/hashes the source, runs it in ignored `runs/<timestamp>/`, and writes a `weights_<timestamp>.md` report. Logs, generated data and measurements.json remain in the run directory. No original files are overwritten; no other stages run.

Measurements cover grid/weight generation, saving W.npy, contour construction and layout. Matplotlib Agg disables interactive display/wait. The original script does not save the plot. Copying and hashing are outside timing; generated output size counts W.npy only, not logs/copied source.

The report records wall/CPU time, peak RSS, output bytes/hash, source hash and environment. GNU time RSS is the largest individual process peak; psutil samples simultaneous process-tree RSS at 20 ms and may double-count shared pages or miss brief peaks. Match measurement backend/settings for before/after comparisons. One invocation is one trial; use repeated completed runs for a median comparison when testing a candidate.

The original implementation and numerical settings are unchanged. Future candidates must preserve its generated weights and output interface. Record baseline and candidate results in [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md).

## Retained baseline

The [13 November completed trial](weights_20261113_163255_483855.md) records **23.271376 s** wall time, 25.18 s CPU time and 193.046875 MiB GNU time peak RSS. The generated float64 weight volume has shape 300×300×150 and occupies 108,000,128 bytes including its NumPy header. Step 7 reuses this saved volume. This is one original trial, not a before/after speedup. Generated arrays remain local ignored run products; the report is retained. Documentation reviewed 18 November 2026; no weight generation was started for this update.
