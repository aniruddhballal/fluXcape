""" Here, we only used diffusion part in SFT. We know that surface magnetic field distribution can be composed of weighted sum of spherical harmonics.
    If you go through my paper, it will be clear that if we include more and more harmonics, small-scale magnetic structures will be captured (increasing 
    resolution). but we can not consider infinite no of harmonics, so we consider max_l = 120 here and constructed the surface field distribution from 
    observation. In my paper, we also mentioned that l_effective = 7-19 will be enough to capture the important contributions (more than 60%). So here we 
    considered another threshold map for max_l = 18. 
    
    
    So, we used max_l = 120 map as initial condition to solve SFT with only diffusion part (without including new flux emergence). As, we update the time 
    loop, because of diffusion term, small-scale structures will diffuse and with time the diffused distribution will contribute to large-scale structures. 
    In other words, max_l = 120 map will almost converge towards max_l = 18 map.
    
    Here we have considered this time update in terms of 'length of polarity line inversion' i.e. the condition is the loop will break 
    if (PIL_120(t) - PIL_18) <= threshold.
    
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
#resized_Br1 = resized_Br[::-1,:]


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

#######################################################################

## Method (a)

print ("-------------skimage--------------")

Br_cons = Br_cons.T
Br_cons = Br_cons.real

Br_cons01 = Br_cons01.T
Br_cons01 = Br_cons01.real

print (np.shape(Br_cons))

##** skimage **##

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

PIL_120 = pil_length_pixels(Br_cons)
PIL_18 = pil_length_pixels(Br_cons01)

print ("PIL_120 = ", PIL_120, "PIL_18 = ", PIL_18)

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

    
    # Reflecting/no-flux at y boundaries (latitude)
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


t = 0.0
dt = 60
check_interval = 86400.0   # check once per day (s)
f = 0.01

time_since_last_check = 0.0
Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

l1 = [PIL_120]

while True:
    # Compute B from current A
    Bz = compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, dx, dy, delta, Rs)
    
    # Apply boundary conditions to B
    Bz[0, :] = Bz[-2, :]
    Bz[-1, :] = Bz[1, :]
    Bz[:, 0] = Bz[:, 1]
    Bz[:, -1] = Bz[:, -2]
    
    # Update A fields
    Ax, Ay = update_A_staggered(Ax, Ay, Bz, 
                                theta_x_pad, theta_y_pad, 
                                dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax, Ay = apply_boundary_conditions(Ax, Ay)
    t += dt
    time_since_last_check += dt
    
    Bz_f = Bz[1:-1, 1:-1]
    
    # Periodically compute power
    if time_since_last_check >= check_interval:

        PIL_t = pil_length_pixels(Bz_f)
        print ("PIL_t = ", PIL_t)
        l1.append(PIL_t)

        # Reset timer
        time_since_last_check = 0.0

        # Check convergence condition
        if (PIL_t - PIL_18) <= f:
            break


with parallel_backend('loky'):
    results_t = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i, Bz_f) for i in range (1,19))

Bz_f01 = sum (results_t)

Bz_f01 = Bz_f01.T
Bz_f01 = Bz_f01.real
        
#############################################################################################
print ()
print ("Days =", t/(24 * 3600))

fig, axes = plt.subplots(1, 3, figsize=(20, 4))

# --- Bz_f plot ---
c1 = axes[0].contourf(Phi_deg_c, Theta_deg_c, Bz_f,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_f)), vmax=np.max(np.abs(Bz_f)))
fig.colorbar(c1, ax=axes[0], label="Magnetic field strength (Bz)")
axes[0].set_title("Bz_120_final_time")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].invert_yaxis()
axes[0].set_yticks([160,140,120,100,80,60,40,20])
axes[0].set_yticklabels(["-70°","-50°","-30°","-10°","10°","30°","50°","70°"])
        
# --- Bz_f01 plot ---
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_f01,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_f01)), vmax=np.max(np.abs(Bz_f01)))
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
plt.savefig("skimage/diff.png", dpi=300)


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
plt.savefig("skimage/total_change.png", dpi=300)

plt.figure(figsize=(8,5))
plt.plot(x1[:], lss1, marker='o', markersize=3, linestyle='-')
plt.grid()
plt.xlabel("No of days")
plt.ylabel("Polarity inversion line length ($l_{i}/l_{0}$)")
plt.title("Variation of length for PIL with time")
plt.savefig("skimage/frac_change.png", dpi=300)



#--------------------------------outputs------------------------------------

# PIL_120 =  17627.282129802497, PIL_18 =  2544.5371677187572
#----------------------------------------------------
# Max abs error: 3.3011371414204405e-12
# diff = (360, 174)
# PIL_t =  13241.773173214684
# PIL_t =  10586.414615096368
# PIL_t =  8889.630099713651
# PIL_t =  7528.5974085215685
# PIL_t =  6582.1486927028855
# PIL_t =  5874.063012363666
# PIL_t =  5316.057138705987
# PIL_t =  4808.110816613822
# PIL_t =  4397.087086105694
# PIL_t =  4054.399694888388
# PIL_t =  3760.213161865847
# PIL_t =  3508.7188283993337
# PIL_t =  3318.4663126145297
# PIL_t =  3137.1577762759844
# PIL_t =  2984.5433710797483
# PIL_t =  2879.0378287699123
# PIL_t =  2782.3153123817456
# PIL_t =  2689.9240873307845
# PIL_t =  2616.740237070003
# PIL_t =  2539.0453734727876

# Days = 20.0

##############################################################################################
##############################################################################################
##############################################################################################
##############################################################################################

# Method (b)

##**Basic_Python**##

print ("--------------Basic Python---------------")

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

PIL_120_1 = pil_length_from_sign_changes(Br_cons)
PIL_18_1 = pil_length_from_sign_changes(Br_cons01)

print ("PIL_120 = ", PIL_120_1, "PIL_18 = ", PIL_18_1)

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
    """
    Compute spherical-harmonic coefficient a_lm
    using Gauss–Legendre quadrature.

    Bz is assumed to be stored as (phi, theta).
    """

    # Interpolator requires (theta, phi) ordering
    interp_Bz = RegularGridInterpolator(
        (theta_c, phi_c),
        Bz.T,                    # <-- IMPORTANT transpose
        bounds_error=False,
        fill_value=0.0
    )

    # Interpolate Bz onto GL nodes
    points = np.stack(
        [Theta_GL.ravel(), Phi_GL.ravel()],
        axis=-1
    )

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


t = 0.0
dt = 60
check_interval = 86400.0   # check once per day (s)
f = 0.01

time_since_last_check = 0.0
Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

l2 = [PIL_120_1]

while True:
    # Compute B from current A
    Bz = compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, dx, dy, delta, Rs)
    
    # Apply boundary conditions to B
    Bz[0, :] = Bz[-2, :]
    Bz[-1, :] = Bz[1, :]
    Bz[:, 0] = Bz[:, 1]
    Bz[:, -1] = Bz[:, -2]
    
    # Update A fields
    Ax, Ay = update_A_staggered(Ax, Ay, Bz, 
                                theta_x_pad, theta_y_pad, 
                                dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions
    Ax, Ay = apply_boundary_conditions(Ax, Ay)
    t += dt
    time_since_last_check += dt
    
    Bz_f1 = Bz[1:-1, 1:-1]
    
    # Periodically compute power
    if time_since_last_check >= check_interval:

        PIL_t_1 = pil_length_from_sign_changes(Bz_f1)
        print ("PIL_t = ", PIL_t_1)
        l2.append(PIL_t_1)

        # Reset timer
        time_since_last_check = 0.0

        # Check convergence condition
        if (PIL_t_1 - PIL_18_1) <= f:
            break


with parallel_backend('loky'):
    results_t1 = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i, Bz_f1) for i in range (1,19))

Bz_f01_1 = sum (results_t1)

Bz_f01_1 = Bz_f01_1.T
Bz_f01_1 = Bz_f01_1.real
        
#############################################################################################
print ()
print ("Days =", t/(24 * 3600))

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
c2 = axes[1].contourf(Phi_deg_c, Theta_deg_c, Bz_f01_1,levels=100, cmap="seismic",vmin=-np.max(np.abs(Bz_f01_1)), vmax=np.max(np.abs(Bz_f01_1)))
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
plt.savefig("basic_python/diff.png", dpi=300)


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
plt.savefig("basic_python/total_change.png", dpi=300)

plt.figure(figsize=(8,5))
plt.plot(x2[:], lss2, marker='o', markersize=3, linestyle='-')
plt.grid()
plt.xlabel("No of days")
plt.ylabel("Polarity inversion line length ($l_{i}/l_{0}$)")
plt.title("Variation of length for PIL with time")
plt.savefig("basic_python/frac_change.png", dpi=300)


#--------------------------------outputs------------------------------------

# PIL_120 =  2403601.8153432244, PIL_18 =  323456.791834651
#----------------------------------------------------
# Max abs error: 3.3011371414204405e-12
# diff = (360, 174)
# PIL_t =  1838323.0515259984
# PIL_t =  1466801.7500861085
# PIL_t =  1233804.1133042257
# PIL_t =  1030982.2533176249
# PIL_t =  891737.7094711668
# PIL_t =  762523.2947667327
# PIL_t =  707310.3699188902
# PIL_t =  637785.150108215
# PIL_t =  586740.8389717203
# PIL_t =  520171.93878309353
# PIL_t =  479877.2701027247
# PIL_t =  448466.8184871689
# PIL_t =  419001.0961950462
# PIL_t =  400557.92341398745
# PIL_t =  365770.9649261411
# PIL_t =  357649.2196794806
# PIL_t =  344847.2462684182
# PIL_t =  336826.83471693203
# PIL_t =  323345.1313172299

# Days = 19.0
			
