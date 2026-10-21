# Solar Physics - Research Topics & Directions

## Aim and approach
Choose a meaningful solar-physics question that **requires learning the Sun's physics**, not merely applying code or machine learning to solar data. A good project can begin by reproducing published results and grow into an independent investigation.

**Research cycle:** learn fundamentals → read papers → obtain observations → compute/simulate → establish intermediate results → visualize and interpret → test hypotheses → choose the next direction. Negative results and model failures are useful findings.

## Seven candidate topics

1. **Why do some solar flares erupt while others remain confined?** Study magnetic structures and overlying fields to understand why some flares produce coronal mass ejections (CMEs). Compare events and test magnetic indicators. *Learn:* reconnection, magnetic topology, MHD, solar imaging.

2. **Where do solar-wind magnetic switchbacks originate?** Analyze spacecraft magnetic-field measurements to distinguish near-Sun reconnection from wave/turbulence explanations. *Learn:* plasma physics, Alfvén waves, heliospheric turbulence.

3. **Can solar flares be forecast using interpretable physics?** Test whether measured magnetic properties improve flare forecasts over simple baselines; investigate errors rather than relying only on black-box ML. *Learn:* magnetograms, statistics, physical modelling.

4. **Why is the solar corona so hot?** Explore simplified Alfvén-wave or nanoflare heating models and compare their predictions with observations. *Learn:* energy transport, thermodynamics, plasma waves, MHD.

5. **What can surface oscillations reveal about the solar interior?** Extract oscillation frequencies and attempt simplified helioseismic inversions. *Learn:* stellar structure, fluid mechanics, Fourier analysis, inverse problems.

6. **Can we improve predictions of future solar magnetic cycles?** Model surface magnetic-flux transport, polar fields, and how variations in active regions affect later solar cycles. Reproduce historical patterns before exploring parameter sensitivities. *Learn:* solar dynamo theory, flux transport, numerical modelling, uncertainty.

7. **Which spatial scales of solar magnetic fields actually matter?** Decompose magnetograms into large- and small-scale components (e.g., spherical harmonics or wavelets), reconstruct fields at different resolutions, and measure what physical information is lost. *Learn:* solar magnetism, spectral analysis, numerical methods, coronal-field modelling.

## Connection to Dr. Prantika Bhowmik (IISc Bengaluru)

Her published research interests include **solar magnetic fields, solar dynamo and cycle prediction, numerical magnetic-field evolution, and coronal eruptions**. These are *research-alignment judgments*, not claims about her personal favourites or current student openings.

| Topic | Approximate alignment | Reason |
|---|---|---|
| **#7 — Magnetic-field spatial scales** | **Very high** | Closely related to her recent work on spatial structure and magnetic-field representations. |
| **#6 — Solar-cycle prediction** | **Very high** | Central to her established solar-dynamo and forecasting research. |
| **#1 — Eruptive vs. confined events** | **High** | Overlaps with magnetic topology and coronal-eruption modelling. |
| #3 — Physics-informed flare forecasts | Moderate–high | Shares magnetic diagnostics, though flare forecasting is not identical to cycle prediction. |
| #5 — Solar interior / helioseismology | Moderate | Interior dynamics matter to dynamo physics; inversion itself is less direct. |
| #2 — Solar-wind switchbacks | Moderate | Related plasma physics, but less central to her research. |
| #4 — Coronal heating | Lower | Relevant physics, but not a clear primary focus. |

**Research fit is not the same as novelty:** a topic that closely resembles her recent work may already have been substantially addressed. Read the latest papers before choosing a specific claim to test.

## Particularly promising combined project: #7 + #1

**Research question:** *How does the spatial resolution of observed solar magnetic fields affect our ability to model and understand coronal eruptions?*

**Possible investigation:**
1. Learn magnetogram interpretation, magnetic-field topology, and basic MHD.
2. Select well-observed eruptive and confined events from SDO observations.
3. Decompose or progressively downsample their magnetic-field maps.
4. Reconstruct/extrapolate coronal magnetic fields at multiple spatial scales.
5. Compare physically meaningful quantities, magnetic structures, and sensitivity to resolution.
6. Visualize 2D/3D fields, quantify uncertainties, and identify when lost small-scale detail changes conclusions.
7. Use the results to decide whether to pursue particular events, modelling assumptions, or alternative diagnostics.

**Why consider it:** it connects the magnetic-scale analysis associated with #7 to the eruption physics of #1, while demanding substantial learning, computing, and interpretation. It is a **proposed direction**, not a verified unsolved problem or a confirmed priority of Dr. Bhowmik's group.

## Practical starting point

- **Best fit for Dr. Bhowmik's research:** start reading about **#7**, followed by **#6** and **#1**.
- **Best broad physics-first investigation:** **#1**, especially if eruption dynamics excite you.
- **Best synthesis to explore:** **#7 + #1**, after checking existing literature for novelty and feasibility.
- **Public resources:** [SDO data](https://sdo.gsfc.nasa.gov/data/dataaccess.php), [NASA heliophysics](https://science.nasa.gov/heliophysics/), Parker Solar Probe and Solar Orbiter archives, published flare catalogs, and [IISc faculty profile](https://physics.iisc.ac.in/people/prantika-bhowmik/).

**Success need not mean a discovery:** independently reproducing a published result, explaining its assumptions, finding its failure cases, and visualizing the physics would already be worthwhile research training.

## Refined direction after reviewing eruption-related research

**Current preference:** Keep **#1 (why eruptions escape or remain confined)** as the core scientific question. Use **#7 (magnetic spatial scales)** as a method for asking a sharper, potentially decision-useful question; #6 remains a strong alternative but is not the immediate priority.

**Working title:** *Scale-Dependent Magnetic Stability of Confined and Eruptive Solar Events*.

**Sharper research question:** *Which spatial scales and topological features of pre-eruption magnetic fields are necessary to distinguish confined from eruptive events? How robust are the inferred stability diagnostics when small-scale magnetic information is removed?*

### Why this might matter to Dr. Bhowmik's group

Her work on **magnetofrictional simulations of stealth CMEs** connects magnetic evolution, free energy/helicity, and eruption onset; her more recent **mode/spatial-scale analysis** motivates asking how much magnetic detail models need. The practical value would be in **deciding which observations, resolutions, and model assumptions are sufficient**, rather than merely reporting a prediction score. This is a plausible research connection, **not evidence that she has requested this project or that its novelty is established**.

### Decision-useful outputs to aim for

- A measured range of **eruption-sensitive magnetic scales**, with uncertainties.
- **Decay-index / critical-height sensitivity** to magnetogram filtering and resolution.
- Cases where a simplified field reconstruction **changes the inferred stability interpretation**.
- Comparisons showing **when lower-resolution models are adequate** and when more detailed modelling may be justified.
- Reproducible plots, 3D magnetic-field visualizations, and clearly documented failures.

### First concrete experiment

Use a well-studied active region with both confined and eruptive flares (a candidate is **NOAA AR 12673, September 2017**):

1. Read the event studies and retrieve pre-event **SDO/HMI magnetograms**.
2. Construct a **potential-field extrapolation** as an accessible baseline.
3. Filter/downsample the boundary magnetic maps across several scales.
4. Recalculate overlying-field **decay indices and estimated critical heights** for each scale.
5. Plot and compare the results across events; assess uncertainty and model sensitivity.
6. Identify whether a more realistic **non-potential or magnetofrictional model** is needed for the next phase.

**Important limitation:** Potential fields cannot represent the full current-carrying eruptive structure. The first experiment tests the **robustness of a stability diagnostic**, not whether an eruption can actually be simulated or reliably predicted. A difference between events does not itself prove causation.

### Essential literature to check before claiming novelty

- Bhowmik, Yeates & Rice (2022), *Exploring the Origin of Stealth Coronal Mass Ejections with Magnetofrictional Simulations*: https://link.springer.com/article/10.1007/s11207-022-01974-x
- Bhowmik & Prior (2026), *Comparing Magnetic Field Distribution of Active Regions: Part 1 — Methods of Mode Analysis*: https://www.researchgate.net/publication/404480091_Comparing_Magnetic_Field_Distribution_of_Active_Regions_Part_1_Methods_of_Mode_Analysis
- Hore & Bhowmik (2026), *Uncovering the Dominant Spatial Scales of the Sun's Magnetic Field in Solar Cycle 24*: https://arxiv.org/abs/2604.10144

**Next decision:** Review these papers and related confined/eruptive-flare studies, determine what resolution-sensitivity tests have already been done, then choose one narrow, falsifiable hypothesis. The goal is an initial **technical report with reproducible code, figures, one robust or surprising result, and limitations**—something worth discussing with a researcher even if it is not a discovery.
