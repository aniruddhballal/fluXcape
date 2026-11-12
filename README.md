# fluXcape

This repository collects solar magnetic-field research code, the work of understanding and checking that code, and development toward a magnetofrictional model of the solar corona.

The main research direction is to **continue from Ananya’s PFSS and surface flux transport work toward a magnetofrictional model that she had not started**. Continuing that work means understanding its mathematical basis, checking what the implementation actually does, testing its assumptions and numerical behaviour, and deciding what to retain or change before building on it. A separate task concerns improving the performance and usability of Anjan’s magnetic-field reconstruction code.

## The three work areas

| Folder | Role | Current state |
| --- | --- | --- |
| [ananya's research work/](<ananya's research work/>) | Inherited PFSS, surface flux transport and spatial-scale experiments, plus an implementation review. | Research scripts are present. Required original FITS inputs and generated model archives are absent. No magnetofrictional solver is supplied here. |
| [my work/](<my work/>) | Study, acquisition of observations, review and validation of the inherited foundations, and preparation for the magnetofrictional model. | Pre-SFT reconstruction is implemented and an accuracy comparison is retained. Magnetofriction remains at the study/planning stage; its engine and output modules are empty. |
| [anjan's performance enhancement work/](<anjan's performance enhancement work/>) | A separate performance task centred on Anjan’s `Main.py`: acceleration, reusable processing and potentially a UI. | Supplied code and preparation data have been inspected and the task documented. Performance changes, a reusable runner and a UI have not been implemented. |

The intended scientific relationship is:

```text
Observed surface magnetic maps
  → reconstruct and check an initial surface map
  → surface flux transport: evolve the surface boundary
  → potential-field modelling: a possible initial coronal field
  → magnetofrictional modelling: develop and validate coronal evolution
```

This is a development direction, not an already connected execution pipeline. Ananya’s SFT and PFSS scripts currently run independently; the repository has no implemented SFT→PFSS→magnetofriction coupling. The exact MF geometry, formulation and boundary-driving interface remain to be decided.

## What the different models do here

| Term | Meaning in this repository |
| --- | --- |
| **Pre-SFT reconstruction** | Remaps neighbouring synoptic rotations to estimate a surface field at a reference time. It is preparation, not the SFT time integration. |
| **SFT — surface flux transport** | Evolves the radial surface field using prescribed differential rotation, meridional flow, diffusion and scheduled active-region sources. |
| **PFSS — potential field source surface** | Ananya’s spherical-harmonic coronal extrapolation with a source-surface boundary. It provides a potential-field model rather than the intended MF evolution. |
| **MF — magnetofriction** | The planned coronal model, using an artificial relaxation velocity and an induction equation. The study notes discuss its assumptions and numerical choices; a solver has not been written. |
| **WSR scientific optimisation** | Anjan’s iterative reconstruction method, labelled WSR in his code. It reduces departures from force-free and divergence-free conditions. It is a separate implementation from the planned MF model. |
| **Performance enhancement** | Making Anjan’s implementation faster and less wasteful, or reusing completed work. This is distinct from the scientific optimisation algorithm. |

## Ananya’s inherited research

[Her original README](<ananya's research work/README.md>) describes the supplied work and recommends her paper, *Uncovering the Dominant Spatial Scales of the Sun’s Magnetic Field in Solar Cycle 24*, for PFSS and Anthony Yeates’s thesis for SFT. Those references are pointers in the inherited documentation; their full texts are not included in this folder.

### PFSS files

| File | Purpose |
| --- | --- |
| [PFSS/CR_2193_80_full.py](<ananya's research work/PFSS/CR_2193_80_full.py>) | Reads a CR2193 map, computes spherical-harmonic coefficients through degree 80, reconstructs surface/coronal fields and diagnostics, and writes field arrays to an NPZ archive. Uses Joblib parallel work for parts of the harmonic calculations. |
| [PFSS/jul80_field_line.py](<ananya's research work/PFSS/jul80_field_line.py>) | Reads `output_fields_93_80_full.npz`, interpolates field components, traces field lines with RK4, and plots them. |

The expected `CR_2193.fits` and generated NPZ archive are absent. These scripts have not been established as a validated source of initial conditions for the future MF engine.

### SFT files

| File | Purpose |
| --- | --- |
| [SFT/Instruction.txt](<ananya's research work/SFT/Instruction.txt>) | Ananya’s explanation of the solver, source catalogue and spatial-scale experiments. Some filenames mentioned in the instructions differ from those actually supplied. |
| [SFT/SFT.py](<ananya's research work/SFT/SFT.py>) | Main surface solver. Constructs an initial map from three MDI-labelled rotations, initializes staggered surface vector potentials, advances them with advection/diffusion, inserts analytic bipolar regions, and saves selected radial-field snapshots. Contains Numba parallel spatial kernels. |
| [SFT/main.py](<ananya's research work/SFT/main.py>) | Catalogue-generation driver adapted from Anthony Yeates’s SHARP/BMR tools. Selects observation dates, processes regions and writes an emergence catalogue. Despite its name, it is not the main SFT integration script. |
| [SFT/sharptools.py](<ananya's research work/SFT/sharptools.py>) | Observational acquisition/remapping, bipole fitting, flux balancing, repeat-region handling and catalogue generation. Includes an auxiliary `SFT1` transport implementation used in catalogue processing. |
| [SFT/bmrsharps_evol.txt](<ananya's research work/SFT/bmrsharps_evol.txt>) | Supplied observation-derived emergence catalogue. Its header lists 1,149 regions over 2009–2020. It is input data, not solver output from the current configuration. |
| [SFT/test_p_diffusion.py](<ananya's research work/SFT/test_p_diffusion.py>) | Diffusion-only experiment comparing harmonic power from a degree-120 map with a degree-18 reference. |
| [SFT/test_p_advection_diffusion.py](<ananya's research work/SFT/test_p_advection_diffusion.py>) | Power-based comparison with advection and diffusion for the detailed map and advection for the reference. |
| [SFT/test_length_zero_line_diffusion.py](<ananya's research work/SFT/test_length_zero_line_diffusion.py>) | Diffusion experiment using polarity-inversion-line length as the comparison criterion, with two length estimators. |
| [SFT/test_zero_length_line_advection_diffusion.py](<ananya's research work/SFT/test_zero_length_line_advection_diffusion.py>) | Related polarity-inversion-line experiment including advection. |

The four `test_*.py` files are substantial research experiments with computation and plotting, not a conventional automated unit-test suite. They expect `2013_10_15.fits`, which is absent. The main solver expects `CR_MDI2095.fits` through `CR_MDI2097.fits`, also absent. HMI maps in `my work/` are not automatically interchangeable with these files.

### Understanding and reviewing the inherited implementation

[sft-implementation-and-magnetogram-handling-review.md](<ananya's research work/sft-implementation-and-magnetogram-handling-review.md>) records what the source actually implements: equations, inputs, grids, emergence handling, outputs and outstanding questions. It is a read-only implementation review, not evidence that the full model was executed or validated.

The important distinctions and checks are:

- Observations initialize the field and supply parameters for new bipolar sources. The main loop does **not** continually replace or blend its predicted pixels with observed magnetograms.
- The initialization appears to pass latitude to a rotation function otherwise used with colatitude. This is a concrete issue to resolve before adopting the initial map.
- Missing-data treatment, polar-boundary transport, source-flux conservation, numerical stability and resolution convergence need checking.
- The source catalogue, regeneration settings, initial data and figure labels do not describe one consistent reproduction configuration.
- The configured SFT run spans 3,500 days at a 60-second step. Saved snapshots are sparse and lack explicit timestamps in the main archive.

These findings guide what to investigate or change; they do not amount to rejecting all of the inherited work.

## My continuation toward magnetofriction

[my work/README.md](<my work/README.md>) contains the detailed local guide and run instructions. The work so far combines understanding the science with checking the preparation that the future model may depend on.

### Data tools and retained observations

| Path | Purpose |
| --- | --- |
| [download_synoptic_maps.py](<my work/download_synoptic_maps.py>) | Checks the JSOC archive and downloads missing HMI radial synoptic maps, offering 720×360 and 3600×1440 products. Prompts before downloading. |
| [download_cr2191_hmi_observations.py](<my work/download_cr2191_hmi_observations.py>) | Acquires the fixed CR2191 comparison observations at 2017-06-09 10:48, 11:00 and 11:12 TAI, preserving raw segments and recording metadata/hashes. Uses three download workers; starts its acquisition without an interactive confirmation. |
| [hmi_fits_data/720x360/](<my work/hmi_fits_data/720x360/>) | Local collection of 221 HMI radial synoptic maps, CR2096–CR2316 inclusive. Filenames identify each Carrington rotation; these files share the same data role. |
| [hmi_fits_data/.gitattributes](<my work/hmi_fits_data/.gitattributes>) | Marks FITS files as binary to preserve their bytes. |
| [requirements.txt](<my work/requirements.txt>) | Astropy and SciPy requirements for the current data tools and reconstruction, with NumPy available through dependencies. It is not a complete environment specification for all inherited code or the future MF solver. |

The full-disk CR2191 observations were removed after the comparison was consolidated. Their downloader remains; the retained results can be read without reacquiring them.

### Implemented pre-SFT reconstruction

[pre_sft_reconstruction/reconstruct_synoptic_map.py](<my work/pre_sft_reconstruction/reconstruct_synoptic_map.py>) reads CR2190, CR2191 and CR2192 from the shared data folder. It derives coordinates from FITS metadata, calculates a backward longitude sampling relation using differential rotation, and interpolates along longitude while preserving missing-data gaps. Latitude is unchanged by this remapping.

This is a specific continuation of the initial-map question in Ananya’s SFT code. It is not yet wired into her complete SFT solver. The module calculates `B_new` when loaded; running it directly prints statistics and accepts a longitude/colatitude sample query. It does not automatically write a reconstructed FITS file.

### Retained accuracy comparison

The [comparison folder](<my work/pre_sft_reconstruction/pre_sft_reconstruction_accuracy_comparison/>) holds:

| File or group | Purpose |
| --- | --- |
| [pre_sft_reconstruction_accuracy_report.md](<my work/pre_sft_reconstruction/pre_sft_reconstruction_accuracy_comparison/pre_sft_reconstruction_accuracy_report.md>) | Methodology, synthetic and observational comparisons, adaptations of Ananya’s reconstruction, numerical findings and limitations. Also records historical paths and the completed cleanup. |
| `synthetic_and_observational_accuracy_metrics.csv` | 342 metric rows from the primary comparison and noise/evolution checks. |
| `spatial_averaging_sensitivity_4x4/accuracy_metrics_4x4_spatial_averaging.csv` | 330 rows for the spatial-averaging sensitivity comparison. |
| `synthetic_{smooth,fine_structure,bipolar}_field_reconstruction_nominal_rotation.png` | Three synthetic-case illustrations; the report links the actual filenames. |
| `vector_radial_field_reconstruction_and_errors_2017-06-09_1100_TAI.png` | Vector-derived radial-field comparison and error maps. |
| `los_radial_field_proxy_reconstruction_and_errors_2017-06-09_1100_TAI.png` | Line-of-sight-derived radial proxy comparison and error maps. |
| `observed_vs_reconstructed_radial_field_scatter_2017-06-09_1100_TAI.png` | Observational scatter comparison. |
| `observational_rmse_comparison_across_observation_times.png` | RMSE comparison over the three observation times. |

There are **672 retained numerical rows and seven plots**. The report supports the revised reconstruction under its specified ideal synthetic model. Observational improvements over the unchanged synoptic map are small and vary with region and metric. Ananya’s literal global-spline reconstruction produces no finite output on these NaN-containing inputs; finite observational comparisons therefore use explicitly documented adaptations. This validates neither the entire inherited SFT model nor a future MF solver. The full SFT evolution was not run in that comparison, and the cleaned archive does not retain the analysis runner or all raw/intermediate data needed for an immediate rerun.

### Magnetofriction planning and study

| File | Purpose and status |
| --- | --- |
| [magnetofriction/model_input_requirements.md](<my work/magnetofriction/model_input_requirements.md>) | Prose checklist of anticipated surface/coronal inputs, grid, boundaries, friction and numerical parameters. |
| [magnetofriction/engine.py](<my work/magnetofriction/engine.py>) | Empty placeholder for the future solver. |
| [magnetofriction/model_output.py](<my work/magnetofriction/model_output.py>) | Empty placeholder for output handling. |
| [magnetofriction/theory-and-numerical-methods/magnetofriction-fundamentals-qa.md](<my work/magnetofriction/theory-and-numerical-methods/magnetofriction-fundamentals-qa.md>) | Study guide covering purpose, inputs, outputs, boundaries, observations and relationships to PFSS/SFT. |
| [magnetofriction/theory-and-numerical-methods/magnetofriction-equations-and-numerical-choices-qa.md](<my work/magnetofriction/theory-and-numerical-methods/magnetofriction-equations-and-numerical-choices-qa.md>) | Study of derivatives, force, artificial velocity, induction, units, coordinate choices and unresolved implementation decisions. It is not a finalized solver specification. |

The next research work is to finish checking the foundations, agree the intended MF formulation and interfaces, implement a controlled initial solver, and validate it before coupling the stages. Studying confined/eruptive events or the importance of magnetic spatial scales is recorded as a possible later application, not a completed result or fixed initial deliverable.

### Earlier personal study

`my work/pre_iisc_self_study/` preserves the learning period before joining IISc:

- `1. layers of the sun.md`: introductory descriptions and analogies.
- `2. Solar Physics - Research Topics.md`: explored questions, research alignment and possible directions.
- `3. magnetofriction_project_and_research_directions.md`: the MF development direction and possible subsequent applications.

These are historical learning notes, not authoritative specifications or validated research conclusions.

## Anjan’s separate performance task

[The folder README](<anjan's performance enhancement work/README.md>) contains the task definition, parallelisation limits, proposed reusable stages, optional UI scope and detailed code review. The folder was previously called `anjan's optimisation work`; old IDE tabs may still show that path.

The observation subfolder `hmi.sharp_cea_720s.4698.20141022_000000_TAI/` contains:

| Files or group | Role |
| --- | --- |
| Three `.Bp.fits`, `.Bt.fits`, `.Br.fits` files | Input vector-field observation for SHARP patch 4698 at 2014-10-22 00:00:00 TAI. |
| `fitsdataextraction.py`, `HMIdataplot.py` | Extract/resample components and view the original radial map. |
| `preproc.c`, compiled `preproc` | Surface-boundary preprocessing source and executable. |
| `plot.py` | Packages processed fields into NumPy arrays and compares them with the input maps. |
| `Main.py` | Initial Cartesian potential-field calculation, grid/boundary preparation and iterative 3D WSR reconstruction. Confirmed target of the performance task. |
| `laplace.py`, `vectormath.py`, `weightfunction.py` | Potential solver, curl/divergence helpers and boundary-taper weights. |
| `changeresolution.py` | Interpolates saved 3D fields onto an analysis box. |
| `Freeenergy.py`, `Freeenergyintegrated.py` | Energy comparisons using sums or volume integration. |
| `alphaparameter.py`, `alphaparameter1.py` | Related alpha-parameter analyses and plots. |
| `unsignedfluxfromfitsfile.py` | Unsigned-flux calculation from the radial FITS map. |
| `plot_dual_fieldlines.py`, `plotCurrent.py` | Initial/reconstructed field-line comparisons and slice/curl-based visualisation. |
| `outputB*.dat` | Extracted original component maps as coordinate/value text. |
| `interpolated_dataB*.dat`, `interpolated_B*.dat` | Resampled text maps; each corresponding pair is byte-identical in this snapshot. |
| `Bpre.dat`, `Bfield_processed.dat` | Preprocessing outputs in different text layouts. |
| `Preprocessedmagneticfield/`, `Preprocessedmagneticfield_interpolated/` | Prepared 300×300 component arrays before/after box interpolation. |
| `weight_function/W.npy` | Generated 300×300×150 weighting volume, retained locally and excluded from Git. Regenerate with `weightfunction.py` from the observation folder. |
| `max_alpha.dat`, `frame_0000.png`, `frame_0001.png`, `alpha_animation.gif` | Retained analysis/visualisation artefacts; these alone do not demonstrate a completed reconstruction run. |

`Wheatland_2000_ApJ_540_1150.pdf` is the supplied paper explaining the underlying scientific optimisation method. The initial and reconstructed 3D-field directories referenced by downstream scripts are absent.

Successive solver iterations depend on previous states. Work within an iteration and independent observations may be parallelised; a useful complementary deliverable is to save and reuse completed stages so a user can select an observation and operation without repeating the entire computation. A UI would sit on that reusable workflow. These remain proposed deliverables.

## Root files, execution and repository state

- `allinonesunvisual.md` currently contains one external solar-visualisation URL. It is a bookmark, not a local application.
- `.gitignore` excludes `.venv/`, Python caches/bytecode, generated products and FITS observation files. FITS data are kept locally, not distributed with a clone. Previously committed data remain in Git history.
- `.git/` holds repository metadata. `__pycache__/` folders contain generated interpreter caches rather than research source or results.

There is no single command that runs this whole repository. For the current data tools, follow [my work/README.md](<my work/README.md>); inherited research scripts need their own inputs, dependencies and configuration. Many scripts execute substantial work when imported. Paths, dates and output locations should be checked before running them.

This overview is based on the current files, source inspection and retained reports. Preparing it did not run the SFT, PFSS, WSR or MF simulations or independently reproduce the archived numerical comparisons.

## Acquiring observation inputs after cloning

FITS files are local data and are not tracked by Git. The inventories above describe the local research data and expected inputs, not files guaranteed to arrive with a clone.

- Run `my work/download_synoptic_maps.py` and select the low-resolution product to acquire the synoptic maps. The current reconstruction specifically needs CR2190, CR2191 and CR2192; newer maps are not substitutes for that experiment. The downloader checks the archive and offers missing maps, rather than automatically running an analysis.
- Run `my work/download_cr2191_hmi_observations.py` to reacquire its fixed June 2017 full-disk observation records if repeating the observational comparison. The cleaned comparison archive does not include its original analysis runner.
- Anjan’s three SHARP files require separate acquisition: `hmi.sharp_cea_720s`, patch 4698, `2014.10.22_00:00:00_TAI`, segments `Bp`, `Bt`, `Br`. There is no downloader for that set in this repository. Existing local copies are preserved.
- Ananya’s original MDI-labelled maps, CR2193 PFSS input and dated experiment map also require separate acquisition and provenance checks; the supplied scripts do not provide one automatic downloader for all of them.

These scripts require archive availability and suitable dependencies. Retrieving the latest observations alone does not reproduce the historical experiments.
