""" Using Sharp data (followed Anthony's github code "https://github.com/antyeates1983/sharps-bmrs/blob/master" to aquire these data) and Anthony's thesis """

# Day 0 (2010.05.06)-- CR_2096

#####################################################################

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, RectBivariateSpline
from astropy.io import fits
from numba import njit, prange
import datetime

''' defining differential rotation and meridional flow as a function of colatitude '''

# differential rotation

def omega(theta):
	omega_deg_day = 0.18 - 2.3 * ((np.cos(theta)) ** 2) - 1.62 * ((np.cos(theta)) ** 4)
	omega_rad_sec = omega_deg_day * (np.pi/180) * (1/(24 * 3600))
	return omega_rad_sec

# meridional flow

def u(theta):

    p = 2.33
    Du = 0.045e5

    u_val = -Du * np.cos(theta) * (np.sin(theta))**p
    
    return u_val

###################################################################
# another meridional flow

#def u(theta):

#    theta_min = np.deg2rad(15)
#    theta_max = np.deg2rad(165)

    # initialize output with zeros
#    u_val = np.zeros_like(theta)

    # mask for valid region
#    mask = (theta >= theta_min) & (theta <= theta_max)

    # compute shape only inside the region
#    arg = np.pi * (theta_max + theta_min - 2*theta[mask]) / (2 * (theta_max - theta_min))
#    shape = np.cos(arg) * np.cos(theta[mask])

    # normalize
#    max_val = np.max(np.abs(shape))
#    C = -1500 / max_val

#    u_val[mask] = C * shape

#    return u_val
##################################################################


''' Import input file (read fits file with the help of astropy).
    Need to consider one carrington map before and after the considered 
    initial date (i.e. corresponding carrington map) so as to get the 
    proper map for that day from its corresponding longitudinal position in CR
    
    (Refer to Anthony's thesis for better understanding, page 38 - 40)
    '''

#--------------Previous-----------------
fits_file = fits.open('CR_MDI2095.fits')
B_prev = fits_file[0].data

#--------------Current------------------
fits_file = fits.open('CR_MDI2096.fits')
B_curr = fits_file[0].data

#--------------Future-------------------
fits_file = fits.open('CR_MDI2097.fits')
B_next = fits_file[0].data


phi_ref = np.deg2rad(180)
omega_0 = 13.2 * (np.pi/180) * (1/(24 * 3600))  # rad/sec
    
phi_original = np.linspace(0, np.deg2rad(360), B_curr.shape[1])
phi_ori_deg = np.rad2deg(phi_original)
theta_original = np.arcsin(np.linspace(-1, 1, B_curr.shape[0]))
theta_ori_deg = np.rad2deg(theta_original)

B_day106 = np.zeros((B_curr.shape[0], B_curr.shape[1]))

spline_prev = RectBivariateSpline(theta_original, phi_original, B_prev)
spline_curr = RectBivariateSpline(theta_original, phi_original, B_curr)
spline_next = RectBivariateSpline(theta_original, phi_original, B_next)


for i in range (len(theta_original)):
	for j in range (len(phi_original)):
		delta_t = (phi_original[j] - phi_ref) / omega_0
		phi_n = phi_original[j] + (omega(theta_original[i]) / omega_0) * (phi_original[j] - phi_ref)
		
		if phi_n < 0:
			selected_map = spline_prev
			phi_wrap = phi_n + np.deg2rad(360)
			
		elif phi_n > np.deg2rad(360):
			selected_map = spline_next
			phi_wrap = phi_n - np.deg2rad(360)
			
		else:
			selected_map = spline_curr
			phi_wrap = phi_n
			
		B_corrected = selected_map(theta_original[i], phi_wrap).item()
		
		B_day106[i, j] = B_corrected



Phi_ori_deg, Theta_ori_deg = np.meshgrid(phi_ori_deg, theta_ori_deg)

######################################################################################

''' Defining Grid scale (according to Anthony's thesis page 33 - 35) and initial values. 
    Here dx = dy = 1. '_c' stands for cell centre (for defining Bz), '_x' for defining Ax grid and '_y' for 
    defining Ay grid.
    '''

delta = 1
D = 3.5e12
Rs = 7e10
dt = 60			
		
			
def y(theta):
    return -(np.log(np.tan(theta/2))) / np.deg2rad(delta)

def theta(y):
    
    return 2*np.arctan(np.exp(-np.deg2rad(delta)*y))

#----------------Grid Setup for Staggered Grid (Refer to the first figure in page 35 of Anthony's thesis) -----------------

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

print (dy, len(y_c), dx)

###################################################################################

#----------------Initialize Fields-----------------

''' Interpolation of initial magnetic fields for desired grid '''

Br_interpolated = np.zeros((len(theta_c), B_day106.shape[1]))  # Intermediate matrix

for j in range(B_day106.shape[1]):  # Loop over phi values
    interp_func = interp1d(theta_original, B_day106[:, j], kind='cubic', fill_value="extrapolate")
    Br_interpolated[:, j] = interp_func(theta_new_c)

interp_func_2D = RectBivariateSpline(theta_new_c, phi_original, Br_interpolated, kx=3, ky=3)
resized_Br = interp_func_2D(theta_new_c, phi_c)
Bz_0 = resized_Br[:,:].T


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


for i in range(Ax.shape[0]):
    for j in range(Ax.shape[1]):
        Ax[i, j] = Ax[i, j] / np.sin(theta_x[j])
        
        
# Initialize Ay (starts at zero)
Ay[:, :] = 0.0

# Compute initial Bz from curl of A
for i in range(len(x_c)):
    for j in range(len(y_c)):
        theta_j = theta_c[j]
        sin_theta = np.sin(theta_j)
        
        # Finite differences for curl
        dAy_dx = (Ay[i+1, j] - Ay[i, j]) / (dx * np.deg2rad(delta) * Rs * sin_theta)
        dAx_dy = ((Ax[i, j+1] * np.sin(theta_x[j+1])) - (Ax[i, j] * np.sin(theta_x[j]))) / (dy * np.deg2rad(delta) * Rs * sin_theta**2)
        
        Bz[i, j] = dAy_dx - dAx_dy


# Store initial Bz for plotting
Bz_initial = Bz.copy()
X_c, Y_c = np.meshgrid(x_c, y_c, indexing='ij')
X_y, Y_y = np.meshgrid(x_y, y_y, indexing='ij')

diff = Bz - Bz_0
print("Max abs error:", np.max(np.abs(diff)))

Bz_time = [Bz.copy()]

Phi_deg_c, Theta_deg_c = np.meshgrid(phi_deg_c, theta_deg_c, indexing='ij')

########################################################################################

# Velocities at Ax locations (horizontal edges)
u_theta_x = u(theta_x)
u_phi_x = omega(theta_x) * Rs * np.sin(theta_x)

# Velocities at Ay locations (vertical edges)
u_theta_y = u(theta_y)
u_phi_y = omega(theta_y) * Rs * np.sin(theta_y)

#----------------Padding for Boundary Conditions-----------------

# ---------------- Bz ----------------
Bz = np.pad(Bz, ((1, 1), (0, 0)), mode='wrap')   # longitude (x / first dim) - periodic
Bz = np.pad(Bz, ((0, 0), (1, 1)), mode='edge')   # latitude (y / second dim) - reflecting

# ---------------- Ax ----------------
Ax = np.pad(Ax, ((1, 1), (0, 0)), mode='wrap')   # longitude
Ax = np.pad(Ax, ((0, 0), (1, 1)), mode='edge')   # latitude

# ---------------- Ay ----------------
Ay = np.pad(Ay, ((1, 1), (0, 0)), mode='wrap')   # longitude
Ay = np.pad(Ay, ((0, 0), (1, 1)), mode='edge')   # latitude



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


def apply_boundary_condition(Bz):
    
    Bz[0, :] = Bz[-2, :]
    Bz[-1, :] = Bz[1, :]
    Bz[:, 0] = Bz[:, 1]
    Bz[:, -1] = Bz[:, -2]
    
    return Bz

#----------------Update Functions-----------------

''' Updating Bz, Ax and Ay following induction equation (refer to Anthony's thesis page 34 & 35) '''

@njit(parallel=True)
def compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, theta_x_pad, dx, dy, delta, Rs):
    
    for i in prange(1, Bz.shape[0]-1):
        for j in range(1, Bz.shape[1]-1):
            theta_j = theta_c_pad[j]
            sin_theta = np.sin(theta_j)
            
            theta_x_j = theta_x_pad[j]
            sin_theta_x_j = np.sin(theta_x_j)
            
            theta_x_j1 = theta_x_pad[j+1]
            sin_theta_x_j1 = np.sin(theta_x_j1)
            
            # Avoid division by very small numbers
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
                
            if abs(sin_theta_x_j) < 0.01:
                sin_theta_x_j = 0.01 if sin_theta_x_j >= 0 else -0.01
                
            if abs(sin_theta_x_j1) < 0.01:
                sin_theta_x_j1 = 0.01 if sin_theta_x_j1 >= 0 else -0.01
            
            # Curl of A
            dAy_dx = (Ay[i+1, j] - Ay[i, j]) / (dx * np.deg2rad(delta) * Rs * sin_theta)
            dAx_dy = ((Ax[i, j+1] * sin_theta_x_j1) - (Ax[i, j] * sin_theta_x_j)) / (dy * np.deg2rad(delta) * Rs * sin_theta**2)
            
            Bz[i, j] = dAy_dx - dAx_dy
    
    return Bz

@njit(parallel=True)
def update_A_staggered(Ax, Ay, Bz, u_theta_x, u_phi_y, theta_x_pad, theta_y_pad, theta_c_pad,
                      dx, dy, delta, Rs, D, dt):
    
    Ax_new = Ax.copy()
    Ay_new = Ay.copy()
    
    # Update Ax (horizontal edges)
    for i in prange(1, Ax.shape[0]-1):
        for j in range(1, Ax.shape[1]-1):
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
                           ((Bz[i, j] - Bz[i, j-1]) / dy)
            
            Ax_new[i, j] = Ax[i, j] + dt * (advection + diffusion)
    
    # Update Ay (vertical edges)
    for i in prange(1, Ay.shape[0]-1):
        for j in range(1, Ay.shape[1]-1):
            theta_j = theta_y_pad[j]
            sin_theta = np.sin(theta_j)
            
            if abs(sin_theta) < 0.01:
                sin_theta = 0.01 if sin_theta >= 0 else -0.01
            
            # Interpolate Bz to Ay location (average of adjacent cells)
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
                           ((Bz[i, j] - Bz[i-1, j]) / dx)
            
            Ay_new[i, j] = Ay[i, j] + dt * (advection + diffusion)
    
    return Ax_new, Ay_new

#-----------------BMR File read to import new flux emergence------------------

import pandas as pd

# Read the BMR file, skipping the descriptive header lines and coloumns are seperated by spaces
bmr_df = pd.read_csv("bmrsharps_evol.txt", sep='\s+', skiprows=7)

# Convert the CM_time column into datetime objects
bmr_df['CM_time'] = pd.to_datetime(bmr_df['CM'], errors='coerce') \
    if 'CM' in bmr_df.columns else pd.to_datetime(bmr_df['CM_time'])

# Group by date
events_by_date = bmr_df.groupby(bmr_df['CM_time'].dt.date)

#----------------Time Integration-----------------

t = np.arange(0, (3500 * 24 * 3600), dt)
t_start = datetime.datetime(2010, 5, 6, 0, 0)
dt_date = datetime.timedelta(seconds=60)

last_checked_day = None

# Apply initial boundary conditions
Ax, Ay = apply_boundary_conditions(Ax, Ay)

# Main time loop
check_interval = max(1, len(t) // 20)

day_counter = 0
last_saved_day = None


@njit(parallel=True)
def Ay_func(Bz):

    Ay_AR = np.zeros((len(x_y), len(y_y)))
    for j in prange(len(y_c)):
        Ay_AR[0,j] = 0.0
        for i in range(len(x_c)):
            theta_mid = theta_c[j]
            Bz_mid = Bz[i, j] * np.sin(theta_mid)
            Ay_AR[i+1,j] = Ay_AR[i,j] + Bz_mid * (dx * np.deg2rad(delta) * Rs)
            
    return Ay_AR


# Updating field with time

for ti in range(1, len(t)):
    current_time = t_start + ti * dt_date
    
    # Update B field
    Bz = compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, theta_x_pad, dx, dy, delta, Rs)
    
    # Apply boundary conditions to B
    Bz = apply_boundary_condition(Bz)
    
    # Update A fields
    Ax, Ay = update_A_staggered(Ax, Ay, Bz, u_theta_x, u_phi_y, 
                               theta_x_pad, theta_y_pad, theta_c_pad, 
                               dx, dy, delta, Rs, D, dt)
    
    # Apply boundary conditions to A
    Ax, Ay = apply_boundary_conditions(Ax, Ay)
    
    # New flux emergence each day
    if last_checked_day != current_time.date():
        print (current_time.date())
        last_checked_day = current_time.date()

        if current_time.date() in events_by_date.groups:
            rows_today = events_by_date.get_group(current_time.date())
            
            Bz_total = np.zeros_like(Bz)
            count_valid = 0

            print(f"== {current_time.date()} has {len(rows_today)} event(s) ==")
            for _, row in rows_today.iterrows():
                sharp_id = row['SHARP']
                noaa     = row['NOAA']
                lat      = row['Latitude']
                led_p    = row['LeadPol']
                carr_lon = row['Carr_Longitude']
                
                # to avoid unphysical longitudinal information
                if (carr_lon < 0) or (carr_lon > 360):
                   continue
                
                count_valid += 1
                
                
                bip_dip  = row['Bip_Dipole']
                flux     = row['Unsgnd_flux']
                rho = row['Bip_Separation'] * (1/(2 * delta))
                rho_0 = rho * Rs * np.deg2rad(delta)
                
                del0 = np.deg2rad(row['Bip_Tilt'])
                
                # Wrapping tilt with in (+-90 degree)
                    
                if del0 > (np.pi/2):
                   del0 = del0 - np.pi
                elif del0 < -(np.pi/2):
                   del0 = del0 + np.pi
                
                
                x0 = carr_lon/delta
                y0 = y(np.deg2rad(90 - lat))
                
                
                # BMR magnetic field function with suitable scale factor 'a' (refer to Anthony's paper "How Good Is the Bipolar Approximation of Active Regions for Surface Flux Transport?")
                a = np.sqrt(1.5)
                B0 = (flux * 2 * np.sqrt(2)) / (np.sqrt(np.pi) * (a ** 3) * (rho_0 ** 2) * np.exp(0.5))
                
                def Bz_func(x, y):
                
                   dx = x - x0
                   dx = (dx + nx/2) % nx - nx/2
                   
                   xp = dx * np.cos(del0) - (y - y0) * np.sin(del0)
                   yp = dx * np.sin(del0) + (y - y0) * np.cos(del0)
                   xi = (xp ** 2 + 2 * yp ** 2) / ((a * rho) ** 2)

                   return -np.sign(led_p) * B0 * np.exp(0.5) * (xp/rho) * np.exp(-xi)
                
   
                Bz_AR = Bz_func(X_c, Y_c)
                Bz_AR = np.pad(Bz_AR, ((1, 1), (0, 0)), mode='wrap')
                Bz_AR = np.pad(Bz_AR, ((0, 0), (1, 1)), mode='edge')
                
                Bz_total += Bz_AR
                
            if count_valid == 0:
               print(f"Timestep {ti}: No valid BMR: skipping figure")
               continue
        
            Bz_total = apply_boundary_condition(Bz_total)
            
            Bz_new = Bz_total[1:-1, 1:-1]
            
            # converting Bz of BMR into Ax, Ay
            Ax_AR = np.zeros((len(x_x), len(y_x)))   # horizontal edges
            Ay_AR = Ay_func(Bz_new)
            Ax_AR = np.pad(Ax_AR, ((1, 1), (0, 0)), mode='wrap')
            Ax_AR = np.pad(Ax_AR, ((0, 0), (1, 1)), mode='edge')
            Ay_AR = np.pad(Ay_AR, ((1, 1), (0, 0)), mode='wrap')
            Ay_AR = np.pad(Ay_AR, ((0, 0), (1, 1)), mode='edge')
            
            
            Ax = Ax + Ax_AR
            Ay = Ay + Ay_AR
            
            Ax, Ay = apply_boundary_conditions(Ax, Ay)
             
    if (current_time.hour == 23 and current_time.minute == 59
        and current_time.date() != last_saved_day):
        
        day_counter += 1   # count model days

        if day_counter % 2 == 1:
        
            Bz = compute_B_from_A_staggered(Ax, Ay, Bz, theta_c_pad, theta_x_pad, dx, dy, delta, Rs)
        
            Bz = apply_boundary_condition(Bz)
        
            Bz_time.append(Bz[1:-1, 1:-1].copy())
        
        last_saved_day = current_time.date()               
    
    
    # Progress monitoring
    if ti % check_interval == 0:
        max_Bz = np.max(np.abs(Bz[1:-1, 1:-1]))
        max_Ax = np.max(np.abs(Ax[1:-1, 1:-1]))
        max_Ay = np.max(np.abs(Ay[1:-1, 1:-1]))
        
        if np.any(np.isnan(Bz)) or np.any(np.isnan(Ax)) or np.any(np.isnan(Ay)):
            print(f"WARNING: NaN detected at timestep {ti}")
            break
        
        print(f"Progress: {100*ti/len(t):.1f}% | Max |Bz|={max_Bz:.3e}, Max |Ax|={max_Ax:.3e}, Max |Ay|={max_Ay:.3e}")
        
        
print ("final_saved_day: ", last_saved_day)

Bz_time = np.stack(Bz_time) 
np.savez("new_report", Bz_time=Bz_time)

#############################################################################################

#--------------------Plotting-------------------

plt.figure(figsize=(10,6))
plt.contourf(Phi_deg_c, Theta_deg_c, Bz_time[-1], levels = 100, cmap = "seismic", vmin=-np.max(np.abs(Bz_time[-1])),vmax=np.max(np.abs(Bz_time[-1])))
plt.colorbar(label = "Magnetic field strength (G)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.gca().invert_yaxis()
plt.yticks([170,150,130,110,90,70,50,30,10],
           ["-80°","-60°", "-40°", "-20°", "0°", "20°","40°","60°","80°"])
plt.xticks([50,100,150,200,250,300,350],
           ["50°", "100°", "150°", "200°", "250°","300°","350°"])
plt.title("Field strength at 2020_12_25 from SFT")
plt.show()
plt.savefig("result/final_2020.png", dpi=300)

plt.figure(figsize=(10,6))
plt.contourf(Phi_deg_c, Theta_deg_c, Bz_time[-1], levels = 100, cmap = "seismic", vmin=-130,vmax=130)
plt.colorbar(label = "Magnetic field strength (G)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.gca().invert_yaxis()
plt.yticks([170,150,130,110,90,70,50,30,10],
           ["-80°","-60°", "-40°", "-20°", "0°", "20°","40°","60°","80°"])
plt.xticks([50,100,150,200,250,300,350],
           ["50°", "100°", "150°", "200°", "250°","300°","350°"])
plt.title("Field strength at 2020_12_25 from SFT")
plt.show()
plt.savefig("result/final_saturated_2020.png", dpi=300)

###############################################################################################
