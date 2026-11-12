from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
rows=json.loads((O/'metrics.json').read_text())+json.loads((O/'supplemental_metrics.json').read_text())

def select(case,region='all'):
 return [r for r in rows if r['case']==case and r['region']==region]
def table(rs):
 text='| Case / region | Model | N | RMSE (G) | MAE (G) | Pearson r | Bias (G) |\n|---|---|---:|---:|---:|---:|---:|\n'
 def f(v):return '—' if v is None else f'{v:.6g}'
 for r in rs:text+=f"| {r['case'].replace('synthetic_','').replace('observation_','')} / {r['region']} | {r['model']} | {r['n']} | "+' | '.join(f(r.get(k)) for k in ['rmse','mae','correlation','bias'])+' |\n'
 return text
mid='observation_20170609_110000_TAI_'
lookup=lambda case,model,region='mu_gt_0.7':next(r for r in rows if r['case']==case and r['model']==model and r['region']==region)
text='''# Fresh independent pre-SFT accuracy comparison

Completed 12 November 2026. All numerical results were calculated anew from original code and FITS/record metadata. No previous audit, experiment, report, or result was consulted. Neither original implementation was edited. The full SFT simulation was never run.

## Findings

The user's implementation is decisively more accurate in the specified ideal differential-rotation synthetic model. It also has lower observational RMSE than the operational, NaN-filled Ananya implementation on all three near-reference observations. This is **not** a universal physical accuracy claim: the advantage over the original synoptic map is small on observations, changes with the region and metric, and is affected by observational construction and the synoptic product's own temporal averaging.

The literal Ananya reconstruction has **zero finite output pixels** on the real FITS inputs because NaNs enter its global tensor cubic splines. Consequently, a literal observational RMSE comparison is undefined. All quoted finite observational comparisons to Ananya use adaptations explicitly listed below; zero valid pixels never means zero error.

'''
for target in ['los_radial_proxy','vector_radial']:
 c=mid+target;u=lookup(c,'user');a=lookup(c,'ananya_nan_filled');b=lookup(c,'baseline');ca=lookup(c,'ananya_coordinate_adapted')
 text+=f"At 11:00 TAI, {target}: user's RMSE **{u['rmse']:.4f} G**, versus **{a['rmse']:.4f} G** for NaN-filled Ananya: **{a['rmse']-u['rmse']:.4f} G ({100*(1-u['rmse']/a['rmse']):.2f}%) lower**. Baseline RMSE is **{b['rmse']:.4f} G**, an improvement of **{b['rmse']-u['rmse']:.4f} G ({100*(1-u['rmse']/b['rmse']):.2f}%)**. After correcting Ananya's coordinate interpretation, RMSE is {ca['rmse']:.4f} G; user's remaining advantage is {100*(1-u['rmse']/ca['rmse']):.2f}%.\n\n"
text+='''The region results are mixed against the baseline. At 11:00 TAI, the user's disk-center (mu>0.9) RMSE is 14.814 G for the LOS proxy and 17.524 G for the vector reference, versus 15.388 G and 18.032 G for the baseline. In contrast, on the strong-vector-reference subset (1,159 cells), user RMSE is **112.270 G versus 111.962 G** for the baseline: a slight worsening. On the strong-LOS subset, MAE also worsens despite a small RMSE reduction. The majority-high-confidence subset has only 38 cells at this time, while the strict all-subpoint high-confidence subset is empty. These small/empty samples do not independently establish vector accuracy.

'''
text+='''## Inputs, preservation, and execution boundary

Inputs are the 360×720 HMI radial synoptic FITS maps CR2190, CR2191, and CR2192; and the 10:48, 11:00, and 11:12 TAI records in `fits_files/observations/cr2191`. All three synoptic rotations are actually used as source data. All three observation times are independently decoded. The reference time in CR2191's header is 2017-06-09 10:56:34 TAI. Record QUALITY values and observer longitudes are saved in `provenance.json`.

`originals/ananya_SFT.py` and `originals/user_main.py` are byte-for-byte snapshots. SHA-256 hashes of originals and every input consumed are in `provenance.json`, together with Python/package versions. The two originals are checked again at completion. `run.log` records the executed calculation and finite coverage.

Only `pre-sft/main.py` is imported. From `SFT.py`, only the AST of its `omega` function is executed. Its reconstruction expressions are reproduced with batch evaluation of the same SciPy tensor spline, validated against scalar calls. No SFT grid initialization, curl calculation, flow integration, flux emergence, or time stepping is executed. The evaluated endpoint is Ananya's `B_day106` versus the user's `B_new`, before the later SFT-specific grid conversion. Those names are historical; all inputs here are CR2190–2192.

## Coordinates, adaptations, and common masks

All scoring uses CR2191's physical 720×360 grid: 0.5° longitude and approximately 1/180 in sin(latitude). Latitude is arcsin of the FITS second-axis coordinate; colatitude is 90° minus latitude. HMI's known synoptic longitude sign convention is handled using positive longitude increments, as in the user's original and the [SunPy HMI synoptic source documentation](https://docs.sunpy.org/en/stable/generated/api/sunpy.map.sources.HMISynopticMap.html). The slight FITS CDELT2 rounding is retained identically across methods. Pixels have equal spherical area to that precision, so unweighted grid metrics are area metrics.

| Name | Treatment |
|---|---|
| baseline | Original CR2191 array, no reconstruction. |
| user | Actual imported reconstruction functions, unchanged. Synthetic inputs replace only arrays/splines temporarily. |
| ananya_native | Original linspace longitude endpoints, arcsin latitude supplied directly to the colatitude rotation function, original plus-sign mapping and previous/next branching. Only file inputs and vectorized evaluation are adapted. Outputs retain their original array indices on the common physical grid, exposing rather than concealing coordinate errors. |
| ananya_nan_filled | Same algorithm as native, with missing source pixels filled by nearest finite pixel in array-index Euclidean distance before global spline construction. This is an operational adaptation, not original-code behavior. |
| ananya_coordinate_adapted | Additional diagnostic: use actual FITS latitude/longitude centers and colatitude in omega. Retain original mapping sign, denominator, and previous/next branches. Not a claim about Ananya's original accuracy. |

For every case and region, all finite operational methods and the baseline are scored on the **intersection** of finite prediction/reference pixels and the same geometric mask. The unusable literal Ananya output is excluded from constructing the operational common mask and is separately reported with N=0. Synthetic inputs have no NaNs, so the literal Ananya output participates normally. No method is scored against a different truth. Individual NPZ files save the exact reference, predictions, and primary mask. Region definitions are explicit in the runner.

The user's real reconstruction has 258,676 finite cells; the baseline has 258,754. The NaN-filled adaptations have 259,200. Common masking prevents a method from benefiting from scoring easier pixels alone, although missing-data imputation can influence nearby spline values. Nearest filling is not a physically validated gap-recovery method.

## Synthetic ground truth and results

Truth is an analytic field F(longitude, latitude) at t=0, evaluated independently of either reconstruction. At unwrapped source longitude s, the idealized synoptic acquisition time is t(s)=(180−s)/13.2 days. For rotation rate w(latitude), the synthetic source map is F(s−w t(s), latitude). CR2190 uses s=longitude+360; CR2192 uses s=longitude−360. Truth and source arrays are evaluated analytically, not generated by running or inverting either reconstruction's code.

Solving the continuous forward observation relation gives source longitude s=phi−w(phi−180)/(13.2+w). This is the user's implemented mapping. Thus, these tests establish numerical correctness **conditional on that physical acquisition/advection model**, not independent evidence that the Sun or this preprocessed HMI product obeys it exactly. Ananya's plus-sign relation and latitude interpretation are distinct hypotheses.

Four fields are tested: a constant field; smooth low-order longitude/latitude structure; modes up to longitudinal order 47; and localized bipolar/longitude-seam features. Each is tested with the nominal law, zero rotation (static truth), and 70% of the nominal rate. Additional tests add independently generated 3 G source noise across three fixed RNG realizations, and exponential amplitude evolution of 2.5% per day. All share the same exact truth per case. The latter tests expose model mismatch rather than silently assuming perfect advection.

### Nominal-law synthetic accuracy

'''
text+=table([r for r in rows if r['case'].startswith('synthetic_') and 'rotation1' in r['case'] and r['region']=='all'])
text+='\n### Static and mismatched-rate conditions\n\n'+table([r for r in rows if r['case'] in ['synthetic_smooth_rotation0','synthetic_smooth_rotation0.7','synthetic_bipoles_rotation0','synthetic_bipoles_rotation0.7'] and r['region']=='all'])
text+='\n### Source noise and intrinsic evolution\n\n'+table([r for r in rows if 'seed' in r['case'] or 'evolution' in r['case']])
text+='''
A static field favors the unremapped baseline, which has exactly zero error. Neither remapping is universally superior to leaving the map unchanged. Source noise cannot be removed by pure interpolation; intrinsic emergence/decay cannot be undone by a rotation-only reconstruction. Low-latitude, mid-latitude, polar, and seam metrics for every primary synthetic case are in `metrics.csv`.

## Observational reference construction

The original FITS segments contain image data but no complete image WCS; record JSON keywords supply WCS and ephemerides. A separate SunPy map is built for each instrument record using its own T_OBS, observer, camera orientation, and pixel geometry. TAI is explicitly retained. Carrington coordinates on the shared grid are transformed to each observation's image coordinates. Compressed images are decoded freshly.

The primary spatial averaging is **8×8 equal-area quadrature per CEA pixel**. At each subpoint, image components are bilinearly sampled, projected, and then averaged. This applies the same target spatial scale to both references and all reconstructed maps. It approximates a pixel-area average; it is not an exact reproduction of HMI's synoptic-map processing or PSF. Only cells with every quadrature subpoint finite and safely on disk are eligible. Primary regions require averaged mu>0.7; the disk-center sensitivity region requires mu>0.9. A strong-reference region requires |reference Br|>50 G and is defined separately for each reference, consistently for all methods within that reference.

Two observation references are kept separate:

1. **LOS radial proxy:** the observed HMI M_720s magnetogram divided by the local normal–observer-ray cosine mu. Valid only to the extent that the local field is radial; it is not vector ground truth.
2. **Vector radial reference:** disambiguate the HMI B_720s azimuth, construct image-frame components Bxi=−B sin(inclination) sin(azimuth), Beta=B sin(inclination) cos(azimuth), Bzeta=B cos(inclination), project the surface normal into the local observer-ray tangent basis, rotate to the CCD basis, and take the dot product. The finite observer distance and camera rotation are included. Disambiguation uses **bit 2**, the radial acute-angle solution in weak pixels; high-confidence pixels use minimum energy. This weak-field radial prior limits its independence from the LOS proxy. Conventions and confidence interpretation follow the [HMI vector pipeline paper, Appendix A](https://arxiv.org/abs/1404.1881) and the [HMI coordinate technical note](https://arxiv.org/abs/1309.2392).

The `high_confidence` sensitivity region requires at least 50% of quadrature points to have CONF_DISAMBIG≥90 and all sampled CONV_FLAG values to be zero. This is explicitly a cell-majority selection; the whole pixel reference still includes its weaker subpoints. `strict_high_confidence` requires every subpoint high confidence and is reported even if empty. Small N and empty subsets must not support a global conclusion.

The observations are near, rather than exactly at, the synoptic reference time. They are compared at fixed Carrington coordinates without transporting them with either candidate rotation law, avoiding a model-dependent observational truth. Their minutes-scale time offsets and 720 s temporal averaging remain limitations; the synoptic data span weeks and have much larger intrinsic timing uncertainty.

### Primary observational metrics, all three times

'''
text+=table([r for r in rows if r['case'].startswith('observation_') and r['region']=='mu_gt_0.7'])
text+='\n### Region sensitivity at 11:00 TAI\n\n'+table([r for r in rows if r['case'].startswith(mid) and r['region']!='mu_gt_0.7'])
text+='''
## Metric definitions and interpretation

Error e=prediction−reference, in gauss. RMSE=sqrt(mean(e²)); MAE=mean(|e|); bias=mean(e). Pearson correlation measures linear structure agreement and is undefined for constant fields. `nrmse_std` divides RMSE by the reference standard deviation. Also saved are 95th-percentile absolute error, sign agreement, reference RMS, predicted/reference means, and unsigned-field ratio. Sign agreement near zero field is noise-sensitive. Unsigned ratio is a partial-area unsigned-flux ratio on these equal-area cells, not a whole-Sun flux measurement. All metrics are descriptive; no independence-based significance claim is made for correlated pixels or the three closely spaced observations.

## Limitations and inconclusive findings

- **There is no observed instantaneous full-Sun radial ground truth.** The far side, polar reconstruction, and most seam behavior can be validated synthetically here but not from these three disk images.
- The synoptic FITS header declares CARSTRCH=1, differential-rotation coefficients, and a 15° longitudinal half-width. These inputs already incorporate temporal/spatial processing and rotation stretching. A model of ideal instantaneous central-meridian strips is not a complete model of this product. Comparisons against observations test end-product agreement, not isolated interpolation correctness.
- The LOS reference assumes radial fields. The vector reference has inversion noise, weak-field disambiguation priors, and calibration systematics. Both come from HMI and may share observations underlying the synoptic product; this is not a statistically independent instrument holdout.
- Supplied per-pixel field/angular error and covariance segments were not propagated. No calibrated chi-square, uncertainty interval, or claim of statistically significant superiority is justified. Correlation is modest, and residuals include genuine solar evolution, source-product mismatch, observational noise, and reconstruction error.
- Common masks remove missing output cells but cannot undo the influence of filling on global splines. Native Ananya cannot be ranked numerically on actual missing-data inputs; finite comparisons necessarily concern its adapted versions.
- The coordinate-adapted diagnostic removes much of Ananya's observational deficit. Therefore the large native-versus-user gap cannot be attributed solely to the time-remapping equation.
- The original synoptic baseline is competitive. Any claim that reconstruction substantially improves real radial-field accuracy would require many rotations, more observation dates, independent references, matched instrument smoothing, and uncertainty-aware validation. The present evidence supports conditional synthetic correctness and a small descriptive observational RMSE advantage, not universal superiority.

## Reproduction and artifacts

Run from any directory with NumPy, SciPy, Astropy, SunPy plus its map dependencies, and Matplotlib:

```bash
/tmp/fluxcape-spline-venv/bin/python 'my work/fresh_accuracy_comparison/run_comparison.py'
/tmp/fluxcape-spline-venv/bin/python 'my work/fresh_accuracy_comparison/supplemental.py'
QUADRATURE=4 /tmp/fluxcape-spline-venv/bin/python 'my work/fresh_accuracy_comparison/run_comparison.py'
/tmp/fluxcape-spline-venv/bin/python 'my work/fresh_accuracy_comparison/write_report.py'
```

The explicit interpreter is the available local environment; package versions are in `provenance.json`. Primary results: `metrics.csv/json`; stress tests: `supplemental_metrics.json`; exact adapters: `adapter_checks.json`; map arrays: `reconstructions.npz`; references and common masks: `observation_*.npz`; analytic truth and predictions: `synthetic_*.npz`; comparison maps/errors: corresponding PNGs. Each plotted row uses a common symmetric field scale. Image coordinates are native CEA array indices, with increasing sin(latitude) upward. The bottom row contains prediction minus reference. `summary.png` and `observational_scatter.png` provide compact comparisons. `quadrature4/` is the separately executed averaging-sensitivity calculation, not a prior audit.
'''
# Independent spatial sampling sensitivity from separate run.
qfile=O/'quadrature4/metrics.json'
if qfile.exists():
 qr=json.loads(qfile.read_text());text+='\n## Spatial averaging sensitivity: 4×4 versus 8×8\n\n'
 text+='| Reference at 11:00 | Model | 4×4 RMSE | 8×8 RMSE | Difference (G) |\n|---|---|---:|---:|---:|\n'
 for target in ['los_radial_proxy','vector_radial']:
  for model in ['baseline','user','ananya_nan_filled','ananya_coordinate_adapted']:
   r8=lookup(mid+target,model);r4=next(r for r in qr if r['case']==mid+target and r['model']==model and r['region']=='mu_gt_0.7')
   text+=f"| {target} | {model} | {r4['rmse']:.5f} | {r8['rmse']:.5f} | {r8['rmse']-r4['rmse']:+.5f} |\n"
 text+='\nThese calculations use independently sampled quadratures, with the same selection rules. Their masks can differ slightly at thresholds. This tests sensitivity, not a proof of numerical convergence or exact agreement with the instrument PSF. Interpret improvements comparable to sampling changes cautiously.\n'
(O/'REPORT.md').write_text(text)
# Joined table includes all primary and supplemental cases.
keys=list(dict.fromkeys(k for r in rows for k in r))
with (O/'all_metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
fig,axes=plt.subplots(1,2,figsize=(12,4))
models=['baseline','user','ananya_nan_filled','ananya_coordinate_adapted']
for ax,target in zip(axes,['los_radial_proxy','vector_radial']):
 for n in models:
  vals=[lookup(f'observation_{stamp}_{target}',n)['rmse'] for stamp in ['20170609_104800_TAI','20170609_110000_TAI','20170609_111200_TAI']]
  ax.plot(['10:48','11:00','11:12'],vals,'o-',label=n)
 ax.set_title(target);ax.set_ylabel('RMSE (G), mu > 0.7');ax.set_xlabel('Observation record time (TAI)')
axes[0].legend(fontsize=7);fig.tight_layout();fig.savefig(O/'summary.png',dpi=160);plt.close(fig)
pred=np.load(O/'reconstructions.npz');fig,axes=plt.subplots(2,4,figsize=(14,7))
for i,target in enumerate(['los_radial_proxy','vector_radial']):
 ref=np.load(O/f'observation_20170609_110000_TAI_{target}.npz');m=ref['mask'];x=ref['reference'][m]
 for ax,n in zip(axes[i],models):
  y=pred[n][m];ax.hexbin(x,y,gridsize=80,bins='log',mincnt=1,cmap='viridis');v=max(np.percentile(abs(x),99),np.percentile(abs(y),99));ax.plot([-v,v],[-v,v],'r--',lw=.6);ax.set_xlim(-v,v);ax.set_ylim(-v,v);ax.set_title(n);ax.set_xlabel(target+' (G)');ax.set_ylabel('prediction (G)')
fig.tight_layout();fig.savefig(O/'observational_scatter.png',dpi=160);plt.close(fig)
print('Report and summary plots written')
