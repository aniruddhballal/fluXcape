""" Solving PFSS using spherical harmonics decomposition. Formulas are all simple and straight forward.
    Go through my paper on PFSS to get all the details about spherical harmonics, field distribution 
    formulas etc.
    
    """


#####################################################################

import numpy as np
import matplotlib.pyplot as plt
from scipy.special import sph_harm
from scipy.interpolate import interp1d, RectBivariateSpline
from mpl_toolkits.mplot3d import Axes3D
from astropy.io import fits
from joblib import Parallel, delayed
from joblib import parallel_backend


#-----------Spherical Harmonics-------------

def Y_lm(l,m,theta,phi):
    return sph_harm(m, l, phi, theta)

max_L= 80
l = np.arange(1,max_L+1,1)
theta = np.linspace(0,np.pi,181)
theta_new = np.linspace(-np.pi/2,np.pi/2,181)
phi = np.linspace(0,2*np.pi,361)
Phi,Theta=np.meshgrid(phi,theta)

#--------------Reading HMI data---------------------

fits_file = fits.open('CR_2193.fits')
B = fits_file[1].data
Br=B[:,:]

#---------------Interpolation----------------------

phi_original = np.linspace(0, 2*np.pi, Br.shape[1])
theta_original = np.arcsin(np.linspace(-1, 1, Br.shape[0]))
Br_interpolated = np.zeros((len(theta), Br.shape[1]))  # Intermediate matrix

for j in range(Br.shape[1]):  # Loop over phi values
    interp_func = interp1d(theta_original, Br[:, j], kind='cubic', fill_value="extrapolate")
    Br_interpolated[:, j] = interp_func(theta_new)

interp_func_2D = RectBivariateSpline(theta_new, phi_original, Br_interpolated, kx=3, ky=3)
resized_Br = interp_func_2D(theta_new, phi)
resized_Br1 = resized_Br[::-1,:]

#---------Integration for the Co-efficient-----------

def func_integ(l,m,theta,phi):
    return (np.conj(Y_lm(l,m,theta,phi)))*np.sin(theta)

F=np.zeros([len(Theta[:,0]),len(Phi[0,:])],dtype=complex)

def simpson_weights(n):
    W_matrix = np.ones(n+1, dtype=complex)
    W_matrix[1:n:2] = 4  # Odd indices
    W_matrix[2:n-1:2] = 2  # Even indices (except first and last)
    return W_matrix

def simpson_2D_weight_matrix(n_x, n_y):
    Wx = simpson_weights(n_x)
    Wy = simpson_weights(n_y)
    W_2D = np.outer(Wx, Wy)
    return W_2D

W = simpson_2D_weight_matrix(len(theta)-1, len(phi)-1)

def C_lm(l,m):
    I=0

    for t in range(len(theta)):
        for p in range(len(phi)):
            F[t,p]=resized_Br1[t,p]*func_integ(l,m,theta[t],phi[p])
            I=I+W[t,p]*F[t,p]
    C=(1/9.0)*(np.pi/(len(theta)-1))*(2*np.pi/(len(phi)-1))*I

    return C

#--------------Reconstructing the magnetic field----------------

def compute_c_for_i(i):
    c_l = 0
    m = 0
    for j in range(-i, i + 1):
        c_l += abs(C_lm(i, j))
        m += abs(j)
    return (c_l / m)

with parallel_backend('loky'):
    c = Parallel(n_jobs=-1)(delayed(compute_c_for_i)(i) for i in l)

print ("c=",c)



def compute_sum1_for_i(i):
    return sum((C_lm(i,j)*Y_lm(i,j,Theta,Phi)) for j in range(-i, i+1))

with parallel_backend('loky'):
    results1 = Parallel(n_jobs=-1)(delayed(compute_sum1_for_i)(i) for i in l)

Br_cons = sum (results1)

print ("Br_cons=",Br_cons)

Err=np.zeros([len(Theta[:,0]),len(Phi[0,:])],dtype=complex)

for t in range(len(theta)):
    for p in range(len(phi)):
        Err[t,p]=Br_cons[t,p]-resized_Br1[t,p]
        
print ("Error=",Err)

##############################################################################

#--------------------Plotting------------------------

from matplotlib.ticker import FuncFormatter

theta = np.linspace(0,np.pi,181)
phi = np.linspace(0,2*np.pi,361)
Phi,Theta=np.meshgrid(phi,theta)

vmin2 = - np.maximum(np.max(Err.real),abs(np.min(Err.real)))
vmax2 = np.maximum(np.max(Err.real),abs(np.min(Err.real)))

levels2 = np.linspace(vmin2, vmax2, 100)
def rad_to_deg(x, pos):
    return f"{np.degrees(x):.0f}°"

fig, ax =plt.subplots(figsize=(10,6))
cax=ax.contourf(Phi,Theta[::-1,:], Err.real , levels=levels2, cmap="seismic", vmin=vmin2, vmax=vmax2)
cbar = fig.colorbar(cax,ax=ax,label="Error in field strength (G)")
ax.set_title("Error in Magnetic field strength for $l_{max} = 80$")
ticks = np.linspace(vmin2, vmax2, 9)
cbar.set_ticks(np.linspace(vmin2, vmax2, 9))
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
yticks = [0, np.pi/6, np.pi/3 , np.pi/2, 2 * np.pi/3, 5 * np.pi/6, np.pi]  # Set positions where you want labels
yticklabels = ["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"]  # Custom labels
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)

# Custom x-ticks (optional)
xticks = np.linspace(0, 2 * np.pi, 7)  # Use the same x range as your plot
xticklabels = ["0°", "60°", "120°", "180°", "240°", "300°", "360°"]
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
plt.savefig("result_93/err_80.png", dpi=300)

vmin1 = -np.maximum(np.max(Br_cons.real),abs(np.min(Br_cons.real)))
vmax1 = np.maximum(np.max(Br_cons.real),abs(np.min(Br_cons.real)))

levels1 = np.linspace(vmin1, vmax1, 100)

fig, ax =plt.subplots(figsize=(10,6))
cax=ax.contourf(Phi,Theta[::-1,:], Br_cons.real , levels=levels1, cmap="seismic", vmin = vmin1, vmax= vmax1)
#zero_contour = ax.contour(Phi, Theta, Br_cons.real, levels=[0], colors='black', linewidths=1)
cbar = fig.colorbar(cax,ax=ax,label="Reconstructed field strength (G)")
ticks = np.linspace(vmin1, vmax1, 9)  # You can adjust the number of ticks as needed
cbar.set_ticks(np.linspace(vmin1, vmax1, 9))
ax.set_title("Constructed Magnetic field strength for $l_{max} = 80$")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
yticks = [0, np.pi/6, np.pi/3 , np.pi/2, 2 * np.pi/3, 5 * np.pi/6, np.pi]  # Set positions where you want labels
yticklabels = ["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"]  # Custom labels
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)

# Custom x-ticks (optional)
xticks = np.linspace(0, 2 * np.pi, 7)  # Use the same x range as your plot
xticklabels = ["0°", "60°", "120°", "180°", "240°", "300°", "360°"]
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
plt.savefig("result_93/cons_80.png", dpi=300)

vmin = -np.maximum(np.max(resized_Br1.real),abs(np.min(resized_Br1.real)))
vmax = np.maximum(np.max(resized_Br1.real),abs(np.min(resized_Br1.real)))


levels = np.linspace(vmin, vmax, 100)
            
fig, ax =plt.subplots(figsize=(10,6))
cax=ax.contourf(Phi,Theta[::-1,:], resized_Br1.real , levels=levels, cmap="seismic", vmin=vmin, vmax=vmax)
#zero_contour = ax.contour(Phi, Theta, resized_Br1.real, levels=[0], colors='black', linewidths=0.5)
cbar = fig.colorbar(cax,ax=ax,label="Original field strength (G)")
ticks = np.linspace(vmin, vmax, 9)  # You can adjust the number of ticks as needed
cbar.set_ticks(np.linspace(vmin, vmax, 9))
ax.set_title("Original Magnetic field strength")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
yticks = [0, np.pi/6, np.pi/3 , np.pi/2, 2 * np.pi/3, 5 * np.pi/6, np.pi]  # Set positions where you want labels
yticklabels = ["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"]  # Custom labels
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)

# Custom x-ticks (optional)
xticks = np.linspace(0, 2 * np.pi, 7)  # Use the same x range as your plot
xticklabels = ["0°", "60°", "120°", "180°", "240°", "300°", "360°"]
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
plt.savefig("result_93/original_80.png", dpi=300)

############################################################################

plt.figure(figsize = (8,6))
plt.plot(l,c, marker='o', markersize=3, linestyle='-')
plt.xlabel("l - values")
plt.ylabel("$C_{l}$")
plt.title("Power Spectrum")
plt.savefig("result_93/spectrum_80.png", dpi=300)

#############################################################################

#---------------Computing Br--------------------
r=np.linspace(1,2.5,100)
Phi,Theta,R=np.meshgrid(phi,theta,r)
Rs=2.5


def B_final(theta,phi,r):
  def compute_sum_for_i(i):
      return sum((((C_lm(i,j))/r**(i+2))*((i+1+i*((r/Rs)**(2*i+1)))/(i+1+i*((1/Rs)**(2*i+1))))*Y_lm(i,j,theta,phi)) for j in range(-i, i+1))

  with parallel_backend('loky'):
      results = Parallel(n_jobs=-1)(delayed(compute_sum_for_i)(i) for i in l)


  return sum(results)

BrF=B_final(Theta,Phi,R)
print ("BrF=",BrF)

################################################################################

Phi,Theta = np.meshgrid(phi,theta)

vmin = - np.maximum(np.max(BrF[:,:,0].real),abs(np.min(BrF[:,:,0].real)))
vmax = np.maximum(np.max(BrF[:,:,0].real),abs(np.min(BrF[:,:,0].real)))

levels = np.linspace(vmin, vmax, 100)

fig, ax =plt.subplots(figsize=(10, 6))
cax=ax.contourf(Phi, Theta[::-1,:], np.array(BrF[:,:,0]).real, levels=levels, cmap="seismic", vmin=vmin, vmax=vmax)
cbar = fig.colorbar(cax,ax=ax,label="Reconstructed field strength (G)")
ticks = np.linspace(vmin, vmax, 9)  # You can adjust the number of ticks as needed
cbar.set_ticks(np.linspace(vmin, vmax, 9))
ax.set_title("Distribution of field strength Over distance from Solar Surface")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
yticks = [0, np.pi/6, np.pi/3 , np.pi/2, 2 * np.pi/3, 5 * np.pi/6, np.pi]  # Set positions where you want labels
yticklabels = ["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"]  # Custom labels
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)

# Custom x-ticks (optional)
xticks = np.linspace(0, 2 * np.pi, 7)  # Use the same x range as your plot
xticklabels = ["0°", "60°", "120°", "180°", "240°", "300°", "360°"]
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)

#################################################################################

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib.colors import Normalize



vmin4 = - np.maximum(np.max(BrF[:,:,-1].real),abs(np.min(BrF[:,:,-1].real)))
vmax4 = np.maximum(np.max(BrF[:,:,-1].real),abs(np.min(BrF[:,:,-1].real)))

levels4 = np.linspace(vmin4, vmax4, 100)

fig, ax =plt.subplots(figsize=(10, 6))
cax=ax.contourf(Phi, Theta[::-1,:], np.array(BrF[:,:,-1]).real, levels = levels4, cmap="seismic")
cbar = fig.colorbar(cax,ax=ax,label="Magnetic field strength (G)")
ticks = np.linspace(vmin4, vmax4, 9)
cbar.set_ticks(np.linspace(vmin4, vmax4, 9))
ax.set_title("Distribution of field strength at Source Surface")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
yticks = [0, np.pi/6, np.pi/3 , np.pi/2, 2 * np.pi/3, 5 * np.pi/6, np.pi]  # Set positions where you want labels
yticklabels = ["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"]  # Custom labels
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)

# Custom x-ticks (optional)
xticks = np.linspace(0, 2 * np.pi, 7)  # Use the same x range as your plot
xticklabels = ["0°", "60°", "120°", "180°", "240°", "300°", "360°"]
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
plt.savefig("result_93/SS.png", dpi=300)

fig, ax =plt.subplots(figsize=(10, 6))
cax=ax.contourf(Phi, Theta[::-1,:], np.array(BrF[:,:,-1]).real, levels = levels, cmap="seismic")
cbar = fig.colorbar(cax,ax=ax,label="Magnetic field strength (G)")
ax.set_title("Distribution of field strength at Source Surface")
ax.set_xlabel("Longitude")
cbar.set_ticks(np.linspace(vmin, vmax, 7))
ax.set_ylabel("Latitude")
yticks = [0, np.pi/6, np.pi/3 , np.pi/2, 2 * np.pi/3, 5 * np.pi/6, np.pi]  # Set positions where you want labels
yticklabels = ["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"]  # Custom labels
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels)

# Custom x-ticks (optional)
xticks = np.linspace(0, 2 * np.pi, 7)  # Use the same x range as your plot
xticklabels = ["0°", "60°", "120°", "180°", "240°", "300°", "360°"]
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
plt.savefig("result_april/ss_p_7.pdf", dpi=300)

############################################################################################

#----------------------Flux Calculation inside corona--------------------------

r1=np.linspace(7e10,1.75e11,100)
F1=np.zeros([len(theta),len(phi)],dtype=complex)
def simpson_weights(n):
    W_matrix = np.ones(n+1, dtype=complex)
    W_matrix[1:n:2] = 4
    W_matrix[2:n-1:2] = 2
    return W_matrix

def simpson_2D_weight_matrix(n_x, n_y):
    Wx = simpson_weights(n_x)
    Wy = simpson_weights(n_y)
    W_2D = np.outer(Wx, Wy)
    return W_2D

W1 = simpson_2D_weight_matrix(len(theta)-1, len(phi)-1)



def flux(r):
    c1=[]
    for a in range (len(r)):
        print (r[a])
        In=0
        for t in range(len(theta)):
            for p in range(len(phi)):
                F1[t,p]=(r[a]**2)*abs(BrF[t,p,a])*np.sin(theta[t])
                In=In+W1[t,p]*F1[t,p]
        Cn=(1/9.0)*(np.pi/(len(theta)-1))*(2*np.pi/(len(phi)-1))*In
        print (f"Cn_{a}",Cn)
        c1.append(Cn)
    return c1

real_parts = [c.real for c in flux(r1)]
F2=np.array(real_parts)
print ("Flux=", np.array2string(F2, separator=','))

##############################################################################################

#---------------------Original Flux on the Solar Surface-----------------------

r2 = 7e10
F3=np.zeros([len(theta),len(phi)],dtype=complex)
def simpson_weights(n):
    W_matrix = np.ones(n+1, dtype=complex)
    W_matrix[1:n:2] = 4
    W_matrix[2:n-1:2] = 2
    return W_matrix

def simpson_2D_weight_matrix(n_x, n_y):
    Wx = simpson_weights(n_x)
    Wy = simpson_weights(n_y)
    W_2D = np.outer(Wx, Wy)
    return W_2D

W2 = simpson_2D_weight_matrix(len(theta)-1, len(phi)-1)




In=0
for t in range(len(theta)):
    for p in range(len(phi)):
        F3[t,p]=(r2**2)*abs(resized_Br1[t,p])*np.sin(theta[t])
        In=In+W2[t,p]*F3[t,p]
Cn=(1/9.0)*(np.pi/(len(theta)-1))*(2*np.pi/(len(phi)-1))*In

print ("Original_flux =",Cn)

##############################################################################################

plt.figure(figsize = (8,6))
r2=[7e10]
or_f=[abs(Cn)]
plt.plot(r1,F2, label="l_max = 80")
plt.plot(r2,or_f,"o", label="Original")
plt.xlabel("Distance (cm)")
plt.ylabel("Magnetic Flux (Maxwell)")
plt.title ("Variation of Flux")
plt.grid()
plt.legend()
plt.savefig("result_93/flux_80.png", dpi=300)

##############################################################################################

#-----------------------Computing B_theta---------------------------

from scipy.special import lpmv


r=np.linspace(1,2.5,100)
Phi,Theta,R=np.meshgrid(phi,theta[1:],r)
Rs=2.5


def dYlm_dtheta(l, m, theta, phi):

    P_lm = lpmv(m, l, np.cos(theta))
    
    P_lm = np.where(P_lm == 0, 1e-6, P_lm)

    dP_lm_dtheta = (1/np.sin(theta)) * (-(l+1) * np.cos(theta) * lpmv(m, l, np.cos(theta)) + (l-m+1) * lpmv(m, l + 1, np.cos(theta)))
    
    dYlm = (Y_lm(l,m,theta,phi) / P_lm) * dP_lm_dtheta
    return dYlm


def B_final2(theta,phi,r):
   def compute_sum_for_i(i):
      return sum((((-C_lm(i,j))/r**(i+2))*((1-((r/Rs)**(2*i+1)))/(i+1+i*((1/Rs)**(2*i+1))))*dYlm_dtheta(i, j, theta, phi)) for j in range(-i, i+1))

   with parallel_backend('loky'):
      results = Parallel(n_jobs=-1)(delayed(compute_sum_for_i)(i) for i in l)


   return sum(results)


BtF=B_final2(Theta,Phi,R)
print ("BtF=",BtF)

#############################################################################################

#-----------------------Computing B_phi---------------------------

r=np.linspace(1,2.5,100)
Phi,Theta,R=np.meshgrid(phi,theta,r)
Rs=2.5
print (C_lm(1,1))
def B_final3(theta,phi,r):
   def compute_sum_for_i(i):
      return sum(((1j)*(((-j*C_lm(i,j))/r**(i+2))*((1-((r/Rs)**(2*i+1)))/(i+1+i*((1/Rs)**(2*i+1))))*(Y_lm(i,j,theta,phi))/np.sin(theta))) for j in range(-i, i+1))

   with parallel_backend('loky'):
      results = Parallel(n_jobs=-1)(delayed(compute_sum_for_i)(i) for i in l)


   return sum(results)


BpF=B_final3(Theta,Phi,R)
print ("BpF",BpF)

###############################################################################################

BpF1 = BpF[1:,:,:].real
BtF1 = BtF[:,:,:].real
BrF1= BrF[1:,:,:].real
print ("BrF1=",BrF1)
print ("BtF1=",BtF1)
print ("BpF1=",BpF1)

np.savez("output_fields_93_80_full.npz", BrF=BrF, BrF1=BrF1, BtF1=BtF1, BpF1=BpF1)
###############################################################################################

