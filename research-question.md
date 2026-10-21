# Scale-Dependent Magnetic Stability of Confined and Eruptive Solar Events

## Research Question

Which spatial scales and topological features of pre-eruption magnetic fields are necessary to distinguish confined from eruptive events? How robust are the inferred stability diagnostics when small-scale magnetic information is removed?

## Computational Roadmap

The project can begin with observational analysis and simple magnetic-field models, then progress toward numerical simulations if the research question requires them. The languages below are suggestions, not requirements.

| Research stage | Suggested tools/languages | Role of Fortran |
| --- | --- | --- |
| Retrieve and process SDO/HMI magnetograms | Python, SunPy, NumPy | Not needed |
| Decompose magnetic fields by spatial scale; filter and visualize | Python, SciPy, Matplotlib | Not needed |
| Extrapolate a potential coronal field; estimate decay index and critical heights | Python initially | Optional |
| Compare diagnostics for confined vs. eruptive events across resolutions | Python | Optional |
| Evolve coronal fields with magnetofrictional models | Python and/or existing Fortran/C++ simulation code | Useful if the chosen code uses it |
| Investigate full 3D MHD eruption dynamics (advanced extension) | Existing HPC simulation frameworks, potentially Fortran or C++ | Potentially important |

### Possible End-to-End Workflow

```text
Python: observations and preprocessing
    SDO/HMI magnetograms → filtering → magnetic boundary conditions
                         ↓
Python: initial modelling and comparisons
    field extrapolation → stability diagnostics → resolution sensitivity
                         ↓
Optional Fortran/C++: numerical evolution
    magnetofrictional or MHD simulations, if justified by earlier results
                         ↓
Python: analysis and visualization
    compare confined/eruptive cases → plot topology and diagnostics
                         ↓
Interpret findings, test assumptions, and decide the next experiment
```

**Why this order?** Python makes it easier to inspect real observations, reproduce published calculations, and identify which physical quantities change when small-scale magnetic information is removed. A potential-field extrapolation is a useful starting approximation for the *overlying field*, but it cannot model the full current-carrying eruptive structure or establish whether an eruption will occur. More sophisticated magnetofrictional or MHD simulations are possible follow-ups, not prerequisites.

**Where Fortran fits:** Many established numerical astrophysics codes use Fortran. If the project advances to evolving coronal magnetic fields, modifying an existing Fortran code may be more sensible than building a new solver in Python. The actual language should follow the physics question and the code used by the research group—not determine the topic in advance.
