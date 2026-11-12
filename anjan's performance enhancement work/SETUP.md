# Requirements and running the workflow

Commands below use Windows PowerShell from the **repository root**, with your Python virtual environment activated, unless another shell is stated. These instructions apply to this folder, not the separate `my work/` workflows.

## Python packages

Use Python 3.12 (the interpreter used during initial inspection). Install the reconstruction and baseline dependencies:

```powershell
python -m pip install "numpy>=2.0" scipy matplotlib astropy psutil
```

NumPy 2.0 or later is needed for the existing calls to `np.trapezoid`. These are dependency requirements, not a fully tested version lock; the baseline report records the installed versions.

For the alpha analysis scripts, also install PyVista (which brings VTK):

```powershell
python -m pip install pyvista
```

Those scripts explicitly select Matplotlib's TkAgg backend, so they also need Tcl/Tk and a graphical desktop. Test Tk with `python -m tkinter`; it should open a small window. If unavailable, enable Tcl/Tk in your Python installation rather than installing a package named `tkinter` with pip. PyVista visualisation needs a working graphics environment.

Check the core environment:

```powershell
python -c "import numpy, scipy, matplotlib, astropy, psutil; assert hasattr(numpy, 'trapezoid'); print('Core dependencies OK')"
```

## C compiler (required for preprocessing)

`preproc.c` is a required surface-boundary preparation stage. A C compiler is needed even if no optimisation of that stage is planned. The baseline runner expects GCC or a GCC-compatible Clang command; Microsoft `cl.exe` uses different flags and is not supported by this runner.

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

Repeat that PATH command in new sessions, or add this directory to your Windows user PATH. Adjust it if MSYS2 is installed elsewhere. Supplying `--compiler` locates the executable, but PATH may still be needed for its companion tools and runtime DLLs.

The baseline compiles with `-O3` and without OpenMP. OpenMP is not a prerequisite for the current baseline; enabling it would be a separate performance experiment.

## Observation inputs

Place these three original inputs in `hmi.sharp_cea_720s.4698.20141022_000000_TAI/` inside this folder, or pass their containing directory to the runner with `--input-dir`:

```text
hmi.sharp_cea_720s.4698.20141022_000000_TAI.Bp.fits
hmi.sharp_cea_720s.4698.20141022_000000_TAI.Bt.fits
hmi.sharp_cea_720s.4698.20141022_000000_TAI.Br.fits
```

They must contain the expected component maps in FITS HDU 1. The filenames and observation are hardcoded in the original extraction script. Synoptic radial-field maps in `my work/hmi_fits_data/` are a different product and cannot replace these three components.

## Run the baseline logger

From the repo root, first check prerequisites:

```powershell
python ".\anjan's performance enhancement work\run_baseline.py" --check-only
```

Then run the full workflow:

```powershell
python ".\anjan's performance enhancement work\run_baseline.py"
```

Optional explicit locations:

```powershell
python ".\anjan's performance enhancement work\run_baseline.py" --input-dir "D:\path\to\SHARP_inputs" --compiler "C:\msys64\ucrt64\bin\gcc.exe"
```

For a bounded initial measurement, add `--max-seconds 600`. A bounded or interrupted run is a **partial measurement**, not a full runtime baseline. Ctrl+C stops the run and preserves its report and generated outputs.

Each invocation writes a new `baseline_<timestamp>.md` beside the runner. Actual execution also creates an isolated `baseline_run_<timestamp>/` with copied sources/inputs, stage logs, sampled `metrics.csv`, and calculated products. Originals are not overwritten. Preflight-only runs create a report without calculating fields. The runner does not install packages or download data.

Measured scope: compilation, FITS extraction, C preprocessing, boundary packaging, weight generation, then `Main.py` (initial potential field plus reconstruction). Optional energy/alpha/visualisation analyses are excluded. Initial-field and reconstruction timings are currently combined under the Main stage. Python, package versions, source/input hashes, CPU time, sampled RAM, process I/O, and storage usage are recorded. This logger records a baseline; it does not yet automate comparisons between runs.

The unchanged settings use a 300 × 300 × 150 grid and permit 2,000,001 accepted reconstruction steps. Working memory can reach multiple GB; the maximum checkpoint configuration can produce roughly **3.24 TB** of field arrays. Choose a time limit for an exploratory run if completion time/storage is unknown. Exact peak RAM and total runtime have not yet been established.

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
| `run_baseline.py` | Core reconstruction packages plus psutil | Original sources, all three FITS files, GCC-compatible compiler |

Some individual scripts open plot windows. Analysis scripts hardcode different run/checkpoint paths; installing packages alone does not make missing generated results available. Inspect their selected paths before running them. When analysing an isolated baseline, its generated fields live in the baseline run directory, not the original observation directory. Do not import scripts casually: several execute calculations and write files on import.
