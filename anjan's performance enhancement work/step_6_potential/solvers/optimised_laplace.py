"""Optional parallel Jacobi kernel; original equations and float64 precision."""
import numpy as np
from numba import njit, prange


@njit(parallel=True, fastmath=False, error_model='numpy', cache=True)
def jacobi_update(old, new, dx2, dy2, dz2, denom, errors):
    """Update independent cells in original expression order; fuse error scan."""
    nx, ny, nz = old.shape
    for i in prange(1, nx - 1):
        maximum = 0.0
        has_nan = False
        for j in range(1, ny - 1):
            for k in range(1, nz - 1):
                value = (
                    (old[i+1, j, k] + old[i-1, j, k]) / dx2 +
                    (old[i, j+1, k] + old[i, j-1, k]) / dy2 +
                    (old[i, j, k+1] + old[i, j, k-1]) / dz2
                ) / denom
                new[i, j, k] = value
                difference = abs(value - old[i, j, k])
                if np.isnan(difference):
                    has_nan = True
                elif difference > maximum:
                    maximum = difference
        errors[i-1] = np.nan if has_nan else maximum


def solve_pfss_cartesian_vectorized(Phi_init, dx, dy, dz, tol=1e-3,
                                   max_iter=100000, verbose=False):
    # Unsupported layouts/types and nonfinite boundaries retain NumPy behaviour.
    # The scoped real workload uses contiguous float64 volumes with finite inputs.
    if (Phi_init.ndim != 3 or Phi_init.dtype != np.float64
            or not Phi_init.flags.c_contiguous or min(Phi_init.shape) < 3
            or not np.isfinite(Phi_init).all()):
        from laplace import solve_pfss_cartesian_vectorized as original
        return original(Phi_init, dx, dy, dz, tol, max_iter, verbose)

    from _step6_progress import ProgressLog
    progress = ProgressLog()
    Phi = Phi_init.copy()
    spare = Phi_init.copy()
    errors = np.empty(Phi.shape[0] - 2, dtype=np.float64)
    dx2, dy2, dz2 = dx**2, dy**2, dz**2
    denom = 2/dx2 + 2/dy2 + 2/dz2
    for step in range(max_iter):
        jacobi_update(Phi, spare, dx2, dy2, dz2, denom, errors)
        Phi, spare = spare, Phi
        error = np.max(errors)
        if verbose and step % 50 == 0:
            print(f'Step {step}, max error = {error:.2e}')
            progress.record(step, error)
        if error < tol:
            print(f'Converged in {step} iterations with error {error:.2e}')
            break
    else:
        print('Did not converge within max_iter steps.')
    return Phi
