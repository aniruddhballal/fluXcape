import numpy as np
import matplotlib.pyplot as plt
from vectormath import curl_scipy  # your helper
import matplotlib
matplotlib.use("TkAgg")
from changeresolution import interpolate_pfss_to_box
import pyvista as pv

X1, Y1, Z1, Bx, By, Bz = interpolate_pfss_to_box(
    input_dir="Optimizedmagneticfield/step_2000",
    output_dir="Optimizedmagneticfield/step_uniform",
    Nx=300, Ny=300, Nz=150,
    LxL = 188, LxR = 1284,
    LyL = 100, LyR = 700,
    Lz = 300, LxL_I = 50,  LxR_I = 1422, LyL_I = 25, LyR_I = 775, Lz_I = 966
)
dx, dy, dz = X1[1]-X1[0], Y1[1]-Y1[0], Z1[1]-Z1[0]
Nx, Ny, Nz = 300, 300, 150

# Sanity check
assert Bx.shape == By.shape == Bz.shape == (Nx, Ny, Nz), "Field array shapes mismatch grid."

# --------------------------
# Compute curl(B)
# --------------------------
Cx, Cy, Cz = curl_scipy(Bx, By, Bz, X1, Y1, Z1)

# --------------------------
# Scalar alpha = (B · curlB)/|B|^2
# --------------------------
B2 = Bx**2 + By**2 + Bz**2
BdotCurl = Bx*Cx + By*Cy + Bz*Cz
eps = 1e-12 * np.nanmax(B2)

with np.errstate(divide='ignore', invalid='ignore'):
    alpha = np.where(B2 > eps, BdotCurl / B2, np.nan)

# --------------------------
# Flux-weighted averages
# --------------------------
def flux_weighted_alpha_plane(alpha, Bz, X1, Y1, z_index=0, mask=None):
    """
    Flux-weighted average of alpha on a z-plane:
        <alpha>_Phi = ∫ alpha |Bz| dx dy / ∫ |Bz| dx dy
    """
    a  = alpha[:, :, z_index]
    bz = Bz[:, :, z_index]
    w  = np.abs(bz)
    if mask is not None:
        a  = np.where(mask, a, np.nan)
        w  = np.where(mask, w, np.nan)

    num = np.trapezoid(
            np.trapezoid(a * w, X1, axis=0),
            Y1, axis=0
          )
    den = np.trapezoid(
            np.trapezoid(w, X1, axis=0),
            Y1, axis=0
          )
    #print("NUmereator",num)
    return num / den


def flux_weighted_alpha_all_z(alpha, Bz, X1, Y1, Z1, mask3d=None):
    """
    Flux-weighted <alpha> for every z-plane and also average over z.
    """
    Nz = alpha.shape[2]
    a_phi_z = np.empty(Nz)
    for k in range(Nz):
        if mask3d is None:
            a_phi_z[k] = flux_weighted_alpha_plane(alpha, Bz, X1, Y1, z_index=k)
        else:
            a_phi_z[k] = flux_weighted_alpha_plane(alpha, Bz, X1, Y1, z_index=k, mask=mask3d[:,:,k])
        #print(a_phi_z[k])
    # Average over z using trapezoidal integration
    one = np.ones(Nz)
    a_phi_global = np.trapezoid(a_phi_z, Z1) / np.trapezoid(one, Z1)

    return a_phi_z, a_phi_global

# Compute
alpha_vs_z, alpha_global = flux_weighted_alpha_all_z(alpha, Bz, X1, Y1, Z1)
max_value = np.nanmax(alpha_vs_z)
print("Max Weighted average alpha",max_value)

import os

# Get folder name (assuming script is inside each folder)
folder = os.path.basename(os.getcwd())

# Compute time index from folder ordering (or file counter)
# You can also parse time directly from folder name if needed.
# For now we assume sequential runs with Δt = 0.5
if os.path.exists("../alpha_results.dat"):
    mode = "a"   # append
else:
    mode = "w"   # write new file

# Count how many entries already exist to determine current step
if mode == "a":
    with open("../alpha_results.dat") as f:
        lines = f.readlines()
    step = len(lines)   # number of previous rows
else:
    step = 0

time = step * 0.5
with open("../alpha_results.dat", mode) as f:
    if mode == "w":
        f.write("# Time   MaxAlpha\n")
    f.write(f"{time:.2f} {max_value:.6e}\n")

# --------------------------
# Plot flux-weighted alpha vs z
# --------------------------
plt.figure(figsize=(8,5))
plt.plot(Z1, alpha_vs_z, marker="o", color="darkred", label=r"$\langle\alpha\rangle_\Phi(z)$")
plt.axhline(alpha_global, color="k", linestyle="--", label="Global average")
plt.xlabel("Height z")
plt.ylabel(r"$\langle \alpha \rangle_\Phi$")
plt.title("Flux-weighted ⟨α⟩ vs Height")
plt.grid(True, alpha=0.5)
plt.legend()
plt.show()

plt.savefig(f"alpha_frame_{step:04d}.png", dpi=150)
plt.close()


# --------------------------
# Example 2D visualization at z = 3
# --------------------------
z_index = 3
alpha_z0 = alpha[:, :, z_index]
Bz_z0    = Bz[:, :, z_index]
X, Y = np.meshgrid(X1, Y1, indexing='ij')

plt.figure(figsize=(8,6))
im = plt.contourf(X, Y, alpha_z0, levels=1000, cmap='RdBu_r')
plt.colorbar(im, label=r"$\alpha$")
cs = plt.contour(X, Y, Bz_z0, levels=100, colors='k', linewidths=1)
plt.clabel(cs, inline=True, fontsize=8, fmt="%.0f")
plt.title(r'Overlay of $\alpha$ (filled) and $B_z$ (contours) at $z=3$')
plt.xlabel("x")
plt.ylabel("y")
plt.gca().set_aspect("equal")
plt.show()

# --------------------------
# 3D visualization with PyVista
# --------------------------
import numpy as np
import pyvista as pv

X, Y, Z = np.meshgrid(X1, Y1, Z1, indexing="ij")

grid = pv.StructuredGrid()
grid.points = np.c_[X.ravel(order="F"), Y.ravel(order="F"), Z.ravel(order="F")]
grid.dimensions = X.shape
grid["alpha"] = alpha.ravel(order="F")

levels = [0.0, 0.1, -0.1]
contours = grid.contour(isosurfaces=levels)

plotter = pv.Plotter()
plotter.add_mesh(contours, cmap="seismic", opacity=0.3)
plotter.show()

