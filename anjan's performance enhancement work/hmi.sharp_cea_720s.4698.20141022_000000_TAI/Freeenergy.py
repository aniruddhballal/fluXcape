import numpy as np
from changeresolution import interpolate_pfss_to_box, interpolate_pfss_to_box_full

X1, Y1, Z1, Bx, By, Bz = interpolate_pfss_to_box(
    input_dir="Optimizedmagneticfield/step_6000",
    output_dir="Optimizedmagneticfield/step_uniform",
    Nx=300, Ny=300, Nz=150,
    LxL = 188, LxR = 1284,
    LyL = 100, LyR = 700,
    Lz = 300, LxL_I = 50,  LxR_I = 1422, LyL_I = 25, LyR_I = 775, Lz_I = 966
)

X1, Y1, Z1, Bx, By, Bz = interpolate_pfss_to_box_full(
    input_dir="PFSSmagneticfield_for_uniform_grid/Bfield_full",
    output_dir="PFSSmagneticfield_for_uniform_grid/Bfield_full1",
    Nx=300, Ny=300, Nz=150,
    LxL = 188, LxR = 1284,
    LyL = 100, LyR = 700,
    Lz = 300, LxL_I = 50,  LxR_I = 1422, LyL_I = 25, LyR_I = 775, Lz_I = 966
)
nlff_bz = np.load('Optimizedmagneticfield/step_uniform/Bz.npy')
MaxBz = np.max(abs(nlff_bz))
def calculate_magnetic_free_energy(nlff_bx: np.ndarray, nlff_by: np.ndarray, nlff_bz: np.ndarray,
                                   potential_bx: np.ndarray, potential_by: np.ndarray, potential_bz: np.ndarray) -> float:
    """
    Calculates the magnetic free energy from 3D numpy arrays representing
    the NLFF and potential magnetic fields.

    The free energy is the difference between the total energy of the NLFF field
    and the total energy of the potential field. The total energy is calculated
    by integrating (summing in a discretized grid) the magnetic energy density
    (proportional to B^2) over the entire volume.

    Args:
        nlff_bx, nlff_by, nlff_bz: numpy arrays for the x, y, z components of the NLFF field.
        potential_bx, potential_by, potential_bz: numpy arrays for the x, y, z components
                                                    of the potential field.

    Returns:
        The calculated magnetic free energy as a float.
    """
    # Calculate the total magnetic energy for the NLFF field.
    # E_total ~ sum(B^2) over the entire volume
    # We use a numpy sum to efficiently add up the squared magnitudes at each point.
    energy_nlff = np.sum(nlff_bx**2 + nlff_by**2 + nlff_bz**2)
    print("NLFF energy: ", energy_nlff)

    # Calculate the total magnetic energy for the potential field.
    energy_potential = np.sum(potential_bx**2 + potential_by**2 + potential_bz**2)
    print("PFSS energy: ", energy_potential)
    # Magnetic free energy is the difference between the two total energies.
    free_energy = energy_nlff - energy_potential

    return free_energy

# --- Main script execution ---

if __name__ == "__main__":
    print("Starting NLFF Magnetic Parameter Calculation...")

    # Load the NLFF magnetic field data from the numpy files provided.
    # This data represents a 3D grid of magnetic field components.
    try:
        nlff_bx = np.load('Optimizedmagneticfield/step_uniform/Bx.npy')
        nlff_by = np.load('Optimizedmagneticfield/step_uniform/By.npy')
        nlff_bz = np.load('Optimizedmagneticfield/step_uniform/Bz.npy')
        print("NLFF magnetic field data loaded successfully.")
    except FileNotFoundError:
        print("Error: Could not find the NLFF numpy files. Please check the file paths.")
        # Create dummy data for demonstration if files are not found
        nlff_bx = np.zeros((10, 10, 10))
        nlff_by = np.zeros((10, 10, 10))
        nlff_bz = np.zeros((10, 10, 10))

    # Load the potential (PFSS) magnetic field data from the numpy files.
    try:
        potential_bx = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full1/Bx_full.npy')
        potential_by = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full1/By_full.npy')
        potential_bz = np.load('PFSSmagneticfield_for_uniform_grid/Bfield_full1/Bz_full.npy')
        potential_bx = (potential_bx/np.max(abs(potential_bz)))*MaxBz
        potential_by = (potential_by/np.max(abs(potential_bz)))*MaxBz
        potential_bz = (potential_bz/np.max(abs(potential_bz)))*MaxBz
        print("Potential (PFSS) magnetic field data loaded successfully.")
    except FileNotFoundError:
        print("Error: Could not find the potential (PFSS) numpy files. Please check the file paths.")
        # Create dummy data for demonstration if files are not found
        shape = nlff_bx.shape
        potential_bx = np.zeros(shape)
        potential_by = np.zeros(shape)
        potential_bz = np.zeros(shape)


    # Perform the calculation
    calculated_free_energy = calculate_magnetic_free_energy(
        nlff_bx, nlff_by, nlff_bz,
        potential_bx, potential_by, potential_bz
    )

    # Print the result to the console
    print("\nCalculation complete.")
    print(f"Simulated Magnetic Free Energy: {calculated_free_energy} units")
    print("\nThis value represents the excess energy stored in the NLFF field.")

