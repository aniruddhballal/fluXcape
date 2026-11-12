import numpy as np 
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator as rgi
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.colors as colors
import matplotlib.cm as cm
from matplotlib.lines import Line2D

# --------------------------
# Grid parameters and domain
# --------------------------\
Nx = 300                                # Number of grid points in x direction
Ny = 300                                # Number of grid points in y direction
Nz = 150                                # Number of grid points in z direction
LxL = 50                                # Box length in x direction
LyL = 25                                # Box length in y direction
LzL = 0                                 # Box length in z direction
LxR = 1422                              # Box length in x direction
LyR = 775                               # Box length in y direction
LzR = 966                               # Box length in z direction

L1x = 50
L2x = 188
L3x = 1284
L4x = 1422

L1y = 25
L2y = 100
L3y = 700
L4y = 775

L1z = -20
L2z = 0
L3z = 770
L4z = 966

X1 = np.linspace(LxL, LxR, Nx)
Y1 = np.linspace(LyL, LyR, Ny)
Z1 = np.linspace(LzL, LzR, Nz)
dx = X1[1] - X1[0]
dy = Y1[1] - Y1[0]
dz = Z1[1] - Z1[0]

# ---------------------------------------
# Load Magnetic Field Components (Field 1)
# ---------------------------------------
Bx = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full/Bx_full.npy')
By = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full/By_full.npy')
Bz = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full/Bz_full.npy')

# ---------------------------------------
# Load Magnetic Field Components (Field 2)
# ---------------------------------------
BX1 = np.load('Optimizedmagneticfield/step_6000/Bx.npy')
BY1 = np.load('Optimizedmagneticfield/step_6000/By.npy')
BZ1 = np.load('Optimizedmagneticfield/step_6000/Bz.npy')  
# -----------------------------
# Interpolators for both fields
# -----------------------------
Bx_interp = rgi((X1, Y1, Z1), Bx, bounds_error=False, fill_value=0)
By_interp = rgi((X1, Y1, Z1), By, bounds_error=False, fill_value=0)
Bz_interp = rgi((X1, Y1, Z1), Bz, bounds_error=False, fill_value=0)

BX1_interp = rgi((X1, Y1, Z1), BX1, bounds_error=False, fill_value=0)
BY1_interp = rgi((X1, Y1, Z1), BY1, bounds_error=False, fill_value=0)
BZ1_interp = rgi((X1, Y1, Z1), BZ1, bounds_error=False, fill_value=0)

# --------------------------
# Normalized vector field 1
# --------------------------
def B_field(pos):
    x, y, z = pos
    if not (L2x <= x <= L3x and L2y <= y <= L3y and L2z <= z <= L3z):
        return np.array([0, 0, 0])
    B = np.array([Bx_interp((x, y, z)), By_interp((x, y, z)), Bz_interp((x, y, z))])
    norm = np.linalg.norm(B)
    return B / norm if norm > 0 else B

# --------------------------
# Normalized vector field 2
# --------------------------
def B_field2(pos):
    x, y, z = pos
    if not (L2x <= x <= L3x and L2y <= y <= L3y and L2z <= z <= L3z):
        return np.array([0, 0, 0])
    B = np.array([BX1_interp((x, y, z)), BY1_interp((x, y, z)), BZ1_interp((x, y, z))])
    norm = np.linalg.norm(B)
    return B / norm if norm > 0 else B

# ---------------------
# RK4 integration step
# ---------------------
def rk4_step(B_func, pos, dt):
    k1 = B_func(pos)
    k2 = B_func(pos + 0.5 * dt * k1)
    k3 = B_func(pos + 0.5 * dt * k2)
    k4 = B_func(pos + dt * k3)
    new_pos = pos + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    if not (L2x <= new_pos[0] <= L3x and L2y <= new_pos[1] <= L3y and L2z <= new_pos[2] <= L3z):
        return None
    return new_pos

# ---------------------------------------
# Field line tracing (bidirectional)
# ---------------------------------------
def trace_fieldline(B_func, seed, steps=100000, dt=0.01):
    # Forward
    fwd = [seed.copy()]
    pos = seed.copy()
    for _ in range(steps):
        pos_new = rk4_step(B_func, pos, dt)
        if pos_new is None:
            break
        fwd.append(pos_new)
        pos = pos_new
    # Backward
    bwd = [seed.copy()]
    pos = seed.copy()
    for _ in range(steps):
        pos_new = rk4_step(B_func, pos, -dt)
        if pos_new is None:
            break
        bwd.append(pos_new)
        pos = pos_new
    return np.array(bwd[::-1] + fwd[1:])

# --------------------------
# Seed points for fieldlines
# --------------------------

seed_x, seed_y, seed_z = np.meshgrid(
    np.linspace(575, 700, 5),   
    np.linspace(300, 430, 5),
    np.linspace(0*dz,  10*dz, 1)
)
seeds = np.vstack([seed_x.ravel(), seed_y.ravel(), seed_z.ravel()]).T

# -----------------------
# 3D plot initialization
# -----------------------
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Contour plot at z=0 for background
Bz_zplane = BZ1[:, :, 0].T
ax.contourf(X1, Y1, Bz_zplane,levels = 300, zdir='z', offset=0, cmap='seismic', alpha=.2)
fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(vmax=np.max(Bz_zplane),
                                                     vmin=- np.max(Bz_zplane)),
                               cmap='seismic'),
             ax=ax, shrink=0.6, aspect=10, label='Bz Magnitude at Z=0')
# Plot field lines from field 1
for seed in seeds:
    line = trace_fieldline(B_field, seed)
    if line.shape[0] > 1:
        ax.plot(line[:, 0], line[:, 1], line[:, 2], color='green', lw=1.5)

# Plot field lines from field 2
for seed in seeds:
    line = trace_fieldline(B_field2, seed)
    if line.shape[0] > 1:
        ax.plot(line[:, 0], line[:, 1], line[:, 2], color='orange', lw=1.5)

# -----------------------
# Labels and formatting
# -----------------------
ax.set_xlim(L2x, L3x)
ax.set_ylim(L2y, L3y)
ax.set_zlim(0, L3z)

ax.set_xlabel("X", fontsize=20)
ax.set_ylabel("Y", fontsize=20)
ax.set_zlabel("Z", fontsize=20)
ax.set_title("Field lines of Two Magnetic Fields", fontsize=20)

# Set tick label size
ax.tick_params(axis='both', labelsize=20)
ax.tick_params(axis='z', labelsize=20)

# Add legend with larger font
legend_elements = [
    Line2D([0], [0], color='green', lw=2, label='PFSS'),
    Line2D([0], [0], color='orange', lw=2, label='Optimized')
]
ax.legend(handles=legend_elements, fontsize=20)

# Turn off axis and grid
#ax.set_axis_off()
ax.grid(True)

plt.tight_layout()
plt.show()


