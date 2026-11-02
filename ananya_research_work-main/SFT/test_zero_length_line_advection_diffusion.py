""" Here, we used both diffusion and advection parts in SFT. We know that surface magnetic field distribution can be composed of 
       weighted sum of spherical harmonics. If you go through my paper, it will be clear that if we include more and more harmonics, small-scale magnetic 
       structures will be captured (increasing resolution). But we can not consider infinite no of harmonics, so we consider max_l = 120 here and 
       constructed the surface field distribution from observation. In my paper, we also mentioned that l_effective = 7-19 will be enough to capture the 
       important contributions (more than 60%). So here we considered another threshold map for max_l = 18. 
    
    
       So, we used max_l = 120 map as initial condition to solve SFT with both the parts (without including new flux emergence) and max_l = 18 map as initial 
       condition to solve SFT with only the advection part (without including new flux emergence). As, we update the time loop, we again try to find out when 
       'length of polarity line inversion' for max_l = 120 map almost converges to that of max_l = 18 map i.e. the condition is the loop will break 
       if (PIL_120(t) - PIL_18(t)) <= threshold.
   
       We used two different methods for finding out this polarity inversion line length, (a) using python package (skimage), (b) basic python. Final results 
       (i.e. time) are almost similar for both the cases.

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
from skimage.measure import find_contours

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
#---------------------------------------------------------

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


print ("cons1_decomposed =",Br_cons1.shape)
print ("cons01_decomposed =",Br_cons01.shape)


########################################################################################

# Method (a)

##** Basic_Python **##

print ("------------Basic Python--------------")

""" Here, we first considered a matrix 'S' consisting only 1, -1 and 0 (if 0 explicitly is present in the the field distribution).
    Then, if we get the |difference| between two grid valus as '2', we have a polarity crossing there. And, we consider a rough 
    point at the middle to have that neutral value. Thus we got the coordinates and finally we found out the total length.
     
    """

def pil_length_from_sign_changes(B):
   
    S = np.zeros_like(B, dtype=int)
    S[B > 0] = 1
    S[B < 0] = -1

    Ny, Nx = S.shape

   
    # diff_x[i,j] = S[i,j+1] - S[i,j]
    diff_x = S[:, 1:] - S[:, :-1]
    pil_x = np.abs(diff_x) == 2   # True where crossing occurs

    # Pixel locations for horizontal crossings
    # These lie BETWEEN (j) and (j+1) → at x = j + 0.5
    x_cross_x = (np.where(pil_x)[1] + 0.5)
    y_cross_x = (np.where(pil_x)[0])

    # diff_y[i,j] = S[i+1,j] - S[i,j]
    diff_y = S[1:, :] - S[:-1, :]
    pil_y = np.abs(diff_y) == 2   # True where crossing occurs

    # Pixel locations for vertical crossings
    # These lie BETWEEN (i) and (i+1) → at y = i + 0.5
    x_cross_y = (np.where(pil_y)[1])
    y_cross_y = (np.where(pil_y)[0] + 0.5)

    x_all = np.concatenate([x_cross_x, x_cross_y])
    y_all = np.concatenate([y_cross_x, y_cross_y])

    points = np.vstack([x_all, y_all]).T

    if len(points) < 2:
        return 0.0

    # Sort points for roughly consistent ordering
    # (not perfect contour ordering but OK for PIL pixels)
    idx = np.argsort(points[:, 0])
    pts = points[idx]

    dx = np.diff(pts[:, 0])
    dy = np.diff(pts[:, 1])
    length = np.sum(np.sqrt(dx*dx + dy*dy))

    return length

PIL_120_1 = pil_length_from_sign_changes(Br_cons1)
PIL_18_1 = pil_length_from_sign_changes(Br_cons01)

print ("PIL_120 = ", PIL_120_1, "PIL_18 = ", PIL_18_1)


########################################################################################

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

Ax01 = np.pad(Ax01, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Ay01 = np.pad(Ay01, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Bz01 = np.pad(Bz01, ((1, 1), (1, 1)), mode='constant', constant_values=0)

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
 

t = 0.0
dt = 60
check_interval = 86400.0   # check once per day (s)
f = 0.01

time_since_last_check = 0.0
Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

l1 = [PIL_120_1]

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
        
        PIL_t_1 = pil_length_from_sign_changes(Bz_f1)
        
        PIL_t_01 = pil_length_from_sign_changes(Bz_f01)
        
        print("PIL_120 =", PIL_t_1, "PIL_18 =", PIL_t_01)
        
        l1.append(PIL_t_1)

        # Reset timer
        time_since_last_check = 0.0

        # Check convergence condition
        if (PIL_t_1 - PIL_t_01) <= f:
            break

#############################################################################################

			
print ("Final_time =", t/(24 * 3600))


#############################################################################################

fig, axes = plt.subplots(1, 3, figsize=(20, 4))

# --- Bz_f plot ---
c1 = axes[0].contourf(Phi_deg_c, Theta_deg_c, Bz_f1,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_f1)), vmax=np.max(np.abs(Bz_f1)))
fig.colorbar(c1, ax=axes[0], label="Magnetic field strength (Bz)")
axes[0].set_title("Bz_120_final_time")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].invert_yaxis()
axes[0].set_yticks([160,140,120,100,80,60,40,20])
axes[0].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])
        
# --- Bz_f01 plot ---
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_f01,levels=100, cmap="seismic",vmin=-np.max(np.abs(Br_cons01)), vmax=np.max(np.abs(Br_cons01)))
fig.colorbar(c2, ax=axes[1], label="Magnetic field strength (Br)")
axes[1].set_title("Bz_18_final_time")
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
plt.savefig("basic_python/diff_advec.png", dpi=300)

lss1 = []
for i in range(len(l1)):
    lss1.append(l1[i]/l1[0])

x1 = np.arange(0, len(l1), 1)

plt.figure(figsize=(8,5))
plt.plot(x1, l1, marker='o', markersize=3, linestyle='-')
plt.grid()
plt.xlabel("No of days")
plt.ylabel("Polarity inversion line length")
plt.title("Variation of length for PIL with time")
plt.savefig("basic_python/advec_total_change.png", dpi=300)

plt.figure(figsize=(8,5))
plt.plot(x1[:], lss1, marker='o', markersize=3, linestyle='-')
plt.grid()
plt.xlabel("No of days")
plt.ylabel("Polarity inversion line length ($l_{i}/l_{0}$)")
plt.title("Variation of length for PIL with time")
plt.savefig("basic_python/advec_fraction_change.png", dpi=300)


#--------------------------------outputs------------------------------------

# PIL_120 =  2403601.8153432244 PIL_18 =  323456.791834651
# ----------------------------------------------------
# Max abs error: 3.3011371414204405e-12
# diff1 = (360, 174)
# Max abs error: 9.023892744153272e-13
# diff01 = (360, 174)
# PIL_120 = 1851518.4792237058 PIL_18 = 324707.89889994846
# PIL_120 = 1460803.9282857897 PIL_18 = 314425.3979781993
# PIL_120 = 1244943.4106663843 PIL_18 = 323564.58639213064
# PIL_120 = 1030645.5479895757 PIL_18 = 329170.2097892829
# PIL_120 = 920251.8537993787 PIL_18 = 331640.42968018434
# PIL_120 = 809901.3636936476 PIL_18 = 331288.5665642723
# PIL_120 = 721641.8130205622 PIL_18 = 330696.8560981855
# PIL_120 = 665492.3408186202 PIL_18 = 342598.2620017013
# PIL_120 = 593080.8972687095 PIL_18 = 352184.1492298704
# PIL_120 = 532851.3196454921 PIL_18 = 354911.9124638397
# PIL_120 = 508340.64331064187 PIL_18 = 363223.67533366487
# PIL_120 = 466942.0401636539 PIL_18 = 369246.4031266164
# PIL_120 = 460339.77107933915 PIL_18 = 375749.0748783522
# PIL_120 = 444029.65284749767 PIL_18 = 383216.97114267264
# PIL_120 = 417927.7136684984 PIL_18 = 378734.51788165024
# PIL_120 = 400756.5111114833 PIL_18 = 395352.1648758368
# PIL_120 = 385175.5193468657 PIL_18 = 386391.13429191074
# Final_time = 17.0

##############################################################################################
##############################################################################################
##############################################################################################
##############################################################################################

# Method (b)

##** skimage **##
print ("---------------skimage----------------")

""" it finds the level zero contours and their corresponding coordinates, which finally leads us to 
    the length. 
    """

def pil_length_pixels(B):
    
    contours = find_contours(B, level=0)
    total_length = 0.0
    Ny, Nx = B.shape

    for cont in contours:
        rows = cont[:, 0]   # fractional row indices (y, pixels)
        cols = cont[:, 1]   # fractional col indices (x, pixels)

        dx = np.diff(cols)  # difference in pixel units
        dy = np.diff(rows)
        total_length += np.sum(np.sqrt(dx*dx + dy*dy))

    return total_length

PIL_120 = pil_length_pixels(Br_cons1)
PIL_18 = pil_length_pixels(Br_cons01)

print ("PIL_120 = ", PIL_120, "PIL_18 = ", PIL_18)



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

Ax01 = np.pad(Ax01, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Ay01 = np.pad(Ay01, ((1, 1), (1, 1)), mode='constant', constant_values=0)
Bz01 = np.pad(Bz01, ((1, 1), (1, 1)), mode='constant', constant_values=0)

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

    
    # Reflecting/no-flux at y boundaries (latitude)
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
 

t = 0.0
dt = 60
check_interval = 86400.0   # check once per day (s)
f = 0.01

time_since_last_check = 0.0
Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

l2 = [PIL_120]

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
        
        PIL_t_1 = pil_length_pixels(Bz_f1)
        
        PIL_t_01 = pil_length_pixels(Bz_f01)
        
        print("PIL_120 =", PIL_t_1, "PIL_18 =", PIL_t_01)
        
        l2.append(PIL_t_1)

        # Reset timer
        time_since_last_check = 0.0

        # Check convergence condition
        if (PIL_t_1 - PIL_t_01) <= f:
            break

#############################################################################################

			
print ("Final_time =", t/(24 * 3600))


#############################################################################################

fig, axes = plt.subplots(1, 3, figsize=(20, 4))

# --- Bz_f plot ---
c1 = axes[0].contourf(Phi_deg_c, Theta_deg_c, Bz_f1,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_f1)), vmax=np.max(np.abs(Bz_f1)))
fig.colorbar(c1, ax=axes[0], label="Magnetic field strength (Bz)")
axes[0].set_title("Bz_120_final_time")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].invert_yaxis()
axes[0].set_yticks([160,140,120,100,80,60,40,20])
axes[0].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])
        
# --- Bz_f01 plot ---
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_f01,levels=100, cmap="seismic",vmin=-np.max(np.abs(Br_cons01)), vmax=np.max(np.abs(Br_cons01)))
fig.colorbar(c2, ax=axes[1], label="Magnetic field strength (Br)")
axes[1].set_title("Bz_18_final_time")
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
plt.savefig("skimage/diff_advec.png", dpi=300)

lss2 = []
for i in range(len(l2)):
    lss2.append(l2[i]/l2[0])

x2 = np.arange(0, len(l2), 1)

plt.figure(figsize=(8,5))
plt.plot(x2, l2, marker='o', markersize=3, linestyle='-')
plt.grid()
plt.xlabel("No of days")
plt.ylabel("Polarity inversion line length")
plt.title("Variation of length for PIL with time")
plt.savefig("skimage/advec_total_change.png", dpi=300)

plt.figure(figsize=(8,5))
plt.plot(x2[:], lss2, marker='o', markersize=3, linestyle='-')
plt.grid()
plt.xlabel("No of days")
plt.ylabel("Polarity inversion line length ($l_{i}/l_{0}$)")
plt.title("Variation of length for PIL with time")
plt.savefig("skimage/advec_fraction_change.png", dpi=300)

#--------------------------- output ---------------------------

# PIL_120 =  17627.282129802497 PIL_18 =  2544.5371677187572
#----------------------------------------------------
# Max abs error: 3.3011371414204405e-12
# diff1 = (360, 174)
# Max abs error: 9.023892744153272e-13
# diff01 = (360, 174)
# PIL_120 = 13215.04941457923 PIL_18 = 2555.091623524919
# PIL_120 = 10610.539165002801 PIL_18 = 2566.6603844180595
# PIL_120 = 8956.268628448968 PIL_18 = 2580.942422669235
# PIL_120 = 7630.758143869582 PIL_18 = 2598.983076043485
# PIL_120 = 6728.346529319187 PIL_18 = 2622.4298766638913
# PIL_120 = 5984.101803885662 PIL_18 = 2645.789926189287
# PIL_120 = 5461.5791965408835 PIL_18 = 2671.5602992033587
# PIL_120 = 4972.750708648096 PIL_18 = 2700.0012104941325
# PIL_120 = 4516.793325269742 PIL_18 = 2730.690427707152
# PIL_120 = 4168.2196770584405 PIL_18 = 2763.6258918094827
# PIL_120 = 3932.4879252060327 PIL_18 = 2798.5935126598824
# PIL_120 = 3712.7958723908137 PIL_18 = 2835.8715799170536
# PIL_120 = 3545.7537670351608 PIL_18 = 2874.7226584975824
# PIL_120 = 3407.0905262198676 PIL_18 = 2913.149896930763
# PIL_120 = 3278.784180304515 PIL_18 = 2956.984190748539
# PIL_120 = 3163.514622229039 PIL_18 = 2999.417097237659
# PIL_120 = 3080.7557457008807 PIL_18 = 3049.1638935988376
# PIL_120 = 3004.1309642750434 PIL_18 = 3097.4028921178624

# Final_time = 18.0


