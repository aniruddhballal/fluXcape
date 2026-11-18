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

The complete observation comparison will be recorded below after the v2 run finishes. No claim of a global performance maximum is justified by this bounded set of experiments.
