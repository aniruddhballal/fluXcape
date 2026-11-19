"""Desktop-tuned exact Jacobi tiles; retains V3 arithmetic and stopping/replay.

The Ryzen 9 9950X / Ubuntu profile uses 16 workers and eight-update tiles.
NUMBA_NUM_THREADS remains an explicit override; this is a measured profile,
not an automatic tuner or a guarantee of optimal settings on other machines.
"""
import json
import os
from pathlib import Path

import numpy as np
from numba import config, get_num_threads, njit, prange, set_num_threads, threading_layer

TILE = 12
DEPTH = 8


@njit(parallel=True, fastmath=False, error_model='numpy', cache=True)
def temporal_update(old, new, dx2, dy2, dz2, denom, errors, steps, bx, by):
    """Advance disjoint cores using private shrinking halos and exact per-step errors."""
    nx, ny, nz = old.shape
    ntx = (nx - 2 + bx - 1) // bx
    nty = (ny - 2 + by - 1) // by
    for tile_unsigned in prange(ntx * nty):
        tile = np.int64(tile_unsigned)
        cx0 = 1 + (tile // nty) * bx
        cy0 = 1 + (tile % nty) * by
        cx1, cy1 = min(nx-1, cx0+bx), min(ny-1, cy0+by)
        x0, y0 = max(0, cx0-steps), max(0, cy0-steps)
        x1, y1 = min(nx, cx1+steps), min(ny, cy1+steps)
        a = np.empty((x1-x0, y1-y0, nz), dtype=np.float64)
        b = np.empty_like(a)
        for i in range(x1-x0):
            for j in range(y1-y0):
                for k in range(nz):
                    value = old[x0+i, y0+j, k]
                    a[i, j, k] = value
                    b[i, j, k] = value
        for t in range(steps):
            margin = steps-t-1
            ix0, iy0 = max(1, cx0-margin)-x0, max(1, cy0-margin)-y0
            ix1, iy1 = min(nx-1, cx1+margin)-x0, min(ny-1, cy1+margin)-y0
            largest = np.uint64(0)
            for i in range(ix0, ix1):
                for j in range(iy0, iy1):
                    core = cx0 <= x0+i < cx1 and cy0 <= y0+j < cy1
                    for k in range(1, nz-1):
                        value = (
                            (a[i+1, j, k] + a[i-1, j, k]) / dx2 +
                            (a[i, j+1, k] + a[i, j-1, k]) / dy2 +
                            (a[i, j, k+1] + a[i, j, k-1]) / dz2
                        ) / denom
                        b[i, j, k] = value
                        if core:
                            bits = np.float64(abs(value-a[i, j, k])).view(np.uint64)
                            if bits > largest:
                                largest = bits
            errors[tile, t] = largest
            a, b = b, a
        for i in range(cx0, cx1):
            for j in range(cy0, cy1):
                for k in range(1, nz-1):
                    new[i, j, k] = a[i-x0, j-y0, k]


def solve_pfss_cartesian_vectorized(Phi_init, dx, dy, dz, tol=1e-3,
                                   max_iter=100000, verbose=False):
    if (Phi_init.ndim != 3 or Phi_init.dtype != np.float64
            or not Phi_init.flags.c_contiguous or min(Phi_init.shape) < 3
            or not np.isfinite(Phi_init).all()):
        from laplace import solve_pfss_cartesian_vectorized as original
        return original(Phi_init, dx, dy, dz, tol, max_iter, verbose)
    from _step6_progress import ProgressLog
    progress = ProgressLog()
    if 'NUMBA_NUM_THREADS' not in os.environ:
        set_num_threads(min(16, config.NUMBA_NUM_THREADS))
    Phi, spare = Phi_init.copy(), Phi_init.copy()
    nx, ny, _ = Phi.shape
    ntiles = ((nx-2+TILE-1)//TILE) * ((ny-2+TILE-1)//TILE)
    errors = np.empty((ntiles, DEPTH), dtype=np.uint64)
    dx2, dy2, dz2 = dx**2, dy**2, dz**2
    denom = 2/dx2 + 2/dy2 + 2/dz2
    runtime = {'implementation': 'optimised-v4', 'numba_threads': get_num_threads(),
               'fastmath': False, 'dtype': 'float64', 'tile': TILE, 'depth': DEPTH,
               'tuning_profile': 'ryzen-9-9950x-ubuntu',
               'error_reduction': 'per-tile-per-update-uint64-max',
               'unused_speculative_updates': 0, 'replayed_updates': 0}
    start = 0
    while start < max_iter:
        # Never cross the next original progress event (0, 50, 100, ...).
        next_log = ((start+49)//50)*50
        width = min(DEPTH, max_iter-start, next_log-start+1)
        temporal_update(Phi, spare, dx2, dy2, dz2, denom, errors, width, TILE, TILE)
        block_errors = np.max(errors[:, :width], axis=0).view(np.float64)
        stop = next((offset for offset, error in enumerate(block_errors) if error < tol), None)
        used = width if stop is None else stop+1
        if used < width:
            # The first converged state is inside the tile batch. Recompute only
            # that prefix from its untouched starting state to retain its field.
            temporal_update(Phi, spare, dx2, dy2, dz2, denom, errors, used, TILE, TILE)
            runtime['unused_speculative_updates'] += width-used
            runtime['replayed_updates'] += used
        Phi, spare = spare, Phi
        if start == 0:
            runtime['threading_layer'] = threading_layer()
            Path('solver_runtime.json').write_text(json.dumps(runtime, indent=2), encoding='utf-8')
        for offset in range(used):
            step, error = start+offset, block_errors[offset]
            if verbose and step % 50 == 0:
                print(f'Step {step}, max error = {error:.2e}')
                progress.record(step, error)
        if stop is not None:
            runtime.update(final_iteration=step, final_max_change=float(error),
                           logical_updates=step+1, stop_reason='tolerance')
            Path('solver_runtime.json').write_text(json.dumps(runtime, indent=2), encoding='utf-8')
            print(f'Converged in {step} iterations with error {error:.2e}')
            break
        start += used
    else:
        if max_iter > 0:
            runtime.update(final_iteration=max_iter-1, final_max_change=float(error),
                           logical_updates=max_iter, stop_reason='iteration_limit')
            Path('solver_runtime.json').write_text(json.dumps(runtime, indent=2), encoding='utf-8')
        print('Did not converge within max_iter steps.')
    return Phi
