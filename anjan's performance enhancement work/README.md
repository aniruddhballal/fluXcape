# Task brief: performance enhancement and reusable magnetic-field workflows

## What needs to be achieved

Make Anjan’s magnetic-field reconstruction work quicker to run and easier to reuse. The confirmed starting point is `Main.py` in the supplied observation folder. The possible outcomes are:

1. Accelerate its expensive calculations, using parallel execution where practical.
2. Provide an automated pipeline that saves reusable results, supports selected observations and operations, and avoids unnecessary reruns.
3. Optionally provide a UI for selecting an observation, requesting a supported operation, and viewing its results.

These are complementary options, not a requirement to build all three immediately. No particular hardware, speedup, UI framework, or deployment arrangement has been agreed. This document defines the work; it does not implement it.

## Scope for this performance task

The existing implementation is the behavioural reference. Preserve its mathematics, physics, numerical settings, conventions and output behaviour while improving runtime, RAM or storage efficiency. Scientific review and correction of inherited algorithms are outside this task unless the user explicitly requests them.

For unchanged baseline runs, report timings, memory, generated files and execution success. No candidate equivalence test is due until a candidate exists. Do not repeatedly present inherited scientific questions, existing compiler warnings or existing output conventions as baseline caveats or prerequisites for performance work. Keep historical observations in their reports without treating them as new blockers.

Flag execution failures, missing prerequisites, measurement problems that affect a reported result, and output differences introduced by our changes. Once an optimisation exists, compare it against the original with fixed inputs/settings, including numerical values, layouts and finite/NaN behaviour. Output equivalence checks protect the existing behaviour; they are not a scientific validation project. Do not claim a speedup from an incomplete or unmatched workload.

## Current approach: improve and measure one stage at a time

Record completed experiments, before/after measurements and validation in [PERFORMANCE_LOG.md](PERFORMANCE_LOG.md). It contains the seven-stage tracker and an entry template to append to as work progresses.

Work on one stage at a time, ideally one per day where practical, rather than wait for the entire original workflow to finish. Some stages may take longer; seven stages are not a promise of seven days.

| Stage | Existing file | Work |
| --- | --- | --- |
| 1 | `preproc.c` and a C compiler | Compile the preprocessor. |
| 2 | `fitsdataextraction.py` | Extract and resample the three FITS maps. |
| 3 | Compiled `preproc` executable | Preprocess the extracted surface field. |
| 4 | `plot.py` | Package the bottom boundary into component arrays. |
| 5 | `weightfunction.py` | Generate the 3D taper weights. |
| 6 | First part of `Main.py`, using `laplace.py` | Solve the initial potential field and prepare the field/boundary grids. |
| 7 | Remaining `Main.py`, using `vectormath.py` | Perform WSR reconstruction. |

For each stage:

1. Preserve the original source and a fixed set of required inputs.
2. Measure original runtime, peak RAM and generated storage.
3. Improve a separate candidate implementation.
4. Repeat with identical inputs, scientific settings and hardware; repeat trials and compare medians.
5. Check numerical output equivalence before accepting the improvement. Do not bundle scientific corrections into performance changes.

Reuse saved preparation outputs while studying a downstream stage; do not rerun the earlier stages for every trial. Stages 6 and 7 currently share Main.py and will need instrumentation or separation when we reach them. A compilation-only measurement script is available in [step_1_compile/](step_1_compile/); An extraction-only baseline tool is available in [step_2_extract/](step_2_extract/); Step 3 execution measurement is available in [step_3_preprocess/](step_3_preprocess/); Step 4 measurement is available in [step_4_package/](step_4_package/); Step 5 measurement is available in [step_5_weights/](step_5_weights/); stages 6–7 testing is future work.

For overall statistics, sum comparable completed stage times to estimate serial runtime reduction. **Never add peak RAM:** report per-stage peaks and their maximum. Splitting processes changes memory lifetimes and adds save/load overhead, so this is an estimate rather than an exact measurement of the original monolithic workflow. Compare storage separately without double-counting reused inputs.

A bounded WSR trial can measure a fixed workload or cost per iteration, not total convergence time. Match actual accepted-step counts and account for rejected attempts, checkpoint writes and early termination. Keep grid, tolerances and stopping conditions consistent. Finish with an integration check; a full end-to-end benchmark is optional confirmation when practical.

The earlier five-minute experiment stopped during extraction and never reached Main.py. Its testing scripts/report have been removed. The compilation-only script is now available in step_1_compile/; step 2 now also has an isolated extraction measurement script; remaining tests will be designed when work on each begins.

## Scientific context and terminology

The supplied inputs are three components of a solar surface magnetic-field map. The scripts prepare this two-dimensional boundary, construct an initial three-dimensional potential field, and iteratively reconstruct a nonlinear force-free magnetic field above the surface. Other scripts calculate quantities or produce plots from the result.

The supplied paper, [Wheatland, Sturrock & Roumeliotis (2000), *An Optimization Approach to Reconstructing Force-Free Fields*](Wheatland_2000_ApJ_540_1150.pdf), describes the scientific optimisation method. Its Section 2, equation (5), defines an objective:

```text
L = integral over the volume of
    [ |curl(B) × B|² / |B|² + |div(B)|² ]
```

The two terms measure departures from force-free and divergence-free conditions. Equations (7)–(11) describe an evolution that reduces this objective while holding the boundary fixed. The evolution variable is a numerical relaxation parameter, not an observation timestamp.

`Main.py` labels its loop WSR optimisation and uses a weighted objective, adding a spatial weight `w` and associated derivative terms. The supplied paper explains the underlying unweighted method; it does not by itself establish the provenance or correctness of every weighted term in this implementation.

**Scientific optimisation** means reconstructing the field by reducing `L`. **Performance enhancement** means reducing the implementation’s runtime, memory use, disk use, or repeated work while preserving the original implementation’s output behaviour. The task concerns the latter.

## What exists now

The folder retains one original observation snapshot, preprocessing and reconstruction source, analysis/plotting scripts, and the paper. Generated data, plots, caches and the compiled executable have been removed; the regeneration steps below describe their dependencies. See the folder guide below for the detailed file inventory.

The inferred workflow is:

```text
Selected observation: Bp, Bt, Br FITS files
  → extract and resample the surface maps
  → preprocess and package the boundary
  → construct the initial potential field
  → prepare the reconstruction box and weights
  → reconstruct the 3D field
  → selected analysis or visualisation
  → saved result for later retrieval
```

Important properties of the current code:

- `Main.py` runs one hardcoded observation through several stages in sequence. It does not currently contain a loop over all observation maps. A larger batch workflow may exist elsewhere, but is not established by this folder.
- Most scripts use fixed filenames, grid settings and output locations. Some perform computation and write files immediately when imported.
- The reconstruction uses a 300 × 300 × 150 grid and allows 2,000,001 accepted steps, with additional rejected attempts. One float64 volume occupies 108 MB, and the three field components occupy 324 MB before temporary arrays.
- Prepared boundary arrays, the weight volume and 3D fields must be generated before reconstruction or downstream analysis. No generated field outputs are retained.
- Analysis scripts select different hardcoded reconstruction checkpoints. They do not yet expose a consistent way to select a run.

## Option 1: accelerate the numerical work

“Complete parallelisation” should be investigated, not promised. Both the reconstruction and the initial Jacobi solver depend on previous iterates. Their successive iterations cannot simply be submitted as independent jobs without changing the algorithm.

There are still useful opportunities:

| Opportunity | Practical interpretation |
| --- | --- |
| Work within an iteration | Derivatives, pointwise field operations and reductions may benefit from compiled parallel kernels or a GPU, subject to profiling and available hardware. Spatial derivatives require neighbouring cells; chunking needs boundary handling. |
| Separate observations | Independent observations can run concurrently if memory and storage permit. Each needs isolated outputs. |
| Independent analyses | Analyses of a completed field can run independently when resources permit. |
| Avoid repeated work | Precompute the unchanged weight gradients, reuse buffers and intermediates where valid, and reduce unnecessary copies and file I/O. These improvements do not require parallelism. |
| Initial potential-field solve | Profile the vectorised Jacobi solver actually called by `Main.py`; consider buffer reuse or a more efficient solver while preserving the existing boundary formulation and checking output equivalence. |

NumPy array syntax already expresses much of the work in compiled operations. It is not evidence that the entire script runs in parallel, nor that wrapping operations in Python threads will speed it up. Establish the execution environment and measure before choosing a backend. Limit concurrent runs by measured memory use; more workers can increase memory pressure and make the workflow slower.

Required outcome for this option: a reproducible before/after benchmark, peak memory and output-volume measurements, and numerical comparisons. A reduced grid is suitable for development; useful speed claims also need a representative workload. No speedup target is set yet.

## Option 2: automate stages and reuse results

This is useful even if numerical parallelisation delivers limited gains. Refactor the existing workflow into callable stages with explicit inputs, settings and outputs, then expose a small command-line runner. A UI can use the same runner later.

The runner should allow a user to:

- Select one observation and a supported operation.
- Run only the missing dependencies for that operation. For example, unsigned flux uses the original Br map and does not require a 3D reconstruction; a field-line comparison requires saved initial and reconstructed fields.
- Reuse valid completed outputs, or explicitly request a rerun.
- Precompute selected observations and products in a batch before users request them.
- Retrieve a completed result without starting the calculation again.

Use one result location per observation and run configuration. Record input identities or hashes, relevant parameters, code version, stage status, and output paths in a small manifest. Reuse a result only when its inputs and settings match; a file’s existence alone is insufficient. Downstream stages must use the selected run or checkpoint rather than a hardcoded directory.

Changing a plot’s appearance should reuse the field. Changing reconstruction settings should recompute the reconstruction and its dependent products, while retaining compatible preparation outputs. Weight volumes can be shared when grid and taper settings match. Independent requests for the same calculation should not launch duplicate jobs.

Precomputation trades computation at request time for computation and storage beforehand. Compute a selected set of useful products, rather than every possible combination. Keep a bounded checkpoint policy: the current interval could produce about 3.24 TB of field arrays at the configured maximum, excluding histories and figures. Restarting from a checkpoint requires solver state and settings as well as the field arrays; existing snapshots should not automatically be treated as complete restart records.

Required outcome for this option: requesting the same observation, operation and settings twice reuses the valid result on the second request; changing a relevant setting recomputes the affected stages; separate observations and configurations do not overwrite each other.

## Option 3: a small UI over the pipeline

Build this after the runner and result format are reliable. The initial UI should offer:

1. Choose an available observation, with enough metadata or a preview to identify it.
2. Choose a compatible operation from the existing workflow: view the surface map, calculate unsigned flux, reconstruct the field, analyse energy or alpha, or visualise saved fields.
3. Display whether a matching result is available, missing, running or failed.
4. Show an existing result immediately, or submit the necessary calculation and display its status.
5. View or download the resulting figures and numerical outputs.

“Any operation on any data” is too broad for the initial scope. Offer supported operations for recognised inputs and explain missing dependencies. Long calculations should run separately from the interactive UI. Arbitrary uploads, arbitrary code execution, accounts, cloud hosting and a general scientific workflow editor are not implied by this task.

## Output equivalence when a candidate exists

Measure the unchanged original first. After implementing a candidate, compare its outputs and actual workload with that reference using the same inputs, settings and hardware. Record differences and justified tolerances; retain existing conventions rather than silently correcting them. Scientific boundary formulations, physical accuracy and algorithm changes are not prerequisites for this performance task.

## Suggested order and scope decisions

Start with independent stage benchmarks and fixed fixtures as described above. Improve and validate each stage before moving to the next; do not wait for the original full reconstruction to finish. Build result reuse on the stage interfaces, then consider a UI once the numerical workflow is reliable.

The decisions still needed before implementation are:

- Whether the first deliverable is runtime improvement, a reusable runner, or both; whether the UI is included initially.
- What “map” means in use: an observation snapshot, a component, or a selected region. The working interpretation here is one observation containing the three required components; region selection is not assumed.
- Target machine resources, representative input sizes and the current runtime.
- Which analyses matter first, and the numerical tolerances and stopping criteria Anjan considers acceptable.

The original brief was based on local source inspection and the supplied paper. The stagewise performance approach is documented; numerical optimisations, benchmark tooling and the UI are still pending.

---

# Anjan’s performance enhancement work: folder guide

This guide is based on inspection of the source and the originally supplied array headers. A historical partial workflow benchmark exists; a completed full reconstruction baseline has not been established. Generated artefacts were subsequently removed as documented below; scientific source code and original FITS inputs are unchanged.

## What the work is about

The scripts implement a solar magnetic-field reconstruction workflow: take a measured, two-dimensional surface magnetic field, prepare it, construct an initial three-dimensional field, then iteratively adjust that field and analyse the result.

The observation folder is `hmi.sharp_cea_720s.4698.20141022_000000_TAI`: the filename identifies SHARP patch 4698 and a snapshot at 2014-10-22 00:00:00 TAI. Bx, By and Bz are the three magnetic-field components.

“Optimisation” has two meanings here:

- **The scientific algorithm:** adjust the magnetic field to reduce a mathematical objective measuring departures from force-free and divergence-free conditions.
- **Software performance:** make that calculation use less time, memory and disk space.

The performance enhancement task targets `Main.py`, as confirmed by the user. Mathematical optimisation describes the reconstruction algorithm; performance enhancement describes making its implementation faster and more memory efficient.

## The parts

All source filenames below are inside the observation folder.

| Part | Files | What they do |
| --- | --- | --- |
| 1. Input observation | Three `.Bp.fits`, `.Bt.fits`, `.Br.fits` files; `HMIdataplot.py` | Supply measured field components; the plotting script displays Br. |
| 2. Extract and resample | `fitsdataextraction.py` | Converts Bp to Bx, negative Bt to By, and Br to Bz; writes coordinate/value text files and uses cubic interpolation to make 300 × 300 maps. |
| 3. Prepare the surface boundary | `preproc.c`, compiled `preproc` | Iteratively balances force, torque, fidelity to the input and smoothing terms. Reads `interpolated_dataB*.dat`; writes `Bpre.dat` and `Bfield_processed.dat`. The source credits an adaptation of Wiegelmann’s code by X. Sun. |
| 4. Package the boundary | `plot.py` | Reads the processed text file, reshapes/transposes components, saves `Preprocessedmagneticfield/*.npy`, and compares original and processed maps. Despite its name, it is a data preparation step as well as a plot. |
| 5. Build an initial 3D field | `Main.py` lines 12–94; `laplace.py` | Solves a Cartesian Laplace equation for a scalar potential, differentiates it to form a field, rescales it and interpolates it onto a smaller box. The code calls these outputs PFSS. |
| 6. Prepare weights and boundary | `weightfunction.py`; `Main.py` lines 96–175 | Creates a weight that tapers near the sides/top, and interpolates the observed boundary onto the smaller box. |
| 7. Iteratively reconstruct the field | `Main.py` lines 177–362; `vectormath.py` | Applies the observed bottom boundary, computes curls/divergence, adjusts the 3D field, accepts steps when the objective decreases, and periodically saves results. The loop is labelled WSR optimisation. |
| 8. Analyse results | `Freeenergy.py`, `Freeenergyintegrated.py`, `alphaparameter.py`, `alphaparameter1.py`, `unsignedfluxfromfitsfile.py` | Compare model and potential-field energy; calculate alpha from B·curl(B)/\|B\|² and averages with height; calculate unsigned flux from the original Br FITS file. |
| 9. Visualise results | `plot_dual_fieldlines.py`, `plotCurrent.py` | Compare initial and optimised field lines; generate component and curl-based plots through height slices. |
| Shared helper | `changeresolution.py` | Interpolates saved 3D fields onto a requested box for analysis. |
| Reference | `Wheatland_2000_ApJ_540_1150.pdf` | A supplied paper, separate from the executable workflow; its contents were not reviewed for this guide. |

## Data flow and likely execution order

```text
FITS observations
  → fitsdataextraction.py → interpolated_dataB*.dat
  → preproc.c / preproc → Bfield_processed.dat
  → plot.py → Preprocessedmagneticfield/*.npy
                                      │
weightfunction.py → weight_function/W.npy
                                      │
                                      ▼
Main.py + laplace.py + vectormath.py
  → initial potential-field arrays
  → interpolated boundary and initial field
  → Optimizedmagneticfield/step_*/{Bx,By,Bz,L_values}.npy
  → energy / alpha / field-line / slice analysis
```

This order is inferred from reads and writes, rather than a supplied run script. Scripts use paths relative to the current working directory, so they expect execution from the observation folder. The saved C executable’s build options and correspondence to the source have not been verified.

## Which files probably need performance work?

### First candidate: Main.py, especially the loop starting at line 231

This is the strongest candidate from static inspection, not a measured bottleneck:

- Grid: 300 × 300 × 150 = **13.5 million points**.
- One float64 volume occupies **108 MB**; the three field components alone occupy **324 MB**. Many additional volumes coexist during each step, so working memory can reach several GB.
- Configured for **2,000,001 accepted steps**, with extra attempts when steps are rejected.
- Numerous full-volume gradients, products, copies and intermediate arrays are created on each attempt.
- The gradient of the unchanged weight `w` is recalculated inside every attempt (lines 276–278). This is a clear opportunity to move invariant work outside the loop.
- Saves three complete field volumes every 200 accepted steps. At the configured maximum that means 10,000 periodic checkpoints: **about 3.24 TB for field arrays alone**, excluding histories, figures, initial/final saves and other outputs. This is a configured upper estimate, not existing disk usage.

Start with a small, reproducible case and measure individual stages before choosing an implementation strategy. Candidate changes include reusing buffers/intermediates, precomputing invariants, avoiding duplicate derivative work, a justified convergence stop, and a more selective checkpoint policy. Validate numerical results when changing arithmetic or derivatives.

### Second candidate: laplace.py

`Main.py:34` calls `solve_pfss_cartesian_vectorized`, defined at `laplace.py:85`. It performs up to 100,000 Jacobi iterations, copying a full 3D array each time and creating more full-volume temporaries.

There is also an obvious triple-Python-loop version at `laplace.py:36`, but **Main.py does not call that version**. Accelerating that unused implementation would not accelerate the current main workflow. More efficient solvers or buffer reuse merit investigation once boundary conditions and numerical equivalence are established.

### Third candidate: weightfunction.py

Lines 76–79 execute three nested Python loops over all 13.5 million cells. This is a strong candidate for array-based computation or compilation, preserving the existing taper exactly. However, it is a preparation step whose result can be reused locally; it may not dominate repeated reconstructions.

### Fourth candidate: fitsdataextraction.py

Repeated pixel-by-pixel list building, large text-file writes followed immediately by reads, and three scattered cubic interpolations are plausible preparation bottlenecks. The input is gridded, so an appropriate grid interpolation method and direct in-memory processing merit investigation. Changing the interpolation method changes numerical results and must be checked.

`preproc.c` already contains conditional OpenMP directives. There is no supplied build recipe demonstrating whether the executable enables them. Its actual runtime should be measured before prioritising it.

## Retained inputs and removed generated files

Retained: **15 Python source files, `preproc.c`, three original FITS component files, the supplied paper and documentation**. The folder-local `.gitignore` prevents generated products from being added again.

Removed **26 generated files**, totalling 254,567,866 bytes (about 243 MiB):

| Files | Count | Producer or role |
| --- | --- | --- |
| `outputBx.dat`, `outputBy.dat`, `outputBz.dat` | 3 | FITS extraction outputs from `fitsdataextraction.py`. |
| `interpolated_dataB*.dat` | 3 | Resampling outputs from `fitsdataextraction.py`, consumed by preprocessing. |
| `interpolated_B*.dat` | 3 | Byte-identical duplicates of the corresponding resampling outputs, verified before removal; no separate producer is needed. |
| `Bpre.dat`, `Bfield_processed.dat` | 2 | Outputs from `preproc.c`. |
| `Preprocessedmagneticfield/{Bx,By,Bz}.npy` | 3 | Outputs from `plot.py`, consumed by `Main.py`. |
| `Preprocessedmagneticfield_interpolated/{Bx,By,Bz}.npy` | 3 | Outputs from `Main.py`. |
| `weight_function/W.npy` | 1 | Output from `weightfunction.py`, consumed by `Main.py`. |
| `max_alpha.dat` | 1 | Output from `alphaparameter.py`. |
| `frame_0000.png`, `frame_0001.png`, `alpha_animation.gif` | 3 | Derived visualisation artefacts; their exact frame/animation generator is not supplied. |
| `preproc` | 1 | Compiled executable; rebuild from retained C source. |
| `__pycache__/*.pyc` | 3 | Automatically generated Python bytecode caches. |

Of these, 22 were tracked files; the weight volume and three bytecode caches were already ignored. No original FITS input or scientific source file was deleted. Deletion changes the working tree; previously committed copies remain in Git history.

### Regenerate the calculation inputs

With the scientific Python dependencies installed and a C compiler available, run these commands **from the observation folder**:

```bash
python3 fitsdataextraction.py
cc -O3 preproc.c -lm -o preproc
./preproc
python3 plot.py
python3 weightfunction.py
```

These prepare the boundary arrays and weight volume. `plot.py` and `weightfunction.py` also display plots, so an interactive plotting environment is needed as written. The compiler command is a basic build recipe, not a claim about the original executable’s compiler flags; OpenMP is optional and not enabled by this example.

`python3 Main.py` then constructs the initial 3D field and runs the expensive reconstruction. It is **not** a lightweight preparation command. Analysis scripts require its generated outputs and their hardcoded checkpoint selections must match an available run. These commands describe dependencies for the existing implementation.

## Practical benchmarking constraints

Use fixed input files and matching checkpoint selections. Preserve array orientation, precision, component signs, numerical parameters and stopping behaviour when testing a candidate. Source scripts may execute immediately on import; use isolated runs. Dependencies and build commands are documented in requirements.txt and SETUP.md. Existing scientific choices are kept as supplied, not audited as part of the performance work.

## Where to start reading

1. `plot.py`: understand what a processed 2D boundary looks like.
2. `Main.py`: read it in three sections—initial field (12–94), boundary preparation (96–175), reconstruction (177–362).
3. `vectormath.py`: understand the repeated derivative operations.
4. `laplace.py:85`: inspect the initial-field solver actually used.

The best initial performance investigation is **Main.py together with vectormath.py and the active solver in laplace.py**. The user has confirmed `Main.py` as the target; a runtime profile is still needed to measure its bottlenecks.

## Original FITS inputs are local

The three original FITS files are preserved on this machine but are ignored and untracked by Git. A fresh clone requires separate acquisition of `Bp`, `Bt` and `Br` from `hmi.sharp_cea_720s`, patch 4698, at `2014.10.22_00:00:00_TAI`, with the filenames expected by `fitsdataextraction.py`. No downloader for this set is supplied. The downloaders in `my work/` target different data products and do not fetch these SHARP inputs.
