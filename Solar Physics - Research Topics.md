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
