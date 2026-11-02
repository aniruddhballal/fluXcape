""" Here, we only used diffusion part in SFT. We know that surface magnetic field distribution can be composed of weighted sum of spherical harmonics.
    If you go through my paper, it will be clear that if we include more and more harmonics, small-scale magnetic structures will be captured (increasing 
    resolution). but we can not consider infinite no of harmonics, so we consider max_l = 120 here and constructed the surface field distribution from 
    observation. In my paper, we also mentioned that l_effective = 7-19 will be enough to capture the important contributions (more than 60%). So here we 
    considered another threshold map for max_l = 18.
    
    
    So, we used max_l = 120 map as initial condition to solve SFT with only the diffusion part (without including new flux emergence). As, we update the time loop, 
    because of diffusion term, small-scale structures will diffuse and with time the diffused distribution will contribute to large-scale structures. Here, 
    we considered it in terms of total power. So, total power for max_l = 120 map almost converges to that of max_l = 18 map i.e. the condition is the loop will break 
    if (Power_120(t) - Power_18) <= threshold.

    """



#####################################################################

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, RectBivariateSpline
from astropy.io import fits
from numba import njit, prange
from scipy.special import sph_harm
from joblib import Parallel, delayed
from joblib import parallel_backend

# Defining Spherical harmonics
def Y_lm(l,m,theta,phi):
    return sph_harm(m,l,phi,theta)

max_L= 120
l = np.arange(1,max_L+1,1)

fits_file = fits.open('2013_10_15.fits')
B_curr = fits_file[1].data

phi_original = np.linspace(0, np.deg2rad(360), B_curr.shape[1])
phi_ori_deg = np.rad2deg(phi_original)
theta_original = np.arcsin(np.linspace(-1, 1, B_curr.shape[0]))
theta_ori_deg = np.rad2deg(theta_original)

######################################################################################

delta = 1
D = 6e12
Rs = 7e10
dt = 60         
        
            
def y(theta):
    return -(np.log(np.tan(theta/2))) / np.deg2rad(delta)

def theta(y):
    
    return 2*np.arctan(np.exp(-np.deg2rad(delta)*y))

#----------------Grid Setup for Staggered Grid-----------------

# Define theta boundaries (ignoring the edges to avoid singularity for [1/ sin (theta)])
theta_m = np.deg2rad(3)
theta_mi = np.deg2rad(177)

# Primary grid (for cell centers - Bz location)
phi_deg_c = np.arange(0.5, 360, delta)  # Cell centers in phi
phi_c = np.deg2rad(phi_deg_c)
x_c = phi_c / np.deg2rad(delta)
nx = len(x_c)

y_m = int(np.floor(y(theta_m)))
y_mi = int(np.ceil(y(theta_mi)))
y_c = np.arange((y_mi + 0.5), y_m, delta)
theta_c = theta(y_c)
theta_new_c = np.deg2rad(90) - theta_c
theta_deg_c = np.rad2deg(theta_c)
theta_new_deg_c = np.rad2deg(theta_new_c)
ny = len(y_c)

# Edge grids for Ax (horizontal edges)
phi_deg_x = np.arange(0.5, 360, delta)  # Same as cell centers in x
phi_x = np.deg2rad(phi_deg_x)
x_x = phi_x / np.deg2rad(delta)

y_x = np.arange(y_mi, (y_m + 0.5), delta)  # Edge points in y
theta_x = theta(y_x)
theta_deg_x = np.rad2deg(theta_x)

# Edge grids for Ay (vertical edges)
phi_deg_y = np.arange(0, 360.5, delta)  # Edge points in x
phi_y = np.deg2rad(phi_deg_y)
x_y = phi_y / np.deg2rad(delta)

y_y = y_c  # Same as cell centers in y
theta_y = theta(y_y)
theta_deg_y = np.rad2deg(theta_y)

# Grid spacing
dx = x_c[1] - x_c[0]
dy = y_c[1] - y_c[0]

#----------------Initialize Fields-----------------

Br_interpolated = np.zeros((len(theta_c), B_curr.shape[1]))  # Intermediate matrix

for j in range(B_curr.shape[1]):  # Loop over phi values
    interp_func = interp1d(theta_original, B_curr[:, j], kind='cubic', fill_value="extrapolate")
    Br_interpolated[:, j] = interp_func(theta_new_c)

interp_func_2D = RectBivariateSpline(theta_new_c, phi_original, Br_interpolated, kx=3, ky=3)
resized_Br = interp_func_2D(theta_new_c, phi_c)


#################################################################################

r2 = 7e10
dtheta = -np.gradient(theta_c)    # handles nonuniform theta
dphi   = np.gradient(phi_c)      # handles uniform phi

# Build 2D integration weight matrix
# Each cell's solid angle ≈ sin(theta_i) * dtheta_i * dphi_j (this is like d\Omega = sin(theta) * dtheta * dphi)
W2 = np.outer(np.sin(theta_c) * dtheta, dphi)    # shape (n_theta, n_phi)

# Compute grid-based magnetic power
phi_n1 = np.sum(((r2**2) * resized_Br) * W2)


B_extra1 = phi_n1/ (4 * np.pi * (r2 ** 2))
resized_Br2 = resized_Br - B_extra1
#---------------------------------------------------------------

phi_n2 = np.sum(((r2**2) * resized_Br2) * W2)

B_extra2 = phi_n2/ (4 * np.pi * (r2 ** 2))
resized_Br3 = resized_Br2 - B_extra2
#----------------------------------------------------------

phi_n3 = np.sum(((r2**2) * resized_Br3) * W2)

B_extra3 = phi_n3/ (4 * np.pi * (r2 ** 2))
resized_Br4 = resized_Br3 - B_extra3



#################################################################################
#--------------------------------Decomposition-----------------------------------

""" For decomposition, we need to find out spherical harmonics coefficients through integration.
    Here, theta is in non-uniform grid so we couldn't use simple trapezoidal or simpson; we used
    Gauss-Legendre.
     
    """

from numpy.polynomial.legendre import leggauss
from scipy.interpolate import RegularGridInterpolator

# --- grid sizes ---
N_theta = len(theta_c)
N_phi   = len(phi_c)

# --- Gauss–Legendre grid in mu = cos(theta) ---
mu_GL, w_theta = leggauss(N_theta)
theta_GL = np.arccos(mu_GL)

phi_GL = phi_c
dphi = np.gradient(phi_GL)

Phi_GL, Theta_GL = np.meshgrid(phi_GL, theta_GL)

# --- interpolate Br from SFT grid to GL grid ---
interp_Br = RegularGridInterpolator((theta_c, phi_c), resized_Br4, bounds_error=False, fill_value=0.0)

points = np.stack([Theta_GL.ravel(), Phi_GL.ravel()], axis=-1)

Br_GL = interp_Br(points).reshape(Theta_GL.shape)

# ---------------------------------------------------------------------------

def C_lm(l, m):
    """Correct spherical-harmonic coefficient using Gauss–Legendre quadrature in theta and uniform phi.
    """
    Ylm = np.conj(Y_lm(l, m, Theta_GL, Phi_GL))
    return np.sum(Br_GL * Ylm * w_theta[:, None] * dphi[None, :])

def compute_c_for_i(lval):
    cl = 0.0
    for m in range(-lval, lval + 1):
        cl += abs(C_lm(lval, m))**2
    return cl

# --- power spectrum ---
with parallel_backend('loky'):
    c = Parallel(n_jobs=-1)(delayed(compute_c_for_i)(i) for i in l)

with parallel_backend('loky'):
    c01 = Parallel(n_jobs=-1)(delayed(compute_c_for_i)(i) for i in range(1, 19))

Power_0  = np.sum(c)
Power_01 = np.sum(c01)

#--------------Reconstructing the magnetic field----------------

""" Reconstructing magnetic field by summing over (coefficients * spherical-harmonics) for two 
    cases max_l = 120 and max_l = 18.
    """

Phi,Theta=np.meshgrid(phi_c,theta_c)

def compute_sum1_for_i(i):
    return sum((C_lm(i,j)*Y_lm(i,j,Theta,Phi)) for j in range(-i, i+1))

with parallel_backend('loky'):
    results1 = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i) for i in l)

Br_cons = sum (results1)

with parallel_backend('loky'):
    results01 = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i) for i in range (1,19))

Br_cons01 = sum (results01)

Br_cons = Br_cons.T
Br_cons = Br_cons.real

Br_cons01 = Br_cons01.T
Br_cons01 = Br_cons01.real


print ("cons_decomposed=",Br_cons.shape)

print ("Power_0 =", Power_0)
print ("Power_01 =", Power_01)

##########################################################################################################

print ("----------------------------------------------------")
Bz_0 = Br_cons

# Allocate staggered arrays
Ax = np.zeros((len(x_x), len(y_x)))   # horizontal edges
Ay = np.zeros((len(x_y), len(y_y)))   # vertical edges
Bz = np.zeros((len(x_c), len(y_c)))   # cell centers

# Initialize Ax using integration
for i in range(len(x_c)):
    Ax[i,0] = 0.0
    for j in range(len(y_c)):
        theta_mid = theta_c[j]
        Bz_mid = -Bz_0[i,j] * (np.sin(theta_mid))**2
        Ax[i,j+1] = Ax[i,j] + Bz_mid * (dy * np.deg2rad(delta) * Rs)

# Initialize Ay (starts at zero)
Ay[:, :] = 0.0

# Compute initial Bz from curl of A
for i in range(len(x_c)):
    for j in range(len(y_c)):
        theta_j = theta_c[j]
        sin_theta = np.sin(theta_j)
        
        # Finite differences for curl
        dAy_dx = (Ay[i+1, j] - Ay[i, j]) / (dx * np.deg2rad(delta) * Rs * sin_theta)
        dAx_dy = (Ax[i, j+1] - Ax[i, j]) / (dy * np.deg2rad(delta) * Rs * sin_theta**2)
        
        Bz[i, j] = dAy_dx - dAx_dy


# Store initial Bz for plotting
Bz_initial = Bz.copy()
X_c, Y_c = np.meshgrid(x_c, y_c, indexing='ij')


diff = Bz - Bz_0
print("Max abs error:", np.max(np.abs(diff)))
print ("diff =",diff.shape)

########################################################################################

#----------------Padding for Boundary Conditions-----------------

# Add padding for periodic boundaries
Ax = np.pad(Ax, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Ay = np.pad(Ay, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Bz = np.pad(Bz, ((1, 1), (1, 1)), mode='constant', constant_values=0)

Ax_1 = Ax.copy()
Ay_1 = Ay.copy()
Bz_1 = Bz.copy()

# Adjust theta arrays for padded grids
theta_x_pad = np.pad(theta_x, (1, 1), mode='edge')
theta_y_pad = np.pad(theta_y, (1, 1), mode='edge')
theta_c_pad = np.pad(theta_c, (1, 1), mode='edge')

#----------------Boundary Conditions-----------------

def apply_boundary_conditions(Ax, Ay):
    
    # Periodic in x (longitude)
    Ax[0, :] = Ax[-2, :]
    Ax[-1, :] = Ax[1, :]
    Ay[0, :] = Ay[-2, :]
    Ay[-1, :] = Ay[1, :]

    
    # Closed in y (latitude)
    Ax[:, 0] = Ax[:, 1]
    Ax[:, -1] = Ax[:, -2]
    Ay[:, 0] = Ay[:, 1]
    Ay[:, -1] = Ay[:, -2]
    
    return Ax, Ay

#----------------Update Functions-----------------

@njit(parallel=True)
def compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, dx, dy, delta, Rs):
    
    for i in prange(1, Bz.shape[0]-1):
        for j in prange(1, Bz.shape[1]-1):
            theta_j = theta_c_pad[j]
            sin_theta = np.sin(theta_j)
            
            # Avoid division by very small numbers
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
            
            # Curl of A
            dAy_dx = (Ay[i+1, j] - Ay[i, j]) / (dx * np.deg2rad(delta) * Rs * sin_theta)
            dAx_dy = (Ax[i, j+1] - Ax[i, j]) / (dy * np.deg2rad(delta) * Rs * sin_theta**2)
            
            Bz[i, j] = dAy_dx - dAx_dy
    
    return Bz

@njit(parallel=True)
def update_A_staggered(Ax, Ay, Bz, theta_x_pad, theta_y_pad, 
                      dx, dy, delta, Rs, D, dt):
    
    Ax_new = Ax.copy()
    Ay_new = Ay.copy()
    
    # Update Ax (horizontal edges)
    for i in prange(1, Ax.shape[0]-1):
        for j in prange(1, Ax.shape[1]-1):
            theta_j = theta_x_pad[j]
            sin_theta = np.sin(theta_j)
            
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
            
            
            # Diffusion term (centered difference)
            diffusion = -(D / (np.deg2rad(delta) * Rs * sin_theta)) * \
                           (Bz[i, j] - Bz[i, j-1]) / dy
            
            Ax_new[i, j] = Ax[i, j] + dt * diffusion
    
    # Update Ay (vertical edges)
    for i in prange(1, Ay.shape[0]-1):
        for j in prange(1, Ay.shape[1]-1):
            theta_j = theta_y_pad[j]
            sin_theta = np.sin(theta_j)
            
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
            
            # Diffusion term (centered difference)
            diffusion = (D / (np.deg2rad(delta) * Rs * sin_theta)) * \
                           (Bz[i, j] - Bz[i-1, j]) / dx
            
            Ay_new[i, j] = Ay[i, j] + dt * diffusion
    
    return Ax_new, Ay_new

#----------------Time Integration-----------------

# Apply initial boundary conditions
Ax, Ay = apply_boundary_conditions(Ax, Ay)


def a_lm(l, m, Bz):

""" Computing spherical-harmonic coefficient a_lm 
    using Gauss–Legendre quadrature.
    
    """

    # Interpolator requires (theta, phi) ordering
    interp_Bz = RegularGridInterpolator((theta_c, phi_c), Bz.T, bounds_error=False, fill_value=0.0)

    # Interpolate Bz onto GL nodes
    points = np.stack([Theta_GL.ravel(), Phi_GL.ravel()], axis=-1)

    Bz_GL = interp_Bz(points).reshape(Theta_GL.shape)

    # Spherical harmonic
    Ylm = np.conj(Y_lm(l, m, Theta_GL, Phi_GL))

    # Correct surface integral
    return np.sum(Bz_GL * Ylm * w_theta[:, None] * dphi[None, :])


# ---------- Power in each l ----------

def compute_a_for_i(i, Bz):
    a_l = 0.0
    for j in range(-i, i + 1):
        a_l += np.abs(a_lm(i, j, Bz))**2
    return a_l

def compute_sum1_for_i(i, Bz):
    return sum((a_lm(i, j, Bz)*Y_lm(i,j,Theta,Phi)) for j in range(-i, i+1))

# ---------- Time evolution diagnostics ----------

t = 0.0
dt = 60.0
check_interval = 86400.0     # once per day
f = 0.01

time_since_last_check = 0.0
P = [Power_0]


while True:

    # --- Compute Bz from A ---
    Bz = compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, dx, dy, delta, Rs)

    # --- Boundary conditions on Bz ---
    Bz[0, :]  = Bz[-2, :]
    Bz[-1, :] = Bz[1, :]
    Bz[:, 0]  = Bz[:, 1]
    Bz[:, -1] = Bz[:, -2]

    # --- Update A ---
    Ax, Ay = update_A_staggered(Ax, Ay, Bz, theta_x_pad, theta_y_pad, dx, dy, delta, Rs, D, dt)

    Ax, Ay = apply_boundary_conditions(Ax, Ay)

    t += dt
    time_since_last_check += dt

    # Interior field only
    Bz_f = Bz[1:-1, 1:-1]

    # --- Diagnostics ---
    if time_since_last_check >= check_interval:

        with parallel_backend('loky'):
            a = Parallel(n_jobs=-1)(delayed(compute_a_for_i)(i, Bz_f) for i in l)

        Power_t = np.sum(a)

        with parallel_backend('loky'):
            a18 = Parallel(n_jobs=-1)(delayed(compute_a_for_i)(i, Bz_f) for i in range(1, 19))

        Power_t18 = np.sum(a18)

        print ("Power_120 =", Power_t, "Power_18 =", Power_t18, "Power_extra =", (Power_t - Power_t18))

        P.append(Power_t)
        time_since_last_check = 0.0

        # Convergence condition
        if (Power_t - Power_01) <= f:
            break
print ("Power = ", P)

if abs(P[-1] - Power_01)< abs(P[-2] - Power_01):
    t1 = t/(24 * 3600)
else:
    t1 = (t/(24 * 3600)) - 1
    
print ()
print (t1)    
print ()

t2 = np.arange(0, (2 * t1 * 24 * 3600), dt)

# Apply initial boundary conditions
Ax_1, Ay_1 = apply_boundary_conditions(Ax_1, Ay_1)

for ti in range(1, len(t2)):

    # Compute B from current A
    Bz_1 = compute_B_from_A_staggered(Ax_1, Ay_1, Bz_1, theta_c_pad, dx, dy, delta, Rs)
    
    # Apply boundary conditions to B
    Bz_1[0, :] = Bz_1[-2, :]
    Bz_1[-1, :] = Bz_1[1, :]
    Bz_1[:, 0] = Bz_1[:, 1]
    Bz_1[:, -1] = Bz_1[:, -2]
    
    # Update A fields
    Ax_1, Ay_1 = update_A_staggered(Ax_1, Ay_1, Bz_1, 
                               theta_x_pad, theta_y_pad, 
                               dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax_1, Ay_1 = apply_boundary_conditions(Ax_1, Ay_1)

# Final computation of Bz
Bz_1 = compute_B_from_A_staggered(Ax_1, Ay_1, Bz_1, theta_c_pad, dx, dy, delta, Rs)

# Remove padding for final results
Bz_final_1 = Bz_1[1:-1, 1:-1]


with parallel_backend('loky'):
    results_final = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i, Bz_final_1) for i in range (1,19))

Bz_f01 = sum (results_final)
Bz_f01 = Bz_f01.T
Bz_f01 = Bz_f01.real

Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

fig, axes = plt.subplots(1, 3, figsize=(20, 4))

# --- Bz_f plot ---
c1 = axes[0].contourf(Phi_deg_c, Theta_deg_c, Bz_final_1,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_final_1)), vmax=np.max(np.abs(Bz_final_1)))
fig.colorbar(c1, ax=axes[0], label="Magnetic field strength (Bz)")
axes[0].set_title("Bz_120_final")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].invert_yaxis()
axes[0].set_yticks([160,140,120,100,80,60,40,20])
axes[0].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])
        
# --- Bz_f01 plot ---
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_f01,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_f01)), vmax=np.max(np.abs(Bz_f01)))
fig.colorbar(c2, ax=axes[1], label="Magnetic field strength (Br)")
axes[1].set_title("Bz_18_final")
axes[1].set_xlabel("Longitude")
axes[1].set_ylabel("Latitude")
axes[1].invert_yaxis()
axes[1].set_yticks([160,140,120,100,80,60,40,20])
axes[1].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])

# --- Br_cons01 plot ---
c3 = axes[2].contourf(Phi_deg_c, Theta_deg_c, Br_cons01,levels=100, cmap="seismic",vmin=-np.max(np.abs(Br_cons01)), vmax=np.max(np.abs(Br_cons01)))
fig.colorbar(c3, ax=axes[2], label="Magnetic field strength (Br)")
axes[2].set_title("Br_cons_18_t=0")
axes[2].set_xlabel("Longitude")
axes[2].set_ylabel("Latitude")
axes[2].invert_yaxis()
axes[2].set_yticks([160,140,120,100,80,60,40,20])
axes[2].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])

plt.tight_layout()
plt.savefig("result_p/power.png", dpi=300)


fig, axes = plt.subplots(1, 3, figsize=(20, 4))

# --- Bz_f plot ---
c1 = axes[0].contourf(Phi_deg_c, Theta_deg_c, Bz_final_1,levels=100, cmap="seismic",vmin=np.min(Bz_final_1), vmax=np.max(Bz_final_1))
fig.colorbar(c1, ax=axes[0], label="Magnetic field strength (Bz)")
axes[0].set_title("Bz_120_final")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].invert_yaxis()
axes[0].set_yticks([160,140,120,100,80,60,40,20])
axes[0].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])
        
# --- Bz_f01 plot ---
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_f01,levels=100, cmap="seismic",vmin=np.min(Bz_f01), vmax=np.max(Bz_f01))
fig.colorbar(c2, ax=axes[1], label="Magnetic field strength (Br)")
axes[1].set_title("Bz_18_final")
axes[1].set_xlabel("Longitude")
axes[1].set_ylabel("Latitude")
axes[1].invert_yaxis()
axes[1].set_yticks([160,140,120,100,80,60,40,20])
axes[1].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])

# --- Br_cons01 plot ---
c3 = axes[2].contourf(Phi_deg_c, Theta_deg_c, Br_cons01,levels=100, cmap="seismic",vmin=np.min(Br_cons01), vmax=np.max(Br_cons01))
fig.colorbar(c3, ax=axes[2], label="Magnetic field strength (Br)")
axes[2].set_title("Br_cons_18_t=0")
axes[2].set_xlabel("Longitude")
axes[2].set_ylabel("Latitude")
axes[2].invert_yaxis()
axes[2].set_yticks([160,140,120,100,80,60,40,20])
axes[2].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])

plt.tight_layout()
plt.savefig("result_p/power_min_max.png", dpi=300)


			
