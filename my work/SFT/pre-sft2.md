# pre-sft2 — Complete Conversation Handoff: Three-CR Reconstruction, Accuracy Validation, and Introduction to SFT

**Prepared:** 2026-11-18  
**Purpose:** Give future Codex agents a faithful, detailed understanding of *what the user has learned, derived, implemented, tested, questioned, and not yet verified* in this conversation. This document covers both physics and coding, including the mathematics the user independently reasoned through, numerical results, scientific limitations, and preferred approach to learning.

> **To future agents:** This is a record of a conversation, not proof that every quoted implementation claim is correct. Separate (a) algebra and code directly inspected, (b) Codex results that the user pasted, (c) reports directly supplied, and (d) remaining open questions. In particular, the complete original **Ananya `SFT.py`** was **not directly available** during the final turns. When explaining *her specific SFT solver*, inspect `SFT.py` first; the user explicitly insists on that.

## 1. User context and expectations

The user is researching solar photospheric magnetic field modeling, specifically a **three-Carrington-rotation (CR) map-reconstruction stage preceding Surface Flux Transport (SFT)**. Their implementation was initially named `pre-sft/main.py` and later reported by Codex as `pre_sft_reconstruction/reconstruct_synoptic_map.py`. The comparison baseline is a larger SFT script by **Ananya**, `SFT.py`, whose reconstruction stage produces something called `B_day106` before the simulation grid is initialized.

The user is investigating a broader solar physics problem related to spatial scales, magnetic-field stability, and distinguishing confined from eruptive solar events. This particular conversation, however, concentrates on *preparing the photospheric field for SFT, testing reconstruction correctness, and learning SFT step by step*.

**Preferred interaction:** Responses in chat should be **extremely short**, direct, mathematical and factual; show one derivation step at a time if asked. Give numeric examples in digits, with units; no unsupported analogies. Do not introduce tangents. Name spatial and time variables clearly. In this **handoff document**, detail is explicitly requested, so the comprehensive format is intentional.

**The user's understanding at the end:** They know why a synoptic magnetogram is not temporally simultaneous, how the 3-CR reconstruction operates, the observing-time sign convention, forward versus backward coordinate mapping, where the exact inverse denominator comes from, and how to test algorithmic accuracy. They are ready to learn **Ananya's actual SFT stepwise**, starting with the initial map, timestep, and solver outputs. They do *not* want further unverified assertions about her code.

## 2. The core problem: synchronized map from three CRs

Three input HMI/SDO **radial synoptic magnetograms**, each **360 rows × 720 columns**, are:

| Role | Rotation | Example FITS filename |
|---|---|---|
| Previous | CR2190 | `hmi.Synoptic_Mr_small.2190.fits` |
| Current/central | CR2191 | `hmi.Synoptic_Mr_small.2191.fits` |
| Next | CR2192 | `hmi.Synoptic_Mr_small.2192.fits` |

A full synoptic map is built from measurements taken at **different dates** as the Sun rotates, spanning approximately **27.2753 days** (a Carrington synodic period). Columns therefore lie in a common **Carrington spatial coordinate system** but represent different **observation times**. The desired reconstruction places measured magnetic features at their expected positions at a chosen **reference time**. The pre-SFT step does **not** yet integrate the entire SFT advection–diffusion–emergence equation or physically recover the full true time evolution of field *strength*; its principal operation is a model-based **spatial remapping/sampling**.

**Input:** 3 FITS magnetic maps, with field strengths (gauss / Mx cm^-2) and latitude-longitude coordinates.  
**Output:** one reconstructed 2D radial photospheric field, called `B_new` in the user's code; `B_day106` in Ananya's reported reconstruction stage.

### 2.1 Reference epoch and angle definitions

Adopt a nominal reference time `t_ref` when the Earth-observed **central-meridian Carrington longitude is 180°**. Define:

- `phi_ref = 180°`: reference central-meridian longitude. **It is not the destination longitude of every pixel.**
- `phi_obs` or `phi_src`: observed/source longitude at `t_obs` from which to read a magnetic field value.
- `phi_dest`: destination longitude of a reconstructed output pixel at reference time `t_ref`.
- `lambda`: solar latitude.
- `theta = 90° - lambda`: solar colatitude.
- `omega(theta)`: residual differential rotation of a feature relative to the Carrington coordinate frame, degrees/day.
- `Omega_C = 360° / 27.2753 days ≈ 13.2°/day`: positive **magnitude** of the apparent *scan rate* of the Earth's observing central meridian through Carrington longitude.

Crucial distinction: `d(phi_scan)/dt ≈ -13.2°/day` refers to **the apparent observing meridian's Carrington longitude**, not to the absolute rotation of a particular magnetic feature. At Carrington rotation speed, a feature is approximately stationary in Carrington coordinates; its **residual** movement is encoded by `omega(theta)`.

The user was especially concerned by the origin of minus signs and demanded that they be derived rather than memorized.

## 3. Deriving signed observation-to-reference time

### 3.1 Establish the scan direction explicitly

The user independently proposed:

- Initial longitude = `360°`; initial time = `0 days`.
- Final longitude = `0°`; final time = `27.2753 days`.

Thus, using **final minus initial** for both deltas:

\[
\Delta\phi_{\rm scan}=0^\circ-360^\circ=-360^\circ,
\qquad
\Delta t_{\rm scan}=27.2753\text{ days}.
\]

\[
\boxed{\frac{\Delta\phi_{\rm scan}}{\Delta t_{\rm scan}}
=\frac{-360^\circ}{27.2753\text{ days}}
\approx-13.2^\circ/\text{day}}
\]

The sign is conventional and must remain consistent throughout the model. Reversing only one difference convention changes the equation.

### 3.2 One consistent physical interval for both forward and backward lookup

The user chose:

\[
\boxed{\Delta t=t_{\rm ref}-t_{\rm obs}}
\]

For the observing-meridian scan between observation and reference:

\[
\Delta\phi_{\rm scan}=\phi_{\rm ref}-\phi_{\rm obs}
=180^\circ-\phi_{\rm src}.
\]

Divide by the **negative** scan rate:

\[
\Delta t=\frac{180^\circ-\phi_{\rm src}}{-13.2^\circ/\text{day}}
\]

so

\[
\boxed{\Delta t=\frac{\phi_{\rm src}-180^\circ}{13.2^\circ/\text{day}}.}\tag{1}
\]

This equation is **valid for either sampling direction**: it defines a physical interval, not an algorithmic direction. Earlier in the chat there was a confusing suggestion to automatically define an opposite signed `delta_t_b=t_obs-t_ref` for backward sampling; the user spotted that *both methods target the same reference epoch*. The final, preferred consistent definition is **`t_ref - t_obs` throughout**. A reverse-signed symbol can be introduced for convenience but must be explicitly labeled and not silently substituted.

- `phi_src=90°`: `delta_t ≈ -6.8182 days` (observation after reference; evolving back to reference is negative time).
- `phi_src=180°`: `delta_t=0`.
- `phi_src=270°`: `delta_t ≈ +6.8182 days` (observation before reference).

The user carefully distinguished `phi_ref=180°` from `phi_dest`: a target pixel may lie anywhere on the output map, while the *reference central meridian* is 180°.

## 4. Differential-rotation model and mapping formulas

The user's `omega(theta)` function is:

\[
\boxed{\omega(\theta)=0.18-2.3\cos^2\theta-1.62\cos^4\theta}
\quad [^\circ/\text{day}].\tag{2}
\]

Here `theta` is **colatitude in degrees**. The implementation uses `cos(radians(theta))` to avoid interpreting degrees as radians. **At the equator** (`theta=90°`), `omega=0.18°/day`. This is a *signed residual* relative to Carrington rotation, not the full solar rotation speed. Passing **latitude** when the formula expects **colatitude** was one of the main reported mistakes in Ananya's version.

### 4.1 Forward mapping — known source, calculate destination

The physical feature's residual longitudinal displacement over `delta_t=t_ref-t_obs` is:

\[
\boxed{\phi_{\rm dest}=\phi_{\rm src}+\omega(\theta)\Delta t.}\tag{3}
\]

If source longitude is known, compute `delta_t` from (1), then destination from (3). This is **forward sampling/mapping**.

### 4.2 Backward/inverse sampling — known destination, find source

When reconstructing an output magnetogram, **every destination pixel's longitude is known**. The unknown is *where to look in the observed source maps*:

\[
\boxed{\phi_{\rm src}=\phi_{\rm dest}-\omega(\theta)\Delta t.}\tag{4}
\]

The **minus sign** follows from rearranging (3), **not** from defining a new opposite-signed time interval. Substitute (4) into (1):

\[
\Delta t=\frac{\phi_{\rm dest}-\omega(\theta)\Delta t-180^\circ}{13.2}.
\]

Rearrange:

\[
\left(13.2+\omega(\theta)\right)\Delta t
=\phi_{\rm dest}-180^\circ.
\]

Therefore:

\[
\boxed{\Delta t=\frac{\phi_{\rm dest}-180^\circ}
{13.2+\omega(\theta)}}\quad\text{[days]}.\tag{5}
\]

Finally,

\[
\boxed{\phi_{\rm src}=\phi_{\rm dest}
-\omega(\theta)\frac{\phi_{\rm dest}-180^\circ}{13.2+\omega(\theta)}.}\tag{6}
\]

**A major conceptual milestone:** The user independently derived why the time offset has **no additional omega term** when the numerator is `phi_src-180°`, but acquires **`+omega(theta)` in the denominator** when expressing the *same time interval* solely in terms of the known `phi_dest`. It comes from eliminating the unknown `phi_src`. The extra denominator is the **exact inverse under this idealized rotation/scan model**, whereas using `13.2` with the destination longitude is a first-order approximation.

### 4.3 Numerical worked example: destination 90° at equator

Given `phi_dest=90°`, `theta=90°`, `omega=0.18°/day`:

\[
\Delta t=\frac{90-180}{13.2+0.18}=-6.7264574\text{ days}.
\]

Correct backward source lookup:

\[
\phi_{\rm src}=90-0.18(-6.7264574)
=\boxed{91.2107623^\circ}.
\]

Wrong sign in `phi_prime` (the function's original ambiguous name):

\[
\phi_{\rm wrong}=90+0.18(-6.7264574)
=\boxed{88.7892377^\circ}.
\]

The two source lookups differ by **2.4215246°**, or **about 4.843 pixels** on a `0.5°/pixel` grid. This example motivated changing the sign **and** replacing `phi_prime(phi,theta)` with descriptively named `calculate_phi_src(phi_dest,theta)`.

**Two different meanings of “backward” discussed:** A *backward coordinate lookup* for a single-time reconstructed map is **not** the same as attempting *backward-in-time full SFT evolution*. The second is generally unstable because SFT has diffusion and uncertain emergence sources (discussed below).

## 5. How three CR maps are sampled

Once `phi_src` is computed, **do not immediately reduce it modulo 360°**; the out-of-range value selects the appropriate *temporal* source CR:

| Unwrapped `phi_src` | Source |
|---|---|
| `<0°` | **Next** CR2192 |
| `0° ≤ phi_src <360°` | **Current** CR2191 |
| `≥360°` | **Previous** CR2190 |

This reversal of apparently intuitive previous/next direction comes from the synoptic **scan chronology** (the observing central meridian's Carrington longitude decreases with increasing time). The user asked specifically about outside-range source longitudes and neighbor selection.

To build the output `B_new`, the program loops over output latitude rows and destination longitude pixels, computes `phi_src`, selects the correct input-map range, interpolates the source magnetic field there, and stores the interpolated value in the corresponding destination pixel. Thus **only backward sampling is required in production**. A forward map can serve as an independent validation, but is not needed to fill `B_new`.

The central input and output are **2D grids of radial magnetic field in gauss**. This pre-SFT step relocates measured samples based on rotation geometry; it is not an SFT temporal integration and does not independently compute new physical magnetic intensities through diffusion/transport.

## 6. The actual uploaded `main.py`

The file was uploaded and inspected directly (217 lines). It reads FITS arrays for the 3 CRs, obtains WCS coordinates, builds a wrapped longitude domain, uses cubic splines on finite data, and generates `B_new`.

Key corrected functions in the uploaded code:

```python
def calculate_delta_t(phi_dest, theta):
    return (phi_dest - 180.0) / (OMEGA_0 + omega(theta))

def omega(theta):
    cos_theta = cos(radians(theta))
    return 0.18 - 2.3*cos_theta**2 - 1.62*cos_theta**4

def calculate_phi_src(phi_dest, theta):
    delta_t = calculate_delta_t(phi_dest, theta)
    return phi_dest - omega(theta) * delta_t
```

Notable other functions:

- `map_coordinates()`: FITS longitude pixel centers, latitude recovered from FITS sine-latitude coordinate, and colatitude.
- `LongitudeSpline`: builds a `scipy.interpolate.CubicSpline` only across contiguous **finite** source pixels, with `extrapolate=False`, preserving missing-data gaps.
- `build_source_splines()`: sorts the longitude coordinates **and field columns together**, extends longitudes as `(longitude-360, longitude, longitude+360)` and fields as `(B_next, B_curr, B_prev)`.
- `source_map_value(phi_src, theta)`: evaluates correct extended spline and uses nearest available colatitude row for an arbitrary interactive query.
- `reconstruct_b_new()`: computes all `phi_src` on each existing latitude row and evaluates the spline row; produces **360×720** output.
- `B_old=B_curr`, `B=B_new`: original and reconstructed maps are kept in memory.
- `grid_info()` and `print_field_statistics()`: FITS dimensions/resolution and field mean/extrema.

The old `REFERENCE_LONGITUDE = float(CURRENT_HEADER['CRVAL1']) % 360` was still present but unused by the corrected `delta_t` formula; the assistant suggested removing it as dead code if desired.

### 6.1 Original three faults, plus other implementation differences

The **three highlighted errors** in the earlier comparison with Ananya were:

1. **Latitude vs colatitude** in the residual rotation law (Ananya reportedly passed latitude where the function intended colatitude).
2. **Wrong direction/sign in source lookup** (Ananya reportedly used a positive correction where the corrected inverse under our `delta_t` convention uses subtraction).
3. **Reversed neighboring-CR choice** (Ananya reportedly mapped negative longitudes to previous rather than next).

The user separately corrected/considered the exact denominator, FITS coordinate grids, and interpolation. These became **six** distinct V0–V6 ablation factors. Do not confuse the original “three bugs” shorthand with the later **six-factor** comparison.

### 6.2 Interpolation difference

Ananya reportedly used **separate 2D `RectBivariateSpline`** interpolators per rotation. The user's program uses a **1D longitude `CubicSpline` per fixed latitude row**, spanning the three mapped CR regions. On an unchanged latitude row, longitude-only interpolation suffices for this mapping; at arbitrary latitudes, bivariate interpolation may have a purpose. Interpolating across adjacent CR seams and handling missing-data gaps are *not identical operations* in the two implementations.

The initial inspected user's output had **524 NaN pixels**; the user's code deliberately preserves NaN gaps. This is important for eventual SFT inputs, which cannot be assumed to accept NaN field arrays.

## 7. FITS coordinates, SunPy validation, and a false-positive bug

### 7.1 Longitude direction

The three HMI input FITS headers contain `CDELT1 = -0.5°`. The user's code deliberately uses:

```python
longitudes = (
    CURRENT_HEADER['CRVAL1']
    + (longitude_pixels - CURRENT_HEADER['CRPIX1'])
      * abs(CURRENT_HEADER['CDELT1'])
) % 360.0
```

Codex initially asserted that taking `abs(CDELT1)` was a bug and suggested removing it; the assistant cautioned that this conclusion was premature. On rechecking the **actual CR2190–2192 files** with **SunPy `HMISynopticMap`**, Codex withdrew the recommendation:

- SunPy **uses +0.5°/pixel** with the field columns unchanged.
- The first longitude centers are **0.3°, 0.8°, 1.3°, 1.8°**.
- The user's coordinates agree with SunPy across **all 720 columns** to **<5×10^-11°**.
- The sign of HMI synoptic `CDELT1` is a **documented product-header inconsistency**, and SunPy's absolute-value treatment agrees with HMI/JSOC map orientation.

**Final decision:** **Keep `abs(CDELT1)` for this HMI product**. Blindly applying the signed header would attach incorrect longitude coordinates to the physical field columns. Codex's verification was limited to SunPy/documented product interpretation; it explicitly said it did not independently track an actual named solar feature against a different instrument image.

SunPy reference cited in the conversation: <https://docs.sunpy.org/en/latest/generated/api/sunpy.map.sources.HMISynopticMap.html>.

### 7.2 Sine latitude, latitude, colatitude

FITS encodes one axis in **sine latitude**; the user's code converts it back with `arcsin`, then converts to colatitude:

```python
latitudes = np.degrees(np.arcsin(
    CURRENT_HEADER['CRVAL2']
    + (latitude_pixels - CURRENT_HEADER['CRPIX2'])
      * CURRENT_HEADER['CDELT2']
))
colatitudes = 90.0 - latitudes
```

This distinguishes **equal increments of sin(latitude)** from **equal increments in degrees latitude**. The user separately investigated Mercator-style SFT grids, unequal changes in spherical latitude, and `delta_x`/`delta_y` in the wider research; in *this* conversation the emphasis is that the **synoptic input grid and the downstream SFT solver grid may differ**. Exact SFT regridding must be verified from Ananya's code, rather than assumed to preserve the 360×720 shape.

### 7.3 Grid construction comparison

Codex described Ananya as using **endpoint-inclusive invented coordinate grids** rather than the original FITS WCS pixel centers, plus two-dimensional coordinate meshgrids. The user's implementation uses actual FITS pixel centers and does not need 2D meshgrid arrays simply to reconstruct output on existing latitude rows. `B_day106` to simulation-grid `Bz_0` regridding was reported to occur around **`SFT.py` lines 194–202**, and was intentionally assigned to **SFT initialization**, after pre-SFT output.

### 7.4 Header time and synoptic processing caveats

An earlier uploaded experiment report called `results(1).md` reports:

- `T_ROT` for the central CR2191 header: **2017-06-09 10:56:34 TAI**.
- The instant at which Earth central-meridian longitude was precisely 180°: **2017-06-09 10:52:02.746 TAI**, about **271.254 s earlier**.
- HMI synoptic maps are temporal composites, and their metadata include `HWNWIDTH=15`, `EQPOINTS=20`, `CARSTRCH=1`, signaling upstream windowing/processing and differential rotation stretching.

The derivation `phi_ref=180°`, `Omega_C=13.2°/day` is thus a useful **idealized geometry**, not an independently demonstrated exact observation time for every HMI pixel. Agents should not overclaim “temporally synchronized” as literally measured instantaneous full-sphere truth.

## 8. Comparing code functionality versus physical accuracy

The user repeatedly insisted: **a comparison between `B_new` and Ananya's `B_day106` is not enough to say which one is correct**. Pixel differences quantify disagreement only. To establish **error against truth**, both must be compared to the **same independently known or observed reference field**, with proper coordinate alignment and masks.

### 8.1 Pre-SFT can be tested without running SFT

Yes. Both reconstruction methods can be run and scored at their **pre-SFT output** stage without integrating any solar surface flow equation. The complete SFT is only needed to investigate *downstream forecast/evolution behavior*, which is a different validation task.

### 8.2 Two validation approaches

**Synthetic analytic ground truth**: Generate an instantaneous analytic magnetic field, simulate observations with known scan times/rotation, reconstruct with each method, and compare against the exact analytic field. Planned cases included stationary fields, latitude-dependent rotation, localized bipolar magnetic features, seam crossings, asymmetric hemispheres, and missing-pixel conditions. Synthetic truth provides exact numerical correctness under the **chosen model** but may not fully represent real HMI behavior.

**Independent observed magnetograms**: Acquire solar observations close to the common nominal reference epoch and construct a suitable radial-field reference, co-registering geometry, resolution and timestamps. HMI vector-derived radial data were preferred; full-disk LOS data can provide a **radial proxy** using a viewing-angle correction and masking low-quality off-center regions. Observational truth is only directly available over reliable visible-disc regions; Earth-observed snapshots cannot prove simultaneous *far-side* full-sphere truth.

### 8.3 Metrics discussed

| Metric | Definition / interpretation | Preferred |
|---|---|---|
| RMSE (G) | `sqrt(mean((prediction-truth)^2))`; penalizes large deviations | Lower |
| MAE (G) | `mean(abs(prediction-truth))` | Lower |
| Bias (G) | Mean signed prediction error | Close to zero |
| Pearson correlation `r` | Linear pattern agreement, not magnitude accuracy | Closer to +1 |
| SSIM | Structural similarity of spatial patterns | Higher, if appropriate to normalization |
| Valid-pixel coverage | How many cells give valid finite predictions | Higher with transparent masking |
| Additional physics checks | Polarity agreement, field/flux preservation, seams, peak field, feature position | Context-dependent |

Evaluation must score matched spatial pixels and use the **same fixed valid reference masks**, otherwise apparently small errors can result from excluding more difficult data. A raw method that produces only NaNs has **undefined error**, not `0`.

## 9. Prerequisite audit, dataset download, and Codex workflow

The user wanted to organize the work so that Codex would **not get partway through a long analysis and stop to request missing data**. Initial instruction was to inspect the repository and report **all missing inputs first**, before execution.

### 9.1 Prevent contamination from old reports

The repository contained previous audits, experiments, reports and outputs. The user explicitly directed Codex to **ignore all previous audits and previous calculated results when performing fresh comparisons**. Each new experiment should independently rerun code against original inputs. *This document* is a history handoff and can describe past findings, but future scientific reruns must not present recycled metrics as newly computed.

### 9.2 What Codex found was needed

From independent code inspection reported by Codex:

- The repo already contained the three **HMI CR2190/2191/2192 synoptic FITS** inputs needed for the same-input comparison.
- **Synthetic validation:** no externally downloaded observations needed; Codex could generate synthetic inputs/truth itself.
- **Observational validation:** needed **independent, time-stamped HMI full-disk magnetograms** near CR2191 reference time.
- Ananya's original script referenced MDI files `CR_MDI2095.fits`, `CR_MDI2096.fits`, and `CR_MDI2097.fits`, absent from the repository, but **optional** if not testing her original separate MDI-specific configuration.
- An unidentified **“Anthony's thesis”**, cited at pages 38–40 in Ananya's code, would be useful to check derivation but was **optional** for numerical validation. Its title/document was **not identified** in the conversation.

### 9.3 Specific observations acquired

The user reported that Codex downloaded **42 full-resolution FITS files (~649 MB)** to `observations/cr2191`, containing HMI vector fields, associated masks/error estimates, and HMI LOS magnetograms. Three epochs were **2017-06-09 10:48, 11:00, 11:12 TAI**. All files passed FITS decoding/dimension checks; all six record quality flags were reportedly zero. Metadata, URLs, and SHA-256 hashes were saved with the dataset. Data source: NASA/Stanford **JSOC**, using series including `hmi.B_720s` (vector) and `hmi.M_720s` (LOS). The conversation considered Codex ready to run after the acquisition completed.

**Caveat:** A downloaded `hmi.B_720s` record is not itself automatically a fully registered global radial-field map; vector-to-radial transformation, observer geometry, masks, quality, and times are analysis stages. Codex reported handling them; those details were not independently audited here.

## 10. First complete comparison: reported results

Codex reported freshly running **both pre-SFT reconstructions** (without SFT) and comparing against independent observations and synthetic truth. Original code files were preserved. At **11:00 TAI**, under common masks/resolution:

| Observational reference | User `B_new` RMSE | Adapted Ananya RMSE | Uncorrected original synoptic map RMSE |
|---|---:|---:|---:|
| LOS radial proxy | **19.459 G** | **27.161 G** | **19.637 G** |
| Vector-derived radial field | **26.907 G** | **34.788 G** | **27.122 G** |

Interpretation:

- The user's reconstruction scored **better than an adapted Ananya reconstruction** on the tested observational reference.
- The user's improvement relative to the original, uncorrected central magnetogram was **only about 0.8–0.9%**, despite the much bigger difference relative to adapted Ananya.
- **Literal Ananya output was entirely nonfinite on the raw HMI inputs**, because global interpolation with NaNs failed. Therefore, comparison against Ananya required declared input or compatibility adaptations. Do not treat adapted results as direct, untouched-program validation.
- Synthetic tests provided stronger model-specific evidence for the direction/sign/colatitude corrections, but synthetic physics is not guaranteed to perfectly reproduce HMI composites.

Codex saved `fresh_accuracy_comparison/REPORT.md`, `all_metrics.csv`, `summary.png`, plus scripts, derived arrays, masks, logs and provenance. These were **reports of artifacts on the user's computer**, not necessarily files available in this chat.

The user asked: “Does the extra `omega(theta)` denominator term alone explain the 0.8–0.9% improvement?” **No**. The quoted improvement compared the **whole final implementation** against the original magnetogram, not a denominator-only variant.

## 11. Controlled ablation: six changes, seven versions (V0–V6)

The user wanted **percentage improvements attributable to each code change**, plus a **cumulative improvement**, without exploring all `2^6=64` binary combinations. The assistant proposed a **stepwise ablation**: start with Ananya, change one factor at a time, and recompute errors at every intermediate version.

| Version | One cumulative change applied |
|---|---|
| V0 | Ananya baseline |
| V1 | Correct **latitude → colatitude** |
| V2 | Correct **neighboring CR selection** |
| V3 | Correct **source-longitude sign** |
| V4 | Include **`omega(theta)` in exact denominator** |
| V5 | Use **FITS physical coordinate grids** |
| V6 | Change to user's **gap-preserving interpolation** |

The per-step RMSE percentage formula is:

\[
\boxed{I_i = 100\frac{\mathrm{RMSE}_{i-1}-\mathrm{RMSE}_{i}}{\mathrm{RMSE}_{i-1}}.}
\]

Cumulative improvement relative to V0:

\[
\boxed{I_{0\to 6} = 100\frac{\mathrm{RMSE}_{0}-\mathrm{RMSE}_{6}}{\mathrm{RMSE}_{0}}.}
\]

**Negative improvement is a *worsening*.** Sequential percentages are **not additive** and depend on **the order** of substitutions. The user knowingly chose the quick sequential design over exhaustive 64-way factorial attribution.

### 11.1 Uploaded ablation report — synthetic ground truth

The actual uploaded `pre_sft_ablation_report.md` and `ablation_metrics.csv` contain the following **12 analytic test cases pooled**:

| Version | n | RMSE (G) | MAE (G) | Pearson r | Step RMSE improvement | Step MAE improvement | Cumulative RMSE improvement |
|---|---:|---:|---:|---:|---:|---:|---:|
| V0 | 3,110,400 | 17.7057 | 8.9584 | 0.2857 | — | — | 0.00% |
| V1 | 3,110,400 | 11.1518 | 4.9461 | 0.7118 | **+37.02%** | **+44.79%** | 37.02% |
| V2 | 3,110,400 | 11.1763 | 4.9560 | 0.7105 | **−0.22%** | **−0.20%** | 36.88% |
| V3 | 3,110,400 | 7.1711 | 2.4400 | 0.8830 | **+35.84%** | **+50.77%** | 59.50% |
| V4 | 3,110,400 | 7.1869 | 2.3250 | 0.8828 | **−0.22%** | **+4.71%** | 59.41% |
| V5 | 3,110,400 | 7.1335 | 2.2527 | 0.8845 | **+0.74%** | **+3.11%** | 59.71% |
| V6 | 3,110,400 | 7.1335 | 2.2526 | 0.8845 | **0.00%** | **+0.01%** | **59.71%** |

**Combined synthetic improvement:** **59.71% RMSE reduction** and **74.86% MAE reduction**. The method as a whole is better under these tests, but **individual changes did not all reduce every error metric**: V2 slightly worsened RMSE and MAE; V4 slightly worsened synthetic RMSE while improving MAE. Do not remove mathematically motivated changes solely because one limited test yields slightly worse aggregate RMSE without first understanding the model, data and test sensitivity.

### 11.2 Actual raw-FITS observational ablation

Using three June 9, 2017 observation times × two reference types (LOS radial proxy and vector radial), six time/reference cases were pooled under a common validity mask with **`mu > 0.7`**:

| Version | n finite scored values | RMSE (G) | MAE (G) | Pearson r | Validity |
|---|---:|---:|---:|---:|---|
| V0–V5 | **0** | — | — | — | **Invalid:** Ananya's global `RectBivariateSpline` propagates NaNs |
| V6 | **231,218** | **23.4898** | **11.3425** | **0.4064** | Valid |

**Important:** There is no valid raw-input V0 RMSE from which to compute a literal percent observational improvement V0→V6. This is an implementation/data handling failure in V0–V5, **not a score of zero**.

### 11.3 Nearest-filled observational diagnostic ablation

Codex ran a **separately labeled diagnostic**: nearest-fill missing values in each input map **for all seven variants**, then score them on an identical mask. This is **not unmodified Ananya behavior**.

| Version | n | RMSE (G) | MAE (G) | Pearson r | Step RMSE improvement | Cumulative RMSE improvement |
|---|---:|---:|---:|---:|---:|---:|
| V0 | 231,218 | 31.2039 | 13.1288 | −0.0554 | — | 0.00% |
| V1 | 231,218 | 24.0326 | 11.5230 | 0.3737 | **+22.98%** | 22.98% |
| V2 | 231,218 | 24.0326 | 11.5230 | 0.3737 | **0.00%** | 22.98% |
| V3 | 231,218 | 23.4945 | 11.3412 | 0.4063 | **+2.24%** | 24.71% |
| V4 | 231,218 | 23.4894 | 11.3430 | 0.4064 | **+0.02%** | 24.72% |
| V5 | 231,218 | 23.4898 | 11.3425 | 0.4064 | ~0.00% | 24.72% |
| V6 | 231,218 | 23.4898 | 11.3425 | 0.4064 | ~0.00% | **24.72%** |

**Combined diagnostic observational improvement:** **24.72% RMSE reduction** and **13.61% MAE reduction** versus the **nearest-filled diagnostic V0**. The largest single observational effect was the colatitude fix (~22.98%), then sign (~2.24%); the denominator change was tiny (+0.02% RMSE) and the CR-selection and interpolation differences negligible under this particular aggregate metric/case. Some subsets can worsen even if the pooled result improves.

### 11.4 Why is the denominator improvement so tiny? Is `omega(theta)` wrong?

The user asked this explicitly. The assistant correctly answered **not necessarily**: the residual `omega(theta)` is typically small relative to `13.2°/day`, so its addition changes the reconstructed source longitude only modestly. Its *algebraic justification* follows the adopted idealized model, but the empirical metric may be dominated by HMI preprocessing, magnetic evolution, interpolation, noise, resolution or the accuracy limits of the assumed reference times. **A small or even negative RMSE change does not establish that the rotation law is incorrect**. It is not legitimate to claim all six changes improved error individually.

### 11.5 Auditability boundary

The user uploaded `pre_sft_ablation_report.md` and `ablation_metrics.csv`; the executable **`run_ablation.py` was not uploaded**. The assistant could analyze reported numbers but **could not independently verify that the runner changed exactly one factor per version**. If a future agent needs strong scientific attribution, inspect the runner and synthetic truth generation, references, masks, and variant isolation.

## 12. Repository artifact management and storage decisions

After the first pre-SFT accuracy experiment, the user saw **76 unstaged files** and asked whether they were all necessary. Their stated priority was **preserving the complete methodology, numerical results, plots, conclusions and limitations**, **not being able to rerun the same analysis later**. Codex reportedly consolidated the essential content into `fresh_accuracy_comparison/REPORT.md` and proposed:

- **Keep 10**: `REPORT.md`, `all_metrics.csv`, `quadrature4/metrics.csv`, plus **7 plots embedded by the report**.
- **Remove 66**: intermediate NPZ arrays, scripts, duplicate results/figures, temporary snapshots, logs and provenance/environment files.
- **Optionally remove 52 downloaded observation files**, plus their acquisition script, that were outside the 76-file set.
- Codex claimed the 2 retained CSV files preserved **672 numerical rows**; removing the 66 proposed files would save **174.53 MiB**, and removing the additional observational products **619.14 MiB**.

The assistant supported the proposed cleanup and told Codex to retain the **original reconstruction implementations** and original **CR2190–CR2192 synoptic FITS maps**. **Scientific caution:** This preference sacrifices full independent reproducibility: deleting raw observations, scripts and provenance prevents reproducing the study from only the retained outputs, even when the final report describes its method. Do not claim the retained report alone proves correctness.

### 12.1 Linux disk measurement discussion

The user ran in `/home/user/Projects/fluXcape`:

```bash
du -sh .      # allocated disk usage in a human-readable unit
du -sb .      # sum of apparent file sizes in bytes
du -sB1 .     # allocated disk usage in bytes
```

The user observed `1.9G .` and later `1116047383 .`. **These figures do not independently prove an intervening deletion:** `du -sh` and `du -sb` measure different things (allocated blocks vs apparent bytes). Filesystems with sparse files, hard links, directory overhead, block allocation and compression can differ. The user also tried `cls` on Ubuntu; normal shell command is `clear`.

## 13. What “SFT” means in the user's current understanding

After finishing the pre-SFT map and metrics, the user said they wanted to **start SFT** and learn **one step or file at a time**. Their questions were:

1. Is the initial source field our constructed three-in-one `B_new` map?
2. Should the field be stored as an `.npy` file or another format?
3. Does the SFT code construct a new 2D field for **every numerical `dt`**? What is `dt` in **Ananya's actual code**?
4. What physical processes evolve the map forward?
5. Can SFT evolve backward in time?
6. Are fresh bipolar magnetic regions injected during the run, with positions and strengths from **SHARP** data?
7. What is *advection*, and where is it in the formula?

### 13.1 Input field and file format

`B_new` in the uploaded user `main.py` is **a 2D NumPy array in memory**, **not automatically a file named `B_new.npy`**. It *could* be stored as `B_new.npy` with `np.save`, or a FITS image with coordinate/time metadata. SFT needs **values + coordinate system + reference timestamp + compatible solver grid**, not merely an array with an arbitrary filename. The generic assistant initially suggested an `.npy` handoff as a simple project design; this suggestion must **not** be mistaken for evidence that Ananya's `SFT.py` actually reads `.npy` or consumes a same-shaped 360×720 array directly.

The generic high-level answer was: treat the reconstructed field as an **initial condition** `B(theta,phi,t0)` and evolve it forward; the initial input need not be overwritten. But the actual regridding, data shape, file format and internal evolution variable are **implementation-dependent**.

### 13.2 Four conceptual SFT processes

A simplified physics summary from this conversation:

\[
\boxed{\mathrm{SFT}=
\underbrace{\mathrm{differential\ rotation}
+\mathrm{meridional\ flow}}_{\mathrm{advection}}
+\mathrm{diffusion}+\mathrm{magnetic\ flux\ emergence}.}
\]

- **Differential rotation:** organized latitude-dependent longitudinal flux transport.
- **Meridional flow:** organized surface flux transport toward poles (in typical solar models).
- **Effective diffusion:** unresolved random motions (often associated with supergranulation) spread/mix magnetic flux.
- **Emergence source:** injects fresh magnetic regions, often represented by **BMRs** (bipolar magnetic regions) with prescribed flux/strength, polarity, geometry, location and emergence date.

The user initially thought SFT might be “just” evolving the field and adding new bipolar regions at their observed timestamps. The correction is that continuous flow and diffusion are essential too. “**Advection**” is not a separate fifth mechanism: differential rotation and meridional flow **are** the advection terms.

### 13.3 SHARP and BMR catalogue

The user proposed that bipolar-emergence parameters come from **SHARP (Space-weather HMI Active Region Patches)** data. **Generally**, SHARP observations can characterize active regions, but a SFT model needs *processed emergence events or analytic source prescriptions*; the model does not simply paste arbitrary full-resolution SHARP FITS images automatically. The exact data source, transformation, source structure and timing must be verified in **Ananya's** implementation. An earlier experiment report (below) claims that her solver uses a **SHARP-derived BMR catalogue** and inserts **analytic bipolar sources**, not a continual pixelwise assimilation of SHARP maps.

### 13.4 Backward-in-time SFT versus backward source lookup

The user specifically challenged reversibility:

- **Advection:** mathematically reversible in principle with known velocity fields, though numerical and physical limitations remain.
- **Diffusion:** backward-time integration is **ill-conditioned/unstable**: fine-scale noise is amplified.
- **Emergence:** reversing sources requires a known, accurate emergence history; generally cannot be uniquely inferred from a later map.

Thus SFT is **generally used to evolve forward in time**, not routinely reversed. This is independent of and must **not** be conflated with the *backward pixel lookup* used in the pre-SFT three-CR reconstruction.

### 13.5 Important unfinished question: numerical timestep vs saved map cadence

The user asked whether one new 2D field map is constructed for **every `dt`** and precisely **how much `dt` is**. The assistant eventually honored the user's explicit constraint:

> “Speak only after you've read Ananya's SFT code. I don't want you to answer outside of her implementation.”

At that point the assistant searched for Ananya's original `SFT.py` and the standing `sft-implementation-and-magnetogram-handling-review.md` but **could not access them as primary sources**. It explicitly refused to assign a code-specific timestep from generic theory and requested the source upload. The user asked “you don't have it, you're sure?”, and a second search again did not locate the original file.

**Important distinction for future agents:** A solver may **compute** the state at every numerical timestep but only **save** a magnetic field to disk every N steps (e.g., every other day). “A 2D map is constructed/updated at each step” and “a 2D map is archived to `.npy` every `dt`” are **different claims**. Read code before answering.

## 14. More detailed SFT implementation notes from an earlier experiment report — SECONDHAND, NOT RECHECKED AGAINST `SFT.py`

A file available here named `results(1).md` is titled **“Before-and-after experiment: Ananya SFT initialization on CR2190–2192.”** It describes an earlier review and end-to-end model experiment. It is **not** the original `SFT.py`, so its statements below are *reported findings* and should be checked against the original source before giving Ananya-specific code answers. This section is included because the user wants **all related topics covered**, and agents can use it as a guide on what to inspect.

### 14.1 Reported numerical values and solver architecture

The earlier report asserts that Ananya's model uses:

| Quantity | Reported value / implementation |
|---|---|
| Numerical integration | **Explicit Euler** |
| Solver timestep `dt` | **60 seconds** |
| Simulation grid angular increment | **1°** (`delta=1°`) |
| Effective turbulent diffusivity | **D = 3.5×10^12 cm²/s = 350 km²/s** |
| Solar radius used | **Rs = 7×10^10 cm** |
| Meridional speed parameter | **Du = 4500 cm/s** |
| Another flow parameter | `p = 2.33` |
| Reference central longitude | **phi_ref = 180°** |
| Scan magnitude | **omega_0 = 13.2°/day** |
| Initial simulation field | `Bz_0`, formed after regridding reconstructed `B_day106` |
| Internal field evolution | Reportedly evolves **two vector-potential components**, reconstructing radial field from their **curl** |
| Longitude boundaries | Reportedly periodic ghost cells |
| Latitude boundaries | Reportedly copied ghost cells |
| Emergence | Analytic bipoles added from a **SHARP-derived catalogue**, keyed by calendar dates |
| Output snapshots | Reportedly archived on **alternate days at 23:59**, not at every 60-second update |
| Output serialization | Reportedly uses `np.savez` / NPZ results after integration |

The report cited indicative locations in Ananya's `SFT.py`: reading 3 maps around lines 71–80, `RectBivariateSpline` about 93–95, source lookup around 98–117, simulation regridding around 194–202, vector potential initialization and curl around 211–237, boundary handling around 289–314, SHARP-derived catalog sourcing around 422–429 and 483–569, Euler updates and saving around 571–584, final saving/plots around 602–635. These **line numbers are pointers provided by the report**, not direct verification from this conversation's accessible original code.

It also states there is **no continuous pixel-by-pixel assimilation of magnetogram observations after initialization**. Existing field is evolved numerically, and new emergence is prescribed by BMR source events. The catalogue provides **dates**, not necessarily precision timestamps. Repeating the full synoptic-map merge at every 60 seconds is **not** what the reported solver does.

### 14.2 Reported past full-run experiments and limitations

The earlier report described a compatibility-adjusted, **3500-day** experiment with:

- **5,039,999** integration updates,
- **1,751** archived maps,
- an original simulation start of **2010-05-06**, and
- a later final archive around **2019-12-03**.

This experiment's simulation epoch was **inconsistent** with the CR2191 HMI reference in **June 2017**, so its long-run values should **not** be presented as an accurately time-aligned 2017 solar forecast. The report separately referred to an aligned-2017 **30-day control**, various compatibility adaptations, stability and conservation checks, and analytic BMR events. It noted sharp source-insertion peaks associated with specific catalogue entries. These are **reported historical audit findings**, not new conclusions established by the present discussion.

That report also gave missing pixel counts in original input CRs:

| Raw input CR | Missing pixels |
|---|---:|
| 2190 | 888 |
| 2191 | 446 |
| 2192 | 1,037 |

A finite supported latitude band of **356 rows** (original zero-based rows **2–357**) was reportedly used in one compatibility experiment to avoid polar NaNs. This is a different workflow from the user's 360×720 standalone `B_new`, which had been reported as having 524 NaNs; do not treat those counts as interchangeable.

**Use these details only as a map to what must be confirmed** by reading Ananya's `SFT.py` and its dependencies. The user's current demand is for **direct evidence from actual code** when learning the SFT stages.

## 15. Suggested stage-by-stage learning sequence, consistent with the user's current progress

**Already studied in detail:**

1. Read three neighboring HMI synoptic CR magnetograms.
2. Derive actual longitude, latitude and colatitude coordinates from FITS metadata.
3. Specify nominal `t_ref` and `phi_ref=180°`.
4. Calculate residual differential rotation `omega(theta)`.
5. Derive physical observation offset and exact inverse `delta_t`.
6. Compute each known destination's unknown source longitude.
7. Pick next/central/previous CR from **unwrapped** source longitude.
8. Interpolate source field and assemble reconstructed 2D map `B_new`.
9. Quantitatively validate pre-SFT results with synthetic truth and real HMI references.
10. Analyze stepwise effects of colatitude, CR selection, longitude sign, denominator, FITS coordinate grid and interpolation.

**Next to study, but strictly by inspecting Ananya's original SFT source:**

1. Precisely how the reconstructed field enters the solver — `B_day106`, `Bz_0`, file versus array, coordinate conversion and NaN handling.
2. Precise simulation grid and any Mercator map transformation; spatial dimensions, boundary conditions and coordinate units.
3. The solver's **state variable(s)**: directly evolving `B_r` versus vector-potential components; reconstruction by curl if applicable.
4. **`dt` in seconds, output/snapshot cadence, number of updates, saved array dimensions and disk format** — the user specifically asked this next.
5. Numerical differential rotation and flow law: identify where full and residual rotation enter and their signs/units.
6. Meridional flow formula and its coordinate dependence.
7. Diffusivity, differential operators, latitude-dependent metric factors and explicit update scheme.
8. SHARP-to-BMR catalog ingestion, emergence timing, bipolar source construction and field injection.
9. Output data structure, dates, scientific validation, mass/flux constraints, stability, epoch alignment and uncertainty.

The user prefers taking **one of these steps at a time** rather than a massive unsolicited SFT lecture.

## 16. Exact sources and status of evidence

**Directly accessible source files supplied in this conversation:**

- `main.py` — user pre-SFT reconstruction, **217 lines**, uploaded and inspected directly.
- `pre_sft_ablation_report.md` — ablation report, **75 lines**, uploaded and inspected directly.
- `ablation_metrics.csv` — uploaded metrics table, present in working folder.
- `results(1).md` — older extensive experiment report, present in working folder; contains **reported** `SFT.py` numeric settings and audit details but is *not the source code itself*.

**Referenced but not directly provided for code inspection here:**

- Ananya's complete `SFT.py`.
- `sft-implementation-and-magnetogram-handling-review.md` (the separately requested standing review file).
- `run_ablation.py`, the executable runner for V0–V6.
- Primary complete `fresh_accuracy_comparison/REPORT.md`, `quadrature4/metrics.csv`, plots.
- Full downloaded observational FITS sequences and their README; reported as existing on the user's computer and potentially cleaned up later.
- Optional original MDI maps and unidentified thesis.

**Evidence hierarchy:** mathematics derived from stated assumptions; source-confirmed facts from `main.py`; numbers reported in the **uploaded** ablation report/CSV; statements that were only **pasted as Codex results**; and more tentative source-specific facts in `results(1).md` that require confirmation from actual `SFT.py`.

### 16.1 Warnings against overclaiming

- The **exact denominator** is exact only **for the adopted idealized observation-scan/rotation model**. It does not prove that a real HMI synoptic map has those exact per-pixel observation times after upstream composite processing.
- **Synthetic** error reductions validate conformity with simulated assumptions; they do **not** establish complete real-Sun accuracy.
- Observational reference tests validate only reliably observed solar regions, with instrumental noise, geometry and limited temporal sampling; full far-side instantaneous truth was not available.
- Observational **24.72% ablation improvement** was a **nearest-filled diagnostic**, *not* a literal successful run of Ananya's original `SFT.py` on raw FITS.
- All previous comparison and ablation outputs were reported by Codex; without the runners and raw data they cannot be independently reproduced here.
- The **0.8–0.9%** improvement of the user's reconstructed map over the **uncorrected original map** is **not** the isolated benefit of the extra denominator term.
- **`delta_t` in the pre-SFT derivation is measured in DAYS and can be negative; `dt` in the numerical SFT solver is a small positive timestep (reportedly 60 SECONDS)**. Do not confuse them.
- Do not assume saving `B_new.npy` is necessary, or that Ananya's SFT **loads `.npy`**; verify her input path.
- Do not assume the SFT solver **saves a 2D FITS/NPY file every 60 seconds** merely because it updates a field at each 60-second integration step.

## 17. Compact handoff profile for Codex

> This user understands the physical and computational logic of three-CR pre-SFT reconstruction: temporally nonuniform synoptic maps, actual FITS/WCS coordinates, latitude versus colatitude, negative Carrington observing-meridian scan rate, a **single** signed `delta_t=t_ref-t_obs`, forward versus backward coordinate mapping, how eliminating `phi_src` produces the **`13.2+omega(theta)`** denominator, the corrected **minus sign** in source longitude, temporal adjacent-CR assignment, and 1D cubic source interpolation with missing-data care. They independently derived the inverse mapping and requested a worked equatorial example (target 90°, source ~91.2108°, wrong-sign ~88.7892°). They wrote/updated a functioning 360×720 Python reconstruction and had Codex run synthetic and real observational accuracy experiments and a V0–V6 ablation. They understand that **59.71% synthetic RMSE reduction**, **24.72% diagnostic observational RMSE reduction**, and **0.8–0.9% gain over the uncorrected original map** are distinct comparisons, and that individual ablation steps can worsen errors. They have started learning SFT conceptually (advection=differential rotation+meridional flow, diffusion, BMR emergence, SHARP data, limits of reverse time evolution), but now **require explanations strictly grounded in Ananya's actual `SFT.py`**. They want one short, exact question answered at a time, starting with **what numerical dt is, whether the model updates a 2D field at every dt, what it saves, and how `B_new` is handed off to initialization**. A prior report claims dt=60 seconds and alternate-day archived maps, but these **must be rechecked against `SFT.py`** before asserting them as direct source-code facts.

---

**End of handoff.** This document intentionally covers all distinct topics and decisions present in the current conversation, including small operational details, conflicting advice later resolved, quantitative results, explicit uncertainty, and the learning boundary at SFT.
