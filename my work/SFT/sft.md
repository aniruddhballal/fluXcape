# SFT learning handoff — discussion, equations, implementation, and current understanding

> **Purpose:** This document preserves the *breadth and depth* of the user's discussion about Ananya's solar surface flux transport (SFT) implementation, so a Codex agent can understand the user's current conceptual and computational knowledge before continuing work. It is **not** a claim that every discussed derivation or line of source code has been independently validated. It records resolved concepts, formulas, examples, indexing choices, previous misunderstandings, and implementation details worth verifying.
>
> **Primary source inspected:** `SFT.py` (638 lines, supplied in this conversation). Line references in this document refer to this version. The previously mentioned `sft-implementation-and-magnetogram-handling-review.md` was **not available to inspect while compiling this handoff**. It is a separate review, and its conclusions should **not** be inferred from this document. Before making claims about findings in that review, Codex must read it directly.
>
> **Scope:** Core SFT simulation and the 3-Carrington-map pre-SFT correction, grid geometry, vector potential initialization, numerical evolution, radial-field recovery, BMR emergence, time integration, and discussion-level comprehension. Related PFSS use and the wider pre-eruption magnetic stability project are context, not a substitute for reading those implementations.

---

## 0. Agent-facing executive summary: what the user currently knows

The user can reason through the overall flow:

1. **Input magnetograms:** a solar photospheric radial-field map assembled using earlier/central/later Carrington rotations.
2. **Pre-SFT map preparation:** latitude/longitude coordinates, reference longitude and time offset, differential-rotation-based *longitude lookup*, selection between previous/current/next maps, interpolation to one corrected field map. The user specifically separates **moving the sampling location** from **actually evolving magnetic-field strengths through time**.
3. **SFT grid:** a 2D rectangular *Mercator computational grid* that represents the spherical solar surface, with constant grid increments in transformed x/y coordinates but nonuniform physical latitudinal increments.
4. **Staggered placement:** radial magnetic field `Bz` at cell centers; vector potential `Ax` on horizontal (north/south) edges; `Ay` on vertical (east/west) edges.
5. **Initial magnetic vector potential:** choose `Ay = 0` as an initial gauge/construction; integrate `Bz` to obtain `Ax`; reconstruct `Bz = (curl A)_r` to verify.
6. **Evolution:** compute current `Bz` from `Ax,Ay`, update `Ax` and `Ay` by a 60-second forward-Euler step including solar meridional flow, differential rotation, and diffusion, then enforce boundary conditions; inject new emerging bipolar regions on catalog dates.
7. **Reconstruction:** any time `Ax` and `Ay` are known, use finite differences of the **2 neighboring `Ay` edges** and **2 neighboring `Ax` edges** to obtain **1 `Bz` value** per cell; the actual spherical/Mercator expression requires `sin(theta)` metric factors.
8. **Numbers:** unpadded `Ax`: 360×417, `Ay`: 361×416, `Bz`: 360×416, total 149,760 cell-centered `Bz` calculations per full rebuild. `dx = dy = 1` in *dimensionless grid units* and `delta_rad = π/180` in the physical angular conversion; the product `dx*delta_rad = dy*delta_rad = π/180` radians is constant in every cell.

**Strongest recently demonstrated conceptual understanding:** The user correctly recognized that equal distances on a Mercator diagram **do not** imply equal changes in actual latitude, while `delta x` corresponds to a fixed longitudinal angular step. They initially inferred that the `delta y` substituted into each `Bz` formula should vary with location, but explicitly resolved that it remains constant **because it is a Mercator-coordinate increment**, while the latitude variation enters through the spherical metric factors.

**Current preferred teaching mode:** very short, factual, staged answers, expanding only one equation component at a time. For documentation, however, the user explicitly requests maximum detail and comprehensive topic coverage. Preserve their chosen notation where helpful; never conflate their pedagogical half-index scheme with the actual Python indices.

---

## 1. Research motivation, architecture, and the SFT–PFSS distinction

### 1.1 Broader scientific interest

The research theme is **scale-dependent magnetic stability of confined and eruptive solar events**, asking which scales and topological features of *pre-eruption magnetic fields* are needed to distinguish confined versus eruptive flares, and how stable inferred diagnostics are when small-scale magnetic information is removed. The user's immediate focus here is **understanding the SFT computational machinery**, not yet implementing the full stability study.

Broad physics concepts discussed in associated learning: solar magnetic fields, surface magnetograms, photospheric radial magnetic field, differential rotation, meridional flow, diffusion, emergence of bipolar magnetic regions (BMRs), vector potential, spherical geometry, Mercator grids, and eventual coronal-field modeling.

### 1.2 Separate roles of components

| Component | Basic purpose | Input/output in this context | Relationship to current study |
|---|---|---|---|
| Photospheric magnetic observations | Measure magnetic field on the solar surface | FITS synoptic magnetic maps / radial field estimates | Starting observational constraint |
| **Pre-SFT map preparation** | Construct a single map by spatially re-sampling 3 Carrington-rotation maps at longitude locations adjusted for rotation | Previous, current, next CR maps → a corrected input map | A one-time preprocessing stage; **not the complete SFT PDE evolution** |
| **SFT** | Evolve the photospheric magnetic field over time under prescribed surface transport and new flux emergence | Initial surface radial field plus velocities, diffusion, BMR data → evolving surface `Bz` | Surface evolution and boundary conditions |
| **PFSS** | Model coronal potential magnetic structure from a photospheric boundary | Surface radial field → coronal extrapolation | A distinct downstream model, not a term in the SFT update |
| Spatial-scale experiments | Smooth/remove magnetic structure at selected scales and compare diagnostics | Maps/fields at different spatial resolutions | Proposed extension of the research |

The user separately asked whether SFT might be used to make a temporally coherent photosphere from a synoptic map and was surprised that Ananya's approach appeared to use SFT differently. The critical distinction settled in discussion is: **pre-SFT CR merging / longitude remapping is distinct from actual time stepping of the photospheric flux distribution.** Any broader conclusion about Ananya's *intent* or the quality of preprocessing must be checked against the separate review and source.

---

## 2. Three Carrington rotation maps and pre-SFT correction

### 2.1 Why 3 maps?

A Carrington synoptic map samples different longitudes at different observation times over roughly one solar rotation (~27.2753 days). The map is registered to a longitude coordinate system; that **does not mean each pixel was observed simultaneously**. Near the two longitudinal edges, original observation times can differ from the reference time by ~13.6 days (idealized half-rotation argument).

This motivated the user's question: does SFT fix the fact that one end of a synoptic map is old and the other end is more recent? The discussion separated:

- **Longitude remapping:** determine which longitude's recorded field value to sample in the previous/current/next synoptic FITS map. This is a *spatial lookup* corrected for rotation.
- **Physical temporal evolution:** advance the surface field using a transport equation that responds to shear, meridional motion, diffusion, and emergence. That is the **SFT integration**.

The earlier user phrasing was approximately “central longitude φ = 180° is today; one side is older, the other newer.” This is a useful conceptual reference for interpreting `phi_ref`, but it is not proof that every pixel has a measured observation timestamp exactly symmetric about that longitude.

### 2.2 Which FITS files the supplied code reads

`SFT.py:70–80`:

```python
B_prev = fits.open('CR_MDI2095.fits')[0].data
B_curr = fits.open('CR_MDI2096.fits')[0].data
B_next = fits.open('CR_MDI2097.fits')[0].data
```

These are **MDI** maps in the supplied code, not HMI files. HMI synoptic maps were discussed at a general conceptual level, and HMI would be a different dataset/input choice. The code comments identify day 0 as 2010-05-06 (CR 2096).

### 2.3 Coordinate assignment and longitude correction

Code definitions (`SFT.py:83–117`):

- Reference longitude `phi_ref = π` radians = 180°.
- Reference angular rate `omega_0 = 13.2°/day` in rad/s.
- Original longitude array `phi_original = linspace(0, 2π, number_of_columns)`.
- Original meridional coordinate `theta_original = arcsin(linspace(-1,1, number_of_rows))` (see **coordinate convention caution** below).
- Spline interpolation created individually for previous, current and next CR maps.

For every location, the code computes:

$$
\boxed{\Delta t = \frac{\phi-\phi_{\rm ref}}{\omega_0}}
$$

and then:

$$
\boxed{\phi' = \phi+\frac{\omega(\vartheta)}{\omega_0}(\phi-\phi_{\rm ref})
      =\phi+\omega(\vartheta)\Delta t}
$$

`vartheta` here means the coordinate passed to `omega` by the pre-SFT loop; the original source calls it `theta_original[i]`. We distinguish it from the **SFT colatitude** `theta` used later because the original coordinate is constructed in `[-π/2,+π/2]` and is latitude-like. The **possible mismatch is a validation item**, not something to silently assume correct.

Sample discussed in earlier stages: with φ = 90°, φ_ref = 180°, ω0 = 13.2°/day:

$$
\Delta t = \frac{90^\circ-180^\circ}{13.2^\circ/\mathrm{day}}
         \approx -6.8182\ \mathrm{days}.
$$

- This offset explains **how far the original longitude is in reference-time units**.
- The correction uses it to change the **coordinate where the map value is looked up**.
- There is **no independent field-strength integration by Δt** at this point.
- Earlier learning examples temporarily used a toy differential-rotation rate of `1°/day` at latitude 30° to explain a longitude shift. That example was illustrative, not the fitted rate in the actual source.
- The user repeatedly asked whether the operation is “cut and paste” versus “a formula”; the actual operation is **continuous spline sampling at corrected coordinates**, not a simple pixel cut/paste.

### 2.4 Selecting the previous/current/next map

The code performs exactly these branches:

```text
if φ' < 0°:       use previous map, lookup φ' + 360°
if 0° ≤ φ' ≤ 360°: use current map,  lookup φ'
if φ' > 360°:    use next map,     lookup φ' − 360°
```

It retrieves the interpolated `B_corrected` from the selected spline and puts it in `B_day106` at the target loop location (`SFT.py:98–117`). Thus a corrected longitude outside the central CR drives the lookup into a neighboring CR map; that was a central point of the user's numerical examples.

No separate latitude remapping is applied inside this loop; the coordinate retained at the lookup is the current loop's `theta_original[i]`.

**Implementation cautions to validate before adopting the math as physically correct:**

1. `omega(theta)` is defined with `cos(theta)` (`SFT.py:18–21`) and described as a function of **colatitude**, while the pre-SFT loop passes `theta_original = arcsin(...)`, a **signed latitude-like** quantity. This is a potentially material coordinate mismatch, particularly at the equator and poles; verify intended frame and transformation directly.
2. The actual `omega` fit returns `0.18 − 2.3cos²θ − 1.62cos⁴θ` degrees/day. This can represent rotation relative to a reference frame rather than a full solar spin; the assumed frame and its combination with `omega_0` should be checked against the cited thesis, not guessed.
3. A variable `delta_t` is calculated, but the program literally constructs `phi_n` from the equivalent ratio expression, **not by referring to `delta_t` again**.
4. `phi_original` includes endpoints 0 and 360 when generated with `linspace`, potentially duplicating a periodic endpoint; original FITS metadata and coordinate mapping deserve validation.
5. Here `B_day106` is merely a variable name. Do not assume it establishes the correct observing time without data provenance.
6. The phrase “temporally synchronized map” must be qualified: **the algorithm corrects longitudinal sampling but does not by itself run the physical SFT time evolution across the entire original synoptic observation interval**.

---

## 3. Coordinate systems: spherical angles, latitude, Mercator y, and grid units

This was one of the most important and most repeatedly clarified topics in the discussion.

### 3.1 Latitude is not colatitude

- `φ` = longitude, increases around the Sun.
- `θ` = **colatitude**, measured from the north pole: 0° north pole, 90° equator, 180° south pole.
- `λ` = **latitude**, north positive, with `λ = 90° − θ`.
- For a calculation at a fixed location, `sin θ` in metric factors uses the colatitude of the quantity's actual location (cell center versus edge).

A previous example `(φ = 90°, θ = 60°)` is equivalent to latitude `λ = +30°`. Many questions in the CR preprocessing used latitude while SFT update formulas used colatitude: Codex must carefully convert before applying an angular velocity formula.

### 3.2 Mercator transformation used by SFT.py

`SFT.py:130–141`:

$$
\delta = 1^\circ,\qquad \delta_{\rm rad}=\frac{\pi}{180}.
$$

Define a dimensionless Mercator-grid coordinate:

$$
\boxed{y(\theta)=-\frac{\ln\tan(\theta/2)}{\delta_{\rm rad}}}
$$

and its unscaled counterpart:

$$
\boxed{\alpha(\theta)=\delta_{\rm rad}y(\theta)
=-\ln\tan(\theta/2)}.
$$

Inverse:

$$
\boxed{\theta(y)=2\arctan\left(e^{-\delta_{\rm rad}y}\right)}
\quad\Longleftrightarrow\quad
\boxed{\theta(\alpha)=2\arctan(e^{-\alpha})}.
$$

The longitude grid uses:

$$
\boxed{x=\phi/\delta_{\rm rad}}.
$$

The code's raw `dx = dy = 1` are **dimensionless grid increments**. After multiplying by `δ_rad` they represent `Δφ = δ_rad` and `Δα = δ_rad`. For clarity in formulas, write either:

- **Grid-index convention:** `dx = dy = 1` and angular increment `dx·δ_rad = dy·δ_rad = π/180`; **or**
- **Angular-transformed convention:** `Δx_ang = Δφ = π/180`, `Δy_ang = Δα = π/180`.

Do **not** combine both scalings in the same denominator by accident.

### 3.3 Derivatives and nonuniform physical latitude

$$
\boxed{\frac{d\alpha}{d\theta}=-\frac{1}{\sin\theta}}
\qquad
\boxed{\frac{d\theta}{d\alpha}=-\sin\theta}.
$$

Therefore:

$$
\boxed{\frac{\partial B_z}{\partial\alpha}
=-\sin\theta\frac{\partial B_z}{\partial\theta}}
$$

and:

$$
\boxed{\frac{\partial B_z}{\partial y}
=-\delta_{\rm rad}\sin\theta\frac{\partial B_z}{\partial\theta}}.
$$

The user initially asked why a field `Bz(θ,φ)` suddenly was evaluated with `α`. The answer: **the actual array is evenly spaced in α (or scaled y), not in θ**; the underlying field can be described in either coordinate system by composing with `θ(α)`. Both are legitimate, but one must be explicit about transformations and units.

- At/near the equator, fixed Δα corresponds to approximately the same magnitude of Δθ in radians.
- At high latitudes, fixed Δα corresponds to a smaller physical Δθ.
- A plot of the Mercator mesh has **equal visual vertical steps**; labeling the vertical axis with true latitudes gives increasingly **compressed latitude differences** toward the poles.
- The user illustrated this with **2 lines 1 cm apart** in a Mercator diagram: the represented latitude difference near the equator differs from that at higher latitude. **Yes.**
- A fixed `Δx` remains a fixed change in longitude `Δφ`, for **any** latitude in the coordinate system; the actual east–west *distance along a latitude circle* still depends on latitude through `sin θ`.
- A fixed `Δy` **does not** represent a fixed change in θ. But its numerical input in the code's magnetic-field equation is **constant**, independent of θ or φ.
- **Important resolved misunderstanding:** the user asked whether `Δy` in `Bz(θ,φ)` should vary by location; **no**. What varies is the physical latitude increment `Δθ` and metric, not computational `Δy`.

### 3.4 Detailed near-equator and near-pole grid coordinates

The original SFT code excludes the singular polar points by using colatitude boundaries `3°` and `177°`. It computes approximately:

```text
y_m  = 208
y_mi = -208
y_c  = -207.5, -206.5, ..., +207.5   (416 cell-center positions)
y_x  = -208, -207, ..., +208        (417 Ax edge positions)
```

(From `floor(y(3°))`, `ceil(y(177°))`, and `np.arange` in `SFT.py:145–180`.)

For **fixed φ**, there are exactly **416 `Bz` values**. They span approximately **−86.93644° to +86.93644° true latitude**, not exactly −87° and +87°. There is **no `Bz` center exactly at 0° latitude**: the adjacent centers are approximately:

```text
−1.499829°, −0.499994°, +0.499994°, +1.499829° ...
```

The first center north of the equator is **+0.499994°** and the next is **+1.499829°**. The previous assistant rounded these as `+0.5°` and `+1.5°`, which is acceptable for intuition but **not exact** and becomes less accurate further poleward. The user's “Bz(−87) through Bz(+87)” statement was an approximation of the extent, not exact sampling every integer degree.

---

## 4. The staggered computational mesh and its indexing

### 4.1 Cell arrangement

For 1 rectangular computational cell:

```text
                  Ax (top; y edge)
             ┌─────────────────┐
             │                 │
  Ay (left)  │   Bz (center)   │  Ay (right)
             │                 │
             └─────────────────┘
                 Ax (bottom; y edge)
```

`Bz` is a radial field sampled at the cell center, `Ax` is a horizontal-edge vector-potential component, `Ay` is a vertical-edge component. These are **different spatial sample sites**, not interchangeable array shapes.

### 4.2 Array dimensions (unpadded)

| Variable | Spatial location | Shape | Number of values |
|---|---|---:|---:|
| `Bz` | cell centers | **360 × 416** | **149,760** |
| `Ax` | horizontal / latitude-direction **edges** | **360 × 417** | **150,120** |
| `Ay` | vertical / longitude-direction **edges** | **361 × 416** | **150,176** |

Why? **360** longitudinal cells require **361** long-edge nodes if both endpoints are explicitly represented; **416** latitudinal cells require **417** horizontal-edge positions. Longitude is periodic, so one boundary column is geometrically equivalent to its wrapped partner, but it is explicitly represented in the arrays.

The code subsequently adds **1 ghost/padding cell at each end of both axes** for its evolution arrays, so don't blindly apply unpadded shapes to runtime arrays (`SFT.py:262–285`). The padded shapes would be `Bz 362×418`, `Ax 362×419`, `Ay 363×418` before considering subsequent modifications. **The number of physical cells is unchanged.**

### 4.3 User's preferred mathematical index convention

The user explicitly explored indexing a pair of horizontal cell edges as:

$$
\boxed{A_x(i)\quad\text{(bottom)},\qquad
       B_z(i+\tfrac12)\quad\text{(center)},\qquad
       A_x(i+1)\quad\text{(top)}}
$$

**provided the index increases upward/northward.** This convention makes staggered locations obvious. It is valid pedagogical notation. `Bz(i)` with *the same edge indexing* does not name a native cell-centered sample at the same spatial site; `Bz` samples have a half-offset relative to the edge coordinate.

An interpolated `Bz` value *at an edge* can be defined for an interior edge using neighboring **cell-center** values:

$$
\boxed{B_z^{\rm edge}(i)
  =\frac{B_z(i-\tfrac12)+B_z(i+\tfrac12)}{2}.}
$$

**Important subtlety:** The user said “Bz(i) refers to the average of Bz(i+.5) and Bz(i−.5), right?” The answer is **yes only if `Bz(i)` is explicitly being *defined* as the interpolated edge value**. The **native** `Bz` data live at centers. Avoid calling the interpolated field the original `Bz` sample without a superscript or annotation.

The assistant also explained that in ordinary numerical software it is more common to use **integer array indices separately for all 3 arrays**, while storing their physical coordinate vectors (`theta_c`, `theta_x`, `theta_y`) separately. Codex should not take the user's half-index convention as a literal Python indexing strategy.

### 4.4 Actual code indices (`i` and `j`) differ from the user's abstract `i`

Inside `SFT.py`:

- First axis `i` = **longitude/x index**.
- Second axis `j` = **Mercator-y/latitudinal index**.
- `Ax[i,j]` and `Ax[i,j+1]` are bottom/top horizontal edges (in the code's y increasing northward orientation).
- `Ay[i,j]` and `Ay[i+1,j]` are left/right vertical edges.
- `Bz[i,j]` is their cell center.

Thus the assistant's proposed `A_x(i) ... B_z(i+1/2) ... A_x(i+1)` pedagogical notation uses `i` along **latitude**, whereas `SFT.py` uses `j` along latitude. **Do not mix them.**

### 4.5 Ax and Bz locations and edge interpolation

For fixed longitude `φ`, an `Ax` location at Mercator coordinate `α` is between 2 `Bz` centers at:

$$
\boxed{(\phi,\alpha-\tfrac12\Delta\alpha),\qquad
       (\phi,\alpha+\tfrac12\Delta\alpha).}
$$

The edge-centered approximation used for meridional advection is:

$$
\boxed{B_z^{A_x}(\alpha,\phi,t)
=\frac{B_z(\alpha-\Delta\alpha/2,\phi,t)+B_z(\alpha+\Delta\alpha/2,\phi,t)}{2}.}
$$

The derivative in the diffusive term uses **their difference**, not their average:

$$
\boxed{\left.\frac{\partial B_z}{\partial\alpha}\right|_{A_x}
\approx \frac{B_z(\alpha+\Delta\alpha/2,\phi,t)-B_z(\alpha-\Delta\alpha/2,\phi,t)}{\Delta\alpha}.}
$$

For an `Ay` edge at longitude `φ`, interpolate in the **longitude** direction from two adjacent `Bz` centers; the corresponding derivative is a difference divided by `Δφ`.

---

## 5. Model constants, units, and solar flows

### 5.1 Constants in source (`SFT.py:130–133`)

| Parameter | Source value | Meaning |
|---|---:|---|
| `delta` | `1` | nominal angular-grid scale in **degrees** |
| `delta_rad` | `π/180` | radians per step |
| `dx`, `dy` | `1`, `1` | spacing **in code grid coordinates** |
| `Rs` | `7×10^10 cm` | approximate solar radius used by model |
| `D` | `3.5×10^12 cm²/s` | turbulent diffusivity |
| `dt` | `60 s` | model timestep |
| `Du` | `0.045e5 = 4500 cm/s` | amplitude in meridional velocity fit |
| `p` | `2.33` | exponent in meridional velocity fit |
| `ω0` | `13.2°/day` | pre-SFT reference angular rate |

The factor `π/180` is used at *every* cell in the appropriate finite-difference denominator, regardless of latitude. For actual distances on the Sun, metric factors involving `Rs` and `sin θ` are needed.

### 5.2 Meridional flow

Source (`SFT.py:25–32`):

$$
\boxed{u(\theta)=-4500\cos\theta\,\sin^{2.33}\theta\quad\mathrm{cm/s}.}
$$

- A latitude-dependent **north–south / poleward** surface transport field (depending on sign convention).
- `θ` here is colatitude.
- Velocity is evaluated at the appropriate **staggered edge location** when updating potential components.
- In the `Ax` update, the advection term is `−u(θ) Bz_at_edge`; expanding `−u` gives **`+4500 cos θ sin^{2.33} θ × Bz_at_edge`**.
- A different `u(theta)` function appears as commented-out alternative source text (`SFT.py:34–58`); it is **not active**.

### 5.3 Differential rotation

Source (`SFT.py:18–21`):

$$
\boxed{\omega(\theta)=
\left[0.18-2.3\cos^2\theta-1.62\cos^4\theta\right]
\frac{\pi/180}{86400}\quad\mathrm{rad/s}.}
$$

- The Sun rotates at different rates at different latitudes.
- `ω(θ)` represents a chosen angular rotation profile; the code's exact reference frame must be respected.
- Corresponding azimuthal linear speed used at `Ay` edge locations:

$$
\boxed{u_\phi(\theta)=R_\odot\sin\theta\,\omega(\theta).}
$$

- Meridional flow transports in the latitudinal direction; differential rotation transports/shears along longitude. The user compared this with rigidly rotating Earth, whose surface does not exhibit the Sun's solar-like latitude-dependent rotation profile.

### 5.4 Diffusion

`D` governs how the surface field is redistributed by an effective turbulent diffusion term. It is not a third explicit flow velocity. The `Ax` and `Ay` equations use **spatial differences in Bz**, with metric and angular-spacing factors. Opposite signs in the `Ax` and `Ay` diffusive expressions reflect the components used in the vector-potential formulation.

---

## 6. Vector potential: why Ax/Ay, initial Ay=0, and initial Ax integration

### 6.1 What the fields are

On the photosphere the radial magnetic field is denoted `Bz` in this planar-looking numerical naming, while the evolved surface vector potential has components `Ax` and `Ay` on staggered edges. The radial magnetic field is recovered as:

$$
\boxed{B_z=(\nabla\times\mathbf A)_r.}
$$

In a *flat Cartesian* grid this looks like `Bz = ∂Ay/∂x − ∂Ax/∂y`; in a **spherical Mercator grid**, the correct discrete expression has **metric factors** (see §8), so the bare Cartesian formula is **not the complete implementation**.

### 6.2 The initial `Ay=0` choice

At `t=0`, `SFT.py` explicitly sets:

```python
Ay[:, :] = 0.0
```

It then constructs `Ax` from the initial `Bz`. This is an **initial representation/construction choice**, consistent with gauge freedom, **not** a physical claim that the meridional/longitudinal magnetic contribution is absent from the Sun. After evolution `Ay` generally becomes nonzero and contributes to the computed `Bz`.

The user asked whether one could instead initialize `Ax=0` and integrate the other component. Conceptually, other vector potential choices exist, but periodicity, net-flux constraints, boundary conditions, and gauge compatibility matter; do not assume a naive alternative works globally without checking. The code's emergence step later uses a *different* construction (`Ax_AR=0`, build `Ay_AR` from `Bz_AR`).

### 6.3 Continuous relationship behind Ax initialization

Starting from the radial curl term when `Ay=0`:

$$
B_z(\theta,\phi)
=\frac{1}{R_\odot\sin\theta}
\frac{\partial\bigl(A_x(\theta,\phi)\sin\theta\bigr)}{\partial\theta}
$$

using a **colatitude** derivative (the equivalent Mercator expression has a minus sign because y increases toward the north). Thus, with an initial reference colatitude `θ0`, and choosing the appropriate integration constant:

$$
\boxed{A_x(\theta,\phi)
=\frac{R_\odot}{\sin\theta}
\int_{\theta_0}^{\theta} B_z(\theta',\phi)\sin\theta'\,d\theta'.}
$$

- `θ` outside the integral: target colatitude.
- `θ'` inside: integration variable.
- `θ0`: fixed starting boundary, where the chosen integration constant sets the potential.
- `φ`: fixed longitude while integrating along the latitudinal direction.
- The user asked specifically to distinguish `θ`, `θ'`, and `θ0` and to understand why a vector potential can be reconstructed by integrating `Bz`.

### 6.4 Code's numerical initialization (literally)

`SFT.py:210–225`:

```python
for i in range(len(x_c)):
    Ax[i,0] = 0.0
    for j in range(len(y_c)):
        theta_mid = theta_c[j]
        Bz_mid = -Bz_0[i,j] * (np.sin(theta_mid))**2
        Ax[i,j+1] = Ax[i,j] + Bz_mid * (dy * delta_rad * Rs)

for i in range(Ax.shape[0]):
    for j in range(Ax.shape[1]):
        Ax[i,j] /= np.sin(theta_x[j])

Ay[:,:] = 0.0
```

This is a **discrete integral/sum** along the Mercator-y grid. Note the **negative sign** and **sin²θ** in the summand. These arise naturally when converting the colatitude integral to the northward Mercator coordinate: `dθ = −sinθ·dα`.

The code then computes the reconstructed initial `Bz` by the staggered curl, compares it with interpolated `Bz_0`, and prints `Max abs error` (`SFT.py:227–246`). This is an **initialization consistency check**, not proof of stability/accuracy of the whole later run.

---

## 7. Time stepping Ax and Ay: the induction-equation update

### 7.1 General forward-Euler principle

The user repeatedly worked from:

$$
\boxed{A^{\rm new}(t+\Delta t)=A(t)+\Delta t\times\bigl(\text{rate of change}\bigr).}
$$

Here `Δt = 60 s`. Each update samples the old time step's radial field `Bz`, velocities and gradients. The full model uses **explicit forward Euler**, not an implicit or analytical time integrator.

### 7.2 Ax at a horizontal / latitude edge

Source code (`SFT.py:359–385`) computes, for interior edges:

```python
Bz_at_edge = 0.5 * (Bz[i,j-1] + Bz[i,j])
advection  = -u_theta_x[j] * Bz_at_edge
diffusion  = -(D / (delta_rad * Rs * sin(theta_x_pad[j]))) * \
             ((Bz[i,j] - Bz[i,j-1]) / dy)
Ax_new[i,j] = Ax[i,j] + dt * (advection + diffusion)
```

The corresponding continuous-looking **Mercator-angular** formula is:

$$
\boxed{
A_x^{\rm new}(\theta,\phi,t+\Delta t)
=A_x(\theta,\phi,t)
+\Delta t\left[-u(\theta)\,B_z^{A_x}
-\frac{D}{R_\odot\sin\theta}
\left.\frac{\partial B_z}{\partial\alpha}\right|_{A_x}
\right].
}
$$

Here `α(θ) = −ln tan(θ/2)`; the derivative above is approximated at the `Ax` edge by the neighboring cell centers. When directly implementing the code, use `delta_rad * dy` in the denominator.

**Fully expanded form as requested during the discussion**, with everything within the single equation (no external “where” section), preserving physical coordinate order `(θ, φ)` as the conceptual basis:

$$
\boxed{
\begin{aligned}
&A_x^{\rm new}(\theta,\phi,t+\Delta t)=A_x(\theta,\phi,t)\\[3pt]
&\quad+\Delta t\Biggl[
4500\cos\theta\sin^{2.33}\theta
\frac{
B_z\!\left(\theta\!\left[\alpha(\theta)-\frac{\Delta\alpha}{2}\right],\phi,t\right)
+B_z\!\left(\theta\!\left[\alpha(\theta)+\frac{\Delta\alpha}{2}\right],\phi,t\right)
}{2}\\[3pt]
&\qquad-\frac{D}{R_\odot\sin\theta}
\frac{
B_z\!\left(\theta\!\left[\alpha(\theta)+\frac{\Delta\alpha}{2}\right],\phi,t\right)
-B_z\!\left(\theta\!\left[\alpha(\theta)-\frac{\Delta\alpha}{2}\right],\phi,t\right)
}{\Delta\alpha}
\Biggr],\qquad
\alpha(\theta)=-\ln\tan\frac{\theta}{2},\quad
\theta(\alpha)=2\arctan e^{-\alpha}.
\end{aligned}}
$$

This version avoids the notational trap of writing `Bz(α,φ)` while claiming all field arguments are `(θ,φ)`; it explicitly evaluates θ at the neighboring α values. An earlier assistant version did write `Bz(α(θ) ± Δα/2,φ,t)` as **coordinate shorthand**. That shorthand is valid if `Bz` is defined as a function of α, but the user preferred seeing the dependence on θ.

**The user explicitly asked these successive conceptual steps:**

1. Begin with `Ax_new = Ax_old + Δt(meridional advection + diffusion)`.
2. Substitute the advection and diffusion terms.
3. Expand `u(θ)` using the source function; verify the sign change from `−u` to `+4500 cosθ sin^2.33θ`.
4. Replace `Bz_at_edge` in advection by the **average of the 2 neighboring cell-center Bz samples**.
5. Replace the diffusive derivative by **the difference between those 2 Bz samples divided by their Mercator separation**.
6. Keep everything in **one displayed equation**, without extra “where” definitions if possible.
7. Ask why `Bz` was written as a function of α while `Ax` was a function of θ; settle that fields are physically functions on the same surface, merely expressed in different coordinates.
8. Prefer `α(θ)` notation to an unwieldy logarithmic expansion at every occurrence, and use consistent field-coordinate notation.

### 7.3 Sign, placement, and the meaning of averaging

When evaluating `Ax` at `(φ, α)`:

- The two `Bz` samples come from **the same φ** but latitudes on opposite sides of the `Ax` edge.
- The **average** is used for the advective product `−u·Bz` evaluated at that edge.
- The **difference/spacing** is used for the diffusive gradient of Bz at that edge.
- `u(θ)` and `sin θ` use the **colatitude of the Ax edge**, not the two Bz centers.
- A constant `Δα = π/180` applies **at all latitudes**; the actual distance in θ between those Bz samples varies with latitude.

### 7.4 Ay at a vertical / longitude edge

`SFT.py:387–413`:

```python
Bz_at_edge = 0.5 * (Bz[i-1,j] + Bz[i,j])
advection = -u_phi_y[j] * Bz_at_edge
diffusion = +(D / (delta_rad * Rs * sin(theta_y_pad[j]))) * \
            ((Bz[i,j] - Bz[i-1,j]) / dx)
Ay_new[i,j] = Ay[i,j] + dt * (advection + diffusion)
```

Equivalently, in transformed angular longitude `φ`:

$$
\boxed{
A_y^{\rm new}(\theta,\phi,t+\Delta t)
=A_y(\theta,\phi,t)
+\Delta t\left[
-R_\odot\sin\theta\,\omega(\theta)\,B_z^{A_y}
+\frac{D}{R_\odot\sin\theta}
\left.\frac{\partial B_z}{\partial\phi}\right|_{A_y}
\right].}
$$

For an interior `Ay` edge at longitude `φ`, `Bz^{Ay}` is the mean of the 2 neighboring cell-center Bz values at **same latitude and neighboring longitudes**, and the derivative is their difference divided by `Δφ`.

**Scope/learning note:** The recent turn-by-turn expansion went most deeply into **Ax**. The user has a broad workflow understanding of **Ay** and differential rotation but may not have yet derived its expanded single-line equation with the same confidence. Codex should not assume fluent mastery of the `Ay` update just because the equation is documented here.

### 7.5 What Ax/Ay evolution means physically

The update of vector potential produces a new field that encodes surface transport. It is *not* necessary to move literal Bz pixels as objects. Instead, at the next step the code reconstructs the radial field from the curl of the updated vector potential. Diffusion moves/smooths flux patterns, differential rotation shears longitudinally, meridional flow carries patterns poleward, and emergence introduces new field.

---

## 8. Computing Bz from the evolved Ax and Ay — focal recent discussion

This was the latest central topic immediately before the report request.

### 8.1 User's question and the correct short answer

User's question, paraphrased: “After any step or at the final step I have an `Ax` array of 360×417 and an `Ay` array of 361×416. How do I produce a `Bz` array of 360×416? Is it just `Bz = ∂Ay/∂x − ∂Ax/∂y`, and how can I get derivatives when I only have arrays?”

Correct answer: **yes in principle, via the curl, but use staggered finite differences and the appropriate spherical/Mercator metric coefficients**. There is **1 Bz calculation per physical cell**, hence **360×416 = 149,760 calculations**.

### 8.2 Continuous-looking formula on the Mercator plane

When `x_ang = φ` and `y_ang = α(θ)` are both angular coordinate increments in radians:

$$
\boxed{
B_z(\theta,\phi)
=\frac{1}{R_\odot\sin\theta}
\frac{\partial A_y}{\partial\phi}
-\frac{1}{R_\odot\sin^2\theta}
\frac{\partial(A_x\sin\theta)}{\partial\alpha}.
}
$$

The earlier assistant sometimes wrote this as `∂Ay/∂x` and `∂(Ax sinθ)/∂y` where **x/y were intended as angular-scaled transformed coordinates**; this is fine only if the scaling convention is defined. `SFT.py` specifically uses dimensionless `x,y` spacing 1 and then multiplies by `delta_rad`.

### 8.3 Exact discretized expression corresponding to source code

At a `Bz` cell center with longitude `φ` and colatitude `θ_c`:

$$
\boxed{
\begin{aligned}
B_z(\theta_c,\phi_c)
=&\frac{A_y(\phi_{\rm right},\theta_c)-A_y(\phi_{\rm left},\theta_c)}
{R_\odot\sin\theta_c\,\Delta\phi}\\[5pt]
&-\frac{
A_x(\phi_c,\theta_{\rm top})\sin\theta_{\rm top}
-A_x(\phi_c,\theta_{\rm bottom})\sin\theta_{\rm bottom}
}{R_\odot\sin^2\theta_c\,\Delta\alpha},
\end{aligned}}
$$

with `Δφ = Δα = π/180` in **radians of transformed angular coordinates**; `top` means the larger Mercator-y/northward position, hence the **smaller colatitude θ**. The suffix `top/bottom` refers to coordinate orientation, not numeric ordering of θ.

Or precisely in the **code's indices** (interior positions, ignoring padding offsets for interpretation):

$$
\boxed{
B_z[i,j]
=\frac{A_y[i+1,j]-A_y[i,j]}{R_\odot\sin\theta_{c,j}\,(dx\,\delta_{\rm rad})}
-\frac{A_x[i,j+1]\sin\theta_{x,j+1}-A_x[i,j]\sin\theta_{x,j}}
{R_\odot\sin^2\theta_{c,j}\,(dy\,\delta_{\rm rad})}.
}
$$

This is the direct mathematical counterpart of `SFT.py:320–350`.

### 8.4 Every sub-question the user explicitly worked through

**Q: Subtracting adjacent Ay values gives `∂Ay/∂x` or merely `ΔAy`?**

It gives **`ΔAy` first**. Approximating the derivative requires:

$$
\left.\frac{\partial A_y}{\partial\phi}\right|_{\rm center}
\approx \frac{A_y(\mathrm{right})-A_y(\mathrm{left})}{\Delta\phi}.
$$

**Q: For Ax do we just subtract top/bottom values?**

Almost: the numerator must be **`Ax_top sinθ_top − Ax_bottom sinθ_bottom`**, not merely `Ax_top − Ax_bottom`. Divide by the **Mercator step `Δα`**; the whole term also has `1/(Rs sin²θ_center)`.

**Q: Does the numerator use a different θ than the denominator?**

**Yes**. The `sinθ` multiplying each `Ax` belongs to **that Ax edge's colatitude**; the outside denominator `sin²θ_center` belongs to the **Bz center**. Similarly the denominator of the Ay term uses `sinθ_center`.

**Q: Does `Ay` use neighboring longitudes and divide by `Δx`, not `Δy`?**

**Yes.** The **longitude difference** of Ay is divided by **longitudinal grid separation**; one may call it `Δx_ang` or `Δφ`. The Ax term uses **vertical Mercator separation** `Δy_ang` / `Δα`.

**Q: Are the Ay samples at `φ±Δφ/2`?**

**Yes**, in the staggered geometry at longitude `φ_c`, the left/right Ay edges lie a half-longitude step to either side. For the Ax edges, the corresponding offset is **`α_c±Δα/2`**, **not `θ_c±Δα/2`**, because θ increments vary with latitude.

**Q: Do we use different numerical Δx/Δy values at different θ,φ?**

**No.** In the 360×416 loop, for all **149,760** cells, `dx=dy=1` and `delta_rad=π/180`; equivalently the *angular coordinate steps* are always `Δφ=Δα=π/180`. **Only θ, φ, A values, and the associated sinθ factors vary.**

**Q: But visual gaps on a Mercator map look equal, and actual latitude gaps don't?**

Correct! The same y step represents different Δθ depending on latitude. The code is in the **Mercator coordinate system**, and the `sinθ` factors handle the spherical geometry.

### 8.5 Explicit schematic matching the finite differences

```text
                  A_x(i, j+1)  at (φ_center, θ_top)
                ┌───────────────────────┐
                │                       │
 A_y(i, j)      │      B_z(i, j)        │   A_y(i+1, j)
  φ_left        │   (φ_center, θ_center)│    φ_right
                │                       │
                └───────────────────────┘
                  A_x(i, j)   at (φ_center, θ_bottom)

Longitudinal term:
   [Ay(right) − Ay(left)] / (Δφ × Rs × sin θ_center)

Mercator-latitudinal term:
   [Ax(top) sin θ_top − Ax(bottom) sin θ_bottom]
   / (Δα × Rs × sin² θ_center)

Bz = longitudinal term − Mercator-latitudinal term
```

The original learning drawing displayed Ax at top/bottom, Ay on sides, and Bz in the middle. The user then reasoned through which values deserve integer indices versus half-integer indices, and asked why `Bz(i)` is not inherently the same site as `Ax(i)`.

### 8.6 Why θ_top and θ_bottom are not simply θ_center ± Δα/2

Since `α = −ln tan(θ/2)` is nonlinear, transforming each edge is necessary:

$$
\theta_{\rm top}=2\arctan\exp[-(\alpha_c+\tfrac12\Delta\alpha)],
\qquad
\theta_{\rm bottom}=2\arctan\exp[-(\alpha_c-\tfrac12\Delta\alpha)].
$$

Their difference in **physical colatitude** changes from cell to cell. An earlier assistant expansion gave `θ± = 2 arctan(tan(θ/2) e^{∓Δα/2})` and used these in an expression; this is an exact coordinate conversion (modulo sign and top/bottom labels), not a statement that θ is uniformly spaced.

---

## 9. Boundary conditions and array padding

The 2 longitude boundaries are **periodic** (`wrap`): at one end, neighbors come from the opposite end of the Carrington-longitude domain. In the latitude/Mercator direction, the code **copies the edge values into padded cells** and imposes “closed” boundaries by assigning boundary samples from the nearest interior samples (`SFT.py:262–314`).

Important nuance: source comments call the y-boundary treatment “reflecting” in the padding section and “closed” in functions. The literal implementation is `mode='edge'` padding plus nearest-interior copying; **do not interpret these labels as proof of a physically precise perfectly reflecting boundary without boundary-flux analysis**.

The code prevents division by tiny `sinθ` in the curl/update loops by clipping it to at least `0.01` in magnitude. It also avoids exact θ=0°,180° poles by limiting the grid around θ≈3° and θ≈177°. Both choices should be noted when checking accuracy near poles.

---

## 10. Flux emergence: bipolar magnetic regions (BMRs)

### 10.1 Why add new magnetic flux

Surface flows/diffusion redistribute pre-existing magnetic fields. The real Sun also generates **new active-region magnetic flux**, so an SFT run that never adds emergence would miss a critical time-dependent source. The user covered this as the “new emergence” part of the algorithm, though the detailed BMR analytic shape was discussed less than staggered grids and Ax evolution.

### 10.2 Catalog and data

`SFT.py:417–429` reads `bmrsharps_evol.txt`, skips 7 header lines, parses a `CM` / `CM_time` column into dates, groups events by date. The loop checks each new model date for matching events (`SFT.py:482–569`). Properties used include:

- `Latitude`, `Carr_Longitude` (location)
- `LeadPol` (polarity convention)
- `Unsgnd_flux` (unsigned flux/amplitude normalization)
- `Bip_Separation` (bipole scale)
- `Bip_Tilt` (orientation)
- `SHARP`, `NOAA` identifiers (read, mostly informational)
- `Bip_Dipole` is read but **not used** in the shown BMR construction.

Events with Carrington longitude outside `[0°,360°]` are skipped.

### 10.3 BMR geometry and analytic radial field in the source

For a catalog event define:

$$
\rho=\frac{\mathrm{Bip\_Separation}}{2\delta},\quad
\rho_0=\rho R_\odot\delta_{\rm rad},\quad
x_0=\frac{\mathrm{Carr\_Longitude}}{\delta},\quad
y_0=y(\pi/2-\mathrm{Latitude}).
$$

Convert the tilt into radians and adjust to the range approximately `[-π/2, π/2]` with ±π corrections. Relative coordinate displacements are rotated:

$$
\begin{aligned}
\Delta x&=\operatorname{wrap}_{[-n_x/2,n_x/2)}(x-x_0),\\
x'&=\Delta x\cos\gamma-(y-y_0)\sin\gamma,\\
y'&=\Delta x\sin\gamma+(y-y_0)\cos\gamma.
\end{aligned}
$$

Set `a = sqrt(1.5)` and:

$$
B_0=\frac{\Phi\,2\sqrt{2}}{\sqrt\pi\,a^3\rho_0^2\,e^{1/2}}.
$$

The injected analytic field is:

$$
\boxed{
B_z^{\rm BMR}(x,y)=
-\operatorname{sgn}(P)B_0e^{1/2}
\frac{x'}{\rho}
\exp\!\left[-\frac{x'^2+2y'^2}{(a\rho)^2}\right].
}
$$

where `P` denotes the catalog leading-polarity variable and `Φ` the unsigned-flux input. The expression gives two opposite-sign lobes. Multiple emergence events on the same date are added into a common `Bz_total`.

**Verify against source before implementing:** the catalog units of unsigned flux, separation, angle, and polarity sign and the desired physical normalization; this report reproduces source code algebra and does not independently validate the units/physics.

### 10.4 Inject through vector potential, not by simply replacing evolved Bz

The emerging BMR radial map is converted to a vector-potential increment:

```text
Ax_AR = 0
Ay_AR = longitude-wise cumulative integral of Bz_AR × sin(theta) × Rs × Δφ
Ax ← Ax + Ax_AR
Ay ← Ay + Ay_AR
apply boundary conditions
```

Exact source (`SFT.py:449–460`) uses:

$$
A_y^{\rm AR}[i+1,j]
=A_y^{\rm AR}[i,j]
+B_z^{\rm AR}[i,j]\sin\theta_{c,j}\;(dx\,\delta_{\rm rad}\,R_\odot).
$$

The user earlier queried why an alternative vector-potential construction can be used; **this is a concrete example** of the code using an `Ay`-integration representation specifically for newly emerged flux, while the initial field used an `Ax`-integration representation.

---

## 11. Full SFT workflow: executable order of operations

### 11.1 Before main loop

1. Import NumPy, SciPy interpolation, Astropy FITS, Numba, pandas, Matplotlib, datetime.
2. Define rotation fit `omega(θ)` and poleward flow profile `u(θ)`.
3. Read MDI previous/current/next Carrington maps.
4. Build interpolators; for each target coordinate, calculate time-offset-derived rotated longitude, select the appropriate map, spline-sample corrected field into `B_day106`.
5. Define `δ=1°`, `D`, `Rs`, `dt`; define Mercator `y(θ)` and inverse `θ(y)`.
6. Make 360 longitude cell centers, 416 Mercator-y centers, and staggered Ax/Ay edge coordinates.
7. Interpolate `B_day106` to the Bz grid, yielding `Bz_0`.
8. Initialize `Ax` by cumulative integration along y; set `Ay=0`.
9. Recover initial `Bz` from curl(A); report maximum difference from `Bz_0`.
10. Precompute velocities at appropriate edge locations, pad arrays, establish boundary conditions.
11. Load and group BMR data by time.

### 11.2 At each 60-second step

Source (`SFT.py:463–585`):

```text
for each time t:
    Bz ← curl(Ax, Ay) from old vector potential
    apply Bz boundaries
    Ax_new, Ay_new ← forward-Euler update using Bz, flows, diffusion
    Ax, Ay ← Ax_new, Ay_new
    apply Ax/Ay boundaries
    on new calendar day:
        if BMR(s) recorded for that day:
            create combined analytic Bz_AR
            represent new Bz_AR via Ax_AR = 0, Ay_AR integral
            add Ax_AR and Ay_AR to Ax and Ay
            re-apply boundaries
    at configured output times:
        recover Bz and save a snapshot
    periodically monitor max amplitudes and NaNs
```

The program defines `t = arange(0, 3500*24*3600, 60)` from `2010-05-06`; that is approximately **3500 simulated days**, with **5,040,000 possible 60-second intervals** (the `arange` length; actual loop starts at index 1). This is a *long* simulation; validation should consider computational cost and stable timestep constraints, rather than assuming the whole run is inexpensive.

At `23:59`, a `day_counter` increments and it saves a Bz snapshot when the counter is **odd**, i.e. approximately every 2 days after the first matching day. The code outputs an `.npz` file with `Bz_time`, and creates contour visualizations (`SFT.py:571–635`).

### 11.3 Relation between Bz and Ax/Ay at successive times

This answers a repeated conceptual question: The code does **not** independently integrate a separate Bz variable and separately evolve two unrelated potentials. At any model time, the field is defined by:

$$
\boxed{B_z(t)=(\nabla\times\mathbf A(t))_r.}
$$

`Ax` and `Ay` carry the evolving degrees of freedom. `Bz` is **reconstructed** from them (including when the code wants to plot or save a magnetic map). The user correctly noticed that after the initial `Ay=0` construction, the later evolved `Ay` will be nonzero; therefore **both** vector-potential components contribute when reconstructing the final field.

---

## 12. Full detailed history of questions, misconceptions, and resolutions

This section preserves the learning path so a future agent can recognize exactly what concepts have *already been explained*, what is still shaky, and which types of phrasing caused confusion.

| Topic/question explored | Resolved understanding | Caution for next agent |
|---|---|---|
| Why use 3 CR maps? | Neighbor rotations permit lookup if longitude correction crosses 0°/360°. | FITS map times are not uniform and actual observation-time treatment needs validation. |
| Is the CR map temporally synchronized? | Carrington-aligned spatially, not one simultaneous observation. | “Synchronized” needs a precise definition. |
| Is the pre-SFT correction physical evolution of `B`? | No: mainly re-sampling the magnetic data at rotation-corrected longitudes. | SFT evolution comes later. |
| What does `Δt` mean? | Offset from φ_ref using ω0, e.g. −6.818 days at φ=90°. | It is computed but not literally referenced later by that variable name. |
| What does `φ'` do? | Determines longitude to sample. | Can use previous/next CR when out of bounds. |
| Are there latitude and longitude corrections? | The shown pre-SFT loop corrects longitude only. | Distinguish coordinates passed into interpolation. |
| Why use differential rotation at all? | Rotation varies by latitude, so lookup longitude shift depends on θ/λ. | Check pre-SFT latitude vs colatitude mismatch in actual source. |
| What is SFT for? | Evolve photospheric radial field using transport plus emergence. | PFSS is a separate extrapolation stage. |
| What does a vector potential do? | Curl of A gives radial B. | A is gauge-dependent; B is not. |
| Why initialize Ay=0? | Convenient initial construction/gauge choice. | After time stepping Ay need not be 0. |
| How initialize Ax? | Integrate initial Bz along latitude with spherical factors. | Check signs/coordinate conversion; code uses Mercator y. |
| Why a Mercator grid? | Uniform numerical y-spacing with spherical geometry encoded by metrics. | Do not confuse θ with y. |
| Where is Bz located? | Cell center. | Native Bz vs interpolated Bz at edge. |
| Where is Ax? | Top/bottom horizontal cell edges. | Number of latitudinal edge positions is 417. |
| Where is Ay? | Left/right vertical cell edges. | Number of longitudinal edge positions is 361. |
| What are their shapes? | Ax 360×417, Ay 361×416, Bz 360×416. | These are **unpadded** shapes. |
| How many Bz values for fixed φ? | 416. | They are nonuniform in physical latitude. |
| Is Bz at exactly latitude 0°? | No; nearest ±0.499994° centers. | The user originally approximated every value as an integer degree. |
| How is cell indexed? | User likes Ax(i), Bz(i+½), Ax(i+1), with i northward. | Python source uses i for longitude, j for latitude. |
| Does Bz(i) exist? | It can mean an *interpolated* edge value if defined so; native Bz is centered. | Always label interpolated Bz explicitly. |
| When calculating Ax, which Bz is used? | The 2 neighboring Bz centers at the **same φ**, different latitude. | Average for advection, difference for diffusion. |
| What is u(theta)? | −4500 cosθ sin^2.33θ cm/s in active source. | Theta at Ax edge; signs matter. |
| Why is Bz written with α? | Because latitudinal mesh uniform in α, not θ. | Can express as Bz(θ(α),φ) for consistency. |
| Can Ax use α too? | Yes, via change of coordinates. | User opted to retain θ language and α(θ) shorthand. |
| Can Δα just be Δ(α(θ))? | Only after properly evaluating actual neighboring grid coordinates. | Don't replace a grid increment with a naive derivative without conversion. |
| How do we get final Bz? | Radial curl of both evolved Ax and Ay using finite differences. | Not simply flat Cartesian curl without sinθ factors. |
| Does subtracting Ay give derivative? | No: raw subtraction = ΔAy; divide by Δx / Δφ for derivative. | Include Rs sinθ in spherical formula. |
| For Ax numerator use sinθ? | Yes, multiply each Ax edge by its own sinθ. | Denominator uses sin²θ of **Bz center**. |
| Ay derivative direction? | Right/left neighbors in φ; denominator Δx (longitudinal). | Not Δy. |
| Are Ax positions θ±½ Δy? | Not in θ because grid uniform in Mercator y/α. | Evaluate θ at α±½Δα. |
| Are Δx and Δy equal? | Both `1` code grid unit, conversion π/180 each. | In physical degrees only Δφ remains constant; Δθ does not. |
| Does Δy depend on latitude and longitude? | **No**. Its numeric value is constant everywhere. | The actual mapping of 1 grid step to latitude varies with θ only, not φ. |
| How many times apply Bz formula? | 360×416 = 149,760 cell computations per full field reconstruction. | Fixed spacings each time; vary local field values and θ factors. |
| What does BMR step add? | New bipolar radial flux via analytic pattern and an Ay potential increment. | Not just another advection/diffusion term. |
| How often is the timestep? | 60 seconds. | Distinguish integration step from output/snapshot cadence. |
| What does SFT output feed into? | Photospheric field evolution; could serve PFSS / coronal analysis. | This script does not implement PFSS itself. |

---

## 13. Practical equation and code cheat sheet

### 13.1 Coordinate helpers

```python
import numpy as np

delta_rad = np.pi / 180

def alpha(theta):
    return -np.log(np.tan(theta / 2))

def theta_from_alpha(alpha_value):
    return 2 * np.arctan(np.exp(-alpha_value))

def mercator_y(theta):
    return alpha(theta) / delta_rad

def theta_from_grid_y(y):
    return theta_from_alpha(delta_rad * y)
```

### 13.2 Actual source-relevant velocities

```python
def omega(theta):
    deg_per_day = 0.18 - 2.3*np.cos(theta)**2 - 1.62*np.cos(theta)**4
    return deg_per_day * (np.pi / 180) / 86400.0

def meridional_velocity(theta):
    return -4500.0 * np.cos(theta) * np.sin(theta)**2.33  # cm/s

u_phi = Rs * np.sin(theta) * omega(theta)
```

### 13.3 Single-cell radial field reconstruction (source algebra)

```python
# Coordinates theta_c[j], theta_x[j], theta_x[j+1] are provided.
# Ax/Ay/Bz shapes are staggered, so this uses the correct edge slots.
# This fragment illustrates an interior, unpadded cell; source uses padded arrays.

dphi   = dx * delta_rad     # equals pi/180
dalpha = dy * delta_rad     # equals pi/180

Bz[i,j] = (
    (Ay[i+1,j] - Ay[i,j])
    / (Rs * np.sin(theta_c[j]) * dphi)
    - (
        Ax[i,j+1] * np.sin(theta_x[j+1])
        - Ax[i,j] * np.sin(theta_x[j])
      )
    / (Rs * np.sin(theta_c[j])**2 * dalpha)
)
```

Notice that **the 2 Ax values use their own θ edge angles** and **both denominator sin terms use the center θ**. The actual source also clips small sine values and uses ghost cells.

### 13.4 Single Ax edge update (source algebra)

```python
Bz_at_Ax = 0.5 * (Bz[i,j-1] + Bz[i,j])

Ax_new[i,j] = Ax[i,j] + dt * (
    -meridional_velocity(theta_x[j]) * Bz_at_Ax
    -(D / (Rs*np.sin(theta_x[j])))
        * ((Bz[i,j]-Bz[i,j-1])/(dy*delta_rad))
)
```

The corresponding `Ay` update uses average of `Bz[i-1,j]` and `Bz[i,j]`, the differential rotation azimuthal speed, and `+D ∂_φ Bz/(Rs sinθ)`.

### 13.5 Why *both* fixed steps are used 149,760 times

```python
for i in range(360):
    for j in range(416):
        # dphi and dalpha below are always the same values:
        dphi = np.pi/180
        dalpha = np.pi/180
        # theta_c[j] and neighboring potential values CHANGE by grid location.
        # Actual implementation handles padding and safe boundary indices.
        pass
```

**This is the exact concept the user confirmed immediately before requesting this file.**

---

## 14. Conceptual precision and implementation issues that should *not* be silently flattened

### 14.1 “A number is 1” versus “the angular increment is π/180”

- The Python variables `dx` and `dy` are assigned differences of `x_c` and `y_c`, and are each **1**.
- Source calculates finite differences with the denominator **`dx * np.deg2rad(delta)`** or **`dy * np.deg2rad(delta)`**, which are each **π/180 radians**.
- An earlier conversational answer said “Δx = Δy = π/180 radians,” using **already converted angular coordinates**. This is **not** literally the code's raw `dx=dy=1`. An agent should communicate the distinction, not declare either answer categorically false.

### 14.2 Physical separation versus coordinate separation

**Equal distances on the Mercator grid are not equal latitudinal angular distances on the Sun.** Physical longitudinal distance for the same Δφ also varies with latitude because a latitude circle contracts toward the poles. `Δφ` and `Δα` nevertheless are constant **coordinate increments**, so the code can use the same denominators everywhere, provided proper metric factors enter the equation.

### 14.3 The sinθ terms do not all use the same θ

The vector potential samples are at different spatial sites. When computing `Bz`:

- `sinθ_x[j]` belongs to **Ax bottom edge**.
- `sinθ_x[j+1]` belongs to **Ax top edge**.
- `sinθ_c[j]` and `sin²θ_c[j]` belong to **Bz center**.
- For `Ay`, its left and right edges share a common y/θ center, so their difference is divided by `Rs sinθ_c Δφ`.

### 14.4 Code-level colatitude ambiguity in pre-SFT fitting

Do not confuse `theta_original` in the CR preprocessing (constructed as arcsine over [−1,1]) with `theta_c` for the SFT grid (constructed as colatitude in [0,π]). `omega()` is called on both. **This deserves an explicit investigation** when checking physics correctness; its discovery here is **a source-reading observation, not a fully adjudicated review verdict**.

### 14.5 Validation of initial Ax integral and Bz recovery

The source prints `Max abs error` for initial Bz reconstruction, which is the right kind of numerical consistency test. But to determine correctness, Codex must inspect its actual value and use explicit tests (known constant/analytic field, conservation, boundaries, convergence). A symbolic identity alone does not guarantee that the discrete implementation satisfies all constraints.

### 14.6 Gauge/boundary issues

`A` is not unique (gauge freedom). The initial `Ay=0` and BMR `Ax_AR=0` are choices of representation. A periodic longitude domain complicates cumulative integration if the emerging radial field's longitude integral does not give a periodic vector potential. Check flux balance and boundary closure. These concerns are flagged for implementation testing; they were **not fully derived to a verdict** in the user's learning session.

### 14.7 Stability / numerical methods not yet proved

The explicit update uses `dt=60 s` and diffusion `D=3.5e12 cm²/s`. Neither physical accuracy nor numerical stability has been proven by conversation. Runtime safety includes clipped small sine factors and NaN checks, but they do not alone establish convergence. A Codex agent may evaluate timestep restrictions and physical invariants if asked for review.

### 14.8 Data-source naming and provenance

The user has discussed HMI/Synoptic data and older solar-physics repo tools in neighboring research contexts. The **exact inspected `SFT.py` reads MDI2095/2096/2097**, not automatically HMI. The BMR file is `bmrsharps_evol.txt`. Don't attribute details from an unseen HMI implementation or from the separate review to this file.

### 14.9 Plots do not change computational definitions

The script plots the evolved Bz array with contour maps, custom tick labels and axis inversion. Its plotting y-axis/tick labels should not be used as the authoritative source for `theta_c` values; the grid transformation does that. In particular, “1°” can mean a Mercator-scaled coordinate interval rather than a uniform latitude interval.

---

## 15. Knowledge calibration for future Codex agents

### 15.1 Concepts the user has explicitly affirmed / accurately reasoned through

- A synoptic map encodes magnetograms gathered at different times; Carrington alignment is **not** simultaneity.
- The pre-SFT stage selects a source location using a differential rotation correction and adjacent CR maps.
- The physics SFT step transports the surface field over time through prescribed flows, diffusion, and emergence.
- The **computational mesh** can be rectangular while representing a spherical photosphere.
- `Ax`, `Ay`, and `Bz` occupy **different sites** of a staggered grid.
- 360×417, 361×416, and 360×416 are the relevant **unpadded** array shapes.
- To compute Bz, use both `Ax` and `Ay` through the radial curl and finite differences, not assume `Ay=0` after initialization.
- The Bz derivative from `Ay` uses **left/right** edge differences in longitude, divided by the **longitude step**.
- The Bz derivative from `Ax` uses **top/bottom** values with their own `sinθ_edge` multipliers; the denominator uses `sin²θ_center`.
- **Same transformed angular coordinate increments** are substituted in every one of the 149,760 Bz cell computations.
- `Δθ` varies with latitude despite `Δα` being constant on a Mercator grid.

### 15.2 Areas the user explored, but future agents should not assume complete mastery

- Deriving the **full `Ay` evolution** formula with all physical constants, indices and signs.
- The precise meaning and physical frame of Ananya's **`omega` differential-rotation fit** relative to Carrington reference rotation.
- Verifying whether the 3-CR preprocessing gives the physically intended **temporal mapping**, including coordinate conventions and possible implementation errors.
- Formal gauge freedom, periodic closure and flux balance when building the **initial** or **BMR-added** vector potential.
- Interpolator assumptions, orientation of FITS arrays, pole boundary conditions, active region normalization, numerical stability and convergence.
- Linking SFT output to a specific **PFSS implementation** and ultimately to scale-dependent stability diagnostics.

### 15.3 How future Codex responses should communicate with the user

- Keep answers **very short, precise, factual**, unless the user explicitly requests detail or a file (as now).
- **One mathematical step at a time** when tutoring: only expand the requested variable/term; retain the previous equation and leave all other terms intact.
- Prefer **numerals** (360, 416, 60 s, 1°) over spelled-out numbers.
- Do not casually switch **latitude / colatitude** or **θ / α / y**, or **grid unit / angular radian / physical distance**.
- If the user requests **one equation**, try to include definitions *inside the equation* and not in extraneous “where” paragraphs.
- If using indices, explicitly distinguish the user's *mathematical 1D vertical index* from Python's `i=longitude, j=latitude`.
- Avoid overexplaining, suggesting unrelated next topics, or treating a correctly stated intuition as needing basic remedial explanation.
- When judging Ananya's code, distinguish **literal documented source behavior**, **deduced math**, **assistant hypotheses**, and **unresolved validation questions**. Read the separate review file if present before claiming its verdicts.

---

## 16. Comprehensive topic index

The following list is intentionally wide, to make it easy for Codex to search topics within this handoff:

- **Solar physics context:** photospheric magnetic field, radial field (`Bz` / `Br`), synoptic maps, Carrington longitudes and rotation periods, equator versus poles, differential rotation, meridional transport, turbulent diffusion, flux emergence, BMRs, surface evolution, downstream PFSS, confined versus eruptive flares and scale-based magnetic analysis.
- **Input data and time:** FITS, MDI CR2095/2096/2097, HMI as separately discussed context, central/previous/next map interpolation, time offsets Δt, reference φ=180°, ω0=13.2°/day, spline lookup, map-wrap at 0°/360°, spatial remapping vs genuine time evolution, central-map observation-time caveats.
- **Coordinate systems:** φ, latitude λ, colatitude θ, θ=90°−λ, scaled Mercator y, unscaled Mercator α, α(θ), θ(α), nonlinear north–south mapping, derivatives and Jacobian, spherical metric terms, units and conversion π/180.
- **Grid construction:** 360×416 cell centers, 360×417 Ax edge array, 361×416 Ay edge array, staggering, initial/outer cells, boundaries ±3° from poles, approximately ±86.936° sample coverage, ±0.5° near-equator Bz centers, 416 samples along latitude at fixed longitude, ghost-cell arrays, periodic x and closed y.
- **Indexing and visualization:** rectangle with Ax top/bottom, Ay left/right, Bz center; user's `Ax(i), Bz(i+½), Ax(i+1)` convention; native vs interpolated Bz; `i` longitude and `j` Mercator latitude in Python; Δx=Δy=1 grid unit; angular δ rad; equal visual spacing on Mercator versus unequal Δθ; equal Δφ even away from equator; actual physical distances depend on θ.
- **Vector potential:** A components, curl, gauge choice, Ay(0)=0, discrete Ax integration and sin² θ, initial Bz reconstruction check, possibility of alternate potential representation.
- **Time update:** forward Euler, 60-second dt, `u(θ)`, `omega(θ)`, `u_phi = Rs sinθ omega`, meridional and longitudinal advection, diffusion, interpolated Bz to edge (mean), gradients of Bz at edge (difference divided by transformed coordinate step), full `Ax_new`/`Ay_new` forms.
- **Bz recovery:** `Bz=(curl A)_r`, Ay right-left difference, Ax top-bottom weighted difference, role of sinθ at center/edges, derivative vs numerator difference, transformed Δφ/Δα fixed for every cell, 149,760 independent cell-center evaluations per reconstruction.
- **BMR emergence:** catalog time, polarities, unsigned flux, Carrington longitude, latitude, separation, tilt, wrapped longitude, two-lobed pattern, additive flux regions, Ay_AR longitudinal integration, zero Ax_AR, adding potential increments to evolved state.
- **Integration and outputs:** boundaries, ghost cells, NaN checks, max diagnostics, initial Bz error, run 3500 days, dt 60s, every-other-day snapshots, NPZ storage, contour plotting, possible numerical stability/conservation checks.
- **Validation concerns:** exact pre-SFT rotation coordinates, differential-rotation frame, FITS dimensions/axis metadata, observed timing, polar metrics, discretization signs and dimensions, gauge/flux balancing, longitudinal periodicity, diffusion stability, interpolation artifacts, convergence, physics versus code-verbatim distinction.

---

## 17. Last established answer / exact continuation point

The user asked whether, in the radial-field recovery formula `Bz(θ,φ)`, they would substitute **the same numerical `Δx` and `Δy` in all 360×416 computations**, even as θ and φ change.

**Answer: YES.** In `SFT.py`, every cell uses:

$$
\boxed{dx=dy=1\quad\text{(code grid units)},\qquad
\delta_{\rm rad}=\pi/180,\qquad
\Delta\phi=dx\,\delta_{\rm rad}=\pi/180,\qquad
\Delta\alpha=dy\,\delta_{\rm rad}=\pi/180.}
$$

The **values of θ, φ, the 2 neighboring Ax values, the 2 neighboring Ay values, and the sinθ geometry factors differ**. The local physical `Δθ` corresponding to `Δα=π/180` differs by latitude, but is **not** the grid step inserted in the original code denominator.

**The user indicated this was clear and then explicitly requested this comprehensive `sft.md` report for future Codex agents.**

---

## 18. Source pointers and scope of confidence

This report directly cross-checked the following ranges in the supplied `SFT.py`:

- Lines **1–58**: imports, rotation fit, meridional flow, inactive alternate flow.
- Lines **62–117**: previous/current/next MDI maps, longitude remapping.
- Lines **125–184**: constants, Mercator transformation, staggered coordinate arrays.
- Lines **190–260**: input interpolation, initial Ax/Ay, Bz reconstruction, initial error, velocities.
- Lines **262–314**: padding and boundary conditions.
- Lines **320–350**: `compute_B_from_A_staggered`, exact radial-curl finite differences.
- Lines **352–415**: `update_A_staggered`, Ax/Ay advection and diffusion.
- Lines **417–460**: emergence catalog and Ay_AR integration.
- Lines **463–603**: time loop, emergence construction and injection, monitoring and NPZ output.
- Lines **607–635**: Bz contour plots.

**Not inspected in this handoff:** the separate `sft-implementation-and-magnetogram-handling-review.md`, the Anthony thesis and cited paper, actual FITS contents/metadata, BMR catalog file, runtime results or graph outputs. All reported implementation facts have been tied to the supplied script; physical/correctness questions beyond the script remain labeled as hypotheses or validation tasks.

---

*End of Codex knowledge handoff.*
