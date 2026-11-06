"""Run from carrington-simulator/: python -m streamlit run app.py."""

import time

import numpy as np
import streamlit as st

from solar_sim.lessons import LESSONS
from solar_sim.physics import (
    CARRINGTON_RATE, HOWARD_COEFFICIENTS, LATITUDES, LONGITUDES, SYNODIC_PERIOD,
    accumulated_map, area_weighted_rmse, displacement, drift_rate, instantaneous_map,
    observation_time, reconstruct, rotation_rate, synoptic_map,
)
from solar_sim.plotting import add_transport_paths, coverage_figure, maps_figure, time_strip

st.set_page_config(page_title="Carrington · Time & motion", page_icon="☀️", layout="wide")

DEFAULTS = dict(differential=False, selected=180, reference=0, phase="Build observations",
                frame=0, playing=False, speed="6 columns / tick", guided=False, lesson=1,
                fill_gaps=True, neighbors=False, reschedule=False, last_tick=0.0)
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def reset():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state.pop("clock_slider", None)


def navigate(delta=None, endpoint=None):
    st.session_state.playing = False
    if endpoint is not None:
        st.session_state.frame = endpoint
    else:
        st.session_state.frame = int(np.clip(st.session_state.frame + delta, 0, 360))


def play():
    if st.session_state.frame >= 360:
        st.session_state.frame = 0
    st.session_state.playing = True
    st.session_state.last_tick = time.monotonic()


def pause():
    st.session_state.playing = False


def change_phase():
    navigate(endpoint=0)


def scrub():
    value = st.session_state.clock_slider
    if st.session_state.phase == "Build observations":
        value = (value + SYNODIC_PERIOD) / SYNODIC_PERIOD
    st.session_state.frame = int(np.clip(round(value * 360), 0, 360))
    st.session_state.playing = False
    st.session_state.reschedule = True


@st.cache_data
def completed_simulation(differential, reference, fill_gaps):
    synoptic = synoptic_map(differential)
    target = float(observation_time(reference))
    remap = reconstruct(synoptic, target, differential, fill_gaps=fill_gaps)
    return synoptic, remap, instantaneous_map(target, differential)


with st.sidebar:
    st.header("Simulation controls")
    st.toggle("Differential Rotation", key="differential",
              help="OFF: rigid rotation matches the Carrington frame. ON: Howard latitude-dependent sidereal rotation.")
    st.markdown(f"**{'ON · latitude-dependent drift' if st.session_state.differential else 'OFF · fixed Carrington longitudes'}**")
    st.slider("Selected longitude (°)", 0, 359, key="selected",
              help="Purple dotted line: inspect this source column and its observation time.")
    st.selectbox("Reference longitude (°)", [0, 180, 359], key="reference",
                 help="Reconstruct at this central-map column's observation time. Default 0° means t = 0.")
    st.selectbox("Playback speed", ["1 column / tick", "6 columns / tick", "18 columns / tick"], key="speed",
                 help="One tick is approximately 0.5 seconds, subject to rendering speed. All 360 columns are sampled at their exact times even if playback skips frames.")
    st.toggle("Fill unsampled gaps", key="fill_gaps",
              help="Periodic linear interpolation across zero-weight nodes. Turn off to expose missing coverage in gray.")
    st.toggle("Guided learning", key="guided")
    st.toggle("Show three rotations", key="neighbors")
    st.button("Reset simulation", on_click=reset, width="stretch")
    st.divider()
    st.caption("Synthetic data · no downloads\n\nBlue: negative Bᵣ · Red: positive Bᵣ\n\nPurple dotted line: selected column\n\nGreen line: observation scan")

st.title("Carrington maps: time & motion")
st.markdown("Watch a solar map being assembled, then bring its measurements to one common time.")
st.info("Teaching convention: 0° is on the left, 359° on the right. Columns farther right were observed earlier. "
        "This orientation and time order are chosen for this simulator; real HMI products may use other layouts.")

if st.session_state.guided:
    st.select_slider("Learning step", options=list(range(1, 9)), key="lesson",
                     format_func=lambda i: f"{i}. {LESSONS[i - 1][0]}")
    title, explanation, formula = LESSONS[st.session_state.lesson - 1]
    with st.container(border=True):
        st.markdown(f"**Step {st.session_state.lesson} · {title}**")
        st.write(explanation)
        st.latex(formula)

st.radio("Animation stage", ["Build observations", "Transport to reference"], horizontal=True,
         key="phase", on_change=change_phase)
buttons = st.columns(6)
buttons[0].button("▶ Play", on_click=play, disabled=st.session_state.playing, width="stretch")
buttons[1].button("Ⅱ Pause", on_click=pause, disabled=not st.session_state.playing, width="stretch")
buttons[2].button("← Back", on_click=navigate, kwargs={"delta": -1}, width="stretch")
buttons[3].button("Forward →", on_click=navigate, kwargs={"delta": 1}, width="stretch")
buttons[4].button("↶ Rewind stage", on_click=navigate, kwargs={"endpoint": 0}, width="stretch")
buttons[5].button("Jump to t = 0" if st.session_state.phase == "Build observations" else "Finish transport",
                  on_click=navigate, kwargs={"endpoint": 360}, width="stretch")


@st.fragment(run_every=0.5 if st.session_state.playing else None)
def dashboard():
    if st.session_state.reschedule:
        st.session_state.reschedule = False
        st.rerun(scope="app")
    if st.session_state.playing and time.monotonic() - st.session_state.last_tick >= 0.45:
        increment = int(st.session_state.speed.split()[0])
        st.session_state.frame = min(360, st.session_state.frame + increment)
        st.session_state.last_tick = time.monotonic()
        if st.session_state.frame == 360:
            st.session_state.playing = False
            st.rerun(scope="app")

    state = st.session_state
    building = state.phase == "Build observations"
    fraction = state.frame / 360
    clock = -SYNODIC_PERIOD + fraction * SYNODIC_PERIOD if building else 0.0
    target = float(observation_time(state.reference))
    observed_at = float(observation_time(state.selected))
    elapsed = target - observed_at

    if building:
        state.clock_slider = float(clock)
        st.slider("Observation timeline (days; t = 0 is the central 0° observation)",
                  -SYNODIC_PERIOD, 0.0, step=SYNODIC_PERIOD / 360,
                  format="%.5f d", key="clock_slider", on_change=scrub)
    else:
        state.clock_slider = float(fraction)
        st.slider("Transport progress s (0 = original positions; 1 = reference-time positions)",
                  0.0, 1.0, step=1 / 360, format="%.3f", key="clock_slider", on_change=scrub)
        st.caption("The observation interval is complete (−27.27 to 0 days). This slider animates each "
                   "measurement's correction; intermediate frames do not represent a single physical time.")

    metrics = st.columns(4)
    metrics[0].metric("Observation clock", f"{clock:+.5f} d", help="Absolute time relative to the central 0° observation.")
    metrics[1].metric("Reference time", f"{target:+.5f} d", help="Target time of the reconstruction.")
    metrics[2].metric(f"{state.selected}° observed at", f"{observed_at:+.5f} d", help="Actual observation time of the selected column.")
    metrics[3].metric("Signed transport interval τ", f"{elapsed:+.5f} d", help="Reference minus selected observation time. Positive = forward; negative = backward.")

    synoptic, final, truth = completed_simulation(state.differential, state.reference, state.fill_gaps)
    scan = 360 - state.frame if building and state.frame > 0 else None
    surface_time = clock if building else target
    surface = instantaneous_map(surface_time, state.differential)
    accumulation = accumulated_map(synoptic, clock) if building else synoptic
    st.subheader("A–B · Watch the surface and collect its columns")
    st.plotly_chart(maps_figure([surface, accumulation],
                                [f"A · Instantaneous surface at {surface_time:+.3f} d",
                                 f"B · Synoptic map: {state.frame if building else 360}/360 columns"],
                                selected=state.selected, scan=scan), width="stretch", key="surface_scan")
    if building:
        if scan is None:
            st.caption("Start boundary: t = −27.27 d. No column has been sampled yet; the first sample is 359° at −27.19425 d.")
        else:
            st.caption(f"Scanning {scan}° at t = {clock:+.5f} d. This column is copied from A to B. "
                       "Skipped playback frames still collect every intervening column at its own observation time.")
    else:
        st.caption("A shows the target-time truth. B contains the completed observations used for reconstruction.")

    st.subheader("C · Transport measurements to the reference time")
    if building:
        partial = reconstruct(accumulation, target, state.differential, fill_gaps=False)
        progress = 1.0
        caption = "Live preview: collected columns transported fully to the target; unobserved destinations stay gray. "
        caption += "Select Transport to reference to animate the completed map's displacement."
        plot_title = "Available measurements synchronized"
    else:
        progress = fraction
        partial = reconstruct(synoptic, target, state.differential, progress, state.fill_gaps)
        caption = "Open circles = source; diamonds = current destination at 0°, 30°, and 60° latitude. Paths wrap at the seam."
        plot_title = f"Transport progress {fraction:.0%} · target t = {target:+.3f} d"
    fig = maps_figure([partial.field], [plot_title], selected=state.selected, height=370)
    if not building or observed_at <= clock + 1e-10:
        add_transport_paths(fig, state.selected, target, state.differential, progress)
    st.plotly_chart(fig, width="stretch", key="transport")
    st.caption(caption)

    left, right = st.columns([1, 1])
    with left:
        st.latex(r"\tau=t_{\rm ref}-t_{\rm obs},\quad\Delta\phi=[\Omega(\lambda)-\Omega_C]\tau")
        st.caption("Positive Δφ moves right (increasing longitude); negative moves left. "
                   "The final longitude is (source + Δφ) modulo 360°.")
        rows = []
        for lat in [0, 30, 60]:
            shift = float(displacement(lat, elapsed, state.differential))
            rows.append({"Latitude (°)": lat, "Ω sidereal (°/d)": round(float(rotation_rate(lat, state.differential)), 5),
                         "Ω − ΩC (°/d)": round(float(drift_rate(lat, state.differential)), 5),
                         "Full Δφ (°)": round(shift, 3), "Destination (°)": round((state.selected + shift) % 360, 3)})
        st.dataframe(rows, hide_index=True, width="stretch")
    with right:
        st.plotly_chart(time_strip(state.selected, target, clock), width="stretch", key="time_strip")

    st.subheader("D · Completed reconstruction versus known truth")
    st.caption("Final-result comparison, independent of playback progress. All three maps share the same ±100 G scale.")
    st.plotly_chart(maps_figure([synoptic, final.field, truth],
                                ["Original mixed-time map", f"Reconstructed at {target:+.3f} d", "Synthetic truth at target"],
                                selected=state.selected, height=310), width="stretch", key="comparison")
    error_before = area_weighted_rmse(synoptic, truth)
    error_after = area_weighted_rmse(final.field, truth)
    supported_error = area_weighted_rmse(final.field, truth, final.supported)
    scores = st.columns(4)
    scores[0].metric("Original vs truth · RMS", f"{error_before:.3f} G")
    scores[1].metric("Reconstructed vs truth · RMS", f"{error_after:.3f} G")
    scores[2].metric("Supported cells only · RMS", f"{supported_error:.3f} G")
    scores[3].metric("Grid nodes without sample weight", f"{100 * np.mean(~final.supported):.1f}%")
    st.caption("RMS uses cos(latitude) area weights. With gap filling OFF, RMS excludes missing values. "
               "The unsupported percentage counts grid nodes, not surface area.")
    with st.expander("Inspect the residual and sampling coverage"):
        st.plotly_chart(maps_figure([final.field - truth], ["Residual: reconstructed − truth (same ±100 G scale)"],
                                    height=290), width="stretch", key="residual")
        st.plotly_chart(coverage_figure(final.weight), width="stretch", key="coverage")
        st.write("Zero weight means no sample was deposited at that node. Larger weights indicate overlapping "
                 "sample contributions. Every sample contributes to two periodic grid nodes; the field is their "
                 "weighted average. Optional gap filling interpolates periodically between supported nodes and "
                 "does not turn missing coverage into a measurement.")
        st.write("Errors arise from the 1° sampling, interpolation, and unobserved longitude intervals after "
                 "transport. Ground truth and reconstruction use the same rotation law, so this experiment has "
                 "no error from unmodeled emergence or decay. Real observations would have those additional uncertainties.")


dashboard()

if st.session_state.neighbors:
    st.subheader("Three consecutive rotations · illustrative identifiers")
    target = float(observation_time(st.session_state.reference))
    maps = [synoptic_map(st.session_state.differential, offset) for offset in [-1, 0, 1]]
    fig = maps_figure(maps, ["CR 2302 · previous", "★ CR 2303 · CENTRAL ★", "CR 2304 · next"],
                      selected=st.session_state.reference, height=330)
    fig.add_vrect(x0=-0.5, x1=359.5, line_width=3, line_color="#7953bc", fillcolor="rgba(0,0,0,0)", row=1, col=2)
    st.plotly_chart(fig, width="stretch")
    timing = []
    for name, offset in [("CR 2302", -1), ("CR 2303 (central)", 0), ("CR 2304", 1)]:
        relative = observation_time(LONGITUDES, offset) - target
        timing.append({"Map": name, "Oldest relative time (d)": round(float(relative.min()), 5),
                       "Newest relative time (d)": round(float(relative.max()), 5),
                       "Older columns": int(np.count_nonzero(relative < -1e-10)),
                       "Same-time columns": int(np.count_nonzero(np.abs(relative) <= 1e-10)),
                       "Newer columns": int(np.count_nonzero(relative > 1e-10))})
    st.dataframe(timing, hide_index=True, width="stretch")
    st.caption("Times here are observation minus chosen reference: negative = older, positive = newer. "
               "In the central map, columns right of the reference are older and those left are newer. "
               "Neighbors add measurements outside the central interval. These labels are illustrative, not "
               "calendar dates; neighboring data are not merged into this reconstruction or used to reproduce a research algorithm.")

with st.expander("Physics, numerical method, and assumptions"):
    a, b, c = HOWARD_COEFFICIENTS
    st.latex(r"t_{\rm obs}(\phi)=-\frac{\phi}{360^\circ}\,27.27\ \mathrm{d}")
    st.latex(r"\Omega(\lambda)=A+B\sin^2\lambda+C\sin^4\lambda")
    st.write(f"ON: A = {a:.6f}, B = {b:.6f}, C = {c:.6f} sidereal degrees/day. "
             f"OFF: Ω = ΩC = {CARRINGTON_RATE} sidereal degrees/day at every latitude.")
    st.markdown("The Howard coefficients are converted from (2.894, −0.428, −0.370) μrad/s, "
                "as documented in [SunPy's rotation models](https://docs.sunpy.org/en/stable/generated/api/sunpy.sun.models.differential_rotation.html). "
                "The [Carrington sidereal rate](https://docs.sunpy.org/en/stable/generated/api/sunpy.sun.constants.sidereal_rotation_rate.html) "
                "is separate from the 27.27-day synodic sampling interval; 360/27.27 is never used as a sidereal velocity.")
    st.latex(r"B(\phi,\lambda,t)=B_0(\phi-v(\lambda)t,\lambda),\qquad v=\Omega-\Omega_C")
    st.write("The truth is evaluated analytically, so animation does not accumulate numerical advection error. "
             "The synoptic map samples that evolving truth once per longitude. Reconstruction uses only those "
             "samples and their times, never the truth map. At intermediate transport progress s, each sample "
             "has effective time t_obs + s(t_ref − t_obs); only s = 1 synchronizes all samples.")
    st.write("Linear deposition splits each field sample between adjacent longitude nodes. Numerators and "
             "weights are added before division, retaining overlapping contributions. These are field-strength "
             "samples, not integrated flux packets; the mixed-time map's pixel sum is not a conserved magnetic flux. "
             "No emergence, decay, meridional flow, or supergranular diffusion is included.")
    st.caption("Latitude is sampled every 2°, longitude every 1°. High-latitude bipolar regions exaggerate the "
               "rotation contrast for teaching. The synthetic field includes balanced bipolar pairs and a weak axial dipole.")
