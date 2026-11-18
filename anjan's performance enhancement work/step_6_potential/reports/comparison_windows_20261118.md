# Windows step 6 first-field comparison - 18 November 2026

Both runs completed successfully and produced all three scoped field files. The optimised outputs are byte-identical to the original outputs, with matching SHA-256 hashes. All saved convergence samples match exactly in iteration label and full-precision maximum change.

Original run: `20261118_194031_937624`. Optimised run: `20261118_214427_942015`.

| Metric | Original | Optimised |
| --- | ---: | ---: |
| Wall time (s) | 6930.678691 | 540.392198 |
| Sampled CPU time (s) | 6895.203125 | 5460.593750 |
| Sampled peak process-tree RSS (MiB) | 713.304688 | 659.179688 |
| Generated field bytes | 324000384.000000 | 324000384.000000 |
| Final zero-based iteration label | 16975 | 16975 |
| Jacobi updates executed | 16976 | 16976 |
| Recorded convergence rows | 340 | 340 |

Observed wall-time speedup: **12.8253x**; elapsed-time reduction: **92.2029%**; time saved: **6390.286493 s**. Sampled peak RSS reduction: **7.5879%**.

## Output comparison

Each array has shape `(300, 300, 150)`, dtype `float64`, and 13,500,000 finite values in each run. All 40,500,000 saved field values match bit-for-bit, including signed-zero representation. No NaNs or infinities are present. Maximum absolute difference is zero for every component; file size is 108,000,128 bytes per component in both runs.

| Component | Minimum (both) | Maximum (both) | Maximum absolute difference |
| --- | ---: | ---: | ---: |
| Bx_full.npy | -2236.1678534362218 | 1526.790584481098 | 0 |
| By_full.npy | -2345.1359553104426 | 2325.679282235039 | 0 |
| Bz_full.npy | -3376.636 | 3165.5356466286189 | 0 |

Matching SHA-256 values:

- `Bx_full.npy`: `24ec5969a05ff26bc1df12ce34fa828bc9a5ff26608dcbc5c6fc88727d8c9416`
- `By_full.npy`: `aea8feee7c020cb95a027a01923fbfc59a0937c3a7b4d584acb63e96a88b1c9e`
- `Bz_full.npy`: `4e3dcd5efef131937d9eebeeb191cb8ecd2e331a4f0c71e171b6bf36b50d077f`

## Convergence history

Every recorded sample matches exactly in iteration label and maximum-change value. Timestamp and elapsed-time columns differ as expected. Samples are logged every 50 updates by zero-based label; stopping at label 16975 occurs between recorded rows. Logs agree on stopping label and rounded final error. The exact error at the stopping update was not saved, and the scalar potential itself was not saved; equivalence statements above concern all saved field outputs and logged convergence samples.

| Label | Maximum change (both) | Original solver elapsed (s) | Optimised solver elapsed (s) |
| --- | ---: | ---: | ---: |
| 0 | 184.13792987483802 | 0.802661 | 1.659467 |
| 1000 | 0.20004285090107032 | 510.260251 | 32.384953 |
| 5000 | 0.012127960367394053 | 2222.316766 | 159.998637 |
| 10000 | 0.0031602086201729662 | 4175.400081 | 319.482433 |
| 15000 | 0.0013292835193112751 | 6157.270214 | 471.140937 |
| 16950 | 0.0010033744427957458 | 6915.819282 | 530.251310 |

## Matching workload and environment

Both runs used the same physical Windows system (AMD64 Family 25 Model 80 Stepping 0, 12 logical CPUs), Python 3.12.7, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2 and psutil 7.2.2. The optimised run additionally used Numba 0.68.1. Both used the original first-field prefix, identical copied sources and identical input files from step 4 run `20261118_192252_109811`, verified from recorded hashes. Original-prefix hashes match. Both preserve the grid, tolerance, stopping rule, gradients, scaling and saves. Interpolation is excluded from both workloads.

Both reports record `OMP_NUM_THREADS=8`. `NUMBA_NUM_THREADS` is unset in the captured environment; the actual Numba worker count was not recorded and must not be inferred to be eight from the OpenMP environment variable.

## Limits

One completed run per implementation, executed sequentially. This is an observed speedup for these matched runs, not a repeated-trial median or a guarantee for other machines/inputs. Sampling is every 100 ms and may miss brief peaks. CPU counters are sampled cumulative process-tree CPU time; parallel CPU time sums work across cores and is not elapsed time. Wall time includes launch, logging, save operations and any JIT compilation; copying and final output hashing are excluded. No separate gradient/scaling/save timings were collected. File/hash equality was independently rechecked from the local files when writing this comparison.
