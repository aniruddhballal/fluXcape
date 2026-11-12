import numpy as np
import matplotlib.pyplot as plt
import os

# === Load processed field (after preprocessing) ===
data = np.loadtxt("Bfield_processed.dat")  # Columns: i, j, Bx, By, Bz
i = data[:, 0].astype(int)
j = data[:, 1].astype(int)
Bx = data[:, 2]
By = data[:, 3]
Bz = data[:, 4]


# Grid shape
Nx = 300
Ny = 300

# Reshape to 2D
Bx2D = Bx.reshape((Ny, Nx))
print(Bx2D.shape)
By2D = By.reshape((Ny, Nx))
Bz2D = Bz.reshape((Ny, Nx))
output_dir = "Preprocessedmagneticfield"
os.makedirs(output_dir, exist_ok=True)

# Save full 3D magnetic field arrays
np.save(os.path.join(output_dir, 'Bx.npy'), Bx2D.T)
np.save(os.path.join(output_dir, 'By.npy'), By2D.T)
np.save(os.path.join(output_dir, 'Bz.npy'), Bz2D.T)
print("saved")
print(Bx2D.shape)
# === Load original (noisy) magnetic field ===
BxN = np.loadtxt("interpolated_dataBx.dat")[:, 2].reshape((Ny, Nx))
ByN = np.loadtxt("interpolated_dataBy.dat")[:, 2].reshape((Ny, Nx))
BzN = np.loadtxt("interpolated_dataBz.dat")[:, 2].reshape((Ny, Nx))

# === Grid for plotting ===
x = np.arange(Nx)
y = np.arange(Ny)
X, Y = np.meshgrid(x, y)

# === Plot all six fields ===
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fields = [(BxN, 'Original $B_x$'), (ByN, 'Original $B_y$'), (BzN, 'Original $B_z$'),
          (Bx2D, 'Processed $B_x$'), (By2D, 'Processed $B_y$'), (Bz2D, 'Processed $B_z$')]

for ax, (B, title) in zip(axes.flat, fields):
    im = ax.contourf(X, Y, B, levels=300, cmap='seismic')
    fig.colorbar(im, ax=ax, orientation='vertical')
    ax.set_title(title)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_aspect('equal')

plt.tight_layout()
plt.show()

