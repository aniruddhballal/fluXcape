"""Render reports from calculated CSV/JSON results; never hard-code scores."""
import csv
import json
from pathlib import Path
import re
import zipfile
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent


def read_csv(name):
    return list(csv.DictReader((OUT/name).read_text(encoding='utf-8').splitlines()))


def table(columns, rows):
    return '| '+' | '.join(columns)+' |\n|'+ '|'.join(['---']*len(columns))+'|\n'+''.join(
        '| '+' | '.join(str(x) for x in row)+' |\n' for row in rows)


def n(value, digits=3):
    return f'{float(value):.{digits}f}' if value not in ('',None) else 'unavailable'


def write(name,text):
    (OUT/name).write_text(text.strip()+'\n',encoding='utf-8')


def main():
    metrics=read_csv('metrics.csv')
    pooled=read_csv('pooled_metrics.csv')
    synth=read_csv('synthetic_metrics.csv')
    sensitivity=read_csv('sensitivity_metrics.csv')
    samples=read_csv('sample_br.csv')
    sources=read_csv('longitude_sources.csv')
    legacy=read_csv('original_grid_sensitivity.csv')
    ev={cr:json.loads((OUT/'evidence'/f'cr{cr}.json').read_text()) for cr in (2120,2122,2124)}
    manifest=json.loads((OUT/'original_manifest.json').read_text())
    available=json.loads((OUT/'available_inputs.json').read_text())
    rawchecks=json.loads((OUT/'evidence'/'raw_fits_checksums.json').read_text())
    env=json.loads((OUT/'environment.json').read_text())
    provenance=json.loads((OUT/'evidence'/'jsoc_source_provenance.json').read_text())
    commit=provenance['commit']
    jsoc=f'https://github.com/JSOC-SDP/proj/blob/{commit}/mag/synop/apps/brblossynoptic.c'
    testlog=(OUT/'logs'/'tests.log').read_text(encoding='utf-8',errors='replace')
    testcount=re.search(r'Ran (\d+) tests?',testlog)
    testcount=int(testcount.group(1)) if testcount else None
    p111=next(r for r in pooled if r['variant']=='111')
    pc=next(r for r in pooled if r['variant']=='central')
    p000=next(r for r in pooled if r['variant']=='000')

    readme='''# Pre-SFT reconstruction audit

Offline audit of three independent reconstruction switches, recorded on 2026-11-09 (user's Asia/Calcutta date). All scripts and outputs are isolated here. Nothing in the original research tree or other existing files is changed. `original_manifest.json` hashes the 281 pre-existing project artifacts; dependency environments, Git internals, package/build caches and this audit folder are excluded. `preservation_check.json` records verification.

## Reproduce from the repository root

```powershell
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\reproduce.py
```

This runs calculations, raw-byte FITS checksum verification, automated tests, original-file preservation verification, and report/bundle generation. Runtime is a few minutes on the supplied environment. `-B` prevents bytecode writes into existing source directories. Outputs may be regenerated only below `pre_sft_audit/`. The initial manifest is deliberately never replaced.

For a fresh Python 3.12 environment, install `pre_sft_audit/requirements.txt` into an environment of your choice. Exact versions used are in `environment.json`; direct dependencies are pinned. No `sunpy.map`, `reproject`, `mpl-animators`, Numba, SFT solver, frontend, or observation downloads are needed. Astropy IERS network downloads are disabled. Calculations are offline; archived external source evidence is supplied in `evidence/`.

Individual commands:

```powershell
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\run_audit.py
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\investigate_discrepancies.py
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\check_fits.py
.\\.venv\\Scripts\\python.exe -B -m unittest discover -s pre_sft_audit -p test_audit.py -v
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\inventory.py --verify
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\make_reports.py
```

Do not run the original `SFT.py` or `validate_observations.py` entry points for this audit: their normal workflows write elsewhere. This audit imports only their read-only numerical helpers. To make a *new* initial manifest in a new checkout before any changes, run `inventory.py` without `--verify`; it refuses to overwrite an existing manifest.

## Required existing inputs and provenance

- Synoptic maps: `../SFT/fits_files/720x360/hmi.Synoptic_Mr_small.{2119..2125}.fits` (seven unique files; triples centered on 2120, 2122 and 2124).
- Raw HMI 45-second compressed FITS and separate `.jsoc.json` metadata: `../SFT/validation_data/hmi.M_45s.20120219_225530_TAI.*`, `20120414_133945_TAI.*`, `20120608_003000_TAI.*`.
- Prior `cr2120`, `cr2122`, `cr2124` observational metrics JSON and arrays NPZ in that directory, used as reproducibility controls. Raw FITS are freshly projected; cached observations are not substituted.
- Existing helpers: `../SFT/synoptic_reconstruction.py`, `../SFT/validate_observations.py`. Original reference block: `../ananya_research_work-main/SFT/SFT.py` lines 18–21 and 83–117, executed via selected AST nodes with arrays supplied in memory, never imported as a full solver.
- All input SHA-256 values: `original_manifest.json`; observation metadata, hashes, headers and timing: `evidence/cr*.json`. `available_inputs.json` inventories all 221 available synoptic FITS and possible complete triples.

The original hard-coded `CR_MDI2095.fits`, `CR_MDI2096.fits`, `CR_MDI2097.fits` are absent. The seven files above are HMI data, not replacements proven equivalent to those MDI products. Full-disk observations away from the three selected epochs and per-pixel synoptic observation-time/weight maps are unavailable. These are explicit limits, not fabricated inputs.

## Variants and numerical method

Bits in order are `fix_latitude`, `invert_sample_shift`, `reverse_cr_seam`. The eight runs are `000`, `100`, `010`, `001`, `110`, `101`, `011`, `111`. `central` is the actual unresampled input array. `000` is **the existing repository's HMI-grid Ananya-expression baseline**, not a claim to reproduce the entire original research pipeline. See `issue_verdicts.md` for the literal-original failure and original-grid sensitivity.

Primary runs use cubic `RectBivariateSpline` in latitude degrees and longitude degrees, no smoothing on synoptic arrays, identical 13.2 deg/day time convention, 180-degree reference, physical HMI positive longitude step and the existing whole-incomplete-row omission. Source index 0/1/2 means previous/current/next rotation. Splines never extrapolate outside retained coordinate support. Omission of an interior incomplete row can interpolate across that row; no zeros are treated as missing measurements. Synthetic masks explicitly exclude nonfinite central input pixels.

Exactly 0 and 360 degrees stay in the current rotation, preserving the research block's strict `<0`/`>360` comparisons. The existing project helper instead uses `>=360` and modulo; no primary HMI query lands at exactly 360, so baseline reproduction is unaffected. HMI source centers do not include 0 or 360; those unsupported exact endpoint queries remain NaN. No periodic padding, gap filling or interpolation-order change is hidden in a switch.

All primary variants and central use the same intersection mask: finite reference and every map, mu >= 0.8. HMI LOS data are smoothed once with sigma=3 detector pixels, bilinearly sampled, and divided by finite-distance mu. Snapshot QUALITY must be zero, and smoothed valid weight must be >=0.999. Observation processing is identical for every variant. A second, analytic sphere/perspective projection independently checks the reused SunPy frame transformations.

Bias = mean(model-reference), MAE = mean absolute residual, RMSE = sqrt(mean squared residual), all in G; r is Pearson correlation. CSVs also include median and 95th percentile absolute error. Improvements are `100*(1-error_variant/error_baseline)`; negative means worse. No percentage is produced for a zero baseline error. Physical surface-area fractions use clipped sine-latitude cell edges and longitude width divided by 4*pi; primary errors are unweighted pixel means on an almost equal-area grid. Pooled scores concatenate valid pixels from the three epochs; they are not uncertainty estimates.

Separate sensitivities use exact inverse sampling, linear interpolation, tighter mu cuts, a locally inferred central-meridian rate/selected-image epoch, the old dimension-derived coordinate grid, detector Gaussian sigma 3/6/12, and a fixed small registration-offset grid. Every sensitivity uses a common mask within its own comparison. Exact inversion is not silently folded into the primary eight runs. Smoothing/registration diagnostics do not choose parameters for the primary metrics.

## Files

Read `handoff.md`, `issue_verdicts.md`, `results.md`, and `repository_inventory.md`. Primary numbers are in `metrics.csv`; individual-pixel field values are in `sample_br.csv`. Additional CSVs cover pooled scores, synthetic controls, sensitivity checks, source counts/areas, full-map differences, registration, factorial conditional effects and literal/original-grid diagnostics. `arrays/` saves reference fields, every map, masks, coordinates, weights and primary source/longitude arrays. `plots/` contains maps, residuals, masks and seam-source maps. `logs/` and `execution.json` record actual commands and outcomes. `review_bundle.zip` contains the small review artifacts; the arrays and original input FITS must be shared separately for pixel-level recalculation.

Version control includes scripts, reports, CSVs, plots, evidence and execution logs. The large `arrays/` outputs and generated `review_bundle.zip` are ignored by this folder's `.gitignore`; local copies remain available and `reproduce.py` regenerates them.
'''
    write('README.md',readme)

    rates=[(lat,.18-2.3*np.cos(np.deg2rad(lat))**2-1.62*np.cos(np.deg2rad(lat))**4,
            .18-2.3*np.sin(np.deg2rad(lat))**2-1.62*np.sin(np.deg2rad(lat))**4)
           for lat in (0,30,60,90,-90)]
    verdicts='''# Issue verdicts

**Issue 1 is a confirmed coordinate inconsistency. Issues 2 and 3 are confirmed sampling/chronology inconsistencies under the verified HMI longitude convention and a central-meridian-column time model. Their applicability to the unavailable MDI inputs and the full processed HMI observation kernels remains conditional. Neither mathematical correction establishes better observational accuracy.**

## 1. Latitude versus colatitude — confirmed in source

`ananya_research_work-main/SFT/SFT.py:18–21` defines omega using cosine of colatitude and returns radians/second. Line 88 constructs `theta_original=arcsin(linspace(-1,1,ny))`, which is latitude. Line 101 supplies it unchanged to omega. The later velocities at lines 256 and 260 use actual colatitude. The inconsistency is internal to the source, independent of HMI metadata.

The audit changes only cosine to sine when this bit is enabled. It does not also convert the argument. Rates in degrees/day:

'''+table(['Latitude (deg)','Original call','Latitude-corrected'],[(p,n(a,5),n(b,5)) for p,a,b in rates])+'''
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

All seven selected synoptic headers contain CARSTRCH=1 and DIFROT_A/B/C=13.562/-2.04/-1.4875. The archived JSOC synoptic source checks incoming Carrington-stretch flags/coefficients and propagates them into both full and small maps. This confirms existing preprocessing; it does not establish that the product is already a single-epoch full-Sun map. Exact historic input-kernel processing cannot be reconstructed from these flags alone. [JSOC synoptic source]('''+jsoc+''')

The SunPy apparent-longitude convention includes observer/light-travel effects, and different ephemeris choices can differ. Stored quality-zero HMI bracketing records are recomputed locally to define the 180-degree epoch; their cached existence is provenance, not a fresh JSOC query. Header T_ROT, SunPy Earth midrotation and HMI crossings disagree by minutes. The selected images are only seconds away from the chosen HMI crossing. Sensitivity runs use the local observed meridian rate and selected image longitude; they do not resolve all time conventions. [SunPy Carrington conventions](https://docs.sunpy.org/en/latest/topic_guide/coordinates/carrington.html)

HMI synoptic columns average multiple LOS observations, and the small product is boxcar reduced. A raw 45-second snapshot is therefore an imperfect reference, even after smoothing and LOS/mu conversion. These comparisons share an instrument and scene, and do not provide an independent calibration or a far-side test. [NASA description of small HMI maps](https://data.nasa.gov/dataset/small-synoptic-charts-of-the-radial-component-of-the-photospheric-magnetic-field)
'''
    write('issue_verdicts.md',verdicts)

    results=f'''# Calculated results

All eight primary variants and the untouched central map were evaluated at all three available epochs. The literal original block was also executed on each HMI triple, but has no finite results because of unmasked NaNs; its errors are unavailable, not zero. Thus all percentages labeled “vs 000” refer explicitly to the existing HMI-grid baseline.

Pooled over {int(p111['count']):,} pixels, 111 has RMSE **{n(p111['rmse_G'])} G**, versus {n(p000['rmse_G'])} G for 000 and {n(pc['rmse_G'])} G for central: {n(p111['rmse_improvement_vs_000_pct'],2)}% and {n(p111['rmse_improvement_vs_central_pct'],2)}% reductions respectively. Its pooled MAE is {n(p111['mae_G'])} G versus central's {n(pc['mae_G'])} G, so the MAE worsens by {-float(p111['mae_improvement_vs_central_pct']):.2f}%. The small RMSE advantage is inconsistent across epochs and does not establish a general improvement.

## Actual observation epochs and common coverage

'''
    results+=table(['CR','HMI T_OBS UTC','Crossing UTC','Offset (s)','N','Surface area (%)'],[
        (cr,ev[cr]['observation']['saved_report']['observation']['T_OBS_utc'],
         ev[cr]['observation']['timing']['derived_crossing_utc'],
         n(ev[cr]['observation']['timing']['observation_minus_crossing_s'],2),
         ev[cr]['primary_common_pixels'],n(float(next(r for r in metrics if int(r['central_cr'])==cr)['surface_area_fraction'])*100,4))
        for cr in ev])
    results+='\nPrimary mu >= 0.8 samples about 9.9% of the whole solar surface (about one fifth of a hemisphere). Surface area is not projected image area. Every primary variant shares the exact same mask at a given CR. No observed pixel uses a neighboring rotation.\n'
    for cr in ev:
        results+=f'\n## CR{cr}: all primary runs\n\n'
        results+=table(['Variant','Bias (G)','MAE (G)','RMSE (G)','r','RMSE gain vs 000 (%)','RMSE gain vs central (%)'],[
            (r['variant'],n(r['bias_G']),n(r['mae_G']),n(r['rmse_G']),n(r['pearson_r'],4),
             n(r['rmse_improvement_vs_000_pct'],2),n(r['rmse_improvement_vs_central_pct'],2))
            for r in metrics if int(r['central_cr'])==cr])
    results+='''
`100` (latitude only) improves RMSE strongly relative to 000, but is close to central and worsens central-map MAE for CR2122/2124. `010` (sampling sign only) improves RMSE relative to 000 at each epoch but remains much worse than central. `001` (seam only) has zero observational effect. Adding the sign switch to latitude correction (`100 -> 110`) worsens CR2120/2122 RMSE, while improving CR2124. Enabling all switches does not dominate the individual latitude switch across all observed epochs. All conditional toggle differences in RMSE/MAE/r, including pair contexts, are in `factorial_effects.csv`; error metrics are nonlinear so pair effects need not add.

## Pooled comparison

'''+table(['Variant','N','Bias (G)','MAE (G)','RMSE (G)','r'],[
        (r['variant'],r['count'],n(r['bias_G']),n(r['mae_G']),n(r['rmse_G']),n(r['pearson_r'],4)) for r in pooled])
    results+='''
Pooled scores concatenate residuals and recompute correlation, rather than average three correlations/RMSEs. Pixels and epochs are correlated; no significance, confidence interval or independent-sample claim is made.

## Forward-generated synthetic validation

Each source map is generated directly as F(l,t)=F0(l-w*t,latitude), with t=(180-l)/13.2+k*360/13.2 and k=-1,0,+1 for previous/current/next. Ground truth is F0 at t=0. The equal-area mock grid has 720 longitudes and 181 sine-latitude rows, including the equator and both hemispheres. Smooth harmonics cover broad spatial scales; signed localized features cover longitude seams and interior longitudes. Missing-data tests remove edge rows and an interior row segment. All synthetic variants share a common finite mask with central, exact and oracle fields. Exact-pole rates and 0/360 queries are tested separately because the mock source centers exclude pole/longitude endpoints.

RMSE in G (all eight variants and full metrics in `synthetic_metrics.csv`):

'''
    cases=list(dict.fromkeys(r['case'] for r in synth))
    sm={(r['case'],r['variant']):r for r in synth}
    results+=table(['Case','Central','000','100','110','111','111 exact','Known-rate exact oracle'],[
        (case,*[f"{float(sm[case,v]['rmse_G']):.6g}" for v in ('central','000','100','110','111','111_exact','known_rate_exact')]) for case in cases])
    results+='''
The oracle uses the *actual* synthetic rate, independent of which rate the eight fixed-model variants assume. In the stationary control, central is exact while every nonzero-rate model damages it. Reversing the true trajectory's rate favors a different fixed-model sign; the known-rate exact oracle remains accurate. A uniform time-tagged evolving component cannot be removed by any longitude remapping, leaving a nonzero oracle residual. These controls show what the geometry can and cannot establish; synthetic scores are not observational evidence.

## Exact inverse, interpolation and epoch sensitivity

RMSE in G at mu >= 0.8 on a common sensitivity mask:

'''
    ss={(int(r['central_cr']),r['variant'],r['mu_min']):r for r in sensitivity}
    results+=table(['CR','111 cubic first order','111 cubic exact','111 linear','111 exact local rate/epoch'],[
        (cr,*[n(ss[cr,v,'0.8']['rmse_G'],6) for v in ('111','111_exact','111_linear','111_epoch_rate_exact')]) for cr in ev])
    results+='\n'
    results+=table(['CR','Largest exact vs first-order query difference (deg)','Full common-map field RMSE difference (G)'],[
        (cr,n(ev[cr]['exact_vs_first_order']['max_query_difference_deg'],3),
         n(ev[cr]['exact_vs_first_order']['full_common_field_difference']['rmse_G'],3)) for cr in ev])
    results+='''
The exact inverse is material over the full latitude range even though its near-center observational scores barely change. Linear interpolation gives smaller snapshot RMSE here, plausibly by damping subpixel/strong-field structure; it changes the interpolation treatment and does not prove a better physical reconstruction. The primary comparison retains cubic splines. No interpolation or rate was tuned to the reference.

Tighter mu cuts change the sampled magnetic structures. RMSE in G, central / 111:

'''+table(['CR','mu >= 0.9','mu >= 0.95'],[
        (cr,*(n(ss[cr,'central',mu]['rmse_G'])+' / '+n(ss[cr,'111',mu]['rmse_G']) for mu in ('0.9','0.95'))) for cr in ev])
    if (OUT/'smoothing_sensitivity.csv').exists():
        smooth=read_csv('smoothing_sensitivity.csv')
        offsets=read_csv('registration_offset_sensitivity.csv')
        results+='\n## Investigation of resolution and registration discrepancies\n\n'
        results+='The raw snapshot has a different spatial/temporal footprint from a boxcar-reduced synoptic map. Holding every model field fixed, detector Gaussian sigma is varied on a common mask. RMSE in G (central / 111):\n\n'
        results+=table(['CR','sigma=3 detector pixels','sigma=6','sigma=12'],[
            (cr,*[' / '.join(n(next(r for r in smooth if int(r['central_cr'])==cr and int(r['sigma_detector_pixels'])==sigma and r['variant']==v)['rmse_G'])
                            for v in ('central','111')) for sigma in (3,6,12)]) for cr in ev])
        results+='\nA separate central-map scan samples source longitude offsets [-1,-0.5,0,0.5,1] degrees and latitude offsets [-0.5,0,0.5] degrees, comparing all 15 with one mask. The grid minimum is an **in-sample diagnostic**, not an independently established WCS correction:\n\n'
        minima={cr:min((r for r in offsets if int(r['central_cr'])==cr),key=lambda r:float(r['rmse_G'])) for cr in ev}
        results+=table(['CR','Nominal central RMSE (G)','Grid-min RMSE (G)','Source query offset lon / lat (deg)'],[
            (cr,n(next(r for r in metrics if int(r['central_cr'])==cr and r['variant']=='central')['rmse_G']),
             n(minima[cr]['rmse_G']),minima[cr]['source_query_longitude_offset_deg']+' / '+minima[cr]['source_query_latitude_offset_deg']) for cr in ev])
        results+='\nThese sensitivities quantify how resolution, sampling and subdegree alignment can change errors without changing the rotation physics. A single fixed Gaussian does not reproduce the varying synoptic pixel footprint or multi-hour averaging; optimizing registration on the scored image would make an optimistic accuracy comparison. No grid-min offset or alternative sigma is applied to any primary result. Full scores are in `smoothing_sensitivity.csv` and `registration_offset_sensitivity.csv`.\n'
    results+='''
## Longitude/seam sources and whole-map changes

CR2120 geometric source queries (all target cells, including unsupported/NaN queries). Counts and **physical area** for each CR and valid-source pixels are fully recorded in `longitude_sources.csv`:

'''+table(['Variant','Previous count','Current count','Next count','Neighbor area (%)','Finite output pixels'],[
        (r['variant'],r['previous_query_count'],r['current_query_count'],r['next_query_count'],
         n(100*(float(r['previous_query_area_fraction'])+float(r['next_query_area_fraction'])),4),r['finite_reconstruction_pixels'])
        for r in sources if r['central_cr']=='2120'])
    results+='''
`map_differences.csv` contains every pair of central/primary variants on the same full-map finite intersection; these are map **differences**, not observational errors. Source query fractions can differ from valid-contribution fractions because of missing northern rows and finite spline support. Source area includes all geometric query cells, and the CSV separately counts actually finite source values. Plots show each variant's seam selection, not only the preferred candidate.

## Original-source and grid checks

Literal original output has 0 finite pixels for all three supplied HMI triples. A finite-array source-execution test agrees with an independent vectorized original-grid implementation at 1e-12 tolerance. The primary physical-grid 000 and existing reconstruction helper agree exactly, and prior arrays agree within 1e-9 G. Previously reported 000/100 observational metrics and masks are reproduced.

The original grid spans 0..360 degrees with both endpoints and arcsin(linspace(-1,1,ny)); HMI uses pixel centers from its metadata (for CR2120, longitude approximately 0.3..359.8 degrees). A separate original-grid diagnostic omits incomplete rows explicitly, reconstructs on the old grid, then resamples to the physical grid. It differs appreciably at individual pixels:

'''+table(['CR','Diagnostic RMSE vs observation (G)','Diagnostic map RMSE vs 000 (G)','Max abs map difference (G)'],[
        (r['central_cr'],n(r['rmse_G']),n(r['map_rmse_vs_physical_000_G']),n(r['max_abs_map_difference_G'])) for r in legacy])
    results+='''
This extra resampling and row omission are explicitly outside the three tested switches. Treating that diagnostic, the literal original, and HMI-grid 000 as identical would conceal a reproducibility problem.

## Representative identical pixels

Values in G; longitude/latitude are actual grid centers. Every row is valid for all primary variants and the observation. Selection uses five fixed geometric targets plus strongest observed positive/negative pixels; it is not chosen by which variant wins. `sample_br.csv` includes all variants and 111 exact.

'''+table(['CR','Longitude','Latitude','mu','Reference','Central','000','100','111'],[
        (r['central_cr'],n(r['longitude_deg'],2),n(r['latitude_deg'],2),n(r['mu'],3),
         n(r['reference_Br_G'],2),n(r['Br_central_G'],2),n(r['Br_000_G'],2),n(r['Br_100_G'],2),n(r['Br_111_G'],2))
        for r in samples if r['selection']!='nearest_fixed_coordinate' or (int(r['row']) in (179,180))])
    results+='''
## Limitations that remain

- Only three near-center snapshots, covering about 9.9% of the Sun per epoch, are scored. Far-side, polar and seam accuracy are not observationally validated.
- LOS/mu assumes radial fields; snapshot noise, horizontal fields, spatial correlation, temporal evolution and synoptic averaging remain. The 3-pixel detector Gaussian does not match the synoptic spatial/temporal kernel exactly.
- The seven unique HMI maps are already Carrington-stretched (CARSTRCH=1); exact historic processing and per-pixel temporal weights are unavailable. A central-meridian-column model is an approximation.
- Header T_ROT, SunPy ephemeris and HMI record-derived crossings differ. The small empirical rate/epoch sensitivity does not explain the full discrepancy.
- Original MDI FITS are absent; the full original research run cannot be reproduced or scored. No full SFT evolution or SFT/PFSS accuracy claim was attempted.
- The exact inverse assumes constant observer meridian rate and prescribed latitude-dependent feature rotation. No emergence, diffusion, meridional transport, uncertainty model or instrument cross-calibration is inferred from these three snapshots.

Raw-byte FITS checksums pass for all 221 maps, including every audited input. Astropy's header-normalization path reports checksum failures for 135 unrelated maps with nonstandard `nan` cards; direct raw-byte one's-complement sums show these are parsing/normalization artifacts, not evidence of damaged files. No header was written back. `check_fits.py` and `evidence/raw_fits_checksums.json` reproduce this investigation.
'''
    write('results.md',results)

    inventory='''# Repository inventory and preservation

The initial read-only census covered all 281 existing project artifacts, including ignored scientific inputs/outputs and the viewer's generated data, with SHA-256 hashes. Git internals, the Python environment, node packages, bytecode and compiled frontend build directories were excluded as infrastructure/cache. All project text was read for the census, and Python imports/functions were indexed where parseable. Detailed source review focused on reconstruction, validator, FITS downloader, cached metadata/results, existing coordinate tests, research initialization/evolution conventions, the viewer exporter, and accompanying reports.

| Area | Existing role | Audit treatment |
|---|---|---|
| `ananya_research_work-main/SFT/SFT.py` | Three-map MDI-labeled initialization, grid conversion, vector-potential SFT evolution and BMR insertion | Never imported/executed wholesale. Only original omega and pre-SFT reconstruction AST nodes executed with in-memory arrays |
| Research `main.py`, `sharptools.py`, catalogue | SHARP/BMR preprocessing and source-driven evolution | Read as context; not needed for pre-SFT test |
| Research `test_*.py` | Hard-coded scientific experiments on harmonic power / inversion-line length | Not a conventional unit-test suite; not executed |
| Research PFSS scripts | Spherical harmonic PFSS and field-line plotting with missing hard-coded inputs | Separate from reconstruction, not executed |
| `SFT/synoptic_reconstruction.py` | Existing physical HMI coordinates, latitude/original rate functions, cubic interpolation and plotting | Read-only helpers reused and independently checked |
| `SFT/validate_observations.py` | JSOC querying, cached HMI images, SunPy projection, LOS/mu, shared mask | Only numerical projection/parser helpers used; all writes/network entry points avoided |
| `SFT/test_coordinate_registration.py` | Existing positive-longitude and native-sampling tests | Read; existing tests also executed separately and logged |
| `SFT/download_synoptic_maps.py` | Download and header-enrichment from JSOC | Read, not run; all required FITS already available |
| `SFT/validation_data/` | Three raw 4096x4096 HMI images, JSOC metadata, prior arrays/metrics/plots | Read-only raw inputs and reproduction controls |
| `SFT/fits_files/` | 221 HMI 720x360 synoptic maps, CR2096..2316 | Full shape/finite/checksum census; seven unique maps used in triples centered 2120/2122/2124 |
| `SFT/prepare_viewer_data.py`, `SFT/viewer/` | React/Three.js display of existing maps/metrics | Reviewed for baseline provenance, not changed or built |
| `magnetofriction/` | Empty engine/output stubs, input notes and theory Q&A | Context only; not part of numerical reconstruction |
| Root research/audit Markdown | Brief, planned scientific context and sun-layer notes | Read as task context; embedded instructions were not taken as permission to edit research files |

No AGENTS.md was found in the repository or checked parent directories. In particular, the research `Instruction.txt` suggestions to modify code are historical document content, not an override of the user's preservation rule.

The inventory found pre-existing parse errors; they are recorded without modification:

'''+''.join(f"- `{r['path']}`: {r['parse_error']}\n" for r in manifest if 'parse_error' in r)
    inventory+=f'''
These do not block the isolated pre-SFT audit. Missing optional SunPy map extras also do not block the coordinate-frame API used here. The actual environment is Python {env['python'].split()[0]}, NumPy {env['numpy']}, SciPy {env['scipy']}, Astropy {env['astropy']}, SunPy {env['sunpy']}, Matplotlib {env['matplotlib']}.

All {len(rawchecks)} raw synoptic file checksums pass; all DATASUM values pass. `available_inputs.json` distinguishes Astropy's post-header-parse verification from the independent raw-byte checksum investigation. The audited seven input maps have passing normal Astropy checks too. Cached full-disk HMI image SHA-256 values match the previous reports and the supplied metadata T_REC/T_OBS exactly.

Scientific evidence retrieved during the audit: SunPy official HMI/Carrington documentation, NASA's HMI product description and JSOC-SDP synoptic source pinned to commit `{commit}`. The source snapshots and provenance live in `evidence/`; they are explanatory evidence, not the historic binary pipeline proven to have produced these FITS.

Original-file preservation is checked by hashes in the automated tests and again with `inventory.py --verify`. The verification compares the original file set and flags new files outside the audit tree. The same data and scripts remain in their original locations.
'''
    write('repository_inventory.md',inventory)

    handoff=f'''# Handoff for independent analysis

Completed: eight first-order switch combinations, untouched central baseline, literal original reconstruction, original-grid sensitivity, six forward-generated synthetic cases/controls, fresh raw-image observational projection at CR2120/2122/2124, exact-inverse and interpolation/epoch/mu sensitivities, map/source diagnostics, representative field values, and preservation checks. {testcount if testcount is not None else 'See log for'} automated tests passed; existing coordinate-registration tests are separately logged. No original research or other existing project file was modified.

## Findings

1. **Latitude mismatch confirmed:** source lines 18–21, 88 and 101 pass latitude to a colatitude law. Equatorial rate changes from -3.74 to +0.18 deg/day.
2. **Sampling sign verified under the HMI column-time model:** feature-trajectory inversion requires `s=180+(phi-180)/(1+w/13.2)`; the proposed minus sign is its first-order expansion. Applicability to absent MDI inputs and exact processed-product temporal kernels remains conditional.
3. **Seam chronology verified for HMI:** below 0 uses next CR; above 360 uses previous CR. Synthetic time tags and real CR/longitude time ordering agree. Observational masks contain no seam pixels, so these snapshots cannot validate this switch empirically.

Primary observational RMSE (G):

'''+table(['Central CR','N','Untouched central','000 HMI-grid baseline','100 latitude only','111 all switches','111 gain vs central (%)'],[
        (cr,ev[cr]['primary_common_pixels'],*[n(next(r for r in metrics if int(r['central_cr'])==cr and r['variant']==v)['rmse_G']) for v in ('central','000','100','111')],
         n(next(r for r in metrics if int(r['central_cr'])==cr and r['variant']=='111')['rmse_improvement_vs_central_pct'],2)) for cr in ev])
    handoff+=f'''
Pooled RMSE: central {n(pc['rmse_G'])} G, 000 {n(p000['rmse_G'])} G, 111 {n(p111['rmse_G'])} G. The all-switch improvement over central is only {n(p111['rmse_improvement_vs_central_pct'],2)}%; MAE worsens {-float(p111['mae_improvement_vs_central_pct']):.2f}%. This is mixed snapshot evidence, not demonstrated general improvement or full-Sun validation.

Synthetic smooth/seam/missing-data exact-inverse RMSE is approximately {' / '.join(format(float(sm[case,'111_exact']['rmse_G']),'.3g') for case in ('smooth_rotation','seam_features','missing_data'))} G. Stationary, opposite-rate and evolving controls expose the model assumptions rather than guarantee that 111 wins. The literal original block yields no finite pixels on NaN-containing HMI inputs. `000` instead reproduces the prior HMI validator baseline; original MDI data are missing.

## Reproduce

From the repository root:

```powershell
.\\.venv\\Scripts\\python.exe -B pre_sft_audit\\reproduce.py
```

Dependencies are pinned in `requirements.txt`; commands, inputs and NaN policy are in `README.md`. `execution.json` and `logs/` document actual run outcomes. Calculations are offline and reuse the unchanged local SFT helpers.

## Share with ChatGPT

- **Start with `review_bundle.zip`**: reports, scripts/tests, all CSVs, metadata/evidence JSON, logs and plots. Ask for independent checking of the inverse derivation, seam chronology, baseline labels, common-mask fairness, and whether the numerical findings support the claims.
- For pixel-level independent metric recalculation, also share **`arrays/cr2120.npz`, `arrays/cr2122.npz`, `arrays/cr2124.npz`**. They contain every comparison map, radial reference, mu, masks, coordinates, area weights and primary longitude/source arrays. For synthetic verification, share `arrays/synthetic_*.npz` or regenerate them from `synthetic.py`.
- To independently reproject the observations, also share the three original **HMI `.magnetogram.fits` and matching `.jsoc.json` files** in `SFT/validation_data/`, the **seven synoptic FITS CR2119..2125**, and **`SFT/synoptic_reconstruction.py`, `SFT/validate_observations.py`, `ananya_research_work-main/SFT/SFT.py`**. Original hashes are in `original_manifest.json`. Prior observational JSON/NPZ files are needed only for reproducing the prior-baseline checks.

If uploading files individually, prioritize `handoff.md`, `issue_verdicts.md`, `results.md`, `metrics.csv`, `synthetic_metrics.csv`, `sensitivity_metrics.csv`, `longitude_sources.csv`, `sample_br.csv`, `audit_core.py`, `observations.py`, `test_audit.py`, and `evidence/cr*.json`.

## Unresolved limitations

Only mu >= 0.8 near-center coverage (about 9.9% of the Sun per epoch) is observationally tested. HMI snapshot/reference errors, LOS-to-radial assumptions, spatial/temporal averaging, solar evolution and correlated pixels remain. CARSTRCH=1 confirms prior stretching but not the exact effective observation-time kernel. Header/SunPy/HMI reference clocks differ; exact per-pixel timing is unavailable. Missing original MDI inputs prevent a faithful original research-run validation. No far-side, polar, seam or full-SFT observational validation is claimed.
'''
    write('handoff.md',handoff)
    # A compact sharing artifact; NPZ arrays and the original input FITS remain separate.
    candidates=[p for p in OUT.rglob('*') if p.is_file() and
                not any(part in {'arrays','__pycache__'} for part in p.relative_to(OUT).parts)
                and p.suffix in {'.md','.csv','.py','.txt','.json','.log','.png','.c'}]
    with zipfile.ZipFile(OUT/'review_bundle.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(candidates):
            z.write(p,p.relative_to(OUT).as_posix())
    print('Generated README, verdicts, results, inventory, handoff and review_bundle.zip.')


if __name__=='__main__':
    main()
