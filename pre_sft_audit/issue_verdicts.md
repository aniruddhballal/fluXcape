# Issue verdicts

**Issue 1 is a confirmed coordinate inconsistency. Issues 2 and 3 are confirmed sampling/chronology inconsistencies under the verified HMI longitude convention and a central-meridian-column time model. Their applicability to the unavailable MDI inputs and the full processed HMI observation kernels remains conditional. Neither mathematical correction establishes better observational accuracy.**

## 1. Latitude versus colatitude — confirmed in source

`ananya_research_work-main/SFT/SFT.py:18–21` defines omega using cosine of colatitude and returns radians/second. Line 88 constructs `theta_original=arcsin(linspace(-1,1,ny))`, which is latitude. Line 101 supplies it unchanged to omega. The later velocities at lines 256 and 260 use actual colatitude. The inconsistency is internal to the source, independent of HMI metadata.

The audit changes only cosine to sine when this bit is enabled. It does not also convert the argument. Rates in degrees/day:

| Latitude (deg) | Original call | Latitude-corrected |
|---|---|---|
| 0 | -3.74000 | 0.18000 |
| 30 | -2.45625 | -0.49625 |
| 60 | -0.49625 | -2.45625 |
| 90 | 0.18000 | -3.74000 |
| -90 | 0.18000 | -3.74000 |

Tests cover signed northern/southern latitudes and exact pole rates. This confirms the coordinate inconsistency, not the physical optimality of the adopted coefficients.

## 2. Signed time offset and backward sampling — confirmed under stated HMI column-time model

Use phi for a desired target longitude at reference time t0, s for a source longitude on an **unwrapped chronological mosaic**, and w for a feature's physical Carrington longitude rate in deg/day (positive toward increasing longitude). SunPy documents the HMI positive array-longitude step despite negative archived CDELT1; the installed source was also read. The reflected-header observational control strongly favors the positive orientation. [SunPy HMI convention](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html)

For the same observer, L_CM(t)=180-Omega0*(t-t0) locally, so a central-meridian column at s has tau=t_obs-t0=(180-s)/Omega0. Thus Ananya's Delta_t_A=(phi-180)/Omega0 is reference-minus-observation time evaluated at the *target* longitude, not a forward elapsed time. Increasing physical Carrington longitude is the prograde direction. The SFT velocity definition uses positive omega for this direction; changing the physical meaning of omega would change the assumed trajectory.

A feature at phi at t0 lies at phi+w*tau when the source column observes it. Backward **sampling**, as implemented by evaluating a spline at each target coordinate, therefore requires

```
s = phi + w*(180-s)/Omega0
s_exact = 180 + (phi-180)/(1+w/Omega0)
s_first_order = phi - (w/Omega0)*(phi-180)
```

The original plus-sign expression is not this inverse. It can resemble a forward coordinate transport, but the code assigns `B_target(phi)=B_synoptic(s)`; that is a backward sampler. For a feature at phi=90 deg with w=+1 deg/day, solving its trajectory gives observation time (180-90)/(13.2+1)=6.3380 days and source longitude 96.3380 deg. The minus candidate gives 96.8182 deg to first order; the original plus expression gives 83.1818 deg. Tests solve intersections in time independently for positive, zero and negative w and for endpoints/interior longitudes.

The first-order error is `s_first_order-s_exact=-(phi-180)*(w/Omega0)^2/(1+w/Omega0)`. It is material at high latitudes, where |w/Omega0| is not tiny. Synthetic forward maps recover the reference to interpolation precision with the exact inverse; wrong-rate, stationary and evolving controls do not falsely validate the candidate. See numeric tables in `results.md`.

This verdict is conditional on representing the processed product as columns at their effective central-meridian epochs and on omega being the feature's Carrington rate. Per-pixel temporal kernels are absent. The sign is derived, not chosen to minimize snapshot error: near-center observational results do **not** consistently prefer the inverse-sign candidate over the opposite sign.

## 3. Neighbor-CR seam choice — confirmed for verified HMI chronology; not identifiable observationally here

Increasing CR number is later time. Within one rotation the observer central meridian moves from near 360 toward 0. The current unwrapped interval is [0,360], previous rotation is [360,720], and next rotation is [-360,0]. Therefore:

| Source query | Physical wrapped longitude | Chronological source |
|---|---|---|
| s < 0 | s + 360 | Next CR |
| 0 <= s <= 360 | s | Current CR (endpoint policy above) |
| s > 360 | s - 360 | Previous CR |

Original source lines 103–113 choose the opposite neighbor for out-of-range queries. SunPy rotation-time calculations, local L0 evaluations and all nine input header times independently establish the ordering; the underlying rotation-number definition also increases in time. [SunPy Carrington time definition](https://docs.sunpy.org/en/stable/generated/api/sunpy.coordinates.sun.carrington_rotation_time.html)

A synthetic tracer whose field equals its observation time checks the two neighbor assignments without using the feature-rotation formula. Original selection associates a wrapped seam query with a time two rotations away from the intended branch, a 54.54545-day error in the constant-13.2 model. Source-count tables show how the sampling-sign switch changes which rows cross seams. Exact endpoint tests preserve deterministic strict comparisons.

All observed masks lie near longitude 180; every included pixel in every variant samples the central CR. Consequently 000=001, 100=101, 010=011 and 110=111 on these masks. This is **lack of observational sensitivity**, not evidence that both seam conventions are physically valid. No full-Sun seam accuracy claim follows from these snapshots.

## Baseline distinction and missing data

The original reconstruction block is executed literally through AST extraction, keeping its radians, dimension-derived coordinates, cubic splines and strict seam tests. Supplying each available HMI triple yields **zero finite output pixels**: NaN northern rows propagate through global cubic spline coefficients. No original missing pixels are filled. Hard-coded original MDI FITS are unavailable, so original research-run scores cannot be recovered.

`000` reproduces the existing HMI validator baseline to numerical precision, with its separate FITS-derived grid and row omission. The saved prior arrays differ by at most about 1e-10 G because the equivalent degree/radian arithmetic differs at floating-point precision. A finite random-array test independently confirms the source block versus vectorized original-grid arithmetic. An explicitly labeled row-omitted old-grid diagnostic is resampled to the physical grid and quantified separately; it is not called an untouched original method.

## Prior processing, time conventions and scope

All seven selected synoptic headers contain CARSTRCH=1 and DIFROT_A/B/C=13.562/-2.04/-1.4875. The archived JSOC synoptic source checks incoming Carrington-stretch flags/coefficients and propagates them into both full and small maps. This confirms existing preprocessing; it does not establish that the product is already a single-epoch full-Sun map. Exact historic input-kernel processing cannot be reconstructed from these flags alone. [JSOC synoptic source](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/mag/synop/apps/brblossynoptic.c)

The SunPy apparent-longitude convention includes observer/light-travel effects, and different ephemeris choices can differ. Stored quality-zero HMI bracketing records are recomputed locally to define the 180-degree epoch; their cached existence is provenance, not a fresh JSOC query. Header T_ROT, SunPy Earth midrotation and HMI crossings disagree by minutes. The selected images are only seconds away from the chosen HMI crossing. Sensitivity runs use the local observed meridian rate and selected image longitude; they do not resolve all time conventions. [SunPy Carrington conventions](https://docs.sunpy.org/en/latest/topic_guide/coordinates/carrington.html)

HMI synoptic columns average multiple LOS observations, and the small product is boxcar reduced. A raw 45-second snapshot is therefore an imperfect reference, even after smoothing and LOS/mu conversion. These comparisons share an instrument and scene, and do not provide an independent calibration or a far-side test. [NASA description of small HMI maps](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field)
