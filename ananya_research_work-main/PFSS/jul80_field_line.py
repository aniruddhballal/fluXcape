
""" Continuation of the file 'CR_2193_80_full.py'. We imported B_r, B_theta and B_phi from the data file created in 'CR_2193_80_full.py'. Here,
    we want to plot field lines.
    
    """


#####################################################################

import numpy as np
import matplotlib.pyplot as plt


data = np.load("output_fields_93_80_full.npz")


BrF = data['BrF']
BrF1 = data['BrF1']
BtF1 = data['BtF1']
BpF1 = data['BpF1']

######################################################################

import numpy as n
from scipy.interpolate import RegularGridInterpolator as rgi


# Specify direction of the viewer
lon0 = n.deg2rad(296.7)
lat0 = n.deg2rad(6.93)

# Specify maximum of colour scale for Br on Solar Surface
bmax = np.maximum(np.max(BrF[:,:,0].real),abs(np.min(BrF[:,:,0].real)))

# initial points to get open magnetic field lines 
nth = 30
th00 = n.linspace(0.02*n.pi, 0.98*n.pi, nth)
th0 = n.concatenate((th00, th00), axis=0)
ph0 = n.concatenate((th00*0 + (lon0 + 0.5*n.pi), th00*0 + (lon0 - 0.5*n.pi)), axis=0)
r0 = th0*0 + 2.5
#r01 = th0*0 + 1.001

theta = np.linspace(0,np.pi,181)
phi = np.linspace(0,2*np.pi,361)
r=np.linspace(1,2.5,100)

# ------------ Function for field lines solution -----------------

def bTrace(x, y, z):
    """
    Compute B/|B| at (x, y, z).
    """
    r = np.sqrt(x**2 + y**2 + z**2)
    if r == 0:
        return np.array([0, 0, 0])  # Avoid division by zero

    ph = (np.arctan2(y, x) + 2*np.pi) % (2*np.pi)
    s = z / r
    rh = np.log(r)
    s = np.clip(s, brgi.grid[0][0], brgi.grid[0][-1])
    ph = np.clip(ph, brgi.grid[1][0], brgi.grid[1][-1])
    rh = np.clip(rh, brgi.grid[2][0], brgi.grid[2][-1])


    B = brgi(np.array([[s, ph, rh]]))[0]  # Ensure correct shape
    # print (B)

    norm_B = np.linalg.norm(B)
    if norm_B == 0:
        return np.array([0, 0, 0])  # Avoid division by zero

    return B / norm_B   # Normalize

# ------------ RK4 field line tracer --------------

def rk4(x, y, z, h, max_steps=10000, Rs=2.5, R_sun=1.0):
    x_list, y_list, z_list = [x], [y], [z]
    
    for _ in range(max_steps):
        k1 = bTrace(x, y, z) * h
        k2 = bTrace(x + 0.5 * k1[0], y + 0.5 * k1[1], z + 0.5 * k1[2]) * h
        k3 = bTrace(x + 0.5 * k2[0], y + 0.5 * k2[1], z + 0.5 * k2[2]) * h
        k4 = bTrace(x + k3[0], y + k3[1], z + k3[2]) * h
        
        dx, dy, dz = (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
        x, y, z = x + dx, y + dy, z + dz

        r = np.sqrt(x**2 + y**2 + z**2)
        
        x_list.append(x)
        y_list.append(y)
        z_list.append(z)
        
        # r = np.sqrt(x**2 + y**2 + z**2)
        if r <= R_sun or abs(r - R_sun) < 0.001 or r>Rs:
            break

    return np.array(x_list), np.array(y_list), np.array(z_list)



# Convert grid to Cartesian components
s = np.cos(theta[1:])
rh = np.log(r)
phi = np.linspace(0, 2 * np.pi, 361)
s3, ph3, rh3 = np.meshgrid(s, phi, rh, indexing='ij')
bx = np.sqrt(1 - s3**2) * np.cos(ph3) * BrF1 + s3 * np.cos(ph3) * BtF1 - np.sin(ph3) * BpF1
by = np.sqrt(1 - s3**2) * np.sin(ph3) * BrF1 + s3 * np.sin(ph3) * BtF1 + np.cos(ph3) * BpF1
bz = s3 * BrF1 - np.sqrt(1 - s3**2) * BtF1
#brgi = rgi((s, phi, rh), np.stack((bx, by, bz), axis=3))
bstack = np.stack((bx,by,bz),axis=3)
del(bx, by, bz)
brgi = rgi((s, phi, rh), bstack, method = 'nearest')
del(bstack)

# Convert starting points to Cartesian
x0 = np.stack((r0*np.cos(ph0)*np.sin(th0), r0*np.sin(ph0)*np.sin(th0), r0*np.cos(th0)), axis=0)
#x01 = np.stack((r01*np.cos(ph0)*np.sin(th0), r01*np.sin(ph0)*np.sin(th0), r01*np.cos(th0)), axis=0)

s = np.cos(theta)
br2 = rgi((s, phi), BrF[:,:,0].real, bounds_error=False, fill_value=-bmax)
  
# Project on to sphere:
xx = np.linspace(-1, 1, 256)
y2, z2 = np.meshgrid(xx, xx, indexing='ij')
r2 = np.sqrt(y2**2 + z2**2)
x2 = y2*0
x2[r2 <= 1] = np.sqrt(1.0 - r2[r2 <= 1]**2)
x2, z2 = np.cos(lat0)*x2 - np.sin(lat0)*z2, np.sin(lat0)*x2 + np.cos(lat0)*z2
x2, y2 = np.cos(lon0)*x2 - np.sin(lon0)*y2, np.sin(lon0)*x2 + np.cos(lon0)*y2    
x2[r2 > 1] = 0
y2[r2 > 1] = 0
sp = z2    
php = (np.arctan2(y2, x2) + 2*np.pi) % (2*np.pi)
brp = br2(np.stack((sp, php), axis=2))
brp[r2 > 1] = np.nan

# --------- Plot setup ----------

plt.figure(figsize=(7,7))
ax = plt.subplot(111)
ax.set_facecolor('black')
rmax=2.5

# Plot br on the solar surface
lev = np.linspace(-bmax, bmax, 128)
y2, z2 = np.meshgrid(xx, xx, indexing='ij')  
plt.contourf(y2, z2, brp, lev, cmap='seismic', extend='both')


# ----------- Trace and plot field lines -------------

for j in range(len(r0)):

    """ Open field lines """
    
    # Forward tracing
    xl_f, yl_f, zl_f = rk4(x0[0, j], x0[1, j], x0[2, j], +0.0005)

    # Backward tracing
    xl_b, yl_b, zl_b = rk4(x0[0, j], x0[1, j], x0[2, j], -0.0005)

    # Combine forward and backward traces for plotting
    xl = np.concatenate((xl_b[::-1], xl_f))  # Reverse backward points and join
    yl = np.concatenate((yl_b[::-1], yl_f))
    zl = np.concatenate((zl_b[::-1], zl_f))

    # Convert to correct coordinates if needed
    xl, yl = xl * np.cos(lon0) + yl * np.sin(lon0), -xl * np.sin(lon0) + yl * np.cos(lon0)
    xl, zl = xl * np.cos(lat0) + zl * np.sin(lat0), -xl * np.sin(lat0) + zl * np.cos(lat0)

    rl = np.sqrt(yl**2 + zl**2)
    ind = (rl >= 1) | (xl > 0)

    # Plot in 3D
    ax.plot(yl[ind], zl[ind], linewidth=1.5, color='yellow')


    """ Closed field lines """
    
    # Forward tracing
    #xl_f1, yl_f1, zl_f1 = rk4(x01[0, j], x01[1, j], x01[2, j], +0.0005)

    # Backward tracing
    #xl_b1, yl_b1, zl_b1 = rk4(x01[0, j], x01[1, j], x01[2, j], -0.0005)

    # Combine forward and backward traces for plotting
    #xl1 = np.concatenate((xl_b1[::-1], xl_f1))  # Reverse backward points and join
    #yl1 = np.concatenate((yl_b1[::-1], yl_f1))
    #zl1 = np.concatenate((zl_b1[::-1], zl_f1))

    # Convert to correct coordinates if needed
    #xl1, yl1 = xl1 * np.cos(lon0) + yl1 * np.sin(lon0), -xl1 * np.sin(lon0) + yl1 * np.cos(lon0)
    #xl1, zl1 = xl1 * np.cos(lat0) + zl1 * np.sin(lat0), -xl1 * np.sin(lat0) + zl1 * np.cos(lat0)

    #rl1 = np.sqrt(yl1**2 + zl1**2)
    #ind = (rl1 >= 1) | (xl1 > 0)

    # Plot in 3D
    #ax.plot(yl1[ind], zl1[ind], linewidth=1.5, color='green')

    # Plot the full traced field line
    #ax.plot(xl, yl, zl, 'k')

# ----------- Final plot adjustments -------------

rmax = 2.5
ax.set_xlim(-rmax, rmax)
ax.set_ylim(-rmax, rmax)
ax.text(1.9, -2.25, '(d)', family='serif', color='white', fontsize=20)
#ax.text(1.5, -2.42, '$\lambda = $%4.2f$^\circ$' % (lat0*180/n.pi), family='serif', color='white', fontsize=9) 
plt.tick_params(axis='both', which='both', bottom='off', top='off', \
                left='off', right='off', labelbottom='off', \
                labelleft='off')
#ax.set_title("Field line Plot")
ax.set_xticks([])
ax.set_yticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])
#ax.set_aspect('equal')
#ax.axis('off')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
plt.show()

#plt.savefig("result_93/line00_new_80.png", dpi=300)



