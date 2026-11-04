# Magnetofrictional modelling: equations and introductory numerical choices Q&A

**Level and scope:** Foundational vector calculus through introductory numerical modelling. This companion to [the fundamentals Q&A](magnetofriction-fundamentals-qa.md) explains the calculations inside the model, connects them to the eight input categories, and records the implementation questions raised at the end of the continued study conversation. It includes worked examples and a forward-Euler update, but does not specify a complete solver, prove numerical stability or choose the project's formulation.

The earlier guide ended with the outline of three stages: calculate magnetic force, calculate an artificial velocity, and update the field. These notes organize the subsequent discussion in a learning sequence. Brief corrections and extensions clarify mathematical assumptions; the conversation's tentative choices are not treated as decisions made by Prantika.

## 1. Understanding the quantities before the equations

### What is the difference between a scalar, a vector and a vector field?

A scalar is a single number at a location, such as temperature. A vector has magnitude and direction and is represented by components in a chosen basis. A vector field assigns a vector to each location.

For example, in Cartesian coordinates:

$$
\mathbf B(x,y,z)=(B_x(x,y,z),B_y(x,y,z),B_z(x,y,z)).
$$

The MF model evolves a magnetic **field**, not just one vector. Calculating spatial derivatives requires knowing how that field varies across the domain.

### Is the magnetic field the only physical field needed to calculate magnetic force density?

In the approximation used here, current density can be obtained from spatial derivatives of the magnetic field. Thus the field supplies the physical information for this calculation, together with a consistent system of units.

On a computer, however, an array of field values is insufficient without its grid, coordinates and relevant boundary information. Those determine how the derivatives are evaluated. A single magnetic vector at an isolated point is insufficient to calculate a curl.

## 2. Del, gradient, divergence, curl and Laplacian

### What is the del operator?

In Cartesian coordinates, the del operator is written

$$
\nabla=
\left(\frac{\partial}{\partial x},
      \frac{\partial}{\partial y},
      \frac{\partial}{\partial z}\right).
$$

It represents spatial differentiation. It is an operator, rather than another measured input or an ordinary numerical vector. Its action depends on the operation and the quantity on which it acts. Its coordinate expressions change in curvilinear systems such as spherical coordinates.

### How are the derivative operations related, and what do they return?

| Operation | Notation | Input | Output at a point |
| --- | --- | --- | --- |
| Gradient | $\nabla f$ | Scalar field | Vector |
| Divergence | $\nabla\cdot\mathbf F$ | Vector field | Scalar |
| Curl | $\nabla\times\mathbf F$ | Vector field | Vector in 3D |
| Scalar Laplacian | $\nabla^2f$ | Scalar field | Scalar |
| Vector Laplacian | $\nabla^2\mathbf F$ | Vector field | Vector |

The conversation's statement that the Laplacian produces a scalar applies to a **scalar input**. The Laplacian of the magnetic field in the induction equation is a vector.

### What do the gradient and divergence look like in Cartesian coordinates?

$$
\nabla f=
\left(\frac{\partial f}{\partial x},
      \frac{\partial f}{\partial y},
      \frac{\partial f}{\partial z}\right),
\qquad
\nabla\cdot\mathbf F=
\frac{\partial F_x}{\partial x}
+\frac{\partial F_y}{\partial y}
+\frac{\partial F_z}{\partial z}.
$$

The gradient points toward the fastest local increase of a scalar field. Divergence measures local net outward flux per unit volume; for a flow, positive and negative divergence correspond to local expansion and convergence.

### What does the curl of the magnetic field look like?

For $\mathbf B=(B_x,B_y,B_z)$ in Cartesian coordinates:

$$
\nabla\times\mathbf B=
\begin{pmatrix}
\dfrac{\partial B_z}{\partial y}-\dfrac{\partial B_y}{\partial z}\\[6pt]
\dfrac{\partial B_x}{\partial z}-\dfrac{\partial B_z}{\partial x}\\[6pt]
\dfrac{\partial B_y}{\partial x}-\dfrac{\partial B_x}{\partial y}
\end{pmatrix}.
$$

The result has three components at each location. For a velocity field, curl describes local circulation and rotation. For the magnetic field, its relationship to current density is what we use below; it does not describe literal spinning of the magnetic field.

### What does the Laplacian mean?

For a scalar in Cartesian coordinates:

$$
\nabla^2f=
\frac{\partial^2 f}{\partial x^2}
+\frac{\partial^2 f}{\partial y^2}
+\frac{\partial^2 f}{\partial z^2}.
$$

It combines curvature in the spatial directions and appears in diffusion equations. In Cartesian coordinates, the vector Laplacian applies this scalar operator to each component:

$$
\nabla^2\mathbf B=
(\nabla^2B_x,\nabla^2B_y,\nabla^2B_z).
$$

In spherical coordinates the basis varies with position, so simply applying a scalar spherical Laplacian separately to each spherical component is not the complete vector Laplacian.

### Can we see numerical input-output examples?

For simple dimensionless examples in the $x,y$ plane, evaluated at $(1,2)$:

| Calculation | Input field | Result across the plane | Result at $(1,2)$ |
| --- | --- | --- | --- |
| Gradient | $f=x^2+y^2$ | $(2x,2y)$ | $(2,4)$ |
| Divergence | $\mathbf F=(x,y)$ | $1+1$ | $2$ |
| Curl | $\mathbf F=(-y,x,0)$, independent of $z$ | $(0,0,1-(-1))$ | $(0,0,2)$ |
| Scalar Laplacian | $f=x^2+y^2$ | $2+2$ | $4$ |

For a vector-Laplacian example in 3D, $\mathbf F=(x^2,y^2,z^2)$ gives $\nabla^2\mathbf F=(2,2,2)$. These are mathematical examples; physical fields and their derivatives also have units.

### What kinds of outputs are possible, and how do we interpret them?

- **Gradient:** any vector, including zero. For example, $(3,0)$ indicates increase toward $+x$, $(-3,0)$ toward $-x$, and $(2,-4)$ toward a combination of $+x$ and $-y$. A zero gradient means no first-order variation at that point, not that the field is constant everywhere.
- **Divergence:** any scalar. Positive means net outward flux locally, negative means inward flux, and zero means no net outward flux. Zero divergence does not imply a uniform field or zero curl.
- **Curl:** any vector in 3D. For an in-plane flow independent of $z$, the only nonzero curl component can be the out-of-plane one: positive $z$ corresponds to counterclockwise circulation viewed from the $+z$ side, negative to clockwise circulation, and zero to no infinitesimal circulation there.
- **Scalar Laplacian:** positive, negative or zero. For a smooth field, its sign describes the leading difference between the nearby isotropic average and the central value: positive corresponds to the average being higher, negative to it being lower. Zero does not mean every nearby value is equal or that the function is constant.

These are categories and examples, not an exhaustive list of numerical values; infinitely many values are possible. For $\nabla^2\mathbf B$, the scalar-Laplacian interpretation can be applied component by component in Cartesian coordinates, but the overall result is a vector.

## 3. Stage 1: magnetic Lorentz force density

### How do we get current density from the magnetic field?

Using Ampere's law while neglecting displacement current, in SI units:

$$
\mathbf J=\frac{\nabla\times\mathbf B}{\mu_0}.
$$

Here $\mathbf B$ is measured in tesla, $\mathbf J$ in amperes per square metre, and $\mu_0$ is the permeability of free space. A code using other units or nondimensional variables may absorb constants into its normalization. Its convention must be checked before copying the equation into code.

### How does current density give magnetic force density?

$$
\mathbf f_{\mathrm L}=\mathbf J\times\mathbf B
=\frac{(\nabla\times\mathbf B)\times\mathbf B}{\mu_0}.
$$

The output is a vector field of force **per unit volume**, measured in $\mathrm{N\,m^{-3}}$ in SI. A force-free magnetic field satisfies $\mathbf J\times\mathbf B=\mathbf0$, including the possibility of nonzero current parallel to the magnetic field. The current and induction relations are part of [Yeates's basic MF formulation](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html).

### Why force density rather than total force?

The relaxation velocity is calculated locally. A total force integrated over a whole volume would lose the distribution of forces needed to evolve the field. Total magnetic force over a volume $V$ is

$$
\mathbf F_{\mathrm L}=\int_V\mathbf f_{\mathrm L}\,\mathrm dV,
$$

which has units of newtons. Different local force densities may cancel in the integral; a small total force therefore does not establish that every location is force-free.

### Is Stage 1 a modelling choice in the same way as the velocity prescription?

Within this magnetic, low-frequency approximation, the relation between field, current and magnetic force density is fixed. The numerical derivatives, variable placement, coordinate system and unit convention still depend on the implementation. Stage 1's conceptual output remains magnetic force density.

## 4. Stage 2: the artificial velocity and friction prescription

### How does force density become an artificial velocity?

Two forms discussed in the conversation were

$$
\mathbf v=\frac{\mathbf f_{\mathrm L}}{\gamma},
\qquad
\mathbf v=\frac{\mathbf f_{\mathrm L}}{\nu B^2}.
$$

The friction parameters are defined differently in these expressions. This is an artificial relaxation rule rather than a solution of the full momentum equation. Its purpose here is to obtain a velocity used in the induction equation. Actual MF models can have additional factors, boundary prescriptions or outflow terms.

The symbols are **nu**, $\nu$, for this friction parameter and **mu naught**, $\mu_0$, for permeability. They are different quantities. Symbols can also be defined differently between papers, so the equation and units matter more than the letter.

### Is $B^2$ a scalar, and how is it calculated?

Here it means the squared magnitude:

$$
B^2=|\mathbf B|^2=\mathbf B\cdot\mathbf B
=B_x^2+B_y^2+B_z^2.
$$

For $\mathbf B=(3,4,0)$, $B^2=9+16=25$. In an orthonormal spherical basis it likewise equals $B_r^2+B_\theta^2+B_\phi^2$. It is not a cross product: $\mathbf B\times\mathbf B=\mathbf0$.

In expressions involving another vector $\mathbf K$, $K^2$ often denotes $\mathbf K\cdot\mathbf K$, but the author's definition should be checked; vector multiplication has no single universal interpretation.

### Can we convert between the two friction parameters?

For equivalent velocities, where the expressions are well defined, choose

$$
\gamma(\mathbf x,t)=\nu(\mathbf x,t)B^2(\mathbf x,t).
$$

A constant $\nu$ therefore generally corresponds to a varying $\gamma$, and a constant $\gamma$ to a varying $\nu$. Choosing a constant for each in two separate runs does not usually produce the same velocity field. Their units also differ because of the $B^2$ factor.

### What happens when $B^2$ is zero or very small?

The expression containing $1/B^2$ requires an explicit treatment at magnetic nulls or weak-field locations. It cannot simply be evaluated at $B=0$. The formulation and any regularization must be specified and tested. [Yeates's analysis of MF limitations](https://arxiv.org/abs/2201.07485) illustrates that relaxation near nulls has physical and mathematical subtleties, beyond avoiding a numerical division by zero.

## 5. Stage 3: calculating the magnetic-field change

### Which equation takes the velocity and updates the field?

The illustrative form discussed in the conversation is

$$
\frac{\partial\mathbf B}{\partial t}
=\nabla\times(\mathbf v\times\mathbf B)
+\eta\nabla^2\mathbf B.
$$

It calculates the **rate of change** of the field. The first term comes from induction with the chosen velocity. The second describes ordinary magnetic diffusion under the assumptions below. Here $\eta$ is magnetic diffusivity, with units $\mathrm{m^2\,s^{-1}}$ in SI; it is not electrical resistivity in ohm metres.

### What assumptions allow the diffusion term to be written as $\eta\nabla^2\mathbf B$?

For scalar ordinary magnetic diffusivity, the resistive contribution can be written

$$
-\nabla\times(\eta\nabla\times\mathbf B).
$$

With constant $\eta$ and $\nabla\cdot\mathbf B=0$, the vector identity for curl of curl reduces this to $+\eta\nabla^2\mathbf B$. Spatially varying diffusivity cannot generally be pulled outside the derivative. Hyperdiffusion is a different prescription and must not be represented by blindly substituting its coefficient into the ordinary Laplacian term.

### Are constant diffusivity and a divergence-free field both optional assumptions?

No. Constant diffusivity is one modelling choice; the physical requirement $\nabla\cdot\mathbf B=0$ remains fundamental. Numerical schemes need to preserve or control this constraint to appropriate accuracy. Selecting a different diffusion prescription does not make magnetic sources or sinks physically permissible.

### How does a rate of change give the next field?

A forward-Euler step uses

$$
\mathbf B^{n+1}
=\mathbf B^n+\Delta t\left(\frac{\partial\mathbf B}{\partial t}\right)^n.
$$

The superscript $n$ labels a time level, not a power. This is a numerical approximation to continuous evolution, with finite-step error. It requires a suitable time step for stability and accuracy. Other integration methods may use multiple intermediate evaluations; forward Euler is the example studied here, not a required project choice.

## 6. Connecting all three stages

### What does the complete illustrative Euler update look like?

With the $\nu B^2$ velocity prescription, ordinary constant diffusivity and the SI definition of current density:

$$
\begin{aligned}
\mathbf J^n &= \frac{\nabla\times\mathbf B^n}{\mu_0},\\
\mathbf f_{\mathrm L}^n &= \mathbf J^n\times\mathbf B^n,\\
\mathbf v^n &= \frac{\mathbf f_{\mathrm L}^n}{\nu|\mathbf B^n|^2},\\
\mathbf B^{n+1} &= \mathbf B^n+\Delta t\left[
\nabla\times(\mathbf v^n\times\mathbf B^n)
+\eta\nabla^2\mathbf B^n\right].
\end{aligned}
$$

Substitution gives the expanded form reached in the conversation:

$$
\boxed{
\mathbf B^{n+1}=\mathbf B^n+\Delta t\left[
\nabla\times\left(
\frac{[(\nabla\times\mathbf B^n)\times\mathbf B^n]\times\mathbf B^n}
{\mu_0\nu|\mathbf B^n|^2}
\right)
+\eta\nabla^2\mathbf B^n
\right].
}
$$

The whole quotient remains **inside the outer curl**. Its denominator contains the spatially varying field magnitude, so it cannot generally be moved outside that derivative. The expression also requires the weak-field treatment discussed above.

This equation combines the chosen example's three stages. It is not a complete numerical algorithm: it still needs a domain, discrete operators, boundary conditions, constraint handling and a stopping rule. Nor does it select the particular MF variant requested for this project.

### Are all the occurrences of $\mathbf B$ the same field within an iteration?

For this explicit Euler update, every occurrence on the right-hand side uses the **current field** $\mathbf B^n$. Different operators act on the same field: it appears in curls, cross products, the squared magnitude and the Laplacian.

| Update | Field used throughout the right-hand side | Result |
| --- | --- | --- |
| First | $\mathbf B^0=\mathbf B_{\mathrm{initial}}$ | $\mathbf B^1$ |
| Second | $\mathbf B^1$ | $\mathbf B^2$ |
| Third | $\mathbf B^2$ | $\mathbf B^3$ |

The original field $\mathbf B^0$ is not reused as the current field forever. This also means an implementation must avoid unintentionally using a mixture of old and already-updated values while calculating a single explicit step. Other time integration schemes have their own rules for intermediate states.

## 7. Where the eight inputs enter the computation

### Why don't the domain, grid, boundaries and stopping rule appear explicitly in the expanded equation?

The written expression describes evolution at the equation level. The numerical model also specifies where it is solved, how derivatives are approximated, how boundary values are obtained and how often the update is repeated.

| Input category | Role in the example |
| --- | --- |
| Initial coronal field | Supplies $\mathbf B^0$; later updates use the previously evolved field. |
| Friction prescription and coefficient | Determine $\mathbf v$, for example through $\nu|\mathbf B|^2$ or $\gamma$. |
| Diffusivity | Enters the selected diffusion term; its form matters as well as its coefficient. |
| Time step | Scales the calculated rate in the Euler update. |
| Grid resolution | Enters the discrete inner curl, outer curl and Laplacian, including appropriate geometric factors. |
| Domain | Defines the locations, extent and geometry over which the field and operators exist. |
| Boundary conditions and driving | Constrain variables at the edges and determine the values or fluxes needed for updates near boundaries. |
| Stopping condition | Controls whether another update is performed; it is a rule surrounding the evolution calculation. |

These are the eight categories from the conversation, not an exhaustive list of every setting a solver may require.

### Can we see grid spacing explicitly in one derivative?

For an interior point of a uniform Cartesian grid, a centred approximation is

$$
\left.\frac{\partial B_y}{\partial x}\right|_{i,j,k}
\approx\frac{B_{y,i+1,j,k}-B_{y,i-1,j,k}}{2\Delta x}.
$$

The field supplies neighbouring values and the grid supplies $\Delta x$. The domain determines which points exist. Near the boundary the method needs a specified stencil or boundary treatment; it cannot assume unavailable neighbours. Spherical operators additionally contain geometric factors, so this Cartesian example cannot be copied unchanged into a spherical solver.

### How can the whole process be represented mathematically?

Let $\mathcal M_h$ denote a complete discrete update on a chosen grid:

$$
\mathbf B_h^{n+1}
=\mathcal M_h\left(\mathbf B_h^n;
\text{friction},\eta,\Delta t,\text{grid},\Omega,\mathrm{BC}\right).
$$

Here $\Omega$ denotes the domain and $\mathrm{BC}$ the boundary conditions and any driving. Initialize from $\mathbf B^0$, apply the chosen boundary treatment, evaluate the update and check the stopping rule. Repeat using the new field when required. The stopping rule is part of the full simulation even though it is outside the local field-update expression.

## 8. Choosing coordinates and interpreting field components

### Must an MF model use Cartesian components?

No. MF can be formulated in Cartesian or spherical coordinates, among other possibilities. The field representation, grid, operators, boundaries and units must be consistent. The earlier conversation's assumption that our project had already chosen a local Cartesian box was premature; its scope remains to be confirmed.

### What are the practical differences between local Cartesian and spherical modelling?

| Aspect | Local Cartesian box | Spherical model |
| --- | --- | --- |
| Typical use | A limited region above an active region | Extended regions or the global corona |
| Surface geometry | Usually approximates the local surface as flat | Represents solar curvature directly |
| Coordinates | Two local horizontal directions and a vertical direction | Radius and two angular directions |
| Numerical considerations | Simpler operator expressions in a uniform box | Geometric factors and possible polar-grid difficulties |
| Important limitation | Flat-surface approximation and surrounding boundary treatment | More involved geometry and grid design |

Neither coordinate system is universally more accurate or inherently always cheaper. Cost and accuracy depend on domain, resolution, numerical method and physical assumptions. Decide the intended physical scope before treating one coordinate system as a project requirement.

### Are $\theta$ and $\phi$ latitude or longitude?

In the spherical convention used here:

- $r$ is radial distance.
- $\theta$ is **colatitude**, measured from the north pole: $0$ at the north pole, $\pi/2$ at the equator and $\pi$ at the south pole.
- $\phi$ is longitude.
- Latitude $\lambda=\pi/2-\theta$, or $90^\circ-\theta$ when using degrees consistently.

The conventional component order is $(B_r,B_\theta,B_\phi)$, matching $(r,\theta,\phi)$. Positive $B_\theta$ points toward increasing colatitude, hence southward. A component positive toward increasing northward latitude has the opposite sign. Coordinate conventions and longitude orientation must always be checked in the data or code.

### What coordinate components do PFSS and NLFFF produce?

That depends on the particular implementation. A global spherical PFSS model commonly provides spherical components. A local Cartesian NLFFF model commonly provides Cartesian components, while spherical NLFFF models also exist. The method's acronym alone does not guarantee an array ordering or basis; inspect the actual output definition.

### How would we use spherical output in a Cartesian model?

We would need to transform the **vector components**, place them in the required coordinate frame and sample them onto the target grid. A conversion to Sun-centred Cartesian components is not automatically a conversion to the local horizontal/vertical axes of an active-region box. Interpolation and basis rotation are distinct steps, and the transferred field must still meet the numerical constraints of the target solver.

Similarly, matching spherical components is not sufficient for direct use if coordinate orientation, sampling, units or variable placement differ. The compatibility of actual inputs must be established rather than inferred from names such as $B_x$ or $B_r$.

## 9. The seven implementation questions raised at the end

### Which choices were still open?

These retain the seven questions' original order, with mathematical notation clarified from the voice transcription. They record decisions to discuss with seniors, not approved answers.

| # | Question | What needs to be specified |
| --- | --- | --- |
| 1 | Should the MF model use Cartesian or spherical coordinates? | Coordinate frame, field basis and compatible numerical operators. |
| 2 | Which artificial friction prescription should be used? | For example, $\mathbf f_{\mathrm L}/\gamma$ or $\mathbf f_{\mathrm L}/(\nu B^2)$; coefficient definitions, normalization and weak-field treatment. |
| 3 | Should the first domain cover an active region or the global corona? | Physical scope, extent and boundaries of the initial modelling problem. |
| 4 | Should diffusion be included, and in what form? | Ideal evolution, ordinary diffusion or another non-ideal prescription, with appropriate parameters. |
| 5 | Should SFT supply surface evolution, or should a different observational driving prescription be used? | How time-dependent photospheric information is constructed and coupled to the corona. |
| 6 | Should PFSS or NLFFF construct the initial coronal field? | Which initial-field assumptions and data suit the intended experiment. |
| 7 | What time step should the model use? | A fixed or adaptive step compatible with the chosen grid, equations and integration scheme. |

### How can these be grouped for discussion?

The conversation grouped them into three broad categories:

- **Geometry and domain:** questions 1 and 3.
- **Physics and modelling assumptions:** questions 2, 4 and 6.
- **Data and numerical practicalities:** questions 5 and 7.

The categories overlap. For example, PFSS/NLFFF is also a data decision; SFT contains physical assumptions; and the stable time step depends on the physics and grid. The list is a discussion aid rather than a set of independent switches.

### Is there a useful order for resolving them?

First establish the intended physical scope and whether the new MF work should extend the inherited code. Then choose compatible geometry, initialization, driving and coronal evolution equations. The time-step strategy follows from those choices and the numerical method. A simple verification exercise may have a different scope from the eventual research simulation.

### Does the earlier eruption question determine these choices already?

No. Developing the MF model is the immediate project. Distinguishing confined and eruptive events, and investigating sensitivity to magnetic spatial scales, remain possible follow-on applications in [research-question.md](../research-question.md). They should not be used to silently fix an active-region domain before Prantika has confirmed the assignment.

## Further reading and related material

- [Magnetofriction fundamentals Q&A](magnetofriction-fundamentals-qa.md) — the preceding conceptual guide, including observations, PFSS, NLFFF and SFT.
- [Anthony Yeates: Magneto-frictional modelling](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html) — the starting model reference supplied by Prantika.
- [Yeates (2022): On the limitations of magneto-frictional relaxation](https://arxiv.org/abs/2201.07485) — a study of relaxation and its limitations near magnetic nulls.
- [Ananya's starter-pack description](../ananya_research_work-main/README.md) — existing PFSS and SFT material; its exact role in the new solver remains to be agreed.
