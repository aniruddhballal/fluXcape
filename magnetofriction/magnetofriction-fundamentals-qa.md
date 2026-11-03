# Magnetofrictional modelling: fundamentals Q&A

These notes reorganize a study conversation into a learning sequence. They preserve its main questions and explanations, with corrections and clarifications where the conversation simplified the physics. These notes are a study guide, not a complete specification of Prantika's intended model.

**Level and scope:** Foundational and conceptual, with an introduction to the governing equations. The questions build an understanding of the model's purpose, inputs, outputs, boundary conditions and relationship to observations, PFSS and SFT. They do not cover detailed derivations, discretization, solver implementation or rigorous validation; those can be studied in more advanced Q&As.

## 1. The basic idea

### What is magnetofrictional modelling?

Magnetofrictional (MF) modelling is a simplified way to calculate how a magnetic field evolves or relaxes. It is often used for the solar corona, where magnetic forces can dominate other forces in some regions.

Instead of solving the full plasma momentum equation, a basic MF model defines an **artificial velocity** related to the magnetic Lorentz force. This velocity changes the magnetic field so that magnetic stresses can relax toward a force-free state. The magnetic field still evolves according to an induction equation.

The velocity is a modelling device; it should not automatically be interpreted as the actual velocity of the solar plasma. See [Anthony Yeates's introduction](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html).

### How does MF differ from full magnetohydrodynamics (MHD)?

Full MHD evolves a coupled plasma and magnetic field using equations including a momentum equation. MF replaces that momentum calculation with a prescribed relaxation velocity. It generally avoids the cost of resolving the full range of fluid dynamics, but also omits inertia and other physics that may matter.

MF can study slowly driven coronal magnetic configurations, their storage of magnetic stress and some forms of eruptive behaviour. It does **not** faithfully calculate the fast plasma dynamics, acceleration or detailed timing of an eruption as a full dynamical MHD model aims to do. Its agreement with a particular observation needs validation. [Bhowmik, Yeates and Rice's study](https://doi.org/10.1007/s11207-022-01974-x) is an example of eruptive behaviour in MF simulations.

### Is MF only useful at large spatial scales?

No. MF models can be global or focused on an active region; in principle they can resolve smaller magnetic structures if the data, grid and physics allow it. Slow evolution and an approximately force-free environment are important conditions, but they are not the only considerations: resolution, boundary information, numerical diffusion and the processes being studied also matter.

An **active region** is a magnetically concentrated region associated with features such as sunspots. It has photospheric signatures and a three-dimensional magnetic structure extending into the atmosphere. A computational box above it is the chosen model domain, not the definition of an active region.

### What does force-free mean?

The magnetic Lorentz force per unit volume is

$$
\mathbf{f}_{\mathrm L}=\mathbf{J}\times\mathbf{B},
$$

where $\mathbf{B}$ is magnetic field and $\mathbf{J}$ is current density. A force-free magnetic field satisfies $\mathbf{J}\times\mathbf{B}=0$: the current is parallel or antiparallel to the field, or is zero. **Force-free does not mean current-free.**

This is an approximation, not a claim that the real corona has no plasma forces. A model with continuous boundary driving or outflow need not settle into an exactly force-free state.

## 2. Input → engine → output

### What is the main input and output?

For a conventional **3D coronal MF simulation**, the starting state is a magnetic field throughout the modelled coronal volume. The principal result is the evolved 3D magnetic field: a later state, a series of states, or a relaxed configuration. Reduced-dimensional test models use correspondingly smaller domains and fields.

Other outputs can be calculated from the field, such as current, magnetic energy or field-line plots. Which diagnostics are useful depends on the experiment.

### What is the difference between relaxation and driven evolution?

- **Relaxation:** start with a field and evolve it toward an equilibrium under the chosen boundary conditions.
- **Driven evolution:** change the boundary over time, for example to represent motions or emerging magnetic flux at the solar surface. The corona responds as the driving continues.

These are related uses of the same modelling approach. A field that is already in equilibrium and has no driving may barely change.

### What inputs did the conversation identify?

The following eight categories are a useful checklist, **not a universal fixed number**. Depending on the implementation, some are chosen internally or computed from other inputs.

| Category | What it specifies |
| --- | --- |
| Initial magnetic field | The starting field in the modelled volume. |
| Domain | The region of space to simulate. |
| Grid and spatial resolution | How the domain is discretized. |
| Boundary conditions and driving | What happens at the edges and how they may change over time. |
| Magnetofriction coefficient | A parameter or prescription in the artificial velocity. |
| Time step | The model-time increment used by a time integration method; it may be selected automatically. |
| Diffusion or other non-ideal terms | The chosen treatment of magnetic diffusion or related effects, if included. |
| Stopping condition | When to end the calculation, such as after a duration, number of steps or a convergence threshold. |

These are not arbitrary values: they must be consistent with the equations, units, numerical stability, chosen physical assumptions and the question being studied. Further inputs, including output cadence and numerical-method choices, may be needed.

## 3. Domain, grid and time

### What is the difference between the domain and the initial field?

The **domain** says *where* the calculation takes place. The **initial field** says *what magnetic field is present there at the beginning*.

For example, a box might be 100,000 km wide and 50,000 km high. The field gives a strength and direction at each appropriate location in that box. Coordinates in a field data set can implicitly specify the domain, so it may not need to be entered twice—but the domain still exists.

A local patch of data does not by itself define an initial field over the whole global corona. Extending to a global domain requires additional observations or assumptions to fill the rest of the volume.

### What is a grid, and what is spatial resolution?

A grid divides the domain into discrete locations or cells for numerical calculation. Grid spacing indicates how finely it is sampled. Smaller spacing generally allows finer structure to be represented, though a feature typically needs several grid cells to be resolved reliably. The information content of the input data and numerical method also limit effective resolution.

In Cartesian coordinates, spacing might be given in kilometres or megametres. In spherical coordinates, angular spacing can be given in degrees or radians, alongside radial spacing. Angular spacing is not a constant physical distance everywhere: for longitude it also depends on latitude, and physical spacing depends on radius.

At a fixed domain size, increasing the number of grid cells makes the grid finer. A fine grid can also represent large structures, but usually costs more memory and computation. A coarse grid is cheaper but may miss important small features.

### What is a time step?

The time step $\Delta t$ is the increment of **model time** advanced in one numerical update. A fixed time step, for example, advances by the same model-time amount each iteration; an adaptive method changes it as needed. Its value must be suitable for numerical stability and accuracy.

In a relaxation experiment the time coordinate may be artificial. In a driven model, boundary driving can introduce a physical time scale, but the MF relaxation velocity still is not generally a measured plasma velocity. Model time should therefore not automatically be treated as the real timing of rapid solar dynamics.

### How can the simulation know when to stop?

Examples include a fixed number of iterations, a specified elapsed **model** time, or a stopping threshold based on field change, magnetic-energy change or a measure of the Lorentz force. Wall-clock time can be a practical computational limit, but is not the same as model time.

For a relaxation calculation, small field and force residuals can suggest convergence; suitable thresholds and checks must be chosen. A small energy change alone does not prove the field is force-free. Conversely, with continuing driving, diffusion or outflow, an exact stationary force-free state may never be reached. On the Sun, the field and energy can continue to change and the corona need not be exactly force-free.

## 4. Boundary conditions

### What is a boundary condition, and why is it needed?

The domain sets the limits of the calculation. Boundary conditions specify how the variables behave at those limits, so the model can be solved consistently. They constrain the **field or related model variables**, rather than the trajectories of individual particles. The correct conditions depend on the formulation.

For a local box there are lower, upper and side boundaries. The lower boundary can represent the solar surface and may be held fixed or driven; side and upper conditions must also be specified.

### Does a global spherical model have boundaries?

Yes. A full spherical surface has no ordinary east–west side edge because longitude wraps around, but a **3D coronal shell** still has an inner boundary near the Sun's surface and an outer boundary at the model's chosen height. Coordinate singularities or numerical treatments at the poles also need care.

### How does the surface drive the corona?

In the global model described by Yeates, an imposed electric field at the inner boundary represents effects including surface flux transport and emergence. The coronal field then responds. His model additionally uses an outflow near its outer boundary; this is a feature of that implementation, not a requirement of every MF model. [Source: Yeates's model overview](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html).

## 5. What happens inside the engine?

### Is the model one equation with eight inputs and one output?

The black-box picture is useful, but the actual calculation uses **interconnected equations and numerical rules**. Some inputs define the field and domain; others affect the velocity, boundary conditions, time integration or stopping condition. The output of one calculation becomes input to the next.

### What is the basic magnetofrictional update cycle?

For the simple idealized form on Yeates's page:

1. Start with the current field $\mathbf{B}$, including suitable initial and boundary conditions.
2. Calculate current density, in SI units: $\mathbf{J}=\mu_0^{-1}\nabla\times\mathbf{B}$.
3. Calculate the Lorentz force density $\mathbf{J}\times\mathbf{B}$.
4. Set an artificial velocity, for example $\nu\mathbf{u}=\mathbf{J}\times\mathbf{B}$, where $\nu$ is the chosen friction coefficient or prescription.
5. Update the field using the ideal induction equation, $\partial\mathbf{B}/\partial t=\nabla\times(\mathbf{u}\times\mathbf{B})$, with the chosen numerical method and boundary conditions.
6. Repeat, record diagnostics and stop according to the experiment's criterion.

Other formulations scale the friction coefficient differently, evolve a magnetic vector potential, or add diffusion, outflow and boundary-driving terms. The equations above are a conceptual starting point, not a complete implementation. [Source: Yeates's MF overview](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html).

### What is the role of the friction coefficient?

It sets the relationship between the calculated Lorentz force and the artificial velocity. Its units and exact interpretation depend on the chosen form of the velocity equation. It controls relaxation in the model; it is not necessarily a measurement of physical friction in the solar plasma.

### What is diffusivity, and is it always required?

Magnetic diffusivity controls a diffusion term in formulations that include one; ordinary magnetic diffusivity has units of area per time, such as $\mathrm{m^2\,s^{-1}}$. Different models may use other non-ideal terms, including hyperdiffusion, with different parameters and units. Numerical methods can also introduce numerical diffusion.

The idealized equation can be written without an explicit diffusion term, but a practical code may need an explicit treatment for stability or the chosen physics. Diffusion affects topology and can permit reconnection; its effects and assumptions require investigation rather than treating it as an arbitrary tuning value.

### Why does the field need to be divergence-free?

Maxwell's equations require $\nabla\cdot\mathbf{B}=0$: magnetic field has no sources or sinks corresponding to isolated magnetic monopoles in this model. The initial field, boundary conditions and numerical scheme must respect this constraint to an appropriate accuracy. Monitoring divergence is an important numerical check.

## 6. From observations to an initial coronal field

### Can we measure the coronal magnetic field directly?

Some coronal magnetic-field measurements and constraints are possible, but measuring the full 3D field routinely and accurately is difficult. We often use better-observed photospheric magnetic fields together with models and assumptions to estimate the coronal field. A derived field is therefore a model-dependent estimate, not a direct complete 3D measurement.

### How can 2D surface observations produce a 3D initial field?

An **extrapolation** uses magnetic information at a boundary plus assumptions about the coronal field to construct an estimate in the volume above it. The conversation discussed two families: PFSS and NLFFF. The choice changes what currents and structures can be represented and what observations are needed.

The pipeline may be:

```text
Photospheric observation or map
        ↓  assumptions + extrapolation
Estimated initial coronal field
        ↓  MF evolution + boundary conditions
Evolved coronal field and diagnostics
```

The input data can also inform **time-dependent boundary driving**; they are not restricted to constructing the initial field.

### What is PFSS?

**Potential Field Source Surface** (PFSS) modelling estimates a global coronal field under a current-free assumption in its model volume. It uses a photospheric radial field boundary and a source-surface condition, commonly chosen so that the field is radial at an outer spherical surface. The result is an approximate 3D coronal field.

A potential field is force-free because its current is zero, but a general force-free field may have currents. PFSS is useful as a baseline or possible initial state; it does not describe the complete current-carrying, stressed pre-eruption structure.

### What is NLFFF?

A **nonlinear force-free field** (NLFFF) extrapolation attempts to construct a coronal field that can contain electric currents while satisfying the force-free approximation. Standard approaches use photospheric vector magnetic information and assumptions or preprocessing appropriate to the method. They have limitations because the observed photosphere is not perfectly force-free and the data have uncertainty.

The three components commonly expressed in solar spherical coordinates are radial, latitudinal and longitudinal. They are components of **one vector field**, not three separate observing products. One component generally cannot be inferred uniquely from another.

## 7. HMI observations and magnetic components

### What are SDO and HMI?

SDO is the Solar Dynamics Observatory spacecraft; HMI is its Helioseismic and Magnetic Imager instrument. HMI data products include line-of-sight magnetograms, vector magnetic-field products and maps assembled over solar rotation. They differ in what they measure or provide, their coverage and their cadence.

### What is the difference between line-of-sight and vector data?

A **line-of-sight** measurement describes the field component along the observer's viewing direction. A **vector** magnetogram estimates the field's strength and direction, from which three components can be expressed in a chosen coordinate system. Conversion to local radial, latitudinal and longitudinal components involves geometry and processing; uncertainties and the transverse-field ambiguity matter.

The conversation cited commonly used HMI cadences of approximately **45 seconds** for line-of-sight products and **12 minutes** for vector products. A synoptic map is assembled over roughly one solar rotation, about **27 days**; its pixels do not all represent observations made at the same instant. Specific data series and cadences should be checked when choosing a data set.

### Does PFSS require a synoptic map, or can it use other HMI data?

A global PFSS model needs a suitable **global radial-field boundary map**, not one mandatory HMI product. Synoptic maps are a standard source because they provide global coverage assembled over time. Other observations, including vector or line-of-sight products, can contribute to constructing a suitable radial map, with appropriate processing and coverage assumptions. Line-of-sight is not generally identical to radial field; approximating one from the other becomes more problematic away from disk centre.

An individual visible-disk magnetogram alone does not provide a simultaneous measurement of the full solar surface. Local potential extrapolations also exist, but should not be confused automatically with a standard global PFSS setup.

### Does NLFFF have to use HMI's 12-minute vector data?

No. HMI vector magnetograms are one possible source of boundary information, not the only instrument or data product usable for NLFFF. Standard vector-boundary methods need information about all three field components; a line-of-sight magnetogram alone does not generally supply that information. A conventional scalar radial synoptic map alone does not supply the full vector boundary either.

### What is the difference between the data products and the three field components?

The products—line-of-sight magnetogram, vector magnetogram and synoptic map—are **different forms of observational data**. Radial, latitudinal and longitudinal are **directions used to describe a magnetic vector**. A suitable vector product can provide information to derive all three components; the three named products are not themselves those three components.

## 8. Surface flux transport

### What is SFT, and how does it relate to MF?

**Surface Flux Transport** (SFT) models the evolution of magnetic flux on the solar surface, for example under differential rotation, meridional flow, diffusion and prescribed flux emergence. MF models the magnetic field in the corona. An SFT model can contribute to a time-dependent lower-boundary description for a global coronal MF model, but coupling the two requires compatible variables and boundary conditions.

SFT is not mandatory for every MF experiment. A simple relaxation may not use it; another driven model could use a different prescription or observational time series. The precise approach for this project remains to be agreed with Prantika.

### Is SFT just interpolation between two magnetograms?

No. SFT is a forward-evolution model. It can start from an initial surface field and evolve it without a final observation specified in advance. Future evolution depends on its assumed flows, diffusion and new-flux emergence; errors and missing emergence can accumulate over time. It can also be used alongside observations or data assimilation, depending on the system.

### If HMI observations are frequent, why use SFT?

Frequent measurements do not provide perfect, simultaneous coverage of the entire solar surface. SFT can represent physical surface evolution, help bridge observational gaps or evolve a global map under specified assumptions. It is not needed merely because a simulation uses time steps shorter than the observational cadence, and it does not magically determine unobserved flux emergence.

In principle, an SFT model can advance an initial map by a short interval such as five minutes, but it is intended for the slower processes included in its equations; such a short evolution is unlikely to reveal much of that large-scale transport.

### Where does Ananya's code fit?

The supplied [starter pack](../ananya_research_work-main/README.md) contains PFSS and SFT research scripts. Its [SFT instructions](../ananya_research_work-main/SFT/Instruction.txt) describe the intended calculations and experiments involving spatial scales. These are useful background and possible starting material; the exact relationship between them and the MF solver Prantika wants is not yet confirmed.

## 9. What remains to be decided and checked?

### What would a sensible first experiment look like?

Once the project's intended formulation is clear, a simple test could prescribe a known initial field and boundary conditions on a small grid, evolve it, and check whether it behaves as expected. For a relaxation test, use a configuration that is not already in equilibrium. Monitor the field, force residual, energy and numerical divergence, and compare with an analytical or published test where available. This is a proposed learning exercise, not a confirmed assignment.

### Can the earlier eruption and spatial-scale questions use this model?

Possibly. After the model is developed and verified, one could discuss comparing magnetic configurations associated with confined and eruptive events, and then investigating how filtering or reducing boundary-field detail changes relevant diagnostics. Whether the particular model and observations support those questions remains to be established. See [research-question.md](../research-question.md).

### What should be clarified with Prantika?

Ask about the model's intended geometry and scope, whether to extend existing code or start afresh, the preferred language and numerical method, how Ananya's SFT/PFSS work fits, the initial test case, and the intended eventual application. The Python files in this folder are placeholders; the input file currently contains plain-text notes, not runnable Python.

## References

- [Anthony Yeates: Magneto-frictional modelling](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html) — the reference Prantika provided and the source of the basic equations above.
- [Bhowmik, Yeates & Rice (2022): Exploring the Origin of Stealth Coronal Mass Ejections with Magnetofrictional Simulations](https://doi.org/10.1007/s11207-022-01974-x) — an example of MF modelling applied to eruptive magnetic structures.
- [Yeates (2022): On the limitations of magneto-frictional relaxation](https://doi.org/10.1080/03091929.2021.2021197) — analysis of limitations in a test case.
