## A. Executive summary

The repository explicitly implements **kinematic surface flux transport of the radial photospheric magnetic field**. Its main solver, `SFT/SFT.py`, evolves two staggered vector-potential components using prescribed differential rotation, meridional circulation and diffusion, then reconstructs the radial field.

Its observational inputs have two distinct roles:

- **Initialization:** three MDI-labelled Carrington maps construct the starting surface field.
- **Subsequent emergence:** an HMI/SHARP-derived catalogue supplies idealized bipolar regions that are added on specified dates.

**The main evolution loop does not periodically overwrite or blend its predicted field with observed magnetogram pixels.** Observation-derived source insertion is present; continual magnetogram assimilation, observational error weighting and ensemble filtering are absent.

The solver produces nearly global magnetic-field snapshots at model times, but has no arbitrary-timestamp query interface. PFSS exists independently and reads its own FITS map; **no SFT→PFSS integration is implemented**.

Several settings require caution: initialization mixes latitude and colatitude conventions, the supplied scripts/catalogue have different date configurations, and plot titles do not match the configured simulation duration.

This investigation was read-only. No source simulations were executed or files changed.

## B. Actual SFT equation reconstructed from the code

Paths below are relative to `ananya_research_work-main/`. Section I provides clickable source references.

### Main implementation

The main numerical routines are:

| File/function | Implemented role |
|---|---|
| `SFT/SFT.py`, `omega(theta)` at line 18 | Prescribed differential rotation. |
| `SFT/SFT.py`, `u(theta)` at line 25 | Prescribed meridional circulation. |
| `SFT/SFT.py`, `compute_B_from_A_staggered()` at line 321 | Reconstructs the radial field from vector potentials. |
| `SFT/SFT.py`, `update_A_staggered()` at line 353 | Advances vector potentials through advection and diffusion. |
| `SFT/SFT.py`, `Ay_func()` at line 450 | Constructs the vector-potential increment used to insert bipolar regions. |
| `SFT/SFT.py`, top-level loop at line 465 | Executes time evolution and scheduled emergence. |

This is an explicit implementation, rather than a call to an installed SFT solver. NumPy, SciPy and Numba provide array operations, interpolation and acceleration. The separate `sharptools.py` module contains code attributed to A. R. Yeates, including an auxiliary SFT solver.

### Field and coordinates

The evolved physical quantity is \(B_r(\theta,\phi,t)\), although the main script calls its array `Bz`.

Its transformed coordinates are

\[
x=\frac{\phi}{\delta},\qquad
y=-\frac{\log\tan(\theta/2)}{\delta},
\]

where \(\delta=\operatorname{deg2rad}(\texttt{delta})\). Here \(\theta\) is colatitude, and increasing \(y\) points northward.

This is **spherical surface geometry expressed on a transformed grid**, rather than a flat Cartesian surface. The spherical metric factors remain in the derivative calculations. Sources: `SFT.py:136`, `:150`, `:159`, `:345`.

### Continuum equation represented by the interior update

Reconstructing the equation from the vector-potential update gives the standard spherical advection–diffusion form:

\[
\boxed{
\begin{aligned}
\frac{\partial B_r}{\partial t}
={}&-\Omega(\theta)\frac{\partial B_r}{\partial\phi}
-\frac{1}{R\sin\theta}
\frac{\partial}{\partial\theta}
\left(\sin\theta\,u_\theta B_r\right)\\
&+\frac{D}{R^2\sin\theta}
\frac{\partial}{\partial\theta}
\left(\sin\theta\,\frac{\partial B_r}{\partial\theta}\right)
+\frac{D}{R^2\sin^2\theta}
\frac{\partial^2B_r}{\partial\phi^2}
+S_{\mathrm{BMR}}.
\end{aligned}}
\]

This is a reconstruction of the **interior continuum equation**. Boundary copying, interpolation, staggered differencing and discrete emergence determine the actual numerical realization.

The prescribed profiles are

\[
\Omega(\theta)=
\left(0.18-2.3\cos^2\theta-1.62\cos^4\theta\right)
\frac{\pi}{180\times86400},
\]

in radians per second, and

\[
u_\theta(\theta)=-D_u\cos\theta\sin^{2.33}\theta,
\qquad D_u=4500.
\]

The radius and flux normalization indicate centimetre-based units: \(D_u\) is therefore interpreted as \(\mathrm{cm\,s^{-1}}\). It is a profile coefficient, not the maximum speed; the profile’s peak magnitude is approximately \(16.27\ \mathrm{m\,s^{-1}}\).

The diffusion coefficient is

\[
D=3.5\times10^{12}\ \mathrm{cm^2\,s^{-1}}
=350\ \mathrm{km^2\,s^{-1}}.
\]

These units are inferred consistently from the code’s radius and magnetic-flux normalization; the absent FITS headers were not inspected.

### What is actually advanced?

Writing \(s=\sin\theta\), the code’s vector-potential expressions correspond to

\[
B_r=
\frac{1}{R\delta s}\frac{\partial A_y}{\partial x}
-\frac{1}{R\delta s^2}
\frac{\partial(sA_x)}{\partial y},
\]

and

\[
\frac{\partial A_x}{\partial t}
=-u_\theta B_r-\frac{D}{R\delta s}\frac{\partial B_r}{\partial y},
\]

\[
\frac{\partial A_y}{\partial t}
=-u_\phi B_r+\frac{D}{R\delta s}\frac{\partial B_r}{\partial x},
\qquad u_\phi=R\sin\theta\,\Omega(\theta).
\]

These are consistent with identifying \(A_x=A_\phi\), \(A_y=-A_\theta\). That identification follows from the implemented metric factors.

The update is explicitly

\[
A^{n+1}=A^n+\Delta t\,(\text{advection}+\text{diffusion}),
\]

as shown in `SFT.py:385` and `:413`.

### How is emergence represented?

For each catalogue event, `Bz_func()` constructs a tilted bipolar profile:

\[
Q=-\operatorname{sgn}(\texttt{LeadPol})\,
B_0e^{1/2}\frac{x'}{\rho}
\exp\left[-\frac{x'^2+2y'^2}{a^2\rho^2}\right],
\qquad a=\sqrt{1.5}.
\]

Position, separation, tilt and unsigned flux come from the catalogue. The profile is converted into an \(A_y\) increment and **added** to the existing potentials.

Thus emergence is a sequence of discrete additions, rather than a continuously evaluated analytic source or replacement of observed pixels. Strictly, its numerical field increment is the discrete curl of the added potentials. Sources: `SFT.py:510`, `:528`, `:531`, `:557`, `:566`.

### Separate auxiliary SFT implementation

`sharptools.py` also defines `SFT1`, a **one-dimensional longitude-averaged SFT model**:

\[
\frac{\partial b}{\partial t}
=
-\frac{\partial(V_s b)}{\partial s}
+\frac{D}{R^2}\frac{\partial}{\partial s}
\left[(1-s^2)\frac{\partial b}{\partial s}\right]
-\frac{b}{\tau},
\qquad s=\sin\lambda.
\]

The decay term is active only when \(\tau>0\); `evolve_forward()` sets \(\tau=0\).

This solver uses finite volumes, upwind advection and zero-flux polar boundaries. It evolves individual regions’ longitude averages for dipole diagnostics; it is **not the main 2D simulation**. Sources: `sharptools.py:163`, `:167`, `:203`, `:841`, `:883`.

## C. Complete inputs table

### Main 2D SFT calculation

The script uses hard-coded settings rather than a public configuration interface.

| Input/control | Physical meaning | Data type/units; current setting | Source in code |
|---|---|---|---|
| `CR_MDI2095.fits` | Previous-rotation surface field | 2D FITS primary-HDU array; field expected in G | `SFT.py:71` |
| `CR_MDI2096.fits` | Central surface map | Same | `SFT.py:75` |
| `CR_MDI2097.fits` | Following-rotation surface field | Same | `SFT.py:79` |
| Assumed map coordinates | Locations of input pixels | Longitude uniformly spanning \(0\)–\(360^\circ\); latitude derived from uniformly spaced sine(latitude) | `SFT.py:86`, `:88` |
| `phi_ref` | Reference longitude for initial-map reconstruction | Float, \(180^\circ\) | `SFT.py:83` |
| `omega_0` | Longitude/time conversion for reconstruction | \(13.2^\circ/\mathrm{day}\) | `SFT.py:84` |
| Rotation coefficients | Axisymmetric differential rotation | \(0.18,-2.3,-1.62\), degrees/day before conversion | `omega()`, `SFT.py:18` |
| Meridional profile | Poleward transport | \(p=2.33\), \(D_u=4500\), inferred cm/s | `u()`, `SFT.py:25` |
| `D` | Surface magnetic diffusivity | \(3.5\times10^{12}\), inferred cm²/s | `SFT.py:131` |
| `Rs` | Solar radius | \(7\times10^{10}\), inferred cm | `SFT.py:132` |
| `delta` | Transformed-grid scale | \(1^\circ\), converted internally to radians | `SFT.py:130` |
| Angular domain | Surface coverage | All longitudes; nominal colatitude limits \(3^\circ,177^\circ\) | `SFT.py:145` |
| `dx`, `dy` | Computational spacing | Both 1 in transformed coordinates, derived from arrays | `SFT.py:182` |
| Boundary prescriptions | Edge treatment | Periodic longitude; copied latitude ghost values | `SFT.py:265`, `:289`, `:307` |
| `dt` | Physical numerical step | Fixed 60 seconds | `SFT.py:133` |
| `t_start` | Declared initial model timestamp | `2010-05-06 00:00`; timezone-naive | `SFT.py:434` |
| `dt_date` | Calendar increment | Separately hard-coded to 60 seconds | `SFT.py:435` |
| Duration | Normal stopping condition | 3500 days | `SFT.py:433` |
| `bmrsharps_evol.txt` | Scheduled emergence catalogue | Whitespace-delimited table; supplied file has 1149 records | `SFT.py:422` |
| `CM_time` | Event insertion date | Parsed date, grouped by calendar day | `SFT.py:425`, `:429` |
| `Latitude`, `Carr_Longitude` | Region location | Degrees | `SFT.py:497`, `:499` |
| `LeadPol` | Leading polarity sign | Signed numeric value | `SFT.py:498` |
| `Unsgnd_flux` | Bipolar normalization | Expected Mx | `SFT.py:509`, `:529` |
| `Bip_Separation`, `Bip_Tilt` | Region size and orientation | Degrees | `SFT.py:510`, `:513` |
| `SHARP`, `NOAA`, `Bip_Dipole` | Catalogue fields accessed by the script | Identifiers/dipole value; not used in the transport update | `SFT.py:495`, `:496`, `:508` |
| Bipole shape factor `a` | Analytic source shape | \(\sqrt{1.5}\), dimensionless | `SFT.py:528` |
| Longitude validity rule | Rejects invalid event locations | Reject outside \(0\)–\(360^\circ\) | `SFT.py:502` |
| Tilt wrapping | Source orientation convention | Wrapped into approximately \(\pm90^\circ\) | `SFT.py:515` |
| Sine floor | Small-denominator protection | Absolute minimum 0.01 in relevant calculations | `SFT.py:335`, `:365` |
| Save schedule | Stored snapshot selection | 23:59 on alternating model days | `SFT.py:571` |
| NaN monitoring | Exceptional termination | Checks every `len(t)//20` iterations | `SFT.py:443`, `:593` |
| Output locations | Archive and plot destinations | `new_report.npz`; `result/` PNG paths | `SFT.py:603`, `:621`, `:635` |

**Operational requirements:** NumPy, Matplotlib, SciPy, Astropy, Numba and pandas; readable input files in the working directory; writable output destinations. The required FITS files are absent from the supplied repository.

### Optional regeneration of the emergence catalogue

These settings belong to `main.py` and `sharptools.py`, rather than the main 2D integrator.

| Input/control | Meaning and configured value | Source |
|---|---|---|
| Time range | 2014-06-10 to 2014-12-10 | `main.py:22`, `:23` |
| `outputpath`, `restart` | Output/cache directory and reuse behaviour | `main.py:15`, `:26` |
| `ns`, `nph` | Catalogue-processing grid: 181 × 361, uniform in sine(latitude) and longitude | `main.py:18` |
| `method`, `maxlon` | Closest-central-meridian snapshot; permitted distance \(90^\circ\) | `main.py:37`, `:43` |
| `magtype` | Radial SHARP field: `'br'` | `main.py:40` |
| `sharps_smoothing` | Gaussian smoothing width: 4 input pixels | `main.py:29`; `readSHARP():674` |
| `imbalance_threshold` | Accepted absolute flux-imbalance fraction: below 0.5 | `main.py:30`; `get_bmrs():330` |
| Minimum separation | At least one processing-grid longitude cell | `get_bmrs():266`, `:330` |
| `bmr_a` | Bipole approximation scale: 0.56 | `main.py:31`; `get_bmrs():331` |
| `repeat_threshold` | Recurrent-region overlap threshold: 1 | `main.py:34`; `get_pair_overlaps():478` |
| SHARP mask and remapping | Retain mask values ≥30; cubic remapping; radial-data NaNs replaced by zero | `readSHARP():710`, `:713`, `:754` |
| Auxiliary SFT parameters | \(D=350\ \mathrm{km^2/s}\), \(v_0=0.016\ \mathrm{km/s}\), \(p=2.33\) | `main.py:63` |
| Auxiliary SFT defaults | \(R=696000\) km; CFL factor 0.2; no decay in this caller | `SFT1.prep_sft():852`; `evolve_forward():167` |

The preprocessing additionally requires access to HMI/JSOC observations through `drms`, plus its imported SunPy and NetCDF-supporting dependencies.

## D. Complete outputs table

These are destinations implemented by the code, **not a claim that the missing-data-dependent scripts were successfully run**.

| Output | Physical meaning | Dimensions | Destination |
|---|---|---|---|
| `B_day106` | Reconstructed starting surface map | Input map’s latitude × longitude shape | Memory; `SFT.py:91` |
| `Bz_initial` | Radial field reconstructed from initialized potentials | 360 × 416 | Memory; `SFT.py:241` |
| `Ax`, `Ay` | Evolving surface vector potentials | Unpadded: 360 × 417 and 361 × 416 | Memory; allocation at `SFT.py:206` |
| `Bz` | Current radial surface field | Interior 360 × 416; padded 362 × 418 | Memory; `SFT.py:208`, `:265` |
| `Bz_time` | Initial map plus selected evolved snapshots | Nominally 1751 × 360 × 416 if the configured run completes normally | `new_report.npz`, key `Bz_time`; `SFT.py:603` |
| Final stored-map figures | Two views of the last **saved** field | 2D plots; 300 dpi | `result/final_2020.png`, `result/final_saturated_2020.png`; `SFT.py:621`, `:635` |
| Progress diagnostics | Max field/potential magnitudes, initialization error and NaN warning | Scalars/messages | Standard output; `SFT.py:246`, `:587` |
| `sharps.p` | Selected region IDs, observation times and insertion times | Three serialized lists | Preprocessor output directory; `get_sharps():571` |
| `allsharps.txt` | Measured region properties and fitted-bipole properties | One row per processed region | Preprocessor output directory; `get_bmrs():286` |
| `sharpNNNNN.nc` | Remapped original region and accepted bipolar approximation | `ns × nph`; variables `br`, optionally `br_bipole` | Preprocessor output directory; `get_bmrs():371` |
| `repeatpairs.txt`, `limb_discards.txt` | Recurrent-region and visibility-selection records | Text tables/lists | `get_pair_overlaps():424`; `getSHARPs():601` |
| `bmrsharps_evol.txt` | Selected source catalogue with additional 10-year dipole diagnostics | Supplied file: 1149 × 14 data entries | Preprocessor output directory; `evolve_forward():181`, `:242` |

The main archive **does not save coordinate arrays, timestamps, vector potentials, uncertainties or provenance metadata**. The last evolved state is also not automatically the last stored snapshot.

Independent PFSS outputs are discussed in E; they are not outputs of the SFT execution.

## E. Step-by-step computational workflow

### 1. Prepare observed active-region sources separately

`main.py` calls:

1. `get_sharps()` to identify SHARPs.
2. `get_bmrs()` to read selected magnetograms and fit bipolar representations.
3. `get_pair_overlaps()` to identify recurrent regions.
4. `evolve_forward()` to generate the final source catalogue and dipole diagnostics.

It does **not** then invoke the main `SFT.py` simulation.

The configured source observations are HMI `hmi.sharp_cea_720s` radial-field cutouts. The query selecting candidate regions samples at one-day intervals; each region subsequently receives one selected frame, normally nearest central meridian. This is not a daily full-disk magnetogram assimilation stream.

Sources: `main.py:54`, `:57`, `:60`, `:63`; `sharptools.py:592`, `:695`, `:801`.

### 2. Construct the initial field from three synoptic maps

The main simulation opens **MDI-labelled** files for CR2095, CR2096 and CR2097, using primary-HDU arrays.

It assumes coordinates from array shapes rather than reading FITS coordinate/time metadata. For each longitude it calculates the equivalent of

\[
\Delta t_\phi=\frac{\phi-\phi_{\rm ref}}{\Omega_0},
\qquad
\phi'=\phi+\omega(\text{input latitude})\,\Delta t_\phi.
\]

It samples the previous, current or following map according to whether the corrected longitude crosses the map boundary.

**Confirmed:** the code attempts to account for longitudinally differing observation times.

**Not established:** that this reconstruction gives an accurately synchronized observational map. Its reference date is not derived from FITS timestamps, and a coordinate inconsistency is described in G.

Sources: `SFT.py:71`, `:83`, `:98`.

### 3. Interpolate and initialize the staggered representation

The reconstructed map is cubically interpolated onto the simulation grid. `Bz_0` is transposed to **longitude-first** ordering.

The script constructs `Ax` by integration, sets `Ay=0`, then reconstructs `Bz` through its discrete curl. It prints the maximum difference from the interpolated input.

Sources: `SFT.py:194`, `:202`, `:210`, `:227`, `:245`.

The code expects a filled map over its simulated longitudes and latitude range. It has **no explicit missing-region mask or global gap-filling algorithm**. Zero-initialized work arrays are subsequently populated; their initialization does not establish a deliberate policy for unknown solar regions.

### 4. Evolve forward

The main loop is `for ti in range(1, len(t))` at `SFT.py:465`.

Each iteration:

1. Computes `Bz` from the current potentials.
2. Copies field boundary values.
3. Advances both potentials with forward Euler.
4. Copies potential boundary values.
5. Applies any source additions scheduled for that date.
6. Saves or monitors when the corresponding conditions apply.

Spatial derivatives use adjacent staggered differences; magnetic values entering the advective terms are averaged onto potential locations. This is an explicit finite-difference implementation with a **fixed 60-second step**, not adaptive stepping.

The actual grid has:

- 360 longitude cells, centred at \(0.5^\circ\) through \(359.5^\circ\).
- 416 transformed-latitude cells.
- Latitude centres approximately \(-86.9364^\circ\) to \(+86.9364^\circ\).
- Nonuniform physical/angular latitude spacing, despite unit spacing in transformed \(y\).

Sources: `SFT.py:145`, `:183`, `:369`, `:397`, `:465`.

### 5. Incorporate observation-derived emergence

At the first iteration on each new calendar date, the script selects catalogue rows for that date and adds their analytic bipolar sources.

**Present:**

- New active-region insertion.
- Observation-derived position, flux, separation, tilt and polarity.
- Daily source-date checking.

**Absent from the main loop:**

- Reading new observed magnetogram images during evolution.
- Replacing predicted pixel values with observations.
- Weighted model–observation blending.
- Innovation/residual corrections.
- Observation-error covariance or uncertainty weighting.
- Ensemble assimilation.
- An independent far-side observation stream.

The existing simulated far side is transported by the same equations as the visible side. Newly emerging, unobserved far-side flux is not independently inferred.

Upstream trust controls do exist: visibility selection, SHARP masking, smoothing, imbalance/separation criteria, flux balancing and recurrent-region filtering. These are **catalogue preprocessing**, not continual correction of the evolving global field.

Sources: `SFT.py:482`, `:566`; `sharptools.py:330`, `:713`, `:795`, `:817`.

### 6. Produce model-time surface snapshots

The simulation advances one shared field state, so its evolved snapshots are **synchronic model maps**: values representing a common model time. They are not simultaneous measurements of the entire surface.

There is no function accepting an arbitrary requested timestamp. The run’s start, duration and recording schedule are hard-coded.

Normal termination follows the 3500-day time array; a periodically detected NaN can terminate earlier. There is no equilibrium/convergence stopping condition in the main simulation.

Sources: `SFT.py:433`, `:571`, `:593`.

### 7. PFSS is a separate execution path

The PFSS script:

- Opens `CR_2193.fits` directly.
- Treats its array as a radial boundary field.
- Calculates a global spherical potential field.
- Uses a source surface at \(2.5R_\odot\).
- Saves \(B_r,B_\theta,B_\phi\).

It does not load `new_report.npz` or `Bz_time`, call the SFT solver, or loop over SFT snapshots. Its field-line plotting script reads the PFSS archive only.

**No SFT-generated arrays or files are transferred to PFSS in the supplied implementation.** There is no executable workflow establishing that SFT runs before PFSS, nor repeated PFSS calculations at different SFT times.

Sources: `PFSS/CR_2193_80_full.py:34`, `:221`, `:442`, `:464`, `:476`; `PFSS/jul80_field_line.py:14`.

## F. Comparison with published SFT approaches

The classical reference describes radial-flux transport through prescribed rotation, meridional circulation, diffusion and sources. The main solver has that mathematical structure, although this does not establish equivalent accuracy or boundary treatment. [Yeates et al. (2023)](https://link.springer.com/article/10.1007/s11214-023-00978-8)

The 2014 paper distinguishes a **noise-weighted magnetogram-assimilating baseline** from separate source-driven experiments. It explicitly models convective flows and adds diffusion for numerical stabilization; it should not be reduced to a generic diffusion-only assimilating model. [Upton & Hathaway (2014)](https://arxiv.org/html/1408.0035)

| Feature | Classical SFT | Observation-assimilating SFT | Ananya’s implementation | Evidence |
|---|---|---|---|---|
| Radial-field evolution | Central variable | Evolved between observation updates | Present | `SFT.py:321`, `:353` |
| Differential rotation | Prescribed axisymmetric profile | Can coexist with observational updates | Fixed analytic profile | `SFT.py:18` |
| Meridional circulation | Usually prescribed | May be measured/time-dependent | Fixed analytic profile | `SFT.py:25` |
| Convective dispersal | Commonly represented by diffusion | Method-dependent; cited 2014 model uses explicit convection | Constant diffusion; no explicit convective flow field | `SFT.py:131`, `:382` |
| Magnetic emergence | Source term | Sources and/or observed-field updates | Catalogue-derived analytic bipoles | `SFT.py:531`, `:566` |
| Repeated magnetogram corrections | Not required | Defining feature | Absent from main evolution | `SFT.py:465`, `:482` |
| Observation uncertainty | Not intrinsically required | Can control update weights | No uncertainty-weighted state update | `SFT.py:422`, `:566` |
| Synchronized surface states | Produced by time evolution | Produced with observational corrections | Model snapshots present | `SFT.py:582` |

**ADAPT comparison:** ADAPT evolves an ensemble and updates it using data assimilation that accounts for model and observational uncertainty. Ananya’s solver has a single deterministic state, no analysis ensemble and no uncertainty-dependent update. Sharing flux-transport terminology does not make it an ADAPT implementation. [NSO’s ADAPT description](https://nso.edu/data/nisp-data/adapt-maps/)

## G. Significant differences or unusual choices

1. **Initialization uses latitude where `omega()` is otherwise used with colatitude.**  
   `theta_original = arcsin(...)` at `SFT.py:88` is latitude. It is passed directly to `omega()` at line 101, whereas the time-evolution velocities use colatitude at line 256. For example, the former evaluates the equator at argument zero, giving \(-3.74^\circ/\mathrm{day}\); the latter evaluates it at \(\pi/2\), giving \(0.18^\circ/\mathrm{day}\). This is an apparent initialization coordinate inconsistency.

2. **The documentation and selected inputs differ.**  
   `Instruction.txt:11` describes HMI initialization, while `SFT.py:71` opens MDI-labelled files. Without those FITS files, their actual provenance and preprocessing cannot be verified.

3. **“Global” excludes polar caps.**  
   The main domain omits the poles. Latitude ghost values are copied. The comment “closed” does not by itself establish mathematically zero total transport flux through those truncated boundaries. See `SFT.py:145`, `:298`.

4. **Two separately specified clocks exist.**  
   Numerical `dt` and calendar `dt_date` currently both equal 60 seconds, but are independently hard-coded. See `SFT.py:133`, `:435`.

5. **Configured dates do not match the figure labels.**  
   Starting on 2010-05-06, the loop’s last scheduled calendar time is **2019-12-04 23:59**, assuming normal completion. Plot titles nevertheless say `2020_12_25`. See `SFT.py:433`, `:466`, `:619`.

6. **The supplied catalogue and regeneration settings differ.**  
   The catalogue advertises a 2009–2020 selection interval and a 180 × 360 grid. The current `main.py` requests June–December 2014 and 181 × 361. These are not one matching reproduction configuration.

7. **Catalogue dates are model insertion conventions.**  
   `SHARPtime()` selects a frame and derives a next-noon “emergence completion” time. `get_bmrs()` stores only its date under the catalogue time column. The main solver then injects at the first step of that date. This is not an independently measured emergence-onset timestamp. See `sharptools.py:833`, `:341`; `SFT.py:483`.

8. **The full observed region morphology is not inserted into the main run.**  
   The main run reconstructs an analytic bipole from catalogue parameters. Upstream NetCDF files preserve remapped observed regions, but `SFT.py` does not read them. Its source-profile implementation also differs from the spherical `bmr2d()` preprocessing routine. See `sharptools.py:22`, `:371`; `SFT.py:531`.

9. **Flux balancing is a preprocessing operation.**  
   `correct_flux_multiplicative()` rescales positive and negative region fluxes. This is not a residual correction against the evolving global model. See `sharptools.py:70`, `:795`.

10. **The main archive is sparsely sampled and lacks timestamps.**  
    It stores alternate-day snapshots, not every 60-second state. The last stored map need not be the final evolved state. See `SFT.py:571`, `:603`.

11. **Auxiliary experiments use different settings and stopping criteria.**  
    The four `test_...py` scripts investigate diffusion/advection effects on harmonic power or polarity-inversion-line length, without new emergence. Their examples use \(D=6\times10^{12}\), corresponding to \(600\ \mathrm{km^2/s}\) under the same length convention, and threshold-based loops. They are distinct experiments, not automated validation of the main configuration.

12. **Successful numerical execution and scientific validation remain unverified.**  
    Required FITS inputs and generated archives are absent. This review establishes what the source implements, not its measured agreement with observations, stability or conservation errors.

## H. Unresolved questions not answerable from the supplied code

- What exact MDI products, calibrations, units, polarity conventions and coordinate metadata are in the three initialization files?
- What absolute observation time does the reference longitude represent?
- Is the latitude/colatitude inconsistency present in the research version actually used for results?
- Which combination of script settings, catalogue and input maps produced the reported research figures?
- Were missing pixels or polar fields corrected before the initialization files were supplied?
- How well do the source insertion and boundary rules conserve the intended signed and unsigned flux numerically?
- Were stability, resolution-convergence and observational-comparison studies performed elsewhere?
- Was SFT→PFSS coupling performed manually or in scripts outside this repository?
- What physical use was intended for the resulting surface maps in the new MF project?

## I. Exact source-code references

| Evidence | Source |
|---|---|
| Rotation profile: `omega()` | [SFT.py:18](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:18>) |
| Meridional profile: `u()` | [SFT.py:25](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:25>) |
| Initialization files and reconstruction | [SFT.py:71](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:71>), [coordinate assumption:88](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:88>), [reconstruction loop:98](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:98>) |
| Parameters, grid and initialized potentials | [SFT.py:130](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:130>), [grid:145](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:145>), [initialization:194](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:194>) |
| Boundary functions | [apply_boundary_conditions():289](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:289>), [apply_boundary_condition():307](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:307>) |
| Main numerical operators | [compute_B_from_A_staggered():321](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:321>), [update_A_staggered():353](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:353>) |
| Catalogue loading, loop and additions | [SFT.py:422](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:422>), [loop:465](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:465>), [sources:482](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:482>) |
| Snapshot selection and archive | [SFT.py:571](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:571>), [archive:603](</D:/post engg/fluXcape/ananya_research_work-main/SFT/SFT.py:603>) |
| Preprocessing entry point | [main.py:15](</D:/post engg/fluXcape/ananya_research_work-main/SFT/main.py:15>), [pipeline calls:54](</D:/post engg/fluXcape/ananya_research_work-main/SFT/main.py:54>) |
| Bipole fitting and selection | [get_bmrs():250](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:250>), [acceptance:330](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:330>) |
| Recurrent-region filtering | [get_pair_overlaps():385](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:385>), [selection in evolve_forward():139](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:139>) |
| Actual observed-field input and processing | [readSHARP():668](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:668>), [radial-field query:695](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:695>), [masking:713](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:713>) |
| Frame and insertion-time selection | [SHARPtime():801](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:801>) |
| Auxiliary 1D SFT | [SFT1:841](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:841>), [prep_sft():852](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:852>), [evolve():883](</D:/post engg/fluXcape/ananya_research_work-main/SFT/sharptools.py:883>) |
| Supplied catalogue metadata | [bmrsharps_evol.txt:1](</D:/post engg/fluXcape/ananya_research_work-main/SFT/bmrsharps_evol.txt:1>) |
| Independent PFSS input and output | [CR_2193_80_full.py:34](</D:/post engg/fluXcape/ananya_research_work-main/PFSS/CR_2193_80_full.py:34>), [output:476](</D:/post engg/fluXcape/ananya_research_work-main/PFSS/CR_2193_80_full.py:476>) |
| Independent field-line plotting | [jul80_field_line.py:14](</D:/post engg/fluXcape/ananya_research_work-main/PFSS/jul80_field_line.py:14>) |
| Power-convergence experiments | [test_p_diffusion.py:425](</D:/post engg/fluXcape/ananya_research_work-main/SFT/test_p_diffusion.py:425>), [test_p_advection_diffusion.py:602](</D:/post engg/fluXcape/ananya_research_work-main/SFT/test_p_advection_diffusion.py:602>) |
| PIL-length experiments | [test_length_zero_line_diffusion.py:450](</D:/post engg/fluXcape/ananya_research_work-main/SFT/test_length_zero_line_diffusion.py:450>), [test_zero_length_line_advection_diffusion.py:621](</D:/post engg/fluXcape/ananya_research_work-main/SFT/test_zero_length_line_advection_diffusion.py:621>) |