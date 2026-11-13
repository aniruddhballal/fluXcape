# Step 2: FITS extraction and resampling

First measure the original `fitsdataextraction.py`; do not change it before obtaining the baseline.

## What this step does

For Bp → Bx, negative Bt → By and Br → Bz, the original code:

1. Reads the component from FITS HDU 1.
2. Builds a Python list of coordinate/value triples for every pixel.
3. Writes `outputB*.dat` with six decimal places, then reads it back.
4. Uses scattered cubic `griddata` interpolation to produce a 300×300 map.
5. Writes `interpolated_dataB*.dat`, omitting NaN values.

The three final interpolated text maps feed the C preprocessor in step 3. The three large `outputB*.dat` files are intermediates.

## Measure the original

From the repository root, in the scientific Python environment:

```bash
python "anjan's performance enhancement work/step_2_extract/measure_extraction.py" --check-only
python "anjan's performance enhancement work/step_2_extract/measure_extraction.py" --label original --max-seconds 600
```

Use `python3` where appropriate. Requires NumPy, SciPy, Matplotlib and Astropy; Windows/non-GNU platforms also need psutil. Use the existing scientific environment rather than installing packages into an unrelated system interpreter.

The default input folder is the original observation folder. `--input-dir PATH` can select another directory containing the same three FITS filenames. The script copies and hashes the source and FITS inputs, then executes only extraction in `runs/<timestamp>/`. It does not modify the originals or run steps 3–7. Paths work independently of the current shell directory.

Each invocation writes an `extraction_<timestamp>.md` report; ignored run directories contain logs, outputs and `measurements.json`. One invocation is one trial. After a successful exploratory run, collect repeated completed trials with matching settings for a median baseline. Preserve an original run's outputs for later numerical comparisons. A 600-second timeout is a partial result; increase the limit or use `--max-seconds 0` for an unlimited extraction-only run if needed.

Measurements: wall time, CPU time, peak RSS, six output file sizes/hashes, source/input hashes and environment. GNU time RSS is the largest individual process peak; psutil samples simultaneous process-tree RSS and can double-count shared pages or miss brief peaks. Compare with the same backend. Timings exclude copying and hashing. Killed GNU time runs may lack CPU/RAM results. Output presence and hashes are not numerical validation.

## Candidate work after the baseline

- Replace per-pixel Python list construction with array operations.
- Avoid the large write/read round trip where possible, accounting for the original six-decimal rounding before interpolation.
- Investigate the cost of triangulation on gridded input. A different interpolation method is a numerical change and needs explicit validation, not just a speed comparison.
- Release unnecessary arrays between components.

Keep the original script unchanged. A candidate can later be benchmarked with `--source PATH --label candidate` using identical FITS inputs. Match the 300×300 coordinates, component sign, order, finite/NaN masks and output precision, then compare numerical differences with justified tolerances. Document accepted changes and measurements in [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md).

## Current status

Source inspected and extraction-only measurement script prepared. Structural smoke checks passed using small stand-in fixtures, including timeout termination. The current Linux Python interpreter lacks the scientific dependencies, so no original scientific extraction baseline has been measured here. No candidate optimisation has been implemented yet.
