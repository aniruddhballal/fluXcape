# Step 1: measure C compilation

From the repository root:

```bash
python "anjan's performance enhancement work/step_1_compile/measure_compile.py"
```

Use `python3` if needed. The script compiles a copy of the original `preproc.c` three times with `-O3`, without executing the resulting program. No FITS or scientific Python packages are needed. A GCC-compatible compiler is required.

Linux uses `/usr/bin/time` from GNU time. Windows and other platforms require `psutil` (`python -m pip install psutil`); the script reports a missing dependency instead of installing anything. On Windows, GCC and its tools/DLLs must be on PATH as explained in [SETUP.md](../SETUP.md).

Optional settings:

```bash
python "anjan's performance enhancement work/step_1_compile/measure_compile.py" --compiler gcc --trials 5 --label baseline
```

`--source PATH` selects another source file; `--flags="-O3 -fopenmp"` changes build flags for a deliberately different experiment. Defaults preserve the existing basic build settings. Testing whether flags speed up the executable belongs to step 3.

Each invocation creates a timestamped `compile_*.md` report here. Ignored `runs/<timestamp>/` directories hold executables, copied source, compiler logs, raw time measurements and `measurements.json`. Reports include trial times, CPU time, peak RSS, executable size, exact commands, source hash and environment. No files in the original observation directory are overwritten.

GNU time's RSS is the largest individual process peak across the compilation tree, not simultaneous total RAM. The psutil fallback measures sampled simultaneous process-tree RSS, may double-count shared memory and miss short-lived processes. Compare results using the same backend. CPU timing can be coarse for short builds. The three consecutive trials are not controlled cold-cache builds.

