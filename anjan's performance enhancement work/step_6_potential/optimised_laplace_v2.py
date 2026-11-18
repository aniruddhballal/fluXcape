"""CPU v2: unchanged field arithmetic with a vectorisable error reduction.

Absolute float64 differences are nonnegative. Their IEEE-754 uint64 bit patterns
sort in the same order as their numeric values; NaN encodings sort above +inf.
An integer maximum therefore preserves the convergence decision (including NaN
propagation) while allowing SIMD without enabling floating-point fast-math.
This is a bit reinterpretation, not an integer conversion or precision change.
"""
import json
import os
from pathlib import Path

import numpy as np
from numba import config, get_num_threads, njit, prange, set_num_threads, threading_layer


@njit(parallel=True, fastmath=False, error_model='numpy', cache=True)
def jacobi_update(old, new, dx2, dy2, dz2, denom, errors):
    nx, ny, nz = old.shape
    for i in prange(1, nx - 1):
        largest = np.uint64(0)
        for j in range(1, ny - 1):
            for k in range(1, nz - 1):
                value = (
                    (old[i+1, j, k] + old[i-1, j, k]) / dx2 +
                    (old[i, j+1, k] + old[i, j-1, k]) / dy2 +
                    (old[i, j, k+1] + old[i, j, k-1]) / dz2
                ) / denom
                new[i, j, k] = value
                bits = np.float64(abs(value - old[i, j, k])).view(np.uint64)
                if bits > largest:
                    largest = bits
        errors[i-1] = largest


def solve_pfss_cartesian_vectorized(Phi_init, dx, dy, dz, tol=1e-3,
                                   max_iter=100000, verbose=False):
    if (Phi_init.ndim != 3 or Phi_init.dtype != np.float64
            or not Phi_init.flags.c_contiguous or min(Phi_init.shape) < 3
            or not np.isfinite(Phi_init).all()):
        from laplace import solve_pfss_cartesian_vectorized as original
        return original(Phi_init, dx, dy, dz, tol, max_iter, verbose)

    from _step6_progress import ProgressLog
    progress = ProgressLog()
    # Target-device default; an explicit NUMBA_NUM_THREADS takes precedence.
    if 'NUMBA_NUM_THREADS' not in os.environ:
        set_num_threads(min(4, config.NUMBA_NUM_THREADS))
    Phi, spare = Phi_init.copy(), Phi_init.copy()
    errors = np.empty(Phi.shape[0] - 2, dtype=np.uint64)
    dx2, dy2, dz2 = dx**2, dy**2, dz**2
    denom = 2/dx2 + 2/dy2 + 2/dz2
    for step in range(max_iter):
        jacobi_update(Phi, spare, dx2, dy2, dz2, denom, errors)
        Phi, spare = spare, Phi
        error = np.max(errors).view(np.float64)
        if step == 0:
            Path('solver_runtime.json').write_text(json.dumps({
                'implementation': 'optimised-v2', 'numba_threads': get_num_threads(),
                'threading_layer': threading_layer(), 'fastmath': False,
                'dtype': 'float64', 'error_reduction': 'nonnegative-float64-bits-uint64-max'
            }, indent=2), encoding='utf-8')
        if verbose and step % 50 == 0:
            print(f'Step {step}, max error = {error:.2e}')
            progress.record(step, error)
        if error < tol:
            print(f'Converged in {step} iterations with error {error:.2e}')
            break
    else:
        print('Did not converge within max_iter steps.')
    return Phi
