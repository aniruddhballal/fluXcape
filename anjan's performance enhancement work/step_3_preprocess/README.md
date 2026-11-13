# Step 3: C preprocessing baseline

Measure execution of the preprocessor, using the executable from step 1 and the three resampled maps from step 2. Compilation, FITS extraction and Main.py are not run or included in the timing.

From the repository root, supply the actual saved directories:

```bash
python "anjan's performance enhancement work/step_3_preprocess/measure_preprocess.py" --binary "PATH_TO_COMPILED_PREPROC" --input-dir "PATH_TO_STEP_2_RUN"
```

On Windows, supply the compiled `.exe`; on Linux, supply the executable without that suffix. The binary must match the current OS. Keep any compiler runtime libraries available on PATH. Linux uses GNU time; other platforms require psutil. No scientific Python packages are needed to measure this C program.

The input directory must contain `interpolated_dataBx.dat`, `interpolated_dataBy.dat`, and `interpolated_dataBz.dat`. These must match the executable's expected grid (the original is 300×300), coordinate order and field convention. The current C reader does not robustly validate every input: use complete, verified step 2 outputs.

Options: `--check-only`, `--label original`, and `--max-seconds 600` (default; zero disables the time limit). Each invocation is one trial. Repeat completed runs with identical inputs/binary and compare median times before accepting a performance claim.

Executable and inputs are copied and hashed into ignored `runs/<timestamp>/` directories. The executable is run there, producing `Bpre.dat` and `Bfield_processed.dat`, plus logs and measurements. A timestamped `preprocess_*.md` report is saved beside this script. Original inputs/executable remain unchanged. Input `.dat` files are excluded from generated-output size.

The report records elapsed time, CPU time, peak RSS, executable/input hashes, output size/hashes and environment. GNU time RSS is the largest individual process peak; psutil samples process-tree RSS and may miss short peaks or double-count shared pages. Timeout results are partial, not completed baselines. The original C program does not print objective convergence diagnostics with its current verbosity setting; successful exit alone does not prove physical convergence or correct preprocessing.

For candidate comparisons, keep the three input maps fixed and select a separately compiled candidate with `--binary`. Record the compiler flags and source commit/hash from its build report, and validate output shapes, coordinates, finite values and field differences before accepting faster execution. Update [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md) with retained measurements and their limitations.
