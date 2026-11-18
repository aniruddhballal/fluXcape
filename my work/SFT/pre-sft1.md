# pre-sft1 — Comprehensive Pre-SFT Learning and Code-Review Handoff

> **Purpose:** A detailed, self-contained learning-state and technical-context document for Codex agents working with the user on solar photospheric magnetograms, Carrington-rotation stitching, longitude/time reconstruction, and initialization before Surface Flux Transport (SFT). It records not only formulas but **what the user understands, what they questioned, what code actually does, numerical walkthroughs, contradictions found in previous explanations, and what remains unresolved**.
>
> **Compilation date:** 2026-11-18. **Primary basis:** The entire visible conversation on Yeates/Ananya longitude correction and mapping, cross-checked against the user's previously supplied `SFT.py` and `sft-implementation-and-magnetogram-handling-review.md`. Some broader background is drawn from earlier established project context and is explicitly labeled. This is a study/handoff record, **not a peer-reviewed validation of the algorithm**.
>
> **Agent instruction (critical):** Do not infer that the comparison's `86.4843°` result is the proven physically correct replacement for Ananya's `93.3835°` lookup. Those values follow **different directional models**. The observation-time convention, sign of the remapping, original FITS coordinate metadata, and target snapshot time are not yet conclusively reconciled. Treat the user's questions about these as scientifically open, not resolved defects.

---

## 0. How to work with this user

- The user is learning the physics, computation, and implementation **incrementally**, and wants to understand every equation, variable, substitution, sign, and data movement—not simply obtain a patch.
- In live chat, give **short, factual answers** (often one sentence or yes/no when asked). A long document is wanted **here** because it will be used as persistent context for coding agents.
- Use **numeric examples in digits**, with units and enough decimal precision to check calculations. Do not gloss over coordinate conventions.
- Keep **confirmed source-code behavior**, **mathematical derivations conditional on assumptions**, and **physically validated conclusions** separate.
- When referring to Ananya's code, consult `sft-implementation-and-magnetogram-handling-review.md` as the standing review, then the actual source `SFT.py` for code-level conclusions. The user has explicitly insisted on examining the file rather than relying on summaries.
- Do not substitute Anthony Yeates' presumed implementation for evidence. The user repeatedly challenged unsupported assertions that Yeates used forward interpolation.
- The user understands the distinction between physically moving magnetic fields on the Sun and **reassigning/correcting measurements on a synoptic map**. Do not repeatedly explain that nuance unless relevant.
- Do not mix the already-known **latitude-vs-colatitude bug** into the analysis of longitude direction unless asked. In later examples the user explicitly said to **assume that bug was fixed**.
- Avoid confusing labels: when explaining source/destination, write explicitly whether source/destination refers to **input data lookup** or the **input/output of an analytical coordinate transformation**. These are not automatically the same roles.

## 1. Scope, motivations, and broader solar-physics project

### 1.1 Research and motivation

The user's broader solar-physics project investigates photospheric and coronal magnetic fields, potentially for distinguishing confined and eruptive solar flares. Their selected research framing from prior conversations is:

**Title:** *Scale-Dependent Magnetic Stability of Confined and Eruptive Solar Events*.

**Research question:** *Which spatial scales and topological features of pre-eruption magnetic fields are necessary to distinguish confined from eruptive events? How robust are the inferred stability diagnostics when small-scale magnetic information is removed?*

They are learning pre-event magnetic fields (strength, direction, magnetic flux, connectivity, field-line structure), photospheric inputs, SFT, PFSS, and potential later modeling. They have worked with an earlier `sunalyse` solar visualization repository that used HMI photospheric maps and PFSS but did not perform SFT. The pre-SFT work is relevant to obtaining a more meaningful initial global magnetic field before further evolution or modeling. This research background is **context**, not proof that the discussed reconstruction actually yields a synchronized map.

### 1.2 What pre-SFT means in this discussion

Before the SFT evolution starts, construct an initial global photospheric radial magnetic-field map from several consecutive Carrington-rotation synoptic magnetograms. A synoptic map is built from measurements made at different times across a roughly 27-day solar-rotation interval. It is therefore spatially assembled in Carrington longitude but **not an instantaneous observation of the full solar surface**. The hope is to account for some of the time offset/differential rotation before SFT starts.

The main subjects covered in **this** conversation:

1. Whether Anthony Yeates' published method is demonstrably forward interpolation, backward interpolation, or neither on the available evidence.
2. What Yeates' quoted longitude equation says, its variables, and its stated constants.
3. What Ananya's `SFT.py` actually does when it constructs and samples corrected longitude coordinates.
4. The definitions of `phi_source`, `phi_destination`, `phi_original`, `phi_n`, reference longitude, angular velocity, and time offset.
5. The mathematical difference between a **forward coordinate transform** and a **backward sampling lookup**, and whether a direct plus-sign application is an inverse.
6. Algebraic derivation of the **exact inverse**, the **first-order approximation** with a minus sign, and when an approximation is accurate.
7. How the 2-D map's left/right longitude indexing relates—or does **not** by itself relate—to physical solar rotation and observation age.
8. Multiple numerical checks around longitude 90°, latitude 30°, and a 3.38° displacement.
9. Source-code comments: did Ananya describe her method as an approximation? (No such designation appears in the relevant code.)
10. A major nuance: **two different sign/convention models can each yield an exact algebraic inverse**; which is physically appropriate is not settled just by showing a round trip.
11. Limits of available thesis source code, original FITS files, and external verification.

---

## 2. The primary source files and where to look

### 2.1 Ananya's `SFT.py`: direct source evidence

The supplied `SFT.py` is about 21 KB and has these pertinent areas (line numbers from supplied copy; recalculate after editing):

| Location | Role |
|---|---|
| Top comment | Mentions Yeates' GitHub `sharps-bmrs` and thesis as sources. |
| Lines ~16–22 | `omega(theta)` differential-rotation profile, defined as a function of **colatitude**. |
| Lines ~65–80 | Three input `CR_MDI2095.fits`, `CR_MDI2096.fits`, `CR_MDI2097.fits` (previous/current/future). |
| Lines ~83–88 | `phi_ref=180°`, `omega_0=13.2°/day`, longitude array 0–360°, and sine-latitude coordinate array. |
| Lines ~92–96 | `RectBivariateSpline` instances for all three magnetograms. |
| Lines ~98–120 | Main longitude-remapping / backward data sampling loop, map selection, and assignment into `B_day106`. |
| Lines ~130–200 | Mercator-like simulation grid and conversions. |
| Lines ~194 onward | Further cubic interpolation onto the SFT simulation grid. |
| Lines ~321/353 | Numerical operators for SFT evolution using vector potentials. |

Direct snippets from original uploaded code:

```python
# differential rotation

def omega(theta):
    omega_deg_day = 0.18 - 2.3 * (np.cos(theta) ** 2) - 1.62 * (np.cos(theta) ** 4)
    omega_rad_sec = omega_deg_day * (np.pi / 180) / (24 * 3600)
    return omega_rad_sec

# Import previous/current/future Carrington maps:
B_prev = fits.open('CR_MDI2095.fits')[0].data
B_curr = fits.open('CR_MDI2096.fits')[0].data
B_next = fits.open('CR_MDI2097.fits')[0].data

phi_ref = np.deg2rad(180)
omega_0 = 13.2 * (np.pi / 180) * (1 / (24 * 3600))
phi_original = np.linspace(0, np.deg2rad(360), B_curr.shape[1])
theta_original = np.arcsin(np.linspace(-1, 1, B_curr.shape[0]))

spline_prev = RectBivariateSpline(theta_original, phi_original, B_prev)
spline_curr = RectBivariateSpline(theta_original, phi_original, B_curr)
spline_next = RectBivariateSpline(theta_original, phi_original, B_next)

for i in range(len(theta_original)):
    for j in range(len(phi_original)):
        delta_t = (phi_original[j] - phi_ref) / omega_0
        phi_n = phi_original[j] + (omega(theta_original[i]) / omega_0) * (phi_original[j] - phi_ref)

        if phi_n < 0:
            selected_map = spline_prev
            phi_wrap = phi_n + np.deg2rad(360)
        elif phi_n > np.deg2rad(360):
            selected_map = spline_next
            phi_wrap = phi_n - np.deg2rad(360)
        else:
            selected_map = spline_curr
            phi_wrap = phi_n

        B_corrected = selected_map(theta_original[i], phi_wrap).item()
        B_day106[i, j] = B_corrected
```

*These snippets normalize indentation and combine FITS loading lines for readability; the original also has additional `fits_file` assignments and comments. For exact edits use the repository version.*

**Important:** `delta_t` is calculated in the original loop but is **not used directly** in the expression for `phi_n`: that expression embeds the same time factor algebraically. Its presence nevertheless makes the time convention clear.

### 2.2 Review document

The user has an existing `sft-implementation-and-magnetogram-handling-review.md` with established findings. Its important verified points are:

- The code explicitly runs a 2-D kinematic SFT model for the radial photospheric magnetic field using differential rotation, meridional flow and diffusion.
- The initial map is constructed from **three MDI-labelled CR magnetograms**. The code does not inspect FITS coordinate/time metadata to establish longitude or observation timestamps.
- `theta_original = arcsin(linspace(-1,1,...))` gives **latitude** in `[-90°, +90°]`, yet `omega(theta)` is written for **colatitude**; a confirmed internal inconsistency.
- The code selects one of three maps and evaluates cubic splines at the computed lookup coordinate.
- The SFT stage later interpolates onto a different simulation grid (360 longitude centers × 416 Mercator-like latitude cells).
- The main SFT loop inserts idealized bipolar sources based on a catalogue; it does **not** periodically overwrite its field with fresh full-disk magnetograms.
- Source files and inputs necessary for complete numerical validation may be unavailable; the supplied original MDI FITS inputs are not verified.

**Standing instruction:** Consult this review whenever discussing Ananya's research code, while independently checking `SFT.py` for questions about exact statements, signs and comments.

### 2.3 Yeates' thesis and source-code search

Reference: Anthony R. Yeates, 2009 PhD thesis, University of St Andrews, thesis record: <https://research-repository.st-andrews.ac.uk/handle/10023/734>. The relevant discussed section is **Section 3.3, approximately pages 38–40; quoted Equation 3.15**. A prior assistant asserted that the thesis explicitly states `Ω₀ = 13.2°/day` and `φ_ref = 180°`, with equation/page references; this assertion was reported as verified in the earlier conversation. **An agent requiring publication-grade attribution should inspect the actual thesis pages and quotation directly.** The equation is reproduced below as *the equation previously attributed in this chat*, not as an independently typeset scan of the thesis in this handoff.

Prior investigations of Yeates' implementation:

- The thesis record's ~37.7 MB “Accompanying software.zip” was downloaded and checked by a Codex agent. The agent reported **12 `.mpg` videos**, not source code.
- A public Yeates GitHub account was identified: <https://github.com/antyeates1983>.
- The public repository <https://github.com/antyeates1983/sft_data> contains later MATLAB SFT code such as `sftdata.m`, `readSynoptic.m`, and `getEmergingRegions.m`, associated with later SFT work (described as ~2015), **not a verified copy of the 2009 thesis three-map method**.
- One earlier check examined the main MATLAB script but did **not** verify the exact interpolation scheme or neighbor count for the 2009 thesis procedure; `readSynoptic.m` had not been directly inspected at that time.
- Another GitHub link explicitly referenced in Ananya's `SFT.py` top comment: <https://github.com/antyeates1983/sharps-bmrs> (relating to SHARP/bipolar region data). Its existence in a comment is **not evidence that it implements the three-map remapping**.
- Accordingly, the **exact 2009 implementation**, whether forward scatter/gridding, backward gather/interpolation, or an equivalent algorithm, **remains unconfirmed** from inspected code.

---

## 3. Fundamentals: solar coordinates, time, and differential rotation

### 3.1 Sun as a sphere; synoptic map as a 2-D representation

The solar photosphere is spherical. A synoptic magnetogram represents a quantity such as radial magnetic-field strength on a 2-D coordinate grid, usually longitude and latitude (or a latitude transform), not an `(x,y,z)` Cartesian volume. The user compared reconstruction to transforming old `(x,y,z)` into new `(x,y,z)`, like a matrix transformation: **useful as a coordinate-remapping analogy**, with an important correction: here the operation is typically `(longitude, latitude, B) → (corrected longitude, latitude, B)` before interpolation. It is not necessarily a single constant linear 3×3 matrix because the longitude displacement depends on latitude and the longitudinal observation time.

For the longitude-only differential-rotation remap used in this discussion, **latitude does not change**; magnetic field is sampled or reassigned at new grid locations. The **magnetic value itself is not multiplied by a rotation matrix**. Subsequent interpolation may combine neighboring magnetic measurements.

### 3.2 Longitude and left/right orientation

Ananya builds a longitude coordinate vector using:

```python
phi_original = np.linspace(0, np.deg2rad(360), B_curr.shape[1])
```

That array **increases with column index**. If displayed in the natural array order with first column on the left, the assumed map goes:

```text
LEFT                                                        RIGHT
  0° -------- 90° -------- 180° -------- 270° -------- 360°
```

Therefore **90° is right of 0°, and 93.3835° is right of 90°**, *in the coordinate convention the code constructs*.

**Critical limitation:** The FITS files' real world-coordinate information and FITS image orientation were not checked by Ananya's code, so this is the **code's assigned coordinate convention**, not a verified claim about how the original MDI file is actually oriented. Scientific plots may also intentionally reverse the x-axis. Likewise, the physical rotation direction cannot be inferred just from whether the plot labels increase to the right.

### 3.3 Carrington synoptic maps are time-staggered

A synoptic magnetogram uses observations over roughly one Carrington rotation (~27.2753 days, as discussed previously). Columns generally correspond to different observation times, not all one instant. To derive a snapshot at a chosen reference epoch, one must decide how to associate each input longitude with a physical observation time and a rotation law.

Ananya's *coded* time-offset model:

\[
\Delta t(\phi)=\frac{\phi-\phi_{\mathrm{ref}}}{\Omega_0}.
\]

With her numbers:

- `φ_ref = 180°` → `Δt = 0` days.
- `φ = 90°` → `Δt = −6.81818` days.
- `φ = 270°` → `Δt = +6.81818` days.
- At 0°/360°, extrema are about `−13.63636/+13.63636` days under 13.2°/day.

Thus **in the program's signed-time convention**, the left half is assigned negative offset and the right half positive offset. If `Δt` truly means `t_observed − t_ref`, left is earlier/older and right is later/newer. **This last identification depends on the physical meaning assigned to the time variable**; it cannot be presumed without cross-checking the FITS provider's chronology and Carrington conventions.

The user asked explicitly whether left is newer than right and whether the physical solar spin goes left-to-right. We explained that **neither follows merely from the map indexing**. Determining that requires real observation-time and solar-coordinate definitions.

### 3.4 Latitude versus colatitude

Two common angular variables:

\[
\lambda=\text{heliographic latitude},\qquad
\theta=90^\circ-\lambda=\text{colatitude}.
\]

For latitude `+30°`, the corresponding colatitude is `60°`.

Ananya's code computes:

```python
theta_original = np.arcsin(np.linspace(-1, 1, B_curr.shape[0]))
```

That is **latitude**, not colatitude. But the velocity function explicitly says it is written as a function of **colatitude**, with `cos(theta)` powers:

\[
\omega(\theta)=0.18-2.3\cos^2\theta-1.62\cos^4\theta
\quad [^\circ/\mathrm{day}].
\]

At `θ=60°` (actual colatitude for latitude `30°`):

\[
\omega(60^\circ)=0.18-2.3(0.25)-1.62(0.0625)
=-0.49625^\circ/\mathrm{day}.
\]

If the code mistakenly passes `30°` directly into the colatitude law:

\[
\omega(30^\circ)=0.18-2.3(0.75)-1.62(0.5625)
=-2.45625^\circ/\mathrm{day}.
\]

This is a **separate confirmed bug/inconsistency**. For all subsequent detailed 90° examples, **assume it is fixed** and use `ω = −0.49625°/day`, as expressly requested by the user. Do not swap it back to `−2.45625` while discussing longitude sampling.

An equivalent correctly written **latitude** law is:

\[
\omega(\lambda)=0.18-2.3\sin^2\lambda-1.62\sin^4\lambda.
\]

### 3.5 Angular speed, coordinate frames, and signs

`Ω₀ = 13.2°/day` converts the angular offset from reference longitude into an assumed time difference. This is distinct from the **Carrington-relative differential rotation** `ω(θ)`. The latter can be positive or negative depending on latitude, since it is measured relative to a rotating frame. A negative `ω` does **not** mean the Sun physically spins westward or backward; it means motion in the chosen coordinate frame is slower/negative relative to a defined rotation.

For the specific latitude `30°`, `ω = −0.49625°/day`. Over `6.81818` days its absolute angular displacement is:

\[
|\omega \Delta t|=0.49625\times6.81818=3.3835227^\circ.
\]

This numerical magnitude is central to the user's questions. **Magnitude alone does not establish the physical direction or whether the source/destination timestamps were chosen consistently.**

---

## 4. Yeates: published equation versus unverified interpolation algorithm

### 4.1 Equation quoted from the thesis in this conversation

The equation repeatedly discussed and attributed to Yeates' thesis Section 3.3 / Eq. 3.15 is:

\[
\boxed{\phi_n=\phi_0+\frac{\Omega(\theta)}{\Omega_0}
(\phi_0-\phi_{\mathrm{ref}})}
\]

with:

\[
\Delta t=\frac{\phi_0-\phi_{\mathrm{ref}}}{\Omega_0},
\qquad
\phi_n=\phi_0+\Omega(\theta)\Delta t.
\]

Parameters in our example: `φ_ref=180°`, `Ω₀=13.2°/day`; rate latitude-dependent. The plus sign was explicitly discussed and challenged.

**What the equation itself establishes:** Given an input `φ₀`, it produces another coordinate `φ_n` based on assumed longitude–time relationship and latitude-dependent rotation. It specifies a numerical **coordinate relationship**, not the entire raster-resampling implementation.

### 4.2 What was claimed, challenged, and later corrected

Early assistant replies confidently called this **Yeates' forward interpolation** and interpreted `(φ₀,B)` being moved to `(φ_n,B)` (a forward scatter/regrid). The user asked pointedly: **How do you know Yeates implemented forward interpolation if his code has not been inspected?**

Corrected evidence assessment:

- The equation's nomenclature (`φ₀ → φ_n`) is *consistent with* a forward description and can be read that way.
- It does **not prove** whether the eventual implementation loops through input samples and splats values forward, loops through output pixels and inverts the transform to sample backward, or uses another equivalent approach.
- Yeates **could implement backward interpolation while leaving the quoted equation unchanged**, by solving/inverting it to find the source coordinate of each output pixel.
- Without the original 2009 source or unambiguous thesis prose specifying interpolation implementation, **do not assert** "Yeates definitely uses forward interpolation".
- The **interpolation kernel** (linear, cubic, nearest, conservative area mapping, etc.) and **number of input neighbors** in Yeates' original implementation remain **unverified**.

The conversation included a request to inspect the thesis's “accompanying software,” followed by the realization that the archive was videos and a search for Yeates' GitHub. Keep that unsuccessful verification attempt in mind; do not casually cite unrelated newer SFT code as evidence of the 2009 interpolation implementation.

### 4.3 Mathematical mapping versus interpolation

A mapping equation computes **positions**. To create a magnetic-field array at regular longitude grid points, an implementation needs an interpolation/regridding policy. There are at least two computational families:

**Forward/particle-style:** For every original sample at `φ_old`, calculate `φ_new = F(φ_old)` and distribute/regrid its `B` onto a target grid. Details include gaps, overlaps, neighbor weights, and flux conservation.

**Backward/image-style:** For every destination grid point `φ_dest`, calculate the original sample longitude `φ_src = F^{-1}(φ_dest)` and interpolate `B_old(φ_src)` to assign `B_new(φ_dest)`.

These can represent **the same geometrical mapping** if the inverse relation and interpolation conventions are implemented consistently. Whether either matches the actual solar chronology is a **separate physical question**.

---

## 5. Ananya's exact behavior as implemented — no assumptions about Yeates

### 5.1 Walk through the loop literally

For each latitude-row `i` and longitude-column `j`:

1. Treat the current column as coordinate `φ = phi_original[j]` (a **destination/index being written**).
2. Compute a nominal time offset:

   \[
   \Delta t=\frac{\phi-180^\circ}{13.2^\circ/\mathrm{day}}.
   \]

3. Compute a sampling longitude:

   \[
   \phi_{\mathrm{lookup}}=\phi+\omega(\theta)\Delta t.
   \]

4. Choose `spline_prev`, `spline_curr` or `spline_next` if that coordinate falls below 0°, within 0°–360°, or above 360°, respectively. Shift out-of-range longitude by 360° to evaluate the chosen map.
5. Evaluate a `RectBivariateSpline` at `(latitude_row, lookup_longitude)`, obtaining a (possibly interpolated) magnetic-field value.
6. Store that value in **the output map at the original grid column**:

   \[
   \boxed{B_{\rm new}(\theta,\phi)=
   B_{\rm selected\ old\ map}(\theta,\phi_{\rm lookup})}.
   \]

**Confirmed implementation property:** This is **backward data sampling / gather resampling**: loop over the destination grid, locate an input value elsewhere, and assign it into that output pixel. The implementation's mapping function has a **plus sign**. The term *backward sampling* describes the data access pattern, **not a claim that the longitude formula necessarily has a minus sign**.

### 5.2 Source and destination labels

In **Ananya's actual assignment**, define:

- `φ_dest`: longitude of `B_day106[i,j]`, i.e. `phi_original[j]`.
- `φ_src`: longitude used by `selected_map(..., phi_wrap)`—the **lookup coordinate** in one of the input CR maps.
- `φ_n` in this code **is operationally the source lookup coordinate**, **not the destination coordinate**, despite the name resembling a forward-remapping variable in a publication.

In code terms:

```text
phi_dest = phi_original[j]
phi_src  = phi_dest + omega(theta) * (phi_dest - 180°)/13.2
B_new[phi_dest] = spline_old(phi_src)
```

That source-vs-destination labeling was at the heart of a repeated user confusion: **the same algebraic formula may be labeled `φ_n`/`φ₀` as a forward coordinate relationship, while a specific program uses its computed `φ_n` as a source coordinate**. Don't silently interchange the meanings.

### 5.3 Is it "approximate" according to her own comments?

The user explicitly demanded inspection of the **actual `SFT.py`**. In the pertinent pre-SFT longitude-correction block, Ananya writes a comment directing readers to **Anthony's thesis, pages 38–40**. She **does not state** that her plus-sign calculation is an approximation to an inverse, nor provide a Taylor expansion or exact inverse formula. She appears to use the quoted plus-sign expression directly as the source lookup.

Careful distinction: "plus-sign forward coordinate equation" can be exact in its own model. **Calling her formula an approximate inverse is not justified by the code comment**; whether it acts as a physically useful approximate source lookup depends on the chosen time/sign model.

### 5.4 Interpolation type in Ananya's code

- `RectBivariateSpline(theta_original, phi_original, B_*)` is called with default spline degrees `kx=3, ky=3`: nominally **bicubic interpolation** on the source map's latitude/longitude coordinate grid (subject to SciPy behavior and constraints).
- In a simple illustrative example, a source longitude at 93.5° between 93° and 94° could be *linearly* approximated from fictitious `B(93°)=110 G` and `B(94°)=120 G` to give `115 G`. The actual code uses cubic splines, so **115 G was pedagogical, not an actual result from FITS and not necessarily what the cubic spline would produce**.
- A separate cubic interpolation stage maps reconstructed data from the original synoptic latitude grid onto the Mercator-like SFT simulation grid. Don't conflate this stage with the initial correction's source lookup.

### 5.5 Three-map boundaries and seams

Ananya uses:

```python
if phi_n < 0:       # previous map, longitude + 360°
elif phi_n > 360°:  # next map, longitude - 360°
else:              # central map
```

**Confirmed:** this is what her code does. **Not yet confirmed:** the map selection corresponds to the physical chronological neighbor for the specific `CR_MDI...fits` inputs. An earlier audit of **HMI** conventions flagged potential opposite neighboring-CR selection; **HMI analysis does not automatically prove the original MDI implementation's seam selection is wrong**. Need original FITS metadata and product definitions.

---

## 6. The main repeated numerical example: 90° longitude, 30° latitude

### 6.1 Constants and conventions

Take target output longitude `φ_dest=90°`, heliographic latitude `λ=30°`, hence colatitude `θ=60°`. Assume the confirmed latitude/colatitude error is fixed. Then:

\[
\boxed{\begin{aligned}
\phi_{\rm dest}&=90^\circ,\\
\phi_{\rm ref}&=180^\circ,\\
\Omega_0&=13.2^\circ/\mathrm{day},\\
\omega(60^\circ)&=-0.49625^\circ/\mathrm{day}.
\end{aligned}}
\]

Time offset evaluated at 90°:

\[
\Delta t(90^\circ)=\frac{90-180}{13.2}
=\boxed{-6.818181818\ \text{days}}.
\]

Angular displacement under that chosen time interval:

\[
\omega\Delta t=(-0.49625)(-6.818181818)
=\boxed{+3.383522727^\circ}.
\]

### 6.2 Exactly what Ananya's loop returns

Her formula:

\[
\boxed{\phi_{\rm lookup}=\phi_{\rm dest}+
\omega(\theta)\frac{\phi_{\rm dest}-180^\circ}{13.2}}.
\]

Substitution:

\[
\begin{aligned}
\phi_{\rm lookup}
&=90+(-0.49625)\frac{90-180}{13.2}\\
&=90+(-0.49625)(-6.818181818)\\
&=\boxed{93.383522727^\circ}.
\end{aligned}
\]

Hence, with latitude suppressed for legibility:

\[
\boxed{B_{\rm new}(90^\circ)=B_{\rm old}(93.383522727^\circ)}.
\]

This is **right-to-left information transfer** in her assumed left-to-right increasing longitude axis:

```text
                      LEFTWARD LOOKUP-TO-OUTPUT
OUTPUT 90°  <-------------------------------- SOURCE 93.3835°
```

The original measurement at exactly 90° is **not** simply moved to 93.3835° by the code. Instead, the code asks the spline at 93.3835° for a value to place at output 90°.

### 6.3 Alternative calculation if latitude bug were NOT fixed (for historical context only)

In one earlier answer the assistant used `ω(30°) = −2.45625°/day` (wrong colatitude input) and obtained:

\[
90+(-2.45625)(-6.8181818)=106.7471591^\circ.
\]

This output reflects the *original implementation's latitude inconsistency*. The user explicitly directed us to **ignore that defect** for subsequent longitude discussions, so the principal example should always use **93.38352°**, not **106.74716°**.

### 6.4 The user's qualitative interpretation

The user correctly concluded:

- In the array order that Ananya assumes, 93.3835° is to the **right** of 90°.
- Ananya takes the B value from the **right** and assigns it at 90° to the **left**.
- This is **data sampling/reassignment**, not literally moving a physical solar pixel.
- A right-to-left shift is not automatically a bug: its correctness depends on observation ages, the sign of relative angular velocity, and the target time.

The user explicitly challenged the assistant's earlier statement that the transfer is wrong *because* Yeates allegedly went the other way. The better methodological stance: **analyze Ananya's code and physical model on its own, then compare only if published conventions and implementations are actually verified**.

---

## 7. Forward mapping, backward sampling, and two different exact inverses

> **This section is crucial.** Earlier dialogue sometimes blended two distinct mapping directions, even while providing correctly solved algebra. A Codex agent should make these models explicit and never use a round-trip proof to choose physics.

### 7.1 Model A: a `+` coordinate transformation considered a *forward map*

Let

\[
F(x)=x+a(x-r),\qquad
 a=\frac{\omega}{\Omega_0},\qquad r=180^\circ.
\]

At 30° latitude, `a=−0.49625/13.2≈−0.0375946970`.

In this **hypothetical model**, `x` represents the **source**, and `F(x)` the **destination**:

\[
\boxed{\phi_{\rm dest}=
\phi_{\rm src}+\omega\frac{\phi_{\rm src}-r}{\Omega_0}}.
\]

At source 90°:

\[
F(90)=90+(-0.49625)\frac{90-180}{13.2}
=\boxed{93.383522727^\circ}.
\]

So Model A's **forward** behavior is 90° → 93.38352°.

#### Algebraic exact inverse of Model A

Start from:

\[
\phi_{\rm dest}=(1+a)\phi_{\rm src}-ar.
\]

Rearrange:

\[
\phi_{\rm dest}-r=(1+a)(\phi_{\rm src}-r).
\]

Hence:

\[
\boxed{\phi_{\rm src}=
 r+\frac{\phi_{\rm dest}-r}{1+\omega/\Omega_0}}.
\]

For destination 90°:

\[
\phi_{\rm src}=180+\frac{90-180}{1-0.49625/13.2}
=\boxed{86.484305815^\circ}.
\]

Check it by applying **the same Model A forward function**, now at the actual source:

\[
\begin{aligned}
\Delta t_{\rm src}&=\frac{86.484305815-180}{13.2}
\approx-7.08452\ \text{days},\\
F(86.484305815)
&=86.484305815+(-0.49625)\Delta t_{\rm src}\\
&=\boxed{90.000000000^\circ}.
\end{aligned}
\]

**Interpretation:** `86.4843° → 90°` is the exact source/destination pair **if Model A is the desired physical coordinate transformation**.

#### First-order approximate inverse of Model A

Let `a=ω/Ω₀`, and use the Taylor/geometric-series approximation for `|a|≪1`:

\[
\frac{1}{1+a}=1-a+a^2-a^3+\cdots\approx1-a.
\]

Then:

\[
\begin{aligned}
\phi_{\rm src}
&=r+(\phi_{\rm dest}-r)\frac{1}{1+a}\\
&\approx r+(\phi_{\rm dest}-r)(1-a)\\
&=\phi_{\rm dest}-\omega\frac{\phi_{\rm dest}-r}{\Omega_0}.
\end{aligned}
\]

Thus:

\[
\boxed{\phi_{\rm src}\approx
\phi_{\rm dest}-\omega\Delta t_{\rm dest}}.
\]

At 90°:

\[
\phi_{\rm src,approx}=90-(-0.49625)(-6.818181818)
=\boxed{86.616477273^\circ}.
\]

Compare: exact Model A inverse `86.484305815°` versus first-order approximation `86.616477273°` (difference ~0.13217°). This **is** the approximation whose derivation the user explicitly asked to see. **Ananya does not use this minus-sign approximation in the supplied `SFT.py`**; she uses the plus sign.

### 7.2 Model B: Ananya's actual `+` operation as a *backward lookup*

Rather than declare that Model A must be physically correct, read her code literally as defining:

\[
\boxed{\phi_{\rm src}=F(\phi_{\rm dest})
=\phi_{\rm dest}+\omega\frac{\phi_{\rm dest}-r}{\Omega_0}}.
\]

Under this **different model**, `F` is itself the **destination-to-source lookup relation**. If one wants to check which source-to-destination rule is its exact inverse, solve the above for `φ_dest`:

\[
\boxed{\phi_{\rm dest}=
 r+\frac{\phi_{\rm src}-r}{1+\omega/\Omega_0}}.
\]

For a source at 93.383522727°:

\[
\phi_{\rm dest}=180+
\frac{93.383522727-180}{1-0.49625/13.2}
=\boxed{90.000000000^\circ}.
\]

**Therefore Ananya's plus-sign lookup is perfectly invertible algebraically.** Her *source→destination* inverse under Model B is **not** the same as treating the `+` equation as Model A's forward transform. Merely saying "plus is forward, therefore her backward lookup is wrong" **assumes which coordinate role is intended**, and that assumption is exactly what the user contested.

### 7.3 A third, physically motivated condition considered in the chat: source time determines rotation

The dialogue tested a **particular assumed physical scenario**: a source observation at longitude `φ_src` was made at

\[
\Delta t_{\rm src}=\frac{\phi_{\rm src}-r}{\Omega_0},
\]

and an observed location advances to a reference epoch by a signed displacement:

\[
\phi_{\rm dest}=\phi_{\rm src}-\omega\Delta t_{\rm src}.
\]

**Notice the minus sign!** This is a *specific time-propagation convention*, **not simply Yeates' `+` function taken as a forward map**. Under this convention the exact inverse source lookup is:

\[
\boxed{\phi_{\rm src}=
 r+\frac{\phi_{\rm dest}-r}{1-\omega/\Omega_0}}.
\]

For destination 90°:

\[
\phi_{\rm src}=180+\frac{90-180}{1+0.49625/13.2}
=\boxed{93.260929086^\circ}.
\]

This source is on the **right** of 90°—like Ananya's lookup—but slightly different:

\[
93.383522727^\circ\quad\text{(Ananya)}
\quad\text{vs.}\quad
93.260929086^\circ\quad\text{(exact for this assumed source-time convention)}.
\]

The discrepancy is ~`0.12259364°` in source longitude. In this model, **Ananya's plus-sign source lookup is the first-order approximation of the `1/(1−a)` exact expression**:

\[
\frac{1}{1-a}\approx1+a
\quad\Rightarrow\quad
\phi_{\rm src}\approx\phi_{\rm dest}+\omega\Delta t_{\rm dest}.
\]

This was the source of the **90.1272° round-trip check** below. **It is false to say every correct backward lookup must use a minus sign; the sign depends on the forward physics/conventions being inverted.**

### 7.4 What is and is not established among these models

- **Proved algebraically:** All three formula sets can be manipulated consistently when their source/destination/time definitions are kept fixed.
- **Confirmed from code:** Ananya's implemented gather is a plus-sign destination→source lookup.
- **Not established:** Which physical time convention and sign applies to her original MDI Carrington arrays; whether her plus-sign lookup is an appropriate approximation, a misinterpretation, or appropriate for a different map chronology.
- **Not established:** Whether Yeates did forward or backward interpolation in the 2009 numerical implementation.
- **Caution:** The earlier assistant's strongly worded conclusion that `86.4843°` is "what Ananya should actually use" was **conditional on Model A and not independently demonstrated**. The later analysis reopened that conclusion, correctly.

---

## 8. The 90° → 93.3835° → 90.1272° test and its comparison to 90° → 86.4843° → 90°

The user requested a detailed **side-by-side numerical round trip**. In chat it was initially presented as one "wrong" and one "right" method. A rigorous handoff must retain the arithmetic *and* note the models are **not identical tests**.

### 8.1 Shared numbers

\[
r=180^\circ,\quad\Omega_0=13.2^\circ/\mathrm{day},\quad
\omega=-0.49625^\circ/\mathrm{day},\quad \phi_{\rm initial}=90^\circ.
\]

### 8.2 Side-by-side table

| Step | **Left: Ananya's computed lookup + a source-time physical test** | **Right: Exact inverse of Model A's plus-sign forward equation** |
|---|---|---|
| **1. Start** | `φ_dest=90°` | `φ_dest=90°` |
| **2. Source equation** | `φ_src = φ_dest + ω(φ_dest−180)/13.2` | `φ_src = 180 + (φ_dest−180)/(1+ω/13.2)` |
| **3. Substitute** | `90 + (−0.49625)(90−180)/13.2` | `180 + (90−180)/(1−0.49625/13.2)` |
| **4. Source longitude** | **`93.383522727°`** | **`86.484305815°`** |
| **5. Source observation-time offset** | `(93.383522727−180)/13.2 = −6.561854339 days` | `(86.484305815−180)/13.2 ≈ −7.08452 days` |
| **6. Test transformation** | `φ_test = φ_src − ω Δt_src` | `φ_test = φ_src + ω Δt_src` |
| **7. Numeric test** | `93.383522727 − (−0.49625)(−6.561854339)` | `86.484305815 + (−0.49625)((86.484305815−180)/13.2)` |
| **8. Result** | **`90.127202512°`** | **`90.000000000°`** |
| **9. What is demonstrated?** | Her first-order displacement is not *exact* under the independently **assumed source-time/minus-sign propagation model**. | Exact inverse of the chosen **plus-sign** mapping returns its destination, by construction. |

The assistant's earlier graphic/answer labeled the left "wrong" and the right "correct." **Do not reuse these labels as empirical conclusions:** the right succeeds because it reverses the same function, while the left pairs Ananya's plus lookup with a **different** minus-sign source-time physical propagation assumption. This is a legitimate *conditional* consistency test, not apples-to-apples proof of the physically correct mapping.

### 8.3 Derivation of the left-hand return value

Ananya's lookup:

\[
\phi_{\rm src}=90+(-0.49625)\left(\frac{90-180}{13.2}\right)
=93.383522727^\circ.
\]

Time assigned to that source longitude:

\[
\Delta t_{\rm src}=(93.383522727-180)/13.2
=\boxed{-6.561854339\ \mathrm{days}}.
\]

If that value represents `t_src−t_ref` and rotation to reference time uses `−ωΔt_src`:

\[
\begin{aligned}
\phi_{\rm test}
&=93.383522727-(-0.49625)(-6.561854339)\\
&=93.383522727-3.256320216\\
&=\boxed{90.127202512^\circ}.
\end{aligned}
\]

The user phrased this as **"the 90° we started out with becomes 90.1272° when we trace it back"**. Preserve that learning milestone, but explain the sign and time assumptions attached to the test.

### 8.4 The right-hand exact inverse test

\[
\begin{aligned}
\phi_{\rm src}
&=180+\frac{90-180}{1-0.49625/13.2}\\
&=\boxed{86.484305815^\circ}.\\
\Delta t_{\rm src}
&=(86.484305815-180)/13.2\approx-7.08452\ \mathrm{days}.\\
\phi_{\rm test}
&=86.484305815+(-0.49625)\Delta t_{\rm src}\\
&=\boxed{90.000000000^\circ}.
\end{aligned}
\]

This proves an **algebraic identity** for Model A, not that the original FITS observations physically require the Model A sign.

### 8.5 Like-for-like round trip for Ananya's *actual code mapping*

To avoid the confusion, use the inverse of **her own function**, not a different sign convention. If her coded mapping is `φ_src=F(φ_dest)` with `F(x)=x+ω(x−180)/13.2`, then:

\[
\begin{aligned}
F(90)&=93.383522727^\circ,\\
F^{-1}(93.383522727)
&=180+\frac{93.383522727-180}{1-0.49625/13.2}\\
&=\boxed{90.000000000^\circ}.
\end{aligned}
\]

So **the code's algebra is invertible and self-consistent**. Whether `F` correctly relates an output pixel to an older/later physical observation is a **physical model validation task**, not a test of whether the function has an inverse.

### 8.6 Like-for-like consistency for the source-time/minus propagation model

For source-time propagation `G(s)=s−ω(s−180)/13.2`, the exact source whose propagated destination is 90° is:

\[
\begin{aligned}
\phi_{\rm src,exact}&=180+\frac{90-180}{1-(-0.49625/13.2)}\\
&=\boxed{93.260929086^\circ},\\
G(93.260929086)&=\boxed{90.000000000^\circ}.
\end{aligned}
\]

This is the appropriate **exact versus approximate** comparison **if** this source-time physical equation is the correct one for the data. There is no need for an 86° leftward source in that particular model.

---

## 9. Other numerical examples and intermediate questions from the discussion

### 9.1 Hypothetical magnetic-field values and interpolation

The learning sequence used an illustrative coordinate **93.5°** instead of 93.3835° to make interpolation easy. If a contrived source map has:

```text
B_old(93°) = 110 G
B_old(94°) = 120 G
```

then *linear* interpolation halfway gives:

\[
B_{\rm old}(93.5^\circ)\approx\frac{110+120}{2}=115\ \mathrm{G}.
\]

Ananya-style gather would put that sampled value in the output cell at `90°`: `B_new(90°)≈115 G`. But the **actual cubic spline** may differ, and no real source FITS measurements were used in this example. The purpose was to show **which data the code retrieves**, not to predict an actual magnetogram.

### 9.2 Multiple similar-looking angular shifts

- Angular speed at heliographic latitude 30°: `−0.49625°/day` relative to the chosen Carrington frame.
- Nominal time difference at `90°`: `−6.8181818 days`.
- Product `ωΔt`: `+3.3835227°`.
- Ananya gathers from **93.38352°** into destination **90°**.
- Model A `+` forward map sends source **90° → 93.38352°**.
- Model A inverse for destination 90° retrieves **86.48431°**, mathematically equivalent only if Model A is the intended physical forward relation.
- Model A first-order inverse (minus sign) gives **86.61648°**.
- Source-time minus-rotation model exact source for destination 90° is **93.26093°**; Ananya's **93.38352°** is a first-order approximation under that model.
- Source-time test on Ananya lookup returns **90.12720°**, an approximately `0.12720°` destination mismatch under that test's assumptions.

### 9.3 Prior numeric slips to avoid

Several earlier assistant utterances gave slightly inconsistent intermediate values when calculating `86.4843°`, `93.2609°`, or time offsets, and one answer briefly conflated the `106.747°` latitude-bug case with the `93.3835°` corrected-latitude case. Recompute before using numbers in code or scientific text. The values above are numerically checked using double precision and the specified constants.

---

## 10. Physical interpretation: the user's critical challenges

### 10.1 Is right-to-left inherently wrong?

**No.** The user rightly objected to the assistant repeatedly equating right-to-left with incorrect physics simply because a quoted Yeates equation seemed to go in the opposite direction. The code's data movement is demonstrably right-to-left for the example, but that direction could be correct depending on:

- How the FITS provider orders Carrington longitude columns.
- Whether a longitude column's signed offset measures `t_obs−t_ref` or `t_ref−t_obs`.
- Whether the magnetic feature is extrapolated forward in physical time or inferred backward in time.
- Which physical angular velocity and reference frame is used.
- Whether the target time really corresponds to reference longitude 180°, and how the selected three CR files align temporally.

### 10.2 Does the Sun rotate left-to-right on the plotted 2-D map?

The map's display direction is **not physically invariant**. Solar rotation is a physical motion in 3-D, while Carrington longitude in the synoptic array is an angular coordinate with a chosen sign and convention. An increasing x-axis in the visualization does not on its own establish whether material rotates toward larger or smaller plotted longitude in the Carrington frame.

### 10.3 Is the right side older or newer?

The code's numerical signed time offset says `Δt(90°) < 0` and `Δt(270°) > 0`, assuming 180° is zero. If these are genuine observation times relative to reference, right has later timestamps. **But the input FITS metadata and the actual observational chronology are unverified**. The review explicitly notes no authoritative FITS timestamp mapping is loaded. Do not equate the sign of `delta_t` with established physical age without defining its sign convention.

### 10.4 Does 3.38352° equal how far the Sun rotates in 6.81818 days?

**By construction for that chosen relative rotation rate:**

\[
|\Delta \phi|=|\omega \Delta t|=0.49625\times6.81818=3.38352^\circ.
\]

But a correct **remapping to a reference time** must use the observation age associated with the **actual source location**, not arbitrarily reuse the destination column's age unless making a documented approximation. The model `Δt(φ)` is part of the logic and changes when `φ` changes, explaining the `0.12720°` comparison in one sign convention.

### 10.5 Distinguish physical reconstruction from algebraic verification

If an exact inverse recovers the original coordinate, that confirms the equations are algebraically inverse. It says nothing by itself about whether those equations describe **the right physics**. A physically correct solver could use an approximate coordinate mapping; a physically wrong model can still have a perfect mathematical inverse.

The user's core request evolved from "Which formula is right?" to **"Analyze Ananya's code without importing assumptions about Yeates' implementation; validate her signs against physical observation times and differential rotation."** Agents should honor this framing.

---

## 11. The role of `delta_t` and the apparent source/destination circularity

The user earlier explored whether `Δt` should be calculated at **the source** or **the destination**, and noticed circularity: if the source coordinate is unknown, and `Δt` depends on that source coordinate, how do we solve for it?

This is the reason an **exact inverse** can contain a denominator different from a simple plus/minus displacement.

For the generic affine coordinate transform:

\[
\phi_{\rm dest}=\phi_{\rm src}+a(\phi_{\rm src}-r)
\]

`φ_src` appears **twice**—once on its own and once inside the time-dependent correction. Rearranging collects both occurrences:

\[
\phi_{\rm src}=r+\frac{\phi_{\rm dest}-r}{1+a}.
\]

A first-order approximation simply **evaluates the time offset at the known destination** instead of the unknown source, yielding the familiar sign-changed expression for this chosen forward transformation. That shortcut is accurate only when the ratio `|ω/Ω₀|` is small enough for the scientific tolerance.

However, **different physical rotation/time conventions produce different denominator signs**. A Codex agent must never 'correct' the plus to minus mechanically without proving what its input and output coordinates and timestamps mean.

---

## 12. Summary of what the user knows and what remains to learn

### 12.1 Established conceptual understanding demonstrated in conversation

The user has demonstrated understanding that:

- A solar synoptic map is a 2-D representation of field measurements on a spherical photosphere.
- Columns correspond to different longitudes **and observation times**; there is a need for temporal alignment.
- The starting map may use three consecutive Carrington rotations to access field values across periodic boundaries.
- Differential rotation depends on latitude, so a longitudinal shift may differ by row.
- Correcting coordinates differs from evolving the magnetic-field values with a full SFT model.
- `Δt` is expressed in days after dividing longitude degrees by degrees/day.
- The core longitude remap involves reference longitude, input longitude, relative rotation rate, and time offset.
- Longitude coordinate increase rightward is **an implementation convention**, not automatically solar spin direction.
- Backward **sampling** means filling each output cell by looking up a coordinate in source data; it does **not inherently imply using a minus sign**.
- The calculated lookup may be fractional, so interpolation of nearby observed values is needed.
- A forward transform can be algebraically inverted, and its inverse can be approximated using `1/(1+x)≈1−x` for small `x`.
- A mapping can be tested numerically by substitution and a round trip, but observational correctness needs more than self-consistency.
- The user has identified and wants to isolate the latitude/colatitude issue from questions about longitude mapping.

### 12.2 Specific concepts that caused repeated confusion

1. **What exactly is `φ_n`?** The symbol's textual label is not sufficient: its role in a given code assignment determines whether it's a source lookup or output coordinate.
2. **Is the `+` equation correct?** It can be mathematically correct in either usage; the correct sign is determined by the physical and temporal coordinate model.
3. **Does "backward interpolation" mean the algebra must use `−ωΔt`?** No. It means **the target pixel queries the source map**. The inverse of the appropriate forward physical relationship may have different signs depending on definitions.
4. **Is `86.4843°` the necessary source for target 90°?** Only if treating the quoted `+` transformation as the correct *source→destination physical mapping*. Not established for the MDI inputs.
5. **Is Ananya's `93.3835°` necessarily wrong?** No proof from source code alone. Under one source-time physical model it is an approximate source and `93.2609°` is exact; under a different model, a different source is needed.
6. **Does a 90° round trip certify physics?** No; it only certifies the chosen equations invert.
7. **Do right/left in the array establish the Sun's direction of motion?** No.
8. **How do interpolated B values differ from relocated sample coordinates?** The equation determines where to sample or deposit; the spline computes the numeric field at fractional coordinates.

### 12.3 Open questions requiring real-world/implementation validation

- What are the exact WCS conventions and timestamp metadata in `CR_MDI2095.fits`, `CR_MDI2096.fits`, and `CR_MDI2097.fits`? Are those exact files available?
- Is the first input array column actually Carrington 0° or 360° in source FITS WCS? Does `np.linspace(0,360,N)` preserve the real coordinate convention and cell centers?
- Which direction does the solar feature drift in the FITS provider's Carrington longitude convention, relative to the model's `ω(θ)`?
- Does `Δt=(φ−180)/13.2` correspond to a source observation age `t_obs−t_ref`, or is the sign convention reversed, or is it an approximation of an observation scheduling rule?
- What exact instant is chosen as reference time? Does `φ_ref=180°` correspond to that instant in the original three maps?
- Does the correct remapping account for the fact that the source observation time itself depends on *source* longitude, and does it need an exact inverse rather than a first-order approximation?
- Is `Ω₀=13.2°/day` appropriate for the specific product and time conversion? How does it relate to the synodic Carrington period ~27.2753 days and other rotation-rate conventions?
- Are previous/next CR choices correct across `0°/360°` seams for these MDI products?
- Are the input maps spatially Carrington registered, stretched, polar filled, or otherwise preprocessed such that applying an extra shift could double-count a correction?
- What error does each candidate remapping actually yield against independent near-central-meridian LOS/vector observations, active-region tracking, or future full-disc maps?
- Does the operation conserve signed/unsigned flux on the sphere when regridded, given latitude-dependent shear and cubic interpolation?
- Is there accessible 2009 Yeates source or unambiguous thesis prose documenting **interpolation kernel and mapping implementation**?

---

## 13. Suggested Codex validation plan (not previously performed in this conversation)

This section is **proposed future work**, distinct from confirmed findings.

1. **Open the exact original MDI FITS files**, including headers. Print data shape, `CRPIX`, `CRVAL`, `CDELT`, longitude units, time keywords, polarity convention, projection, polar treatment, and pixel-center locations. Preserve/review exact filenames and source provenance.
2. **Formalize a physical coordinate convention** on one page: longitude increases which way? How does a fixed surface feature drift in Carrington longitude for `ω>0` or `ω<0`? Precisely what is `Δt(φ)`? Define reference time.
3. **Derive `φ_source(φ_destination)` from the physical timing model**, rather than borrowing a plus/minus sign from a differently labeled coordinate transform.
4. **Build synthetic tests** with known moving Gaussian magnetic regions at known latitudes and observation times. Generate synoptic samples at each column's assigned time. Recover a reference snapshot with (a) current plus lookup, (b) exact inverse based on derived physical model, and (c) first-order approximation. Measure longitude error in degrees and map error in gauss.
5. **Check longitude seam chronology** with synthetic spots crossing 0°/360°, testing previous and next CR selection. Make plots and assert map identity at known points.
6. **Test spline behavior** on gradients and polar conditions, including overshoot, field sign preservation, flux conservation, and effects of spatial resolution.
7. **Validate with observed full-disc reference snapshots** where possible, including uncertainty from far-side unobserved regions and magnetogram calibration.
8. **Compare with published reconstruction methods** only after verifying exact source text and implementations, including Yeates' thesis pages 38–40.
9. **Keep latitude/colatitude fix separate** in isolated regression tests before evaluating the longitude change.
10. **Write a traceable issue verdict** for each suspected bug: code evidence, assumed physical model, proof/test, numerical discrepancy, data-specific caveat, and recommended change.

The review from prior work also mentions initial-map assimilation limitations: evolution after initialization is model-based and not continuously replaced with full observed maps. This should not be confused with the pre-SFT reconstruction quality.

---

## 14. Conversation chronology / question-by-question map

This index records the *width* of the discussed topics, including important unsuccessful reasoning and revisions. It is useful for future agents to reconstruct the user's mental model and avoid repeating disputed claims.

| Stage | User's question or insight | What was discussed or established |
|---|---|---|
| 1 | "We were supposed to check what interpolation Anthony used?" | Goal: identify exact interpolation type and neighbors, not simply quote the longitude equation. |
| 2 | "Check" Yeates' repository | Public MATLAB repo identified, but original 2009 remapping code not verified. |
| 3 | "How do you even know Anthony uses forward interpolation?" | Assistant retracted excessive certainty: equation ≠ verified implementation. |
| 4 | "Could he also use backward interpolation?" | Yes; a backward implementation can invert a published coordinate relation. |
| 5 | "Without changing any published equations?" | Yes, mathematically solve the same published equation for lookup coordinate. |
| 6 | "Is Ananya using backward interpolation? Is it wrong?" | Code definitively fills destination grid from source spline; physical correctness of its longitude relation remained conditional. |
| 7 | "Just change plus to minus?" | Early assistant said minus approximates inverse of a **chosen plus-forward model**; later nuance: not automatically applicable to her source-time convention. |
| 8 | "Why bring up exact inverse?" | Explained first-order shortcut vs inverse of an affine map. |
| 9 | "Is inverse formula in Anthony's paper?" | Not verified there; derived algebraically by assistant. |
| 10 | "Why can't she use the plus formula?" | Earlier answer presumed plus equation was a physically mandated forward map; user challenged that presumption. |
| 11 | "What's Yeates' main formula?" | Repeated `φ_n=φ₀+[Ω(θ)/Ω₀](φ₀−φ_ref)`. |
| 12 | "Did he state 13.2 and 180? Yes/no" | Prior assistant reported yes and cited thesis p.40; future source audit should recheck. |
| 13 | "What do phi_source and phi_destination mean?" | Source = where B is read; destination = where new B is stored; equation labels must be interpreted in context. |
| 14 | "Is this like a matrix transformation?" | Approximately a coordinate remap on the solar sphere; latitude-dependent, not simply constant Cartesian matrix. |
| 15 | "What's approximate backward formula and derivation?" | For **inverse of Model A**, Taylor series yields `φ_src≈φ_dest−ωΔt_dest`. |
| 16 | "Does Ananya ever say her equation is approximate?" | Review was insufficient; user insisted on checking real `SFT.py`; relevant comments do not say so. |
| 17 | "She's using minus sign, right?" | No; exact code uses the plus sign. |
| 18 | "But phi_n is destination, so isn't her plus formula right?" | Operationally in her code `phi_n` is the **source spline lookup**, whereas `phi_original[j]` is destination index. |
| 19 | "Show numbers substituted, actual output versus proposed output" | 90° → 93.38352° code lookup (fixed latitude); conditional Model A inverse → 86.48431°. |
| 20 | "Don't mix latitude-colatitude with this" | From here on always use `θ=60°` for latitude 30° and `ω=−0.49625°/day`. |
| 21 | "Show side by side phi_source and phi_destination" | Source/destination tabulated, emphasizing both methods fill output 90°. |
| 22 | "Is 90° right or left of 0°?" | Depends on display/coordinate orientation. |
| 23 | "What numbering does Ananya's input use?" | Her *assigned* longitude array increases 0→360° as column index increases; original FITS WCS unverified. |
| 24 | "She takes right and puts left?" | Yes: 93.38352° → output 90° in the example. |
| 25 | "Isn't that the correct direction?" | Could be; assistant's automatic objection based on presumed Yeates forward mapping was unjustified. |
| 26 | "Don't compare to Yeates; analyze her code alone" | Agreed. Physical correctness needs timestamps, relative rotation sign, target time. |
| 27 | "If right→left makes sense, does Sun rotate left→right, and is left newer?" | Neither follows from plot direction. Code's `Δt` numerically gives negative on left, positive on right; interpretation depends on physical convention. |
| 28 | "What's inherently wrong with copying right to left?" | Nothing by itself; correct/incorrect depends on model. |
| 29 | "Does her 93.3835→90 shift match rotation in that time?" | Magnitude matches `|ωΔt(90)|`, but source's own time differs; one assumed source-time propagation gives 90.1272°, not 90°. |
| 30 | "Can exact inverse go 90→86 and back to 90?" | Yes: the algebraic inverse of chosen Model A does; that does not prove Model A is physical. |
| 31 | "Show both complete step-by-step, side by side" | Produced 90→93.3835→90.1272 against 90→86.4843→90, later noted **these are different transformation definitions**. |
| 32 | "Make `pre-sft1.md` with all topics for Codex" | This document; includes technical details, examples, corrections and open questions, and learner-state summary. |

---

## 15. Compact formula reference sheet

### Definitions

\[
\begin{aligned}
\lambda&=\text{latitude},\\
\theta&=90^\circ-\lambda=\text{colatitude},\\
\omega(\theta)&=0.18-2.3\cos^2\theta-1.62\cos^4\theta\ [^\circ/\mathrm{day}],\\
\Omega_0&=13.2^\circ/\mathrm{day},\\
r&=\phi_{\rm ref}=180^\circ,\\
a&=\omega/\Omega_0,\\
T(\phi)&=(\phi-r)/\Omega_0.
\end{aligned}
\]

### Ananya's implemented backward gather

\[
\boxed{\phi_{\rm src}=\phi_{\rm dest}+\omega T(\phi_{\rm dest})}
\]

\[
\boxed{B_{\rm new}(\theta,\phi_{\rm dest})=
B_{\rm old}(\theta,\phi_{\rm src})}
\]

### Algebraic inverse of `F(x)=x+ωT(x)` (if `F` is the forward transform)

\[
\boxed{F^{-1}(y)=r+\frac{y-r}{1+a}}
\]

First-order approximation:

\[
\boxed{F^{-1}(y)\approx y-\omega T(y)}
\quad (|a|\ll1).
\]

### Algebraic inverse of `G(x)=x−ωT(x)` (if this is physical source→destination propagation)

\[
\boxed{G^{-1}(y)=r+\frac{y-r}{1-a}}
\]

First-order approximation:

\[
\boxed{G^{-1}(y)\approx y+\omega T(y)}
\quad (|a|\ll1).
\]

**Do not interchange these two equations or their physical interpretations.**

### Numbers for latitude 30° and target longitude 90°

| Quantity | Value |
|---|---:|
| Colatitude | 60° |
| `ω(60°)` | −0.49625 °/day |
| `T(90°)` | −6.818181818 days |
| Ananya `φ_src = F(90°)` | **93.383522727°** |
| Inverse of plus-forward map `F⁻¹(90°)` | **86.484305815°** |
| First-order approximation `90°−ωT(90°)` | **86.616477273°** |
| Exact inverse of minus-forward map `G⁻¹(90°)` | **93.260929086°** |
| Test `G(F(90°))` | **90.127202512°** |
| Test `F(F⁻¹(90°))` | **90.000000000°** |
| Test `G(G⁻¹(90°))` | **90.000000000°** |
| Test `F⁻¹(F(90°))` | **90.000000000°** |

---

## 16. Agent guardrails and next conversation state

**Do:**

- Treat `SFT.py` as authoritative for *what it computes*; cross-reference the review and original code.
- Ask what a variable represents in source code **at the point of sampling or assignment**, instead of relying on Greek symbol labels.
- Keep same-number examples with units and correctly fixed colatitude throughout.
- Separate mathematical identity checks from physical checks against observational metadata and solar-rotation signs.
- Reassess the 0°/360° map seam choices using actual MDI product metadata.
- For claims about Yeates, verify the original source or thesis rather than extrapolating from a later GitHub repo.

**Do not:**

- Announce that Ananya's plus-sign lookup is physically wrong solely because a plus-sign *forward* interpretation exists.
- Announce that 86.4843° is the actual correct source location without establishing that Model A is the physical mapping.
- Declare `90.1272°` a universal error from Ananya's code. It is the result of an additional specific source-time/minus-rotation test, not a value `SFT.py` itself prints.
- Assume the original FITS file is oriented exactly as Ananya's constructed 0→360° vector.
- Assume any algebraically invertible transform is observationally correct.
- Conflate relative differential rotation `ω` with total sidereal/synodic solar spin.
- Use the known latitude/colatitude bug to distract from the user's current investigation of the longitude shift.

**Current place in the learning dialogue:** The user has understood that the code's **93.3835° (right) → 90° (left)** data transfer is a lookup, that its magnitude is `|ωΔt|`, that the physical validity of its sign requires independent checking, and that comparing `90→93.3835→90.1272` with `90→86.4843→90` involves **different assumed directional equations**. They wanted a persistent, comprehensive Markdown handoff before taking the investigation further.

---

## 17. Source/provenance map and strength of evidence

| Claim | Status | Source or basis |
|---|---|---|
| Ananya loads 3 MDI-labelled CR FITS files | **Code-confirmed** | `SFT.py`, import section ~lines 71–79 |
| Ananya constructs longitudes 0–360° increasing with column index | **Code-confirmed** | `SFT.py`, `phi_original` ~line 86 |
| Ananya uses 180° reference, 13.2°/day base rate | **Code-confirmed** | `SFT.py` ~lines 83–84 |
| Ananya calculates a plus-sign lookup and samples `RectBivariateSpline` | **Code-confirmed** | `SFT.py` ~lines 98–116 |
| Ananya uses default bicubic spline for sampling | **API/code-inferred** | `RectBivariateSpline` defaults and absence of `kx,ky` overrides |
| The map's input theta array is actually latitude | **Code/math-confirmed** | `arcsin(linspace(-1,1,N))` versus `omega(theta)` colatitude usage |
| Ananya's comments call its mapping an approximation | **Not found in relevant code** | Comments around map-loading/remapping block |
| Yeates Eq. 3.15 as quoted with plus sign | **Quoted earlier; primary text should be cross-checked** | Yeates 2009 thesis, Section 3.3, record link above |
| Yeates 2009 code uses forward interpolation | **Unverified** | No original remapping source inspected |
| Yeates 2009 code uses backward interpolation | **Also unverified** | No original remapping source inspected |
| Exact inverse of `F(x)=x+a(x−r)` | **Mathematically proven** | Derivation in §7.1 |
| First-order inverse Taylor series | **Mathematically proven, conditional on small `|a|`** | Derivation in §7.1 |
| Ananya's 93.3835° lookup at corrected latitude | **Code/math-confirmed** | Direct substitution in source expression |
| 90.1272° return from using `G(F(90))` | **Mathematically correct conditional calculation** | Explicit auxiliary minus-sign/source-time propagation assumption |
| 86.4843° is physically correct source for MDI snapshot | **Not established** | Requires verified timing/sign model |
| Right-to-left on Ananya's plotted x-axis | **True in its constructed coordinate ordering** | Code's longitude indexing; actual FITS orientation unverified |
| Ananya's initial map is successfully time synchronized | **Not established** | Review notes missing metadata/validation |

---

## 18. Glossary of terms in the conversation

- **Photosphere:** Solar visible-surface layer where many magnetic observations are referenced.
- **Radial magnetic field `B_r` / `Bz`:** Surface-normal magnetic field, often in gauss (G), mapped over latitude and longitude.
- **Synoptic magnetogram:** Compiled map using observations collected across a solar-rotation interval rather than a simultaneous full-globe image.
- **Carrington rotation (CR):** Solar-rotation indexing used to define longitudinally organized synoptic products.
- **Carrington longitude `φ`:** Longitude coordinate in a rotating solar frame; plotting orientation and time convention must be defined.
- **Latitude `λ`:** Signed north/south angle, −90° to +90°.
- **Colatitude `θ`:** Angle from north pole, 0° to 180°; `θ=90°−λ`.
- **Reference longitude `φ_ref`:** Chosen longitude whose nominal time offset is zero (180° in code).
- **`Ω₀`:** Angular rate used to convert longitudinal position difference to a nominal time offset (13.2°/day in code).
- **Differential rotation `ω(θ)`:** Latitude-dependent angular rate relative to chosen Carrington/rotating frame.
- **`Δt`:** Signed nominal time difference between a longitude's observation and reference, dependent on convention.
- **Forward mapping:** Compute destination coordinate for a known source coordinate.
- **Backward sampling / pull resampling:** For each destination output pixel, query source data at a calculated source coordinate.
- **Exact inverse:** Algebraically solve a mapping equation for the input variable, under the same definitions.
- **First-order approximation:** Keep only constant/linear terms in a small parameter such as `ω/Ω₀`; introduces calculable error.
- **Cubic spline interpolation:** Smooth interpolation from neighboring values; Ananya uses `RectBivariateSpline` for source-field lookups.
- **SFT:** Surface Flux Transport, numerical evolution of photospheric radial magnetic field using prescribed flows, diffusion and sources.
- **PFSS:** Potential-Field Source-Surface coronal field extrapolation; not performed as a consequence of Ananya's SFT in the supplied code.
- **MDI/HMI:** Solar magnetic observation instruments/product families, whose metadata and map chronology must not be treated as interchangeable without inspection.

---

**End of handoff. Main takeaway for Codex:** The user can track the equations and their numerical consequences and wants a **source-grounded, physically defensible sign and timing analysis** for Ananya's pre-SFT magnetogram reconstruction. The remaining problem is not merely "flip a sign"; it is to establish source/output coordinate roles, physical time conventions, FITS longitude ordering, differential-rotation reference frame, and appropriate mapping inversion before making a scientifically justified correction.
