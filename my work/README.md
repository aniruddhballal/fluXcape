# Solar magnetic-field research and model development

This folder contains my solar-physics learning notes, data-download tools,
pre-SFT magnetic-field reconstruction, and the beginnings of the
magnetofrictional model I am working toward developing at IISc.

The long-term goal is the **magnetofrictional model** in `magnetofriction/`.
The other folders hold background study, shared observations, and work on
reconstructing a photospheric magnetic-field map before surface flux transport
(SFT). The magnetofrictional solver is still at the planning stage.

## What is here

| Path | Purpose and current state |
|---|---|
| [magnetofriction/](magnetofriction/) | The intended final model: planning files and theory/numerical-method study notes. The solver is not implemented yet. |
| [pre_iisc_self_study/](<pre_iisc_self_study/>) | Personal solar-physics exploration from before joining IISc, undertaken out of interest over roughly one week before work began. These are historical learning notes and early research directions. |
| [pre_sft_reconstruction/](pre_sft_reconstruction/) | The implemented three-map pre-SFT reconstruction and its retained accuracy comparison. |
| [hmi_fits_data/](hmi_fits_data/) | Shared FITS data storage. Currently contains 221 low-resolution HMI synoptic maps in `720x360/`, CR2096–CR2316 inclusive. CR2096 is the preserved historical input; CR2097–CR2316 are the current JSOC archive range. |
| [data_acquisition/](data_acquisition/) | Data-download utilities for HMI synoptic maps and CR2191 full-disk observations. |
| [requirements.txt](requirements.txt) | Python dependency requirements for the FITS tools and pre-SFT reconstruction. This is a `.txt` file, not a `.tsx` file. |

The two HMI downloaders are grouped in `data_acquisition/`.
There are additional Python files inside `pre_sft_reconstruction/` and `magnetofriction/`,
explained below.

## Magnetofrictional model: the development goal

[magnetofriction/](magnetofriction/) is the home for the final model being
planned and developed. Its present files describe intended responsibilities;
they do not yet form a working model:

- [model_input_requirements.md](magnetofriction/model_input_requirements.md) contains a prose checklist
  of anticipated inputs: photospheric radial field, coronal initial field,
  computational grid, boundary conditions, friction coefficient, timesteps,
  and other numerical/physical parameters. It is a Markdown planning document rather than an executable input module.
- [engine.py](magnetofriction/engine.py) is an empty placeholder for the
  modelling engine.
- [model_output.py](magnetofriction/model_output.py) is an empty placeholder
  for output handling.
- [theory-and-numerical-methods/](magnetofriction/theory-and-numerical-methods/)
  holds two study guides: [fundamentals Q&A](magnetofriction/theory-and-numerical-methods/magnetofriction-fundamentals-qa.md)
  and [equations and introductory numerical choices Q&A](magnetofriction/theory-and-numerical-methods/magnetofriction-equations-and-numerical-choices-qa.md).
  They explain the ideas being studied and the implementation questions still
  to resolve; they are not a finalized solver specification.

## Personal study before IISc

[pre_iisc_self_study/](<pre_iisc_self_study/>) preserves the earlier, approximately week-long
period of self-directed exploration:

1. [Layers of the Sun](<pre_iisc_self_study/1. layers of the sun.md>) — introductory
   notes and analogies about the solar interior and atmosphere.
2. [Solar-physics research topics](<pre_iisc_self_study/2. Solar Physics - Research Topics.md>)
   — candidate questions and possible directions for learning and research.
3. [Magnetofriction project and research directions](<pre_iisc_self_study/3. magnetofriction_project_and_research_directions.md>)
   — the recorded direction toward developing a magnetofrictional model,
   with possible subsequent research applications.

These files preserve the learning process and its context. The implementation
status is described in the model-development section above.

## Pre-SFT reconstruction and accuracy comparison

[pre_sft_reconstruction/reconstruct_synoptic_map.py](pre_sft_reconstruction/reconstruct_synoptic_map.py) reconstructs a radial magnetic-field map
from three neighboring HMI synoptic maps:

- CR2190: previous rotation.
- CR2191: central rotation being reconstructed.
- CR2192: next rotation.

It reads those maps from `hmi_fits_data/720x360/`, derives the longitude and
latitude grids from the central FITS header, calculates backward longitude
sampling using a differential-rotation law, and interpolates along longitude
with cubic splines. Neighboring rotations supply boundary data, and missing
source-data gaps are preserved. Latitude is unchanged by the remapping.

The module computes `B_new` when loaded. Running it directly prints field
statistics and then asks for a destination longitude and **colatitude**, both
in degrees, to inspect one remapped sample. It performs reconstruction only;
it does not run the full SFT simulation or the magnetofrictional model, and it
does not automatically save a reconstructed FITS file.

The [pre-SFT ablation justification](pre_sft_reconstruction/pre_sft_ablation_justification.md)
is the single source of truth for the changes relative to Ananya's
implementation. It records the physical rationale, stepwise quantitative
effects, cumulative improvement, validation methodology, masks, limitations,
and the fact that full SFT evolution was not run.

## FITS data and the two download scripts

[hmi_fits_data/](hmi_fits_data/) stores shared data rather than model code or project
documentation. Its `.gitattributes` file marks FITS files as binary so Git
preserves their bytes. The CR2190–2192 maps needed by `pre_sft_reconstruction/reconstruct_synoptic_map.py` remain
in `720x360/`.

### Synoptic-map downloader

[data_acquisition/download_synoptic_maps.py](data_acquisition/download_synoptic_maps.py) checks which Carrington
rotations are available from JSOC and which files are already stored locally.
It offers two resolutions:

| Menu choice | JSOC series | Destination |
|---|---|---|
| `1` | `hmi.mrsynop_small_720s` | `hmi_fits_data/720x360/` |
| `2` | `hmi.synoptic_mr_720s` | `hmi_fits_data/3600x1440/` |

It lists missing rotations, estimates download volume, and asks before
retrieving missing maps. Existing filenames are skipped. Downloaded image
segments are written with JSOC record metadata in their FITS headers, and
shape, rotation, and FITS checksums are verified.

### CR2191 observation downloader

[data_acquisition/download_cr2191_hmi_observations.py](data_acquisition/download_cr2191_hmi_observations.py) retrieves
specific full-disk records at **2017-06-09 10:48, 11:00, and 11:12 TAI**:

- `hmi.M_720s`: LOS magnetograms.
- `hmi.B_720s`: vector-field strength, inclination, azimuth, disambiguation,
  confidence, error/covariance, and processing-status segments.

It writes to `hmi_fits_data/observations/cr2191/`. Raw FITS segments are preserved
unchanged; separate JSON records provide WCS and other metadata. The script
checks record quality, image shape, finite data, and available FITS checksums,
then records SHA-256 hashes and acquisition results in a manifest. It uses
three concurrent download workers and retries failed acquisitions.

These observation files were removed after their analysis was consolidated.
The downloader remains available to acquire them again. Unlike the synoptic
map downloader, this script starts its fixed acquisition without an interactive
confirmation. It downloads data only; it does not run reconstruction,
validation, SFT, or magnetofrictional evolution.

Both downloaders resolve their destinations relative to their own script
locations, independently of the shell's working directory. Network access to
JSOC is needed to use them. Reading the retained comparison report and tables
does not require downloading observations again.

## Dependencies and running the tools

[requirements.txt](requirements.txt) declares Astropy (`>=7.2,<8`) for FITS
handling and SciPy (`>=1.12,<2`) for interpolation. The scripts also use NumPy,
which is installed through these packages' dependencies. This requirements file
covers the current data tools and pre-SFT reconstruction; it is not a finalized
environment for a future magnetofrictional solver or the removed analysis runner.

From the repository root, with a suitable Python environment active:

```bash
python -m pip install -r "my work/requirements.txt"
```

Choose the task to run:

```bash
# Check the archive and optionally download missing synoptic maps.
python "my work/data_acquisition/download_synoptic_maps.py"

# Download the fixed CR2191 full-disk observation set.
python "my work/data_acquisition/download_cr2191_hmi_observations.py"

# Reconstruct CR2191 and inspect a user-selected sample.
python "my work/pre_sft_reconstruction/reconstruct_synoptic_map.py"
```

Use `python3` instead of `python` where that is the interpreter command in your
environment. The reconstruction needs its three existing synoptic input files;
it does not invoke either downloader automatically.

## Local FITS storage and cloning

FITS files are ignored and untracked; the local collection described above remains on the working machine but is not included in a fresh clone. Use the synoptic downloader to acquire the required rotations before running reconstruction (currently CR2190–2192). Use the observation downloader for the fixed CR2191 full-disk records when needed. Fetching newer observations does not replace the specific inputs required to reproduce these experiments.
