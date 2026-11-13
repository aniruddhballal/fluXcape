# Step 6: initial potential field and grid preparation

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

A timeout is recorded as partial, not a completed runtime; no outputs may exist if the initial solve has not finished. Progress is diagnostic and is not extrapolated into a guaranteed completion time. Use the same workload, backend and settings when later comparing a candidate. The existing implementation is the reference; no scientific changes are made.
