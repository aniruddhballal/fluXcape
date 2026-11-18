# Device inspection and version 2 experiments - 18 November 2026

Scope: only the initial potential solve, gradients, scaling and first three field files of step 6. No other stage was changed.

## Performance-relevant device inventory

| Item | Observed value |
| --- | --- |
| Device | HP Victus 16-e0xxx laptop |
| CPU | AMD Ryzen 5 5600H; 6 physical cores, 12 logical processors |
| CPU caches (WMI) | 3 MiB L2, 16 MiB L3 |
| RAM | One reported 8 GiB module; configured at 3200 MT/s; Windows reports 7,887,097,856 usable bytes |
| Available RAM snapshot | Approximately 2.1 GiB before benchmarking; changes with other applications |
| Discrete GPU | NVIDIA GeForce GTX 1650, compute capability 7.5, 4096 MiB VRAM; approximately 3935 MiB free at inspection |
| GPU driver | NVIDIA 592.82 |
| Integrated GPU | AMD Radeon Graphics; WMI-reported adapter memory 512 MiB |
| Storage | SK hynix PC711 HFS512GDE9X073N, 512,105,932,800 bytes |
| OS | Windows 11 Home Single Language, version 10.0.26200 |
| Active power scheme | HP Recommended; no power settings were changed |
| Python environment | Python 3.12.7, NumPy 2.5.4, Numba 0.68.1, llvmlite 0.50.0 |

This is a relevant hardware/environment inventory, not a claim to have inspected every device setting. CPU temperature, sustained clock frequencies and AC/battery state were not established. No BIOS, driver, power or OS changes were made.

The NVIDIA driver could identify the device through Numba, but `cuda.is_available()` returned false and NVVM availability was false. No CUDA kernel was compiled or benchmarked. This does not establish the GPU's potential performance; adding a CUDA compiler/toolkit would be separate work.

## Version 2 approach

`optimised_laplace_v2.py` preserves the Jacobi field expression, float64 divisions/additions in their original order, two-buffer swaps, fixed faces and stopping rule. It changes the maximum-error reduction. The absolute differences are nonnegative float64 values; viewing their bits as uint64 preserves ordering for finite values and +infinity, while NaN bit patterns sort above infinity. An integer maximum can therefore be used and viewed back as float64 for the original stopping comparison. This is bit reinterpretation, not quantisation, rounding or reduced precision.

The integer reduction permits compiler SIMD without floating-point reassociation or fast-math. Assembly inspection after recompilation found packed double divides (`vdivpd`) in v2 and none in v1's kernel. Neither kernel enables fast-math. A per-device default of four workers was chosen from the measurements below. An explicit `NUMBA_NUM_THREADS` overrides that default. V2 records actual worker count, threading layer, dtype and reduction method in `solver_runtime.json`; the runner incorporates these into the report.

The entry point now supports `--implementation original`, `optimised` and `optimised-v2`. Original remains the default. Anjan's sources and the existing version 1 module are untouched. Gradients, scaling and file saves remain the original code.

## Fixed-workload benchmark

Each trial performs 60 full-grid Jacobi updates on `(300, 300, 150)` with the same Bz boundary used by the completed Windows runs. Three trials per implementation/worker count, alternating implementation order. Initialisation/copies and compilation are outside timing; kernel calls and per-update error reduction are inside. Every trial's final potential bits and all 60 errors match the v1 reference exactly. These results are not full convergence times.

| Workers | V1 median (s) | V2 median (s) | V1/V2 |
| ---: | ---: | ---: | ---: |
| 1 | 7.368513 | 2.217257 | 3.323x |
| 2 | 3.745979 | 1.451400 | 2.581x |
| 4 | 1.866760 | 1.284992 | 1.453x |
| 6 | 1.540725 | 1.334719 | 1.154x |
| 8 | 1.885152 | 1.477827 | 1.276x |
| 12 | 2.002073 | 1.802542 | 1.111x |

Raw trials and input hash: [kernel_benchmark_windows_v2_20261118.json](kernel_benchmark_windows_v2_20261118.json). Thermal conditions, background load and CPU clocks were not controlled. Four workers gave the lowest measured v2 median in this sweep; this is a measured choice on this laptop, not a universal optimal worker count.

## Validation

Seven unit/integration tests passed before starting the full-input v2 solve. Both optimised implementations were compared with the original NumPy solver on fixed-step and convergent fixtures. Tests cover exact output bits, stopping labels and progress errors, unchanged inputs, nonfinite inputs, generated overflow, subnormals, signed zero, noncontiguous/float32 fallback, default/explicit worker settings and all three runner selectors. First-three files match byte-for-byte on the runner fixture. The original full-step path still produces nine files.

The completed full-observation comparison is recorded below. No claim of a global performance maximum is justified by this bounded set of experiments.

## Completed full-observation comparison

V2 run `20261118_221042_587814` completed successfully with four workers and the recorded Numba threading layer `omp`. The optional benchmark was followed by a full solve, using the exact input files and source snapshots from both earlier Windows runs.

| Metric | Original | V1 | V2 |
| --- | ---: | ---: | ---: |
| Wall time (s) | 6930.678691 | 540.392198 | 408.807531 |
| Sampled CPU time (s) | 6895.203125 | 5460.593750 | 1581.125000 |
| Sampled peak RSS (MiB) | 713.304688 | 659.179688 | 656.183594 |
| Generated field bytes | 324000384.000000 | 324000384.000000 | 324000384.000000 |
| Zero-based stopping label | 16975 | 16975 | 16975 |
| Jacobi updates | 16976 | 16976 | 16976 |
| Recorded convergence samples | 340 | 340 | 340 |

V2 was **1.3219x faster than V1**, reducing wall time by **24.3498%** and saving **131.584667 s**. Relative to the original it was **16.9534x faster**. These are one completed full run per implementation, not full-run repeated medians. Compilation, logging, gradients, scaling and saves are included; input copying and final output hashing are excluded. No separate gradient/scaling/save timings were collected.

### Accuracy verification

All three files were independently SHA-256 hashed from disk after V2 completed and matched both earlier runs. All 40,500,000 field values also matched bit-for-bit on independent array comparison; every value is finite, shape `(300, 300, 150)`, dtype float64, with maximum absolute difference zero. Each file is 108,000,128 bytes. All 340 recorded iteration/error pairs match exactly across all three runs. The same zero-based stopping label 16975 appears in all logs (16976 updates). The scalar potential and exact final stopping-update error were not saved, so direct full-run comparisons of those unsaved quantities cannot be claimed.

| Component | Minimum (all runs) | Maximum (all runs) | SHA-256 (all runs) |
| --- | ---: | ---: | --- |
| Bx_full.npy | -2236.1678534362218 | 1526.790584481098 | `24ec5969a05ff26bc1df12ce34fa828bc9a5ff26608dcbc5c6fc88727d8c9416` |
| By_full.npy | -2345.1359553104426 | 2325.679282235039 | `aea8feee7c020cb95a027a01923fbfc59a0937c3a7b4d584acb63e96a88b1c9e` |
| Bz_full.npy | -3376.636 | 3165.5356466286189 | `4e3dcd5efef131937d9eebeeb191cb8ecd2e331a4f0c71e171b6bf36b50d077f` |

### Matched-run details and limits

Original run: `20261118_194031_937624`; V1: `20261118_214427_942015`; V2: `20261118_221042_587814`. All use step 4 inputs from `20261118_192252_109811`. All original-prefix and copied source/input hashes match. All runs use Python 3.12.7, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2 and psutil 7.2.2; V1 and V2 use Numba 0.68.1. Their observation/grid/tolerance/stopping rules and final gradient/scaling/save code are unchanged. Only the solver selector differs.

V2 captured `NUMBA_NUM_THREADS=4` and `OMP_NUM_THREADS=8`; its actual runtime confirms four Numba workers and the `omp` threading layer. The historical V1 report captures only `OMP_NUM_THREADS=8`, not its actual Numba worker count; the current environment defaults to 12, but that must not be represented as a recorded historical count.

CPU times sum activity across worker threads, so they are not elapsed time. RAM is sampled every 100 ms and brief peaks may be missed. Temperature, clocks, application load and AC/battery state were not controlled. The repeatable short-workload sweep favoured V2 with four workers; the full run confirms a further wall-time improvement and exact saved results on this input. This is not a proof of a global optimum or a CUDA performance conclusion.
