import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
import vectormath as v 

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
# ------------------------
# Load Magnetic Field Components
# ------------------------
Bx = np.load('Optimizedmagneticfield/step_6000/Bx.npy')
By = np.load('Optimizedmagneticfield/step_6000/By.npy')
Bz = np.load('Optimizedmagneticfield/step_6000/Bz.npy')

# Compute |B|
modB = np.sqrt(Bx**2 + By**2 + Bz**2)

# ------------------------
# Output Directory
# ------------------------
output_dir = "Optimizedmagneticfield/step_6000/Bfield_full/Magnetic Field Components"
os.makedirs(output_dir, exist_ok=True)

# ------------------------
# Meshgrid for plotting
# ------------------------
X, Y = np.meshgrid(X1, Y1, indexing='ij')  # shape (Nx, Ny)

# ------------------------
# Plot Function with Grid Overlay
# ------------------------
def overlay_grid(ax, X1, Y1):
    # Vertical lines (constant x)
    for x in X1:
        ax.plot([x]*len(Y1), Y1, color='k', lw=0.5, alpha=0.3)
    # Horizontal lines (constant y)
    for y in Y1:
        ax.plot(X1, [y]*len(X1), color='k', lw=0.5, alpha=0.3)

# ------------------------
# Loop over z slices
# ------------------------
for d in range(Nz):
    mid_z = Z1[d]

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Magnetic Field Components at Z = {mid_z:.3f}', fontsize=16)

    # Bx
    im1 = axs[0, 0].contourf(X, Y, Bx[:, :, d], cmap='seismic', levels = 300,
                             vmin=np.min(Bx[:,:,d]), vmax=np.max(Bx[:,:,d]))
    axs[0, 0].set_title('$B_x$')
    axs[0, 0].set_xlim(L2x, L3x)
    axs[0, 0].set_ylim(L2y, L3y)
    fig.colorbar(im1, ax=axs[0, 0])
    overlay_grid(axs[0, 0], X1, Y1)

    # By
    im2 = axs[0, 1].contourf(X, Y, By[:, :, d], cmap='seismic',levels = 300,
                             vmin=np.min(By[:,:,d]), vmax=np.max(By[:,:,d]))
    axs[0, 1].set_title('$B_y$')
    axs[0, 1].set_xlim(L2x, L3x)
    axs[0, 1].set_ylim(L2y, L3y)
    fig.colorbar(im2, ax=axs[0, 1])
    overlay_grid(axs[0, 1], X1, Y1)

    # Bz
    im3 = axs[1, 0].contourf(X, Y, Bz[:, :, d], cmap='seismic', levels = 300,
                             vmin=np.min(Bz[:,:,d]), vmax=np.max(Bz[:,:,d]))
    axs[1, 0].set_title('$B_z$')
    axs[1, 0].set_xlim(L2x, L3x)
    axs[1, 0].set_ylim(L2y, L3y)
    fig.colorbar(im3, ax=axs[1, 0])
    overlay_grid(axs[1, 0], X1, Y1)

    # |B|
    im4 = axs[1, 1].contourf(X, Y, modB[:, :, d], cmap='seismic',levels = 300,
                             vmin=np.min(modB[:,:,d]), vmax=np.max(modB[:,:,d]))
    axs[1, 1].set_title('$|\\mathbf{B}|$')
    axs[1, 1].set_xlim(L2x, L3x)
    axs[1, 1].set_ylim(L2y, L3y)
    fig.colorbar(im4, ax=axs[1, 1])
    overlay_grid(axs[1, 1], X1, Y1)

    # Axis settings
    for ax in axs.flat:
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_aspect('auto')  # Use 'auto' for non-uniform
        ax.grid(False)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    filename = f"B_components_with_grid_z{mid_z:.3f}.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close(fig)
    
mu0 = 4 * np.pi * 1e-7  # Permeability of free space

# Compute current density (J = (1/mu0) * curl B)
Jx, Jy, Jz = v.curl_scipy(Bx, By, Bz, X1, Y1, Z1)

# Compute modB and |J| if not already done
J_magnitude = np.sqrt(Jx**2 + Jy**2 + Jz**2)
modB = np.sqrt(Bx**2 + By**2 + Bz**2)

# Create output directory
output_dir = "Optimizedmagneticfield/step_6000/Bfield_full/current_components"
os.makedirs(output_dir, exist_ok=True)

# Loop over Z slices
for d in range(Nz):
    mid_z = Z1[d]
    
    
    # Normalize color scales
    vmin_Jx, vmax_Jx = np.min(Jx[:,:,d]), np.max(Jx[:,:,d])
    vmin_Jy, vmax_Jy = np.min(Jy[:,:,d]), np.max(Jy[:,:,d])
    vmin_Jz, vmax_Jz = np.min(Jz[:,:,d]), np.max(Jz[:,:,d])
    vmin_J,  vmax_J  = np.min(J_magnitude[:,:,d]), np.max(J_magnitude[:,:,d])

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Current Density Components at Z = {mid_z:.3f}', fontsize=16)

    # Jx
    im1 = axs[0, 0].contourf(X1, Y1, Jx[:, :, d].T, cmap='seismic', vmin=-vmax_Jx, vmax=vmax_Jx)
    axs[0, 0].set_title('$J_x$')
    fig.colorbar(im1, ax=axs[0, 0])
    overlay_grid(axs[0, 0], X1, Y1)

    # Jy
    im2 = axs[0, 1].contourf(X1, Y1, Jy[:, :, d].T, cmap='seismic', vmin=-vmax_Jy, vmax=vmax_Jy)
    axs[0, 1].set_title('$J_y$')
    fig.colorbar(im2, ax=axs[0, 1])
    overlay_grid(axs[0, 1], X1, Y1)

    # Jz
    im3 = axs[1, 0].contourf(X1, Y1, Jz[:, :, d].T, cmap='seismic', vmin=-vmax_Jz, vmax=vmax_Jz)
    axs[1, 0].set_title('$J_z$')
    fig.colorbar(im3, ax=axs[1, 0])
    overlay_grid(axs[1, 0], X1, Y1)

    # |J|
    im4 = axs[1, 1].contourf(X1, Y1, J_magnitude[:, :, d].T, cmap='seismic', vmin=-vmax_J, vmax=vmax_J)
    axs[1, 1].set_title('$|\\mathbf{J}|$')
    fig.colorbar(im4, ax=axs[1, 1])
    overlay_grid(axs[1, 1], X1, Y1)

    for ax in axs.flat:
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_aspect('equal')
        ax.grid(False)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    filename = f"J_components_z{mid_z:.3f}.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close(fig)
