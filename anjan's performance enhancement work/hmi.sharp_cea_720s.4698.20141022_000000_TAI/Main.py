import numpy as np
import os
import matplotlib.pyplot as plt
from laplace import solve_pfss_cartesian
from laplace import solve_pfss_cartesian_vectorized
from laplace import laplace_solver_nonuniform
from scipy.interpolate import RegularGridInterpolator as rgi
from vectormath import curl_scipy, compute_divergence_nonuniform
import matplotlib.colors as colors
import matplotlib.cm as cm

# Grid parameters
Nx = 300                                # Number of grid points in x direction
Ny = 300                                # Number of grid points in y direction
Nz = 150                                # Number of grid points in z direction
Lx = 1471                                 # Box length in x direction
Ly = 799                                 # Box length in y direction
Lz = 1000                                 # Box length in z direction
X1 = np.linspace(0, Lx, Nx)
Y1 = np.linspace(0, Ly, Ny)
Z1 = np.linspace(0, Lz, Nz)
dx = X1[1] - X1[0]
dy = Y1[1] - Y1[0]
dz = Z1[1] - Z1[0] 

# Initialize potential grid
Phi = np.zeros((Nx, Ny, Nz))  
X, Y = np.meshgrid(np.linspace(0, Lx, Nx), np.linspace(0, Ly, Ny), indexing='ij')        
Bz = np.load('Preprocessedmagneticfield/Bz.npy') 
MaxBz = np.max(abs(Bz))
Phi[:,:,0] = Bz
print("Phi",np.max(abs(Phi)))

Phi = solve_pfss_cartesian_vectorized(Phi, dx, dy, dz, tol=1e-3, max_iter=100000, verbose=True)
print("Phi",np.max(abs(Phi)))

Bx = -np.gradient(Phi, X1, axis=0, edge_order=2)
By = -np.gradient(Phi, Y1, axis=1, edge_order=2)
Bz = -np.gradient(Phi, Z1, axis=2, edge_order=2)
Bx = Bx*MaxBz/np.max(abs(Bz))
By = By*MaxBz/np.max(abs(Bz))
Bz = Bz*MaxBz/np.max(abs(Bz))
print("edge_order2",np.max(abs(Bz)))


output_dir = "PFSSmagneticfield/Bfield_full"
os.makedirs(output_dir, exist_ok=True)

# Save full 3D magnetic field arrays
np.save(os.path.join(output_dir, 'Bx_full.npy'), Bx)
np.save(os.path.join(output_dir, 'By_full.npy'), By)
np.save(os.path.join(output_dir, 'Bz_full.npy'), Bz)
print("saved")

# ------------------------------------------------------------
# 3. Interpolate uniform B-field onto non-uniform grid points
# ------------------------------------------------------------
Bx_interp_func = rgi((X1, Y1, Z1), Bx, bounds_error=False, fill_value=0)
By_interp_func = rgi((X1, Y1, Z1), By, bounds_error=False, fill_value=0)
Bz_interp_func = rgi((X1, Y1, Z1), Bz, bounds_error=False, fill_value=0)

# --------------------------
# Grid parameters and domain
# --------------------------
Nx = 300                                # Number of grid points in x direction
Ny = 300                                # Number of grid points in y direction
Nz = 150                                # Number of grid points in z direction
LxL = 50
LxR = 1422                                 # Box length in x direction
LyL = 25
LyR = 775                                 # Box length in y direction
Lz = 966                                 # Box length in z direction
X1 = np.linspace(LxL, LxR, Nx)
Y1 = np.linspace(LyL, LyR, Ny)
Z1 = np.linspace(0, Lz, Nz)
dx = X1[1] - X1[0]
dy = Y1[1] - Y1[0]
dz = Z1[1] - Z1[0]          

X, Y, Z = np.meshgrid(X1, Y1, Z1, indexing='ij')  # shape (Nx, Ny, Nz)
points_nonuniform = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=-1)

Bx = Bx_interp_func(points_nonuniform).reshape((Nx, Ny, Nz))
By = By_interp_func(points_nonuniform).reshape((Nx, Ny, Nz))
Bz = Bz_interp_func(points_nonuniform).reshape((Nx, Ny, Nz))
print(np.max(abs(Bz)))
output_dir = "PFSSmagneticfield_for_uniform_grid/Bfield_full"
os.makedirs(output_dir, exist_ok=True)

# Save full 3D magnetic field arrays
np.save(os.path.join(output_dir, 'Bx_full.npy'), Bx)
np.save(os.path.join(output_dir, 'By_full.npy'), By)
np.save(os.path.join(output_dir, 'Bz_full.npy'), Bz)
print("saved")

# ----------------------------------------
# 1. Load 2D magnetic field data
# ----------------------------------------
Bx = np.load('Preprocessedmagneticfield/Bx.npy')
By = np.load('Preprocessedmagneticfield/By.npy')
Bz = np.load('Preprocessedmagneticfield/Bz.npy')
print("Max |Bz| (original):", np.max(np.abs(Bz)))

# ----------------------------------------
# 2. Original uniform grid
# ----------------------------------------
Nx = 300
Ny = 300
Lx = 1471                                 # Box length in x direction
Ly = 799  
x_uniform = np.linspace(0, Lx, Nx)
y_uniform = np.linspace(0, Ly, Ny)

# ----------------------------------------------------------
# 3. New non-uniform grid
# ----------------------------------------------------------
Nx_new = 300
Ny_new = 300
LxL = 50
LxR = 1422                                 # Box length in x direction
LyL = 25
LyR = 775 
x_nonuniform = np.linspace(LxL, LxR, Nx_new)
y_nonuniform = np.linspace(LyL, LyR, Ny_new)
X_new, Y_new = np.meshgrid(x_nonuniform, y_nonuniform, indexing='ij')
points_new = np.stack([X_new.ravel(), Y_new.ravel()], axis=-1)

# ----------------------------------------------------------
# 4. Interpolate onto the new grid
# ----------------------------------------------------------
Bx_interp_func = rgi((x_uniform, y_uniform), Bx, bounds_error=False, fill_value=0)
By_interp_func = rgi((x_uniform, y_uniform), By, bounds_error=False, fill_value=0)
Bz_interp_func = rgi((x_uniform, y_uniform), Bz, bounds_error=False, fill_value=0)

Bx_new = Bx_interp_func(points_new).reshape((Nx_new, Ny_new))
By_new = By_interp_func(points_new).reshape((Nx_new, Ny_new))
Bz_new = Bz_interp_func(points_new).reshape((Nx_new, Ny_new))
print("Max |Bz| (interpolated):", np.max(np.abs(Bz_new)))

# ----------------------------------------
# 5. Save interpolated arrays
# ----------------------------------------
output_dir = "Preprocessedmagneticfield_interpolated"
os.makedirs(output_dir, exist_ok=True)

np.save(os.path.join(output_dir, 'Bx.npy'), Bx_new)
np.save(os.path.join(output_dir, 'By.npy'), By_new)
np.save(os.path.join(output_dir, 'Bz.npy'), Bz_new)
print("2D fields saved.")

# --------------------------
# Grid parameters and domain
# --------------------------
Nx = 300                                # Number of grid points in x direction
Ny = 300                                # Number of grid points in y direction
Nz = 150                                # Number of grid points in z direction
LxL = 50
LxR = 1422                                 # Box length in x direction
LyL = 25
LyR = 775                                 # Box length in y direction
Lz = 966                                 # Box length in z direction
X1 = np.linspace(LxL, LxR, Nx)
Y1 = np.linspace(LyL, LyR, Ny)
Z1 = np.linspace(0, Lz, Nz)
dx = X1[1] - X1[0]
dy = Y1[1] - Y1[0]
dz = Z1[1] - Z1[0]           


BxC = np.load('Preprocessedmagneticfield_interpolated/Bx.npy')
ByC = np.load('Preprocessedmagneticfield_interpolated/By.npy')
BzC = np.load('Preprocessedmagneticfield_interpolated/Bz.npy')  
print(np.max(abs(BzC)))        
#print(BzC.shape)
w = np.load('weight_function/W.npy')

# Other parameters
dt = .0001
num_steps = 2000001
save_interval =200 
dx_arr, dy_arr, dz_arr = np.diff(X1), np.diff(Y1), np.diff(Z1)

# Load initial PFSS magnetic field
Bx = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full/Bx_full.npy')
By = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full/By_full.npy')
Bz = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full/Bz_full.npy')
print(np.max(abs(Bz))) 
#print(Bz.shape)
# Apply boundary values from analytical field
Bx[:, :, 0] = BxC[:, :]
By[:, :, 0] = ByC[:, :]
Bz[:, :, 0] = BzC[:, :]

BxI = Bx.copy()
ByI = By.copy()
BzI = Bz.copy()

# Allocate arrays for L and time
L_correct = np.zeros(num_steps)
L_another = np.zeros(num_steps+1)
time = np.zeros(num_steps)

Cx, Cy, Cz = curl_scipy(Bx, By, Bz, X1, Y1, Z1)

omegax = (Cy * Bz - Cz * By)
omegay = (Cz * Bx - Cx * Bz)
omegaz = (Cx * By - Cy * Bx)

divB = compute_divergence_nonuniform(Bx, By, Bz, X1, Y1, Z1)
modB = np.sqrt(Bx**2 + By**2 + Bz**2)

Lintegrand_correct = w*((omegax**2 + omegay**2 + omegaz**2) / modB**2 + divB**2)
L_yx = np.trapezoid(Lintegrand_correct, x=Z1, axis=2)
L_x = np.trapezoid(L_yx, x=Y1, axis=1)
L = np.trapezoid(L_x, x=X1, axis=0)
L_another[0] = L

# Main WSR optimization loop
current_dt = dt
L_values = [L_another[0]]
time = [0.0]

step = 0

step_dir = os.path.join("Optimizedmagneticfield", f"step_{step}")
os.makedirs(step_dir, exist_ok=True)
np.save(os.path.join(step_dir, 'Bx.npy'), Bx)
np.save(os.path.join(step_dir, 'By.npy'), By)
np.save(os.path.join(step_dir, 'Bz.npy'), Bz)
np.save(os.path.join(step_dir, 'L_values.npy'), np.array(L_values))
while step < num_steps:
    # Save current field state
    Bx_temp, By_temp, Bz_temp = Bx.copy(), By.copy(), Bz.copy()

    # Recalculate all needed fields
    modB = np.sqrt(Bx**2 + By**2 + Bz**2)
    Cx, Cy, Cz = curl_scipy(Bx, By, Bz, X1, Y1, Z1)
    omegax = Cy * Bz - Cz * By
    omegay = Cz * Bx - Cx * Bz
    omegaz = Cx * By - Cy * Bx

    omegaAAAx = omegax / modB**2
    omegaAAAy = omegay / modB**2
    omegaAAAz = omegaz / modB**2

    
    omegaBBBx = divB * Bx / modB**2
    omegaBBBy = divB * By / modB**2
    omegaBBBz = divB * Bz / modB**2
    
    # Evolution step
    omegax = (omegax - divB * Bx) / modB**2
    omegay = (omegay - divB * By) / modB**2
    omegaz = (omegaz - divB * Bz) / modB**2
    modomega = np.sqrt(omegax**2 + omegay**2 + omegaz**2)

    omegacBx = omegay * Bz - omegaz * By
    omegacBy = omegaz * Bx - omegax * Bz
    omegacBz = omegax * By - omegay * Bx

    Fx, Fy, Fz = curl_scipy(omegacBx, omegacBy, omegacBz, X1, Y1, Z1)
    Fx -= omegay * Cz - omegaz * Cy
    Fy -= omegaz * Cx - omegax * Cz
    Fz -= omegax * Cy - omegay * Cx

    omegadB = omegax * Bx + omegay * By + omegaz * Bz
    grad_x = np.gradient(omegadB, X1, axis=0, edge_order=2)
    grad_y = np.gradient(omegadB, Y1, axis=1, edge_order=2)
    grad_z = np.gradient(omegadB, Z1, axis=2, edge_order=2)

    Fx = Fx - grad_x + omegax * divB + Bx * (modomega**2)
    Fy = Fy - grad_y + omegay * divB + By * (modomega**2)
    Fz = Fz - grad_z + omegaz * divB + Bz * (modomega**2)

    omegaBBBdB = omegaBBBx * Bx + omegaBBBy * By + omegaBBBz * Bz
    gradw_x = np.gradient(w, X1, axis=0, edge_order=2)
    gradw_y = np.gradient(w, Y1, axis=1, edge_order=2)
    gradw_z = np.gradient(w, Z1, axis=2, edge_order=2)

    omegaAAAcBx = omegaAAAy * Bz - omegaAAAz * By
    omegaAAAcBy = omegaAAAz * Bx - omegaAAAx * Bz
    omegaAAAcBz = omegaAAAx * By - omegaAAAy * Bx

    omegaAAAcBcgrad_x = (omegaAAAcBy * gradw_z - omegaAAAcBz * gradw_y) + (omegaBBBdB * gradw_x)
    omegaAAAcBcgrad_y = (omegaAAAcBz * gradw_x - omegaAAAcBx * gradw_z) + (omegaBBBdB * gradw_y)
    omegaAAAcBcgrad_z = (omegaAAAcBx * gradw_y - omegaAAAcBy * gradw_x) + (omegaBBBdB * gradw_z)

    Ftildex = w * Fx + omegaAAAcBcgrad_x
    Ftildey = w * Fy + omegaAAAcBcgrad_y
    Ftildez = w * Fz + omegaAAAcBcgrad_z

    Bx += current_dt * Ftildex
    By += current_dt * Ftildey
    Bz += current_dt * Ftildez

    # Enforce boundary condition
    Bx[0,:,:], Bx[-1,:,:] = BxI[0,:,:], BxI[-1,:,:]
    Bx[:,0,:], Bx[:,-1,:] = BxI[:,0,:], BxI[:,-1,:]
    Bx[:,:,0], Bx[:,:,-1] = BxI[:,:,0], BxI[:,:,-1]
    By[0,:,:], By[-1,:,:] = ByI[0,:,:], ByI[-1,:,:]
    By[:,0,:], By[:,-1,:] = ByI[:,0,:], ByI[:,-1,:]
    By[:,:,0], By[:,:,-1] = ByI[:,:,0], ByI[:,:,-1]
    Bz[0,:,:], Bz[-1,:,:] = BzI[0,:,:], BzI[-1,:,:]
    Bz[:,0,:], Bz[:,-1,:] = BzI[:,0,:], BzI[:,-1,:]
    Bz[:,:,0], Bz[:,:,-1] = BzI[:,:,0], BzI[:,:,-1]
    
    modB = np.sqrt(Bx**2 + By**2 + Bz**2)
    Cx, Cy, Cz = curl_scipy(Bx, By, Bz, X1, Y1, Z1)
    omegax = Cy * Bz - Cz * By
    omegay = Cz * Bx - Cx * Bz
    omegaz = Cx * By - Cy * Bx
    
    divB = compute_divergence_nonuniform(Bx, By, Bz, X1, Y1, Z1)
    
    Lintegrand_correct = w * ((omegax**2 + omegay**2 + omegaz**2) / modB**2 + divB**2)
    L_yx = np.trapezoid(Lintegrand_correct, x=Z1, axis=2)
    L_x = np.trapezoid(L_yx, x=Y1, axis=1)
    Lnew = np.trapezoid(L_x, x=X1, axis=0)

    # Check L descent condition
    if Lnew <= L_values[-1]:
        # Accept the step
        L_values.append(Lnew)
        time.append(time[-1] + current_dt)
        print(f"[Step {step}] L: {Lnew:.4e}, dt: {current_dt:.2e}")
        step += 1
        current_dt *= 1.01  # slowly increase dt

        # Save every `save_interval` steps
        if step % save_interval == 0:
            step_dir = os.path.join("Optimizedmagneticfield", f"step_{step}")
            os.makedirs(step_dir, exist_ok=True)
            np.save(os.path.join(step_dir, 'Bx.npy'), Bx)
            np.save(os.path.join(step_dir, 'By.npy'), By)
            np.save(os.path.join(step_dir, 'Bz.npy'), Bz)
            np.save(os.path.join(step_dir, 'L_values.npy'), np.array(L_values))

            plt.figure()
            plt.semilogy(time, np.array(L_values)/L_values[0])
            plt.xlabel("Time")
            plt.ylabel("Normalized L (semilogy)")
            plt.title("L vs Time")
            plt.savefig(os.path.join(step_dir, "L_functional_semilogy.png"))
            plt.close()

    else:
        # Reject the step
        Bx, By, Bz = Bx_temp, By_temp, Bz_temp
        current_dt /= 2
        print(f"[Step {step}] L ↑. Reducing dt to {current_dt:.2e}")

        if current_dt < dt/1000:
            print("Terminating: dt too small.")
            break

step_dir = os.path.join("Optimizedmagneticfield", f"step_{step}")
os.makedirs(step_dir, exist_ok=True)
np.save(os.path.join(step_dir, 'Bx.npy'), Bx)
np.save(os.path.join(step_dir, 'By.npy'), By)
np.save(os.path.join(step_dir, 'Bz.npy'), Bz)
np.save(os.path.join(step_dir, 'L_values.npy'), np.array(L_values))
print("Final step complete.")





