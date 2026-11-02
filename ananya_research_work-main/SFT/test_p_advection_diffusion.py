""" Here, we used both diffusion and advection parts in SFT. We know that surface magnetic field distribution can be composed of 
       weighted sum of spherical harmonics. If you go through my paper, it will be clear that if we include more and more harmonics, small-scale magnetic 
       structures will be captured (increasing resolution). But we can not consider infinite no of harmonics, so we consider max_l = 120 here and 
       constructed the surface field distribution from observation. In my paper, we also mentioned that l_effective = 7-19 will be enough to capture the 
       important contributions (more than 60%). So here we considered another threshold map for max_l = 18. 
    
    
       So, we used max_l = 120 map as initial condition to solve SFT with both the parts (without including new flux emergence) and max_l = 18 map as initial 
       condition to solve SFT with only the advection part (without including new flux emergence). As, we update the time loop, we again try to find out when 
       total power for max_l = 120 map almost converges to that of max_l = 18 map i.e. the condition is the loop will break 
       if (Power_120(t) - Power_18(t)) <= threshold.
   
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

#-----------------Differential rotation and Meridional circulation---------------------

def omega(theta):
    omega_deg_day = 0.18 - 2.3 * ((np.cos(theta)) ** 2) - 1.62 * ((np.cos(theta)) ** 4)
    omega_rad_sec = omega_deg_day * (np.pi/180) * (1/(24 * 3600))
    return omega_rad_sec

def u(theta):
    theta_min = np.deg2rad(3)
    theta_max = np.deg2rad(177)
    arg = np.pi * (theta_max + theta_min - 2*theta) / (2 * (theta_max - theta_min))
    shape = np.cos(arg) * np.cos(theta)
    max_val = np.max(np.abs(shape))
    C = -1600 / max_val
    return C * shape

#--------------------------------------------------------------------------------------

# Defining Spherical harmonics
def Y_lm(l,m,theta,phi):
    return sph_harm(m,l,phi,theta)

max_L= 120
l = np.arange(1,max_L+1,1)

max_L1 = 18

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

phi_n2 = np.sum(((r2**2) * resized_Br2) * W2)

B_extra2 = phi_n2/ (4 * np.pi * (r2 ** 2))
resized_Br3 = resized_Br2 - B_extra2

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

# ----power spectrum----
with parallel_backend('loky'):
    c = Parallel(n_jobs=-1)(
        delayed(compute_c_for_i)(i) for i in l)

with parallel_backend('loky'):
    c01 = Parallel(n_jobs=-1)(
        delayed(compute_c_for_i)(i) for i in range(1, 19))

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

with parallel_backend('loky'):
    results01 = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i) for i in range (1, max_L1+1))

Br_cons1 = sum (results1)
Br_cons01 = sum (results01)

Br_cons1 = Br_cons1.T
Br_cons1 = Br_cons1.real

Br_cons01 = Br_cons01.T
Br_cons01 = Br_cons01.real


print ("cons_decomposed=",Br_cons1.shape)
print ("cons_decomposed=",Br_cons01.shape)

print ("Power_0 =", Power_0)
print ("Power_01 =", Power_01)

#########################################################################################


print ("----------------------------------------------------")
Bz_0 = Br_cons1

# Allocate staggered arrays
Ax1 = np.zeros((len(x_x), len(y_x)))   # horizontal edges
Ay1 = np.zeros((len(x_y), len(y_y)))   # vertical edges
Bz1 = np.zeros((len(x_c), len(y_c)))   # cell centers

# Initialize Ax using integration
for i in range(len(x_c)):
    Ax1[i,0] = 0.0
    for j in range(len(y_c)):
        theta_mid = theta_c[j]
        Bz_mid1 = -Bz_0[i,j] * (np.sin(theta_mid))**2
        Ax1[i,j+1] = Ax1[i,j] + Bz_mid1 * (dy * np.deg2rad(delta) * Rs)

# Initialize Ay (starts at zero)
Ay1[:, :] = 0.0

# Compute initial Bz from curl of A
for i in range(len(x_c)):
    for j in range(len(y_c)):
        theta_j = theta_c[j]
        sin_theta = np.sin(theta_j)
        
        # Finite differences for curl
        dAy_dx1 = (Ay1[i+1, j] - Ay1[i, j]) / (dx * np.deg2rad(delta) * Rs * sin_theta)
        dAx_dy1 = (Ax1[i, j+1] - Ax1[i, j]) / (dy * np.deg2rad(delta) * Rs * sin_theta**2)
        
        Bz1[i, j] = dAy_dx1 - dAx_dy1


# Store initial Bz for plotting
Bz_initial1 = Bz1.copy()
X_c, Y_c = np.meshgrid(x_c, y_c, indexing='ij')


diff1 = Bz1 - Bz_0
print("Max abs error:", np.max(np.abs(diff1)))
print ("diff1 =",diff1.shape)

########################################################################################

Bz_01 = Br_cons01

# Allocate staggered arrays
Ax01 = np.zeros((len(x_x), len(y_x)))   # horizontal edges
Ay01 = np.zeros((len(x_y), len(y_y)))   # vertical edges
Bz01 = np.zeros((len(x_c), len(y_c)))   # cell centers

# Initialize Ax using integration
for i in range(len(x_c)):
    Ax01[i,0] = 0.0
    for j in range(len(y_c)):
        theta_mid = theta_c[j]
        Bz_mid01 = -Bz_01[i,j] * (np.sin(theta_mid))**2
        Ax01[i,j+1] = Ax01[i,j] + Bz_mid01 * (dy * np.deg2rad(delta) * Rs)

# Initialize Ay (starts at zero)
Ay01[:, :] = 0.0

# Compute initial Bz from curl of A
for i in range(len(x_c)):
    for j in range(len(y_c)):
        theta_j = theta_c[j]
        sin_theta = np.sin(theta_j)
        
        # Finite differences for curl
        dAy_dx01 = (Ay01[i+1, j] - Ay01[i, j]) / (dx * np.deg2rad(delta) * Rs * sin_theta)
        dAx_dy01 = (Ax01[i, j+1] - Ax01[i, j]) / (dy * np.deg2rad(delta) * Rs * sin_theta**2)
        
        Bz01[i, j] = dAy_dx01 - dAx_dy01


# Store initial Bz for plotting
Bz_initial01 = Bz01.copy()
X_c, Y_c = np.meshgrid(x_c, y_c, indexing='ij')


diff01 = Bz01 - Bz_01
print("Max abs error:", np.max(np.abs(diff01)))
print ("diff01 =",diff01.shape)




########################################################################################

#----------------Velocities on Staggered Grid-----------------

# Velocities at Ax locations (horizontal edges)
u_theta_x = u(theta_x)
u_phi_x = omega(theta_x) * Rs * np.sin(theta_x)

# Velocities at Ay locations (vertical edges)
u_theta_y = u(theta_y)
u_phi_y = omega(theta_y) * Rs * np.sin(theta_y)


#----------------Padding for Boundary Conditions-----------------

# Add padding for periodic boundaries
Ax1 = np.pad(Ax1, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Ay1 = np.pad(Ay1, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Bz1 = np.pad(Bz1, ((1, 1), (1, 1)), mode='constant', constant_values=0)

Ax_11 = Ax1.copy()
Ay_11 = Ay1.copy()
Bz_11 = Bz1.copy()

Ax01 = np.pad(Ax01, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Ay01 = np.pad(Ay01, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Bz01 = np.pad(Bz01, ((1, 1), (1, 1)), mode='constant', constant_values=0)

Ax_011 = Ax01.copy()
Ay_011 = Ay01.copy()
Bz_011 = Bz01.copy()

# Adjust theta arrays for padded grids
theta_x_pad = np.pad(theta_x, (1, 1), mode='edge')
theta_y_pad = np.pad(theta_y, (1, 1), mode='edge')
theta_c_pad = np.pad(theta_c, (1, 1), mode='edge')

# Adjust velocity arrays for padded grids
u_theta_x = np.pad(u_theta_x, (1, 1), mode='edge')
u_phi_y = np.pad(u_phi_y, (1, 1), mode='edge')

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


def apply_boundary_conditions_Bz(Bz):
    
    Bz[0, :] = Bz[-2, :]
    Bz[-1, :] = Bz[1, :]
    Bz[:, 0] = Bz[:, 1]
    Bz[:, -1] = Bz[:, -2]

    return Bz

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
def update_A_staggered(Ax, Ay, Bz, u_theta_x, u_phi_y, theta_x_pad, theta_y_pad, 
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
            
            # Interpolate Bz to Ax location (average of adjacent cells)
            if j > 0 and j <= Bz.shape[1] - 1:
                Bz_at_edge = 0.5 * (Bz[i, j-1] + Bz[i, j])
            elif j == 0:
                # At lower boundary
                Bz_at_edge = Bz[i, 0]
            else:
                # At upper boundary  
                Bz_at_edge = Bz[i, -1]
            
            # Advection term
            advection = -u_theta_x[j] * Bz_at_edge
            
            # Diffusion term (centered difference)
            diffusion = -(D / (np.deg2rad(delta) * Rs * sin_theta)) * \
                           (Bz[i, j] - Bz[i, j-1]) / dy
            
            Ax_new[i, j] = Ax[i, j] + dt * (diffusion + advection)
    
    # Update Ay (vertical edges)
    for i in prange(1, Ay.shape[0]-1):
        for j in prange(1, Ay.shape[1]-1):
            theta_j = theta_y_pad[j]
            sin_theta = np.sin(theta_j)
            
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
            
            if i > 0 and i <= Bz.shape[0]:
                Bz_at_edge = 0.5 * (Bz[i-1, j] + Bz[i, j])
            elif i == 0:
                # At left boundary
                Bz_at_edge = Bz[0, j]
            else:
                # At right boundary
                Bz_at_edge = Bz[-1, j]
            
            # Advection term
            advection = -u_phi_y[j] * Bz_at_edge
            
            # Diffusion term (centered difference)
            diffusion = (D / (np.deg2rad(delta) * Rs * sin_theta)) * \
                           (Bz[i, j] - Bz[i-1, j]) / dx
            
            Ay_new[i, j] = Ay[i, j] + dt * (diffusion + advection)
    
    return Ax_new, Ay_new

@njit(parallel=True)
def update_A_staggered1(Ax, Ay, Bz, u_theta_x, u_phi_y, theta_x_pad, theta_y_pad, 
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
            
            if j > 0 and j <= Bz.shape[1] - 1:
                Bz_at_edge = 0.5 * (Bz[i, j-1] + Bz[i, j])
            elif j == 0:
                # At lower boundary
                Bz_at_edge = Bz[i, 0]
            else:
                # At upper boundary  
                Bz_at_edge = Bz[i, -1]
            
            # Advection term
            advection = -u_theta_x[j] * Bz_at_edge
            
            Ax_new[i, j] = Ax[i, j] + dt * advection
    
    # Update Ay (vertical edges)
    for i in prange(1, Ay.shape[0]-1):
        for j in prange(1, Ay.shape[1]-1):
            theta_j = theta_y_pad[j]
            sin_theta = np.sin(theta_j)
            
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
            
            if i > 0 and i <= Bz.shape[0]:
                Bz_at_edge = 0.5 * (Bz[i-1, j] + Bz[i, j])
            elif i == 0:
                # At left boundary
                Bz_at_edge = Bz[0, j]
            else:
                # At right boundary
                Bz_at_edge = Bz[-1, j]
            
            # Advection term
            advection = -u_phi_y[j] * Bz_at_edge
            
            Ay_new[i, j] = Ay[i, j] + dt * advection
    
    return Ax_new, Ay_new

#----------------Time Integration-----------------

# Apply initial boundary conditions
Ax1, Ay1 = apply_boundary_conditions(Ax1, Ay1)
Ax01, Ay01 = apply_boundary_conditions(Ax01, Ay01)


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
 

t = 0.0
dt = 60
check_interval = 86400.0   # check once per day (s)
f = 0.01

time_since_last_check = 0.0
Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

P = [Power_0]

while True:
    # Compute B from current A
    Bz1 = compute_B_from_A_staggered(Ax1, Ay1, Bz1, theta_c_pad, dx, dy, delta, Rs)
    Bz01 = compute_B_from_A_staggered(Ax01, Ay01, Bz01, theta_c_pad, dx, dy, delta, Rs)
    
    # Apply boundary conditions to B
    Bz1 = apply_boundary_conditions_Bz(Bz1)
    Bz01 = apply_boundary_conditions_Bz(Bz01)
    
    # Update A fields
    Ax1, Ay1 = update_A_staggered(Ax1, Ay1, Bz1, u_theta_x, u_phi_y, 
                                theta_x_pad, theta_y_pad, 
                                dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax1, Ay1 = apply_boundary_conditions(Ax1, Ay1)

    Ax01, Ay01 = update_A_staggered1(Ax01, Ay01, Bz01, u_theta_x, u_phi_y, 
                                theta_x_pad, theta_y_pad, 
                                dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax01, Ay01 = apply_boundary_conditions(Ax01, Ay01)
    
    t += dt
    time_since_last_check += dt
    
    Bz_f1 = Bz1[1:-1, 1:-1]
    Bz_f01 = Bz01[1:-1, 1:-1]
    
    # Periodically compute power
    if time_since_last_check >= check_interval:
        with parallel_backend('loky'):
            a1 = Parallel(n_jobs=-1)(delayed(compute_a_for_i)(i, Bz_f1) for i in l)

        with parallel_backend('loky'):
            a01 = Parallel(n_jobs=-1)(delayed(compute_a_for_i)(i, Bz_f01) for i in range(1, max_L1+1))

        Power_t1 = sum(a1)
        Power_t01 = sum(a01)

        print("Power_120 =", Power_t1, "Power_18 =", Power_t01)
        
        P.append(Power_t1)

        # Reset timer
        time_since_last_check = 0.0

        # Check convergence condition
        if (Power_t1-Power_t01) <= f:
            break

#############################################################################################

print("Power = ", P)
print ()			
print ("Days =", t/(24 * 3600))

t1 = t/(24 * 3600)

t2 = np.arange(0, (2 * t1 * 24 * 3600), dt)

# Apply initial boundary conditions
Ax_11, Ay_11 = apply_boundary_conditions(Ax_11, Ay_11)
Ax_011, Ay_011 = apply_boundary_conditions(Ax_011, Ay_011)

for ti in range(1, len(t2)):

    Bz_11 = compute_B_from_A_staggered(Ax_11, Ay_11, Bz_11, theta_c_pad, dx, dy, delta, Rs)
    Bz_011 = compute_B_from_A_staggered(Ax_011, Ay_011, Bz_011, theta_c_pad, dx, dy, delta, Rs)
    
    # Apply boundary conditions to B
    Bz_11 = apply_boundary_conditions_Bz(Bz_11)
    Bz_011 = apply_boundary_conditions_Bz(Bz_011)
    
    # Update A fields
    Ax_11, Ay_11 = update_A_staggered(Ax_11, Ay_11, Bz_11, u_theta_x, u_phi_y, 
                                theta_x_pad, theta_y_pad, 
                                dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax_11, Ay_11 = apply_boundary_conditions(Ax_11, Ay_11)

    Ax_011, Ay_011 = update_A_staggered1(Ax_011, Ay_011, Bz_011, u_theta_x, u_phi_y, 
                                theta_x_pad, theta_y_pad, 
                                dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax_011, Ay_011 = apply_boundary_conditions(Ax_011, Ay_011)

# Final computation of Bz
Bz_11 = compute_B_from_A_staggered(Ax_11, Ay_11, Bz_11, theta_c_pad, dx, dy, delta, Rs)

# Remove padding for final results
Bz_final_11 = Bz_11[1:-1, 1:-1]

Bz_011 = compute_B_from_A_staggered(Ax_011, Ay_011, Bz_011, theta_c_pad, dx, dy, delta, Rs)

# Remove padding for final results
Bz_final_011 = Bz_011[1:-1, 1:-1]
#############################################################################################

Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

fig, axes = plt.subplots(1, 3, figsize=(20, 4))

# --- Bz_f plot ---
c1 = axes[0].contourf(Phi_deg_c, Theta_deg_c, Bz_final_11,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_final_11)), vmax=np.max(np.abs(Bz_final_11)))
fig.colorbar(c1, ax=axes[0], label="Magnetic field strength (Bz)")
axes[0].set_title("Bz_120_final")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].invert_yaxis()
axes[0].set_yticks([160,140,120,100,80,60,40,20])
axes[0].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])
        
# --- Bz_f01 plot ---
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_final_011, levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_final_011)), vmax=np.max(np.abs(Bz_final_011)))
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
plt.savefig("result_p/power_advec.png", dpi=300)


