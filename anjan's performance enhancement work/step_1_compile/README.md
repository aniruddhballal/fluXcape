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

An initial Linux/GCC measurement is retained in [the timestamped report](compile_20261113_113407_004146.md) and summarised in [PERFORMANCE_LOG.md](../PERFORMANCE_LOG.md). It is not a measurement of your Windows machine or of preprocessing runtime.

## Retained builds (reviewed 18 November 2026)

- [Original build, 13 November](compile_20261113_113407_004146.md): three `-O3` trials; median wall time 0.142465 s; executable size 28,912 bytes.
- [OpenMP build, 17 November](compile_20261117_110829_071919.md): three `-O3 -fopenmp` trials; median wall time 0.150748 s; executable size 29,776 bytes.

Both compiled unchanged `preproc.c`. Their runtime/output comparison belongs to [step 3](../step_3_preprocess/README.md), where the OpenMP output is documented as numerically different. These compilation reports do not establish execution speedup. Executables and detailed compiler logs are local ignored run artifacts, not clone contents.
