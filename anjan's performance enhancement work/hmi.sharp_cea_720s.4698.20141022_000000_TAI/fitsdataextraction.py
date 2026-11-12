# In this code i am extracting fits file data to dat and text file

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
from scipy.interpolate import griddata


# Load the FITS file
filename = "hmi.sharp_cea_720s.4698.20141022_000000_TAI.Bp.fits"

with fits.open(filename) as hdul:
    data = hdul[1].data  # Extract data from HDU 1

# Get dimensions
rows, cols = data.shape
x_values = np.arange(cols)  # X-axis (longitude pixels)
y_values = np.arange(rows)  # Y-axis (latitude pixels)

# Convert to (X, Y, Magnetic Field) format
output_data = []
for i in range(rows):
    for j in range(cols):
        output_data.append([x_values[j], y_values[i], data[i, j]])

# Convert list to NumPy array
output_data = np.array(output_data)

# Save as .dat file
np.savetxt("outputBx.dat", output_data, fmt="%.6f", delimiter=" ", header="X Y Magnetic_Field", comments="")

print("Conversion complete Data saved as outputBx.dat .")

# Load data from file (assuming three columns: x, y, magnetic_field)
filename = "outputBx.dat"
data = np.loadtxt(filename, skiprows=1)  # Adjust delimiter if needed

# Extract x, y, and magnetic field values
x, y, magnetic_field = data[:, 0], data[:, 1], data[:, 2]

# Create a finer grid for interpolation
x_grid = np.linspace(min(x), max(x), 300)  # Adjust resolution as needed
y_grid = np.linspace(min(y), max(y), 300)
X, Y = np.meshgrid(x_grid, y_grid)

# Perform interpolation
Z = griddata((x, y), magnetic_field, (X, Y), method='cubic')  # 'cubic' for smooth interpolation

# Save interpolated data to a new file
output_filename = "interpolated_dataBx.dat"
with open(output_filename, "w") as f:
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            if not np.isnan(Z[i, j]):  # Avoid saving NaN values
                f.write(f"{X[i, j]:.6f}\t{Y[i, j]:.6f}\t{Z[i, j]:.6f}\n")
print(f"Interpolated data saved to {output_filename}")

# Load the FITS file
filename = "hmi.sharp_cea_720s.4698.20141022_000000_TAI.Bt.fits"

with fits.open(filename) as hdul:
    data = hdul[1].data  # Extract data from HDU 1

# Get dimensions
rows, cols = data.shape
x_values = np.arange(cols)  # X-axis (longitude pixels)
y_values = np.arange(rows)  # Y-axis (latitude pixels)

# Convert to (X, Y, Magnetic Field) format
output_data = []
for i in range(rows):
    for j in range(cols):
        output_data.append([x_values[j], y_values[i], -data[i, j]])

# Convert list to NumPy array
output_data = np.array(output_data)

# Save as .dat file
np.savetxt("outputBy.dat", output_data, fmt="%.6f", delimiter=" ", header="X Y Magnetic_Field", comments="")

print("Conversion complete Data saved as outputBy.dat .")

# Load data from file (assuming three columns: x, y, magnetic_field)
filename = "outputBy.dat"
data = np.loadtxt(filename, skiprows=1)  # Adjust delimiter if needed

# Extract x, y, and magnetic field values
x, y, magnetic_field = data[:, 0], data[:, 1], data[:, 2]

# Create a finer grid for interpolation
x_grid = np.linspace(min(x), max(x), 300)  # Adjust resolution as needed
y_grid = np.linspace(min(y), max(y), 300)
X, Y = np.meshgrid(x_grid, y_grid)

# Perform interpolation
Z = griddata((x, y), magnetic_field, (X, Y), method='cubic')  # 'cubic' for smooth interpolation

# Save interpolated data to a new file
output_filename = "interpolated_dataBy.dat"
with open(output_filename, "w") as f:
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            if not np.isnan(Z[i, j]):  # Avoid saving NaN values
                f.write(f"{X[i, j]:.6f}\t{Y[i, j]:.6f}\t{Z[i, j]:.6f}\n")
print(f"Interpolated data saved to {output_filename}")

# Load the FITS file
filename = "hmi.sharp_cea_720s.4698.20141022_000000_TAI.Br.fits"

with fits.open(filename) as hdul:
    data = hdul[1].data  # Extract data from HDU 1

# Get dimensions
rows, cols = data.shape
x_values = np.arange(cols)  # X-axis (longitude pixels)
y_values = np.arange(rows)  # Y-axis (latitude pixels)

# Convert to (X, Y, Magnetic Field) format
output_data = []
for i in range(rows):
    for j in range(cols):
        output_data.append([x_values[j], y_values[i], data[i, j]])

# Convert list to NumPy array
output_data = np.array(output_data)

# Save as .dat file
np.savetxt("outputBz.dat", output_data, fmt="%.6f", delimiter=" ", header="X Y Magnetic_Field", comments="")

print("Conversion complete Data saved as outputBz.dat .")

# Load data from file (assuming three columns: x, y, magnetic_field)
filename = "outputBz.dat"
data = np.loadtxt(filename, skiprows=1)  # Adjust delimiter if needed

# Extract x, y, and magnetic field values
x, y, magnetic_field = data[:, 0], data[:, 1], data[:, 2]

# Create a finer grid for interpolation
x_grid = np.linspace(min(x), max(x), 300)  # Adjust resolution as needed
y_grid = np.linspace(min(y), max(y), 300)
X, Y = np.meshgrid(x_grid, y_grid)

# Perform interpolation
Z = griddata((x, y), magnetic_field, (X, Y), method='cubic')  # 'cubic' for smooth interpolation

# Save interpolated data to a new file
output_filename = "interpolated_dataBz.dat"
with open(output_filename, "w") as f:
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            if not np.isnan(Z[i, j]):  # Avoid saving NaN values
                f.write(f"{X[i, j]:.6f}\t{Y[i, j]:.6f}\t{Z[i, j]:.6f}\n")
print(f"Interpolated data saved to {output_filename}")

