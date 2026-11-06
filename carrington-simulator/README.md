# Carrington synoptic-map time simulator

A standalone, locally runnable Streamlit + Plotly teaching app in `carrington-simulator/`.
It generates synthetic bipolar radial magnetic fields with NumPy; no solar files,
accounts, or data downloads are needed. Existing research code is independent of this app.

## Run locally

Use Python 3.10 or newer (tested with Python 3.12). From the repository root:

```powershell
cd carrington-simulator
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. Stop the server with Ctrl+C. These commands do not
require PowerShell script activation. Dependencies need an internet connection
for their initial installation; the application itself works offline.

macOS / Linux:

```bash
cd carrington-simulator
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Run the physics and Streamlit interaction tests from `carrington-simulator/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

`pytest.ini` limits default discovery to this standalone app's `tests/` directory;
the existing research scripts elsewhere in the repository are not part of this suite.

## Suggested walkthrough

1. Leave **Differential Rotation OFF** (the default). Enable **Guided learning**.
2. In **Build observations**, press **Play**. The scan starts at 359° and moves
   toward 0°. Panel A is the instantaneous surface, and B accumulates its columns.
   Rigid rotation matching the Carrington frame produces no visible drift.
3. Select 180° to see its observation at −13.635 days and its +13.635-day transport
   interval to the default reference. Purple lines identify your selected column;
   green lines identify the observation scan. Hover, zoom, and pan with Plotly.
4. Toggle differential rotation ON, rewind, and replay. The surface shears with
   latitude. The high-latitude regions make the effect easy to see.
5. Choose **Transport to reference**, then play. The completed synoptic map moves
   from its original positions to synchronized positions. Circles mark source
   locations and diamonds follow destinations at 0°, 30°, and 60° latitude.
6. Inspect Panel D, the residual, and the sampling weights. Turn **Fill unsampled
   gaps** off to see where a single rotation cannot supply a direct measurement.
7. Change the reference to 180° or 359°. Some measurements now require backward
   transport. The optional three-rotation view explains older/newer observations.

Play/pause, one-column forward/back, rewind, speed, and scrubbing share one state.
The observation slider spans −27.27 through 0 days in 0.07575-day increments.
The transport stage instead uses dimensionless progress s = 0…1; this avoids
misrepresenting an intermediate correction as a physical instantaneous map.
**Jump to t = 0** reaches the observation endpoint; **Finish transport** reaches
the selected target in the second stage. Playback stops automatically at the end.
Reset restores the initial state, including differential rotation OFF.

## Physics and coordinate conventions

All longitudes increase toward the right, in the direction of rotation. The display
runs from 0° to 359° and is periodic in space. Observation ordering is an explicit
teaching convention, not a claim about every real HMI FITS product.

For longitude φ in degrees:

```text
t_obs(φ) = −(φ / 360) × 27.27 days
t_ref    = t_obs(reference longitude)
τ        = t_ref − t_obs(φ)
```

| Longitude | Observation time (days) |
|---|---:|
| 0° | 0 |
| 1° | −0.07575 |
| 90° | −6.8175 |
| 180° | −13.635 |
| 270° | −20.4525 |
| 359° | −27.19425 |

The continuous interval is 27.27 days. Since 360° is not duplicated on the grid,
the oldest stored column is at −27.19425 days; the starting boundary has no sample.
Spatially 360° wraps to 0°, but their observation times must not be conflated.

OFF uses Ω = ΩC = 14.1844 **sidereal degrees/day** at all latitudes. ON uses the
Howard et al. (1990) law as tabulated in
[SunPy's differential-rotation documentation](https://docs.sunpy.org/en/stable/generated/api/sunpy.sun.models.differential_rotation.html):

```text
Ω(λ) = A + B sin²(λ) + C sin⁴(λ)
(A, B, C) = (2.894, −0.428, −0.370) microradians/second
          × (10⁻⁶ × 86400 × 180/π) → sidereal degrees/day
v(λ) = Ω(λ) − ΩC
Δφ = v(λ) τ
φ_destination = (φ + Δφ) modulo 360°
```

The [Carrington sidereal rate](https://docs.sunpy.org/en/stable/generated/api/sunpy.sun.constants.sidereal_rotation_rate.html)
is 14.1844°/day (Archinal et al. 2018, via SunPy). The **27.27-day synodic period**
is used only for sampling times; 360/27.27 is never substituted for ΩC.
Positive displacement moves right, negative left, with periodic wrapping.

Synthetic truth is evaluated analytically:

```text
B(φ, λ, t) = B₀(φ − v(λ)t, λ)
synoptic(φ, λ) = B(φ, λ, t_obs(φ))
```

This is pure longitudinal advection: there is no emergence, decay, meridional
flow, diffusion, observer projection, or instrument noise. The six smooth bipolar
pairs have balanced polarities, with a weak axial dipole. Regions near ±60° are
deliberate educational tracers rather than a realistic sunspot-latitude distribution.
The grid is 360 longitudes × 91 latitudes (2° latitude spacing). All magnetic panels,
including the residual, share a fixed blue–white–red ±100 G scale.

## Reconstruction and its limitations

Reconstruction reads only the sampled synoptic values and their observation times.
It never consults the known instantaneous truth. At progress s, source samples move
to `φ + s × v(λ) × τ`; their effective times are `t_obs + s × τ`.
Only s = 1 gives all samples the same time.

Each transported value deposits linearly into its two neighboring periodic
longitude nodes. Both the weighted numerator and sample weight accumulate via
`numpy.add.at`, so collisions never overwrite earlier measurements. Dividing by
the accumulated weight estimates the local **field strength**. All finite samples
contribute, including samples crossing the 0°/360° seam. This is not a finite-volume
flux-conservation algorithm: a mixed-time map is not an instantaneous set of equal
material surface patches, and its pixel sum is not a conserved magnetic flux.

Latitude-dependent transport compresses or stretches the sampled longitude range,
creating overlaps or gaps. With filling OFF, zero-weight nodes remain NaN (gray).
With filling ON, periodic linear interpolation fills them, while their weights
remain zero. Long gaps can conceal features that were never observed; interpolation
does not recover that missing information. The app reports overall and supported-cell
RMS errors, with cos(latitude) area weighting, and exposes the coverage map.

Remaining differences are due to finite sampling, remapping interpolation, and
coverage gaps. Missing physics does not cause errors in this controlled experiment,
because the truth obeys the same simplified rotation law. Real observations would
also be affected by field evolution and modeling uncertainties. OFF reconstructs
exactly; ON is generally improved but is not guaranteed to recover unobserved regions.

The optional CR 2302/2303/2304 view uses illustrative identifiers, not real dates.
Neighbor observation times are shifted by −27.27/0/+27.27 days. Their times relative
to the selected reference are tabulated, but the neighbors are not merged into the
reconstruction. This does not implement a particular researcher's correction algorithm.

## Files

- `app.py`: dashboard, playback, controls, reference selection, and learning mode.
- `solar_sim/physics.py`: analytic truth, timing, rotation, sampling, periodic remapping.
- `solar_sim/plotting.py`: Plotly magnetic maps, paths, timing plot, and coverage.
- `solar_sim/lessons.py`: eight guided learning steps.
- `tests/test_physics.py`: physical conventions and numerical validation.
- `tests/test_app.py`: Streamlit control, playback, and reset integration tests.
- `requirements.txt`: runtime libraries and test runner.

Animation uses [Streamlit timed fragments](https://docs.streamlit.io/develop/tutorials/execution-flow/start-and-stop-fragment-auto-reruns)
to refresh the Plotly panels from one shared state. Rendering speed depends on the
machine/browser; speed settings control samples advanced per nominal 0.5-second tick,
not an exact wall-clock simulation rate. Every source column is still sampled at its
exact observation time even when an animation frame advances several columns.
