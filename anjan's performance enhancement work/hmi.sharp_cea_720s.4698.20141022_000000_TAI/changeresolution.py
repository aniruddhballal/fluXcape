import numpy as np
import os
from scipy.interpolate import RegularGridInterpolator as rgi

def interpolate_pfss_to_box(
    input_dir,
    output_dir,
    Nx=300, Ny=300, Nz=150,
    LxL = 174, LxR = 626,
    LyL = 95, LyR = 315,
    Lz = 66, LxL_I = 60,  LxR_I = 740, LyL_I = 40, LyR_I = 370, Lz_I = 100
):
    """
    Interpolate PFSS magnetic field from uniform grid to a specified Cartesian box.

    Parameters
    ----------
    input_dir : str
        Path to directory with Bx_full.npy, By_full.npy, Bz_full.npy (uniform grid).
    output_dir : str
        Path where interpolated Bx, By, Bz will be saved.
    Nx, Ny, Nz : int
        Number of grid points in x, y, z directions for the target box.
    LxL, LxR : float
        Left and right bounds in x direction.
    LyL, LyR : float
        Left and right bounds in y direction.
    Lz : float
        Upper bound in z direction (lower bound fixed at 0).
    """

    # ------------------------
    # 1. Load uniform grid data
    # ------------------------
    Bx_u = np.load(os.path.join(input_dir, 'Bx.npy'))  # shape (Nx_u, Ny_u, Nz_u)
    By_u = np.load(os.path.join(input_dir, 'By.npy'))
    Bz_u = np.load(os.path.join(input_dir, 'Bz.npy'))

    Nx_u, Ny_u, Nz_u = Bx_u.shape
    print("Loaded uniform field:", Bx_u.shape)

    # Define uniform source grid coordinates
    X_u = np.linspace(LxL_I, LxR_I, Nx_u)
    Y_u = np.linspace(LyL_I, LyR_I, Ny_u)
    Z_u = np.linspace(0, Lz_I, Nz_u)

    # Interpolators
    Bx_interp = rgi((X_u, Y_u, Z_u), Bx_u, bounds_error=False, fill_value=0)
    By_interp = rgi((X_u, Y_u, Z_u), By_u, bounds_error=False, fill_value=0)
    Bz_interp = rgi((X_u, Y_u, Z_u), Bz_u, bounds_error=False, fill_value=0)

    # --------------------------
    # 2. Target non-uniform grid
    # --------------------------
    X1 = np.linspace(LxL, LxR, Nx)
    Y1 = np.linspace(LyL, LyR, Ny)
    Z1 = np.linspace(0, Lz, Nz)

    X, Y, Z = np.meshgrid(X1, Y1, Z1, indexing='ij')
    points = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=-1)

    # --------------------------
    # 3. Interpolation
    # --------------------------
    Bx_new = Bx_interp(points).reshape((Nx, Ny, Nz))
    By_new = By_interp(points).reshape((Nx, Ny, Nz))
    Bz_new = Bz_interp(points).reshape((Nx, Ny, Nz))

    print("Max |Bz| after interpolation:", np.max(np.abs(Bz_new)))

    # --------------------------
    # 4. Save output
    # --------------------------
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, 'Bx.npy'), Bx_new)
    np.save(os.path.join(output_dir, 'By.npy'), By_new)
    np.save(os.path.join(output_dir, 'Bz.npy'), Bz_new)
    print("Saved interpolated fields to:", output_dir)

    return X1, Y1, Z1, Bx_new, By_new, Bz_new
    
def interpolate_pfss_to_box_full(
    input_dir,
    output_dir,
    Nx=300, Ny=300, Nz=150,
    LxL = 174, LxR = 626,
    LyL = 95, LyR = 315,
    Lz = 66, LxL_I = 60,  LxR_I = 740, LyL_I = 40, LyR_I = 370, Lz_I = 100
):
    """
    Interpolate PFSS magnetic field from uniform grid to a specified Cartesian box.

    Parameters
    ----------
    input_dir : str
        Path to directory with Bx_full.npy, By_full.npy, Bz_full.npy (uniform grid).
    output_dir : str
        Path where interpolated Bx, By, Bz will be saved.
    Nx, Ny, Nz : int
        Number of grid points in x, y, z directions for the target box.
    LxL, LxR : float
        Left and right bounds in x direction.
    LyL, LyR : float
        Left and right bounds in y direction.
    Lz : float
        Upper bound in z direction (lower bound fixed at 0).
    """

    # ------------------------
    # 1. Load uniform grid data
    # ------------------------
    Bx_u = np.load(os.path.join(input_dir, 'Bx_full.npy'))  # shape (Nx_u, Ny_u, Nz_u)
    By_u = np.load(os.path.join(input_dir, 'By_full.npy'))
    Bz_u = np.load(os.path.join(input_dir, 'Bz_full.npy'))

    Nx_u, Ny_u, Nz_u = Bx_u.shape
    print("Loaded uniform field:", Bx_u.shape)

    # Define uniform source grid coordinates
    X_u = np.linspace(LxL_I, LxR_I, Nx_u)
    Y_u = np.linspace(LyL_I, LyR_I, Ny_u)
    Z_u = np.linspace(0, Lz_I, Nz_u)

    # Interpolators
    Bx_interp = rgi((X_u, Y_u, Z_u), Bx_u, bounds_error=False, fill_value=0)
    By_interp = rgi((X_u, Y_u, Z_u), By_u, bounds_error=False, fill_value=0)
    Bz_interp = rgi((X_u, Y_u, Z_u), Bz_u, bounds_error=False, fill_value=0)

    # --------------------------
    # 2. Target non-uniform grid
    # --------------------------
    X1 = np.linspace(LxL, LxR, Nx)
    Y1 = np.linspace(LyL, LyR, Ny)
    Z1 = np.linspace(0, Lz, Nz)

    X, Y, Z = np.meshgrid(X1, Y1, Z1, indexing='ij')
    points = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=-1)

    # --------------------------
    # 3. Interpolation
    # --------------------------
    Bx_new = Bx_interp(points).reshape((Nx, Ny, Nz))
    By_new = By_interp(points).reshape((Nx, Ny, Nz))
    Bz_new = Bz_interp(points).reshape((Nx, Ny, Nz))

    print("Max |Bz| after interpolation:", np.max(np.abs(Bz_new)))

    # --------------------------
    # 4. Save output
    # --------------------------
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, 'Bx_full.npy'), Bx_new)
    np.save(os.path.join(output_dir, 'By_full.npy'), By_new)
    np.save(os.path.join(output_dir, 'Bz_full.npy'), Bz_new)
    print("Saved interpolated fields to:", output_dir)

    return X1, Y1, Z1, Bx_new, By_new, Bz_new    
    
"""X1, Y1, Z1, Bx, By, Bz = interpolate_pfss_to_box(
    input_dir="PFSSmagneticfield/Bfield_full",
    output_dir="PFSSmagneticfield_for_uniform_grid1/Bfield_full",
    Nx=300, Ny=300, Nz=150,
    LxL=60, LxR=740,
    LyL=40, LyR=370,
    Lz=100,
)"""


