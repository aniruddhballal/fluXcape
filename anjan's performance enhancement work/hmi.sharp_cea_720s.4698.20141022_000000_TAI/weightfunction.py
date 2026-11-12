import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D   # noqa: F401 (import registers 3D)


# Taper width (assumed 0.5 since the box ranges are -0.5 to 0.5 and 0 to 0.5)
N1 = 120
N2 = 150
m = 1/(N2-N1)
NNN = 150
# Cosine tapering profile for 0 <= s <= 1
def cosine_profile(x, dx, x1, NNN = 150 ):
    m = 1/(N2-N1)
    m = m/dx
    x = x
    N = x/dx
    N = N - NNN
    if (-N2<=N<-N1):
        f = 0.5*(1+np.cos(m*np.pi*dx*(N+N1)))
    elif (N1<N<=N2):
        f = 0.5*(1+np.cos(m*np.pi*dx*(N-N1)))
    elif (-N1<=N<=N1):
        f = 1
    else:
        f = 0    
    return f

# Weighting function with tapering on all 5 boundaries (not at z = 0)
def cube_weight_function_zpos(x, y, z, dx, dy, dz, x1, y1, z1, NNN = 150):
    """
    Weight function w(x,y,z) defined on a half-cube domain (z > 0),
    with w = 1 inside an inner cube and a smooth taper in the boundary shell.
    """
    x = x - x1
    y = y - y1
    z = z - z1
    Nx = x/dx
    Ny = y/dy
    Nz = z/dz
    A = np.maximum.reduce([np.abs(Nx-NNN), np.abs(Ny-NNN), np.abs(Nz)])
    if (A == np.abs(Nx-NNN)):
        r_inf = x
        w = cosine_profile(r_inf, dx, x1, NNN)
    elif (A == np.abs(Ny-NNN)):
        r_inf = y
        w = cosine_profile(r_inf, dy, y1, NNN)
    else:
        r_inf = z
        w = cosine_profile(r_inf, dz, z1, 0)
    
    return w

Nx = 300                                # Number of grid points in x direction
Ny = 300                                # Number of grid points in y direction
Nz = 150                                # Number of grid points in z direction
LxL = 50
LxR = 1422                              # Box length in x direction
LyL = 25
LyR = 775                               # Box length in y direction
Lz = 966                                # Box length in z direction
X1 = np.linspace(LxL, LxR, Nx)
Y1 = np.linspace(LyL, LyR, Ny)
Z1 = np.linspace(0, Lz, Nz)
dx = X1[1] - X1[0]
dy = Y1[1] - Y1[0]
dz = Z1[1] - Z1[0]                      # time interval
W = np.zeros((Nx,Ny,Nz))
y = np.zeros(Nx)
y1 = np.zeros(Ny)
y11 = np.zeros(Nz)


for i in range(Nx):
    for j in range(Ny):
        for k in range(Nz):
            W[i,j,k] = cube_weight_function_zpos(X1[i], Y1[j], Z1[k], dx, dy, dz, LxL, LyL, 0, NNN)

output_dir = "weight_function"
os.makedirs(output_dir, exist_ok=True)
np.save(os.path.join(output_dir, 'W.npy'), W)
print("saved")  

Bz_zplane = W[:, :, 75].T               # transpose for plotting
# Plot
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
contour = ax.contourf(X1, Y1, Bz_zplane, zdir='z', offset=0, cmap='seismic', alpha=0.6, levels = 100)
fig.colorbar(contour, ax=ax, shrink=0.8, label='w(x, y, z=0)')

# Axes labels
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('w')
ax.set_title('Weight Function Contour at z = 0')
plt.tight_layout()
plt.show()                  

