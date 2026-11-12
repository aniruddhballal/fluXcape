import numpy as np

def curl_scipy(Bx, By, Bz, X, Y, Z):
    """
    Compute curl of B = (Bx, By, Bz) on a non-uniform Cartesian grid.
    
    Parameters:
        Bx, By, Bz : 3D numpy arrays of shape (nx, ny, nz)
            Components of the vector field.
        X, Y, Z : 1D numpy arrays of shape (nx,), (ny,), (nz,)
            Non-uniform coordinates in each direction.
    
    Returns:
        (Cx, Cy, Cz): 3D numpy arrays representing the curl components.
    """
    # ∂Bz/∂y and ∂By/∂z
    dBz_dy = np.gradient(Bz, Y, axis=1, edge_order=2)
    dBy_dz = np.gradient(By, Z, axis=2, edge_order=2)
    Cx = dBz_dy - dBy_dz

    # ∂Bx/∂z and ∂Bz/∂x
    dBx_dz = np.gradient(Bx, Z, axis=2, edge_order=2)
    dBz_dx = np.gradient(Bz, X, axis=0, edge_order=2)
    Cy = dBx_dz - dBz_dx

    # ∂By/∂x and ∂Bx/∂y
    dBy_dx = np.gradient(By, X, axis=0, edge_order=2)
    dBx_dy = np.gradient(Bx, Y, axis=1, edge_order=2)
    Cz = dBy_dx - dBx_dy

    return Cx, Cy, Cz
    
def compute_divergence_nonuniform(Bx, By, Bz, X, Y, Z):
    """
    Compute divergence of vector field B = (Bx, By, Bz) on a non-uniform grid.
    
    Parameters:
        Bx, By, Bz : 3D numpy arrays of shape (nx, ny, nz)
            Vector field components.
        X, Y, Z : 1D numpy arrays
            Non-uniform coordinate arrays for each axis.
    
    Returns:
        divB : 3D numpy array of divergence values.
    """
    dBx_dx = np.gradient(Bx, X, axis=0, edge_order=2)
    dBy_dy = np.gradient(By, Y, axis=1, edge_order=2)
    dBz_dz = np.gradient(Bz, Z, axis=2, edge_order=2)

    divB = dBx_dx + dBy_dy + dBz_dz
    return divB



