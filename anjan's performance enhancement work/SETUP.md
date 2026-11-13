# Requirements and running the workflow

Commands below use Windows PowerShell from the **repository root**, with your Python virtual environment activated, unless another shell is stated. These instructions apply to this folder, not the separate `my work/` workflows.

## Python packages

Use Python 3.12 (the interpreter used during initial inspection). Install the reconstruction dependencies:

```powershell
python -m pip install -r "anjan's performance enhancement work/requirements.txt"
```

NumPy 2.0 or later is needed for the existing calls to `np.trapezoid`. These are dependency requirements, not a fully tested version lock; the baseline report records the installed versions.

The requirements file also includes psutil for measurement tools and PyVista (which brings VTK) for the optional alpha-analysis scripts. It covers this folder, not Ananya's separate SFT/PFSS dependencies. It is not a version lock; record installed versions with each benchmark.

Those scripts explicitly select Matplotlib's TkAgg backend, so they also need Tcl/Tk and a graphical desktop. Test Tk with `python -m tkinter`; it should open a small window. If unavailable, enable Tcl/Tk in your Python installation rather than installing a package named `tkinter` with pip. PyVista visualisation needs a working graphics environment.

Check the core environment:

```powershell
python -c "import numpy, scipy, matplotlib, astropy; assert hasattr(numpy, 'trapezoid'); print('Core dependencies OK')"
```

## C compiler (required for preprocessing)

`preproc.c` is a required surface-boundary preparation stage. A C compiler is needed even if no optimisation of that stage is planned. The example commands use GCC; Clang or Microsoft C compilers require appropriate compiler-specific commands.

Check availability:

```powershell
gcc --version
```

This searches PATH; failure does not establish that GCC is absent everywhere on the computer. A Python venv does not supply GCC.

For a Windows x64 installation, follow the [official MSYS2 installation instructions](https://www.msys2.org/), using the default `C:\msys64` location. In the **MSYS2 UCRT64 terminal**, install GCC:

```bash
pacman -S mingw-w64-ucrt-x86_64-gcc
gcc --version
```

Back in the **PowerShell terminal with the Python venv activated**, add the compiler and its runtime libraries to PATH for this terminal session:

```powershell
$env:Path = "C:\msys64\ucrt64\bin;$env:Path"
gcc --version
```

Repeat that PATH command in new sessions, or add this directory to your Windows user PATH. Adjust it if MSYS2 is installed elsewhere. PATH must also make the compiler’s companion tools and runtime DLLs available.

The build example uses `-O3` without OpenMP. Enabling OpenMP would be a separate performance experiment.

## Observation inputs

Place these three original inputs in `hmi.sharp_cea_720s.4698.20141022_000000_TAI/` inside this folder:

```text
hmi.sharp_cea_720s.4698.20141022_000000_TAI.Bp.fits
hmi.sharp_cea_720s.4698.20141022_000000_TAI.Bt.fits
hmi.sharp_cea_720s.4698.20141022_000000_TAI.Br.fits
```

They must contain the expected component maps in FITS HDU 1. The filenames and observation are hardcoded in the original extraction script. Synoptic radial-field maps in `my work/hmi_fits_data/` are a different product and cannot replace these three components.

## Planned performance work

The current approach is documented in [README.md](README.md): measure and improve one of the seven stages at a time using fixed inputs, rather than require a full end-to-end baseline first. The old end-to-end testing scripts and report were removed. A focused compilation-only tool is now available: see [step_1_compile/README.md](step_1_compile/README.md). It does not run the remaining workflow. For the next stage, see [step_2_extract/README.md](step_2_extract/README.md) for the extraction-only measurement command and dependencies.

When implementing each stage's tests, compare original/candidate runtime, peak RAM, storage and numerical outputs with matching settings. Sum comparable stage times for an approximate serial total; use the maximum memory peak rather than their sum. Main.py still combines stages 6 and 7; instrumentation or separation is future work.

## Run individual stages

Original scripts resolve data paths relative to the current directory. Enter the observation folder first:

```powershell
Set-Location ".\anjan's performance enhancement work\hmi.sharp_cea_720s.4698.20141022_000000_TAI"
```

Run stages in dependency order (these direct commands write outputs into that observation folder):

```powershell
python fitsdataextraction.py
gcc -O3 preproc.c -lm -o preproc.exe
.\preproc.exe
python plot.py
python weightfunction.py
python Main.py
```

| Script/stage | Python packages | Required data |
| --- | --- | --- |
| `fitsdataextraction.py` | NumPy, SciPy, Matplotlib, Astropy | All three original component FITS files |
| `preproc.c` | None; needs C compiler to build | Extracted `interpolated_dataB*.dat` |
| `plot.py` | NumPy, Matplotlib | `Bfield_processed.dat` and extracted interpolated maps |
| `weightfunction.py` | NumPy, Matplotlib | Hardcoded grid settings; writes `weight_function/W.npy` |
| `Main.py` | NumPy >=2.0, SciPy, Matplotlib | `Preprocessedmagneticfield/{Bx,By,Bz}.npy`, weight volume, local `laplace.py` and `vectormath.py` |
| `HMIdataplot.py` | NumPy, Matplotlib, Astropy | Original Br FITS file |
| `unsignedfluxfromfitsfile.py` | NumPy, Astropy | Original Br FITS file |
| `Freeenergy.py`, `Freeenergyintegrated.py` | NumPy, SciPy (including imported interpolation helper) | Saved potential/reconstructed fields and script-selected checkpoints |
| `alphaparameter.py`, `alphaparameter1.py` | NumPy >=2.0, SciPy, Matplotlib, PyVista; Tcl/Tk | Saved fields and selected checkpoints |
| `plotCurrent.py` | NumPy, Matplotlib | Selected reconstructed checkpoint; `vectormath.py` |
| `plot_dual_fieldlines.py` | NumPy, SciPy, Matplotlib | Saved potential field and selected reconstructed checkpoint |
| `laplace.py`, `vectormath.py`, `changeresolution.py` | NumPy; SciPy additionally for `changeresolution.py` | Helper modules; not independent workflow stages |

Some individual scripts open plot windows. Analysis scripts hardcode different run/checkpoint paths; installing packages alone does not make missing generated results available. Inspect their selected paths before running them. Do not import scripts casually: several execute calculations and write files on import.

## Step 3 baseline

See [step_3_preprocess/README.md](step_3_preprocess/README.md). Supply an existing step 1 executable and the saved step 2 output directory; compilation and extraction are not repeated.

Performance scope: preserve existing mathematics, physics and output behaviour. Baseline runs establish measurements; output-equivalence checks apply once a candidate change exists. See [README.md](README.md#scope-for-this-performance-task).
