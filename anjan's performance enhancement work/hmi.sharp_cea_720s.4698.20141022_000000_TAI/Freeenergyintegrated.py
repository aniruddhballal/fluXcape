import numpy as np
from changeresolution import interpolate_pfss_to_box, interpolate_pfss_to_box_full
from scipy.integrate import simpson

# ============================================================
# 2. Interpolate NLFFF and PFSS to SAME uniform grid
# ============================================================
X1, Y1, Z1, _, _, _ = interpolate_pfss_to_box(
    input_dir="Optimizedmagneticfield/step_8600",
    output_dir="Optimizedmagneticfield/step_7104_uniform",
    Nx=300, Ny=300, Nz=61,
    LxL = 250, LxR = 1200,
    LyL = 150, LyR = 650,
    Lz = 50, LxL_I = 50,  LxR_I = 1422, LyL_I = 25, LyR_I = 775, Lz_I = 966
)

_, _, _, _, _, _ = interpolate_pfss_to_box_full(
    input_dir="PFSSmagneticfield_for_uniform_grid/Bfield_full",
    output_dir="PFSSmagneticfield_for_uniform_grid/Bfield_full1",
    Nx=300, Ny=300, Nz=61,
    LxL = 250, LxR = 1200,
    LyL = 150, LyR = 650,
    Lz = 50, LxL_I = 50,  LxR_I = 1422, LyL_I = 25, LyR_I = 775, Lz_I = 966
)

nlff_bz = np.load('Optimizedmagneticfield/step_7104_uniform/Bz.npy')
MaxBz = np.max(abs(nlff_bz))

# ============================================================
# 3. Load NLFFF magnetic field
# ============================================================
nlff_bx = np.load("Optimizedmagneticfield/step_7104_uniform/Bx.npy")
nlff_by = np.load("Optimizedmagneticfield/step_7104_uniform/By.npy")
nlff_bz = np.load("Optimizedmagneticfield/step_7104_uniform/Bz.npy")
print("✓ NLFFF field loaded")

# ============================================================
# 4. Load PFSS magnetic field and normalize consistently
# ============================================================
pfss_bx = np.load("PFSSmagneticfield_for_uniform_grid/Bfield_full1/Bx_full.npy")
pfss_by = np.load("PFSSmagneticfield_for_uniform_grid/Bfield_full1/By_full.npy")
pfss_bz = np.load("PFSSmagneticfield_for_uniform_grid/Bfield_full1/Bz_full.npy")

pfss_norm = np.max(np.abs(pfss_bz))
pfss_bx = (pfss_bx / pfss_norm) * MaxBz
pfss_by = (pfss_by / pfss_norm) * MaxBz
pfss_bz = (pfss_bz / pfss_norm) * MaxBz

print("✓ PFSS field loaded and normalized")

# ============================================================
# 5. Magnetic energy via volume integration (Simpson)
# ============================================================
def magnetic_energy(Bx, By, Bz, x, y, z):
    """
    Compute magnetic energy using Simpson volume integration.
    x, y, z must be 1D arrays.
    """
    energy_density = Bx**2 + By**2 + Bz**2

    # Integrate over z
    Ez = simpson(energy_density, z, axis=2)

    # Integrate over y
    Eyz = simpson(Ez, y, axis=1)

    # Integrate over x
    E = simpson(Eyz, x, axis=0)

    return E


# ============================================================
# 6. Compute energies
# ============================================================
E_nlff = magnetic_energy(nlff_bx, nlff_by, nlff_bz, X1, Y1, Z1)
E_pfss = magnetic_energy(pfss_bx, pfss_by, pfss_bz, X1, Y1, Z1)
E_free = E_nlff - E_pfss

# ============================================================
# 7. Output
# ============================================================
print("\n================ ENERGY RESULTS ================")
print(f"NLFFF magnetic energy : {E_nlff:.6e}")
print(f"PFSS magnetic energy : {E_pfss:.6e}")
print(f"Free magnetic energy : {E_free:.6e}")
print(f"Free energy fraction : {E_free / E_nlff:.4f}")
print("================================================")

