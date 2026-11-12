import numpy as np

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

    for step in range(max_iter):
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
            print(f"✅ Converged in {step} iterations with error {error:.2e}")
            break
    else:
        print("⚠️ Did not converge within max_iter steps.")
    
    return Phi

