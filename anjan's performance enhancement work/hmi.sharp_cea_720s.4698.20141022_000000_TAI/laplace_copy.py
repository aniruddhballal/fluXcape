import os
import numpy as np
from numba import config, njit, prange, set_num_threads

def laplace_solver_nonuniform(Phi, dx, dy, dz, tol=1e-3, max_iter=100000):
    nx, ny, nz = Phi.shape
    
    for iteration in range(max_iter):
        Phi_old = Phi.copy()
        print(iteration)
        wx = 1 / (dx * (2 * dx))
        wx_p = 1 / (dx * (2 * dx))
        
        wy = 1 / (dy * (2 * dy))
        wy_p = 1 / (dy * (2 * dy))
        
        wz = 1 / (dz * (2 * dz))
        wz_p = 1 / (dz * (2 * dz))
        
        denom = wx + wx_p + wy + wy_p + wz + wz_p

        Phi[1:-1, 1:-1, 1:-1] = (
            wx * Phi_old[2:, 1:-1, 1:-1] +
            wx_p * Phi_old[:-2, 1:-1, 1:-1] +
            wy * Phi_old[1:-1, 2:, 1:-1] +
            wy_p * Phi_old[1:-1, :-2, 1:-1] +
            wz * Phi_old[1:-1, 1:-1, 2:] +
            wz_p * Phi_old[1:-1, 1:-1, :-2]
        ) / denom
        error = np.max(np.abs(Phi - Phi_old))
        if error < tol:
            print(f'Converged in {iteration} iterations')
            break

        
    return Phi
    
def solve_pfss_cartesian(Phi_init, dx, dy, dz, tol=1e-4, max_iter=100000, verbose=False):
    """
    Solve Laplace's equation ∇²Φ = 0 with dx ≠ dy ≠ dz using Jacobi iteration.
    
    Parameters:
        Phi_init : ndarray
            3D array of shape (Nx, Ny, Nz) with initial guess and boundary conditions.
        dx, dy, dz : float
            Grid spacing in x, y, z directions respectively.
        tol : float
            Convergence tolerance for maximum change in Φ.
        max_iter : int
            Maximum number of Jacobi iterations.
        verbose : bool
            If True, print progress every 50 iterations.
    
    Returns:
        Phi : ndarray
            3D potential field solution Φ(x,y,z).
    """
    Phi = Phi_init.copy()
    Nx, Ny, Nz = Phi.shape

    for step in range(max_iter):
        print(step)
        Phi_old = Phi.copy()
        for i in range(1, Nx-1):
            for j in range(1, Ny-1):
                for k in range(1, Nz-1):
                    term_x = (Phi_old[i+1,j,k] + Phi_old[i-1,j,k]) / dx**2
                    term_y = (Phi_old[i,j+1,k] + Phi_old[i,j-1,k]) / dy**2
                    term_z = (Phi_old[i,j,k+1] + Phi_old[i,j,k-1]) / dz**2
                    denom = 2/dx**2 + 2/dy**2 + 2/dz**2
                    Phi[i,j,k] = (term_x + term_y + term_z) / denom

        error = np.max(np.abs(Phi - Phi_old))
        if verbose and step % 50 == 0:
            print(f"Step {step}, max error = {error:.2e}")
        if error < tol:
            print(f'✅ Converged in {step} iterations with error {error:.2e}')
            break

    else:
        print("⚠️ Did not converge within max_iter steps.")
    
    return Phi
    
import numpy as np

@njit(parallel=True, fastmath=False, error_model='numpy', cache=True)
def _jacobi_update(Phi_old, Phi, dx2, dy2, dz2, denom, errors, steps, bx, by):
    """Advance disjoint cores using private shrinking halos and exact per-step errors."""
    Nx, Ny, Nz = Phi_old.shape
    ntx = (Nx - 2 + bx - 1) // bx
    nty = (Ny - 2 + by - 1) // by
    for tile_unsigned in prange(ntx * nty):
        tile = np.int64(tile_unsigned)
        cx0 = 1 + (tile // nty) * bx
        cy0 = 1 + (tile % nty) * by
        cx1, cy1 = min(Nx-1, cx0+bx), min(Ny-1, cy0+by)
        x0, y0 = max(0, cx0-steps), max(0, cy0-steps)
        x1, y1 = min(Nx, cx1+steps), min(Ny, cy1+steps)
        a = np.empty((x1-x0, y1-y0, Nz), dtype=np.float64)
        b = np.empty_like(a)
        for i in range(x1-x0):
            for j in range(y1-y0):
                for k in range(Nz):
                    value = Phi_old[x0+i, y0+j, k]
                    a[i, j, k] = value
                    b[i, j, k] = value
        for t in range(steps):
            margin = steps-t-1
            ix0, iy0 = max(1, cx0-margin)-x0, max(1, cy0-margin)-y0
            ix1, iy1 = min(Nx-1, cx1+margin)-x0, min(Ny-1, cy1+margin)-y0
            maximum = np.uint64(0)
            for i in range(ix0, ix1):
                for j in range(iy0, iy1):
                    core = cx0 <= x0+i < cx1 and cy0 <= y0+j < cy1
                    for k in range(1, Nz-1):
                        value = (
                            (a[i+1, j, k] + a[i-1, j, k]) / dx2 +
                            (a[i, j+1, k] + a[i, j-1, k]) / dy2 +
                            (a[i, j, k+1] + a[i, j, k-1]) / dz2
                        ) / denom
                        b[i, j, k] = value
                        if core:
                            bits = np.float64(abs(value-a[i, j, k])).view(np.uint64)
                            if bits > maximum:
                                maximum = bits
            errors[tile, t] = maximum
            a, b = b, a
        for i in range(cx0, cx1):
            for j in range(cy0, cy1):
                for k in range(1, Nz-1):
                    Phi[i, j, k] = a[i-x0, j-y0, k]


def solve_pfss_cartesian_vectorized(Phi_init, dx, dy, dz, tol=1e-3, max_iter=100000, verbose=False):
    """
    Vectorized Jacobi solver for ∇²Φ = 0 with unequal grid spacing (dx, dy, dz).
    
    Parameters:
        Phi_init : ndarray
            Initial 3D potential field with boundary conditions.
        dx, dy, dz : float
            Grid spacing in x, y, z directions respectively.
        tol : float
            Convergence tolerance.
        max_iter : int
            Maximum number of iterations.
        verbose : bool
            Print progress every 50 steps if True.
    
    Returns:
        Phi : ndarray
            The converged 3D potential field.
    """
    Phi = Phi_init.copy()
    Nx, Ny, Nz = Phi.shape

    dx2, dy2, dz2 = dx**2, dy**2, dz**2
    denom = 2/dx2 + 2/dy2 + 2/dz2
    use_numba = (Phi_init.dtype == np.float64 and Phi_init.flags.c_contiguous
                 and min(Phi.shape) >= 3 and np.isfinite(Phi_init).all())
    if use_numba:
        if 'NUMBA_NUM_THREADS' not in os.environ:
            set_num_threads(min(4, config.NUMBA_NUM_THREADS))
        Phi_old = Phi.copy()
        tile, depth = 16, 4
        ntiles = ((Nx-2+tile-1)//tile) * ((Ny-2+tile-1)//tile)
        errors = np.empty((ntiles, depth), dtype=np.uint64)
        start, width = 0, 0

    for step in range(max_iter):
        if use_numba:
            if step == start+width:
                start = step
                # Keep batches within the original progress boundaries.
                next_log = ((start+49)//50)*50
                width = min(depth, max_iter-start, next_log-start+1)
                Phi, Phi_old = Phi_old, Phi
                _jacobi_update(Phi_old, Phi, dx2, dy2, dz2, denom, errors, width, tile, tile)
                block_errors = np.max(errors[:, :width], axis=0).view(np.float64)
            error = block_errors[step-start]
        else:
            Phi_old = Phi.copy()

            Phi[1:-1, 1:-1, 1:-1] = (
                (Phi_old[2:  , 1:-1, 1:-1] + Phi_old[0:-2, 1:-1, 1:-1]) / dx2 +
                (Phi_old[1:-1, 2:  , 1:-1] + Phi_old[1:-1, 0:-2, 1:-1]) / dy2 +
                (Phi_old[1:-1, 1:-1, 2:  ] + Phi_old[1:-1, 1:-1, 0:-2]) / dz2
            ) / denom

            error = np.max(np.abs(Phi - Phi_old))
        if verbose and step % 50 == 0:
            print(f"Step {step}, max error = {error:.2e}")
        if error < tol:
            if use_numba and step < start+width-1:
                # Recover the first converged field, not the batch's later field.
                _jacobi_update(Phi_old, Phi, dx2, dy2, dz2, denom, errors, step-start+1, tile, tile)
            print(f"✅ Converged in {step} iterations with error {error:.2e}")
            break
    else:
        print("⚠️ Did not converge within max_iter steps.")
    
    return Phi

