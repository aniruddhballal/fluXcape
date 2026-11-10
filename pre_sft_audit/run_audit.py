"""Run the complete offline pre-SFT audit. All writes stay under pre_sft_audit/."""
from __future__ import annotations
import csv
import itertools
import json
import platform
from pathlib import Path
import sys

import astropy
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage import map_coordinates
import scipy
import sunpy
from sunpy.coordinates.sun import carrington_rotation_time, carrington_rotation_number, L0
import astropy.units as u

from audit_core import (ROOT, VARIANTS, Sampler, existing, rotation_rate, run_variant,
                        score, area_weights, original_source_run, original_grid_vectorized)
from inventory import sha256
from observations import load_and_project, validator
from synthetic import run_synthetic

OUT = Path(__file__).resolve().parent


def write_json(path, data):
    def clean(x):
        if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)): return [clean(v) for v in x]
        if isinstance(x,np.generic): return clean(x.item())
        if isinstance(x,float) and not np.isfinite(x): return None
        if x is None or isinstance(x,(str,int,float,bool)): return x
        return str(x)
    path.write_text(json.dumps(clean(data),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path, rows):
    if not rows:
        return
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def improvements(row, base):
    for metric in ('rmse_G','mae_G'):
        for v in ('000','central'):
            row[f'{metric[:-2]}_improvement_vs_{v}_pct'] = 100*(1-row[metric]/base[v][metric]) if base[v][metric] else None
    return row


def plot_maps(path,lon,lat,fields,reference,mask,runs,title):
    fig,axs = plt.subplots(3,3,figsize=(15,10),layout='constrained')
    panels = [(fields['central'],'Untouched central map'),(reference,'Reference'),
              (mask.astype(float),'Common mask (0=excluded, 1=included)'),
              (fields['000'],'000: original expression, HMI grid'),
              (fields['100'],'100: latitude switch'),(fields['111'],'111: all switches'),
              (np.where(mask,fields['000']-reference,np.nan),'000 minus reference'),
              (np.where(mask,fields['111']-reference,np.nan),'111 minus reference'),
              (fields['111']-fields['central'],'111 minus untouched central')]
    for ax,(data,label) in zip(axs.flat,panels):
        is_mask = 'mask' in label
        im = ax.pcolormesh(lon,np.sin(np.deg2rad(lat)),data,cmap='gray' if is_mask else 'RdBu_r',
                          vmin=0 if is_mask else -100,vmax=1 if is_mask else 100,shading='auto',rasterized=True)
        ax.set_title(label,fontsize=10)
        ax.set_xlabel('Carrington longitude (deg)')
        ax.set_ylabel('sin(latitude)')
    fig.colorbar(axs[0,0].collections[0],ax=list(axs[:,[0,1]].flat),label='Field / residual (G)',shrink=.6)
    fig.suptitle(title)
    fig.savefig(path,dpi=130)
    plt.close(fig)
    if not runs:
        return
    fig,axs = plt.subplots(2,4,figsize=(16,7),layout='constrained')
    for ax,v in zip(axs.flat,VARIANTS):
        source = runs[v][2]
        im=ax.pcolormesh(lon,np.sin(np.deg2rad(lat)),source,cmap='viridis',vmin=0,vmax=2,shading='auto',rasterized=True)
        ax.set_title(v)
        ax.set_xlabel('Longitude (deg)')
        ax.set_ylabel('sin(latitude)')
    fig.colorbar(im,ax=list(axs.flat),ticks=[0,1,2],label='Source: previous / current / next CR',shrink=.65)
    fig.suptitle(title+': selected source, including queries that remain NaN')
    fig.savefig(path.with_name(path.stem+'_sources.png'),dpi=130)
    plt.close(fig)


def input_evidence():
    all_inputs=[]
    for path in sorted((ROOT/'SFT'/'fits_files').rglob('*.fits')):
        with fits.open(path,memmap=False,checksum=True) as hdu:
            h=hdu[0].header
            d=hdu[0].data
            all_inputs.append({'path':path.relative_to(ROOT).as_posix(),'rotation':h.get('CAR_ROT'),
                               'shape':list(d.shape),'finite_pixels':int(np.isfinite(d).sum()),
                               'checksum_ok':hdu[0].verify_checksum()==1,
                               'datasum_ok':hdu[0].verify_datasum()==1})
    rotations=sorted({r['rotation'] for r in all_inputs})
    write_json(OUT/'available_inputs.json',{'maps':all_inputs,'available_central_triples':
                 [n for n in rotations if n-1 in rotations and n+1 in rotations]})
    return all_inputs


def main():
    for directory in ('arrays','plots','logs','evidence'):
        (OUT/directory).mkdir(exist_ok=True)
    env={'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,
         'scipy':scipy.__version__,'astropy':astropy.__version__,'sunpy':sunpy.__version__,
         'matplotlib':matplotlib.__version__, 'automatic_network_downloads':False}
    write_json(OUT/'environment.json',env)
    print('Inventorying FITS data and checksums...',flush=True)
    inputs=input_evidence()
    metrics, samples, sensitivity, diagnostics, mapdiff, registration = [],[],[],[],[],[]
    literal_metrics, legacy_metrics, effects = [],[],[]
    pooled={v:[[],[]] for v in ('central',)+VARIANTS}
    evidence={}
    for center in (2120,2122,2124):
        print(f'CR{center}: loading maps and independently reprojecting raw HMI observation...',flush=True)
        maps,headers=existing.load_maps(ROOT/'SFT'/'fits_files'/'720x360',(center-1,center,center+1))
        if [h['CAR_ROT'] for h in headers] != [center-1,center,center+1]:
            raise AssertionError('CR chronology mismatch')
        obs,mu,lon,lat,obs_ev=load_and_project(center,headers[1])
        weights=area_weights(headers[1])
        sampler=Sampler(maps,headers)
        runs={v:run_variant(sampler,lon,lat,v) for v in VARIANTS}
        fields={'central':maps[1],**{v:runs[v][0] for v in VARIANTS}}
        extras={v+'_exact':run_variant(sampler,lon,lat,v,exact=True)[0] for v in ('010','011','110','111')}
        linear=Sampler(maps,headers,degree=1)
        extras.update({v+'_linear':run_variant(linear,lon,lat,v)[0] for v in ('000','100','111')})
        extras['111_epoch_rate_exact']=run_variant(sampler,lon,lat,'111',exact=True,
                                      omega0=obs_ev['timing']['derived_CM_rate_deg_day'],
                                      reference=float(obs_ev['metadata']['CRLN_OBS']))[0]
        full=np.isfinite(maps[1])
        for f in fields.values():
            full &= np.isfinite(f)
        mask=full & np.isfinite(obs)&(mu>=.8)
        if not mask.any():
            raise RuntimeError('No common observational pixels.')
        base={v:score(f,obs,mask) for v,f in fields.items()}
        # Reproduce existing pipeline and saved prior scores, independently.
        checks={}
        cache=np.load(ROOT/'SFT'/'validation_data'/f'cr{center}_observational_arrays.npz')
        for v,name in (('000','ananya'),('100','fixed')):
            old=existing.interpolate_field(maps,headers,lat,runs[v][2],runs[v][3])
            c=np.isfinite(old)&np.isfinite(fields[v])
            checks[v]={'existing_pipeline_same_finite_mask':bool(np.array_equal(np.isfinite(old),np.isfinite(fields[v]))),
                       'existing_pipeline_max_abs_difference_G':float(np.max(abs(old[c]-fields[v][c]))),
                       'cached_map_max_abs_difference_G':float(np.nanmax(abs(cache[name]-fields[v])))}
            if not checks[v]['existing_pipeline_same_finite_mask'] or checks[v]['existing_pipeline_max_abs_difference_G']>1e-9:
                raise AssertionError('Baseline reproduction failed.')
        for v,f in fields.items():
            row={'central_cr':center,'variant':v,'reference':'HMI45s radial estimate',
                 'mask':'common central+all8; finite observation; mu>=0.8',
                 'surface_area_fraction':float(weights[mask].sum()),**base[v]}
            improvements(row,base)
            metrics.append(row)
            pooled[v][0].append(f[mask]); pooled[v][1].append(obs[mask])
        sensmask=mask.copy()
        for f in extras.values():
            sensmask &= np.isfinite(f)
        sb={v:score(f,obs,sensmask) for v,f in fields.items()}
        for v,f in {**fields,**extras}.items():
            row={'central_cr':center,'variant':v,'mu_min':.8,'count_primary_mask':int(mask.sum()),
                 'surface_area_fraction':float(weights[sensmask].sum()),**score(f,obs,sensmask)}
            improvements(row,sb); sensitivity.append(row)
        for cutoff in (.9,.95):
            mm=mask&(mu>=cutoff)
            scores={v:score(f,obs,mm) for v,f in fields.items()}
            for v in fields:
                sensitivity.append(improvements({'central_cr':center,'variant':v,'mu_min':cutoff,
                    'surface_area_fraction':float(weights[mm].sum()),**scores[v]},scores))
        for v in VARIANTS:
            shifted,source=runs[v][1:3]
            delta=shifted-lon[None,:]
            row={'central_cr':center,'variant':v,'shift_min_deg':float(delta.min()),'shift_max_deg':float(delta.max()),
                 'shift_mean_abs_deg':float(np.mean(abs(delta))), 'sample_longitude_min_deg':float(shifted.min()),
                 'sample_longitude_max_deg':float(shifted.max()),'finite_reconstruction_pixels':int(np.isfinite(fields[v]).sum()),
                 'finite_reconstruction_area_fraction':float(weights[np.isfinite(fields[v])].sum())}
            for index,name in enumerate(('previous','current','next')):
                ss=source==index
                row[name+'_query_count']=int(ss.sum())
                row[name+'_query_area_fraction']=float(weights[ss].sum())
                row[name+'_finite_count']=int((ss&np.isfinite(fields[v])).sum())
                row[name+'_observation_mask_count']=int((ss&mask).sum())
            diagnostics.append(row)
        for a,b in itertools.combinations(fields,2):
            mapdiff.append({'central_cr':center,'variant_a':a,'variant_b':b,
                            'mask':'full sphere common central+all8',
                            'surface_area_fraction':float(weights[full].sum()),**score(fields[a],fields[b],full)})
        for bit,name in enumerate(('latitude','sampling_sign','seam')):
            for v in VARIANTS:
                if v[bit]=='1': continue
                target=v[:bit]+'1'+v[bit+1:]
                effects.append({'central_cr':center,'switch':name,'from':v,'to':target,
                                'delta_rmse_G':base[target]['rmse_G']-base[v]['rmse_G'],
                                'delta_mae_G':base[target]['mae_G']-base[v]['mae_G'],
                                'delta_r':base[target]['pearson_r']-base[v]['pearson_r']})
        # Fixed, identical coordinate samples: five geometric positions and strongest observed +/- values.
        selected=[]
        ll,bb=np.meshgrid(lon,lat)
        for target_lon,target_lat in ((180,0),(165,-15),(195,15),(180,-25),(180,25)):
            distance=((ll-target_lon)*np.cos(np.deg2rad(target_lat)))**2+(bb-target_lat)**2
            distance[~mask]=np.inf
            selected.append(('nearest_fixed_coordinate',np.unravel_index(np.argmin(distance),mask.shape)))
        for kind,arr in (('largest_observed_positive',np.where(mask,obs,-np.inf)),
                         ('largest_observed_negative',np.where(mask,-obs,-np.inf))):
            selected.append((kind,np.unravel_index(np.argmax(arr),mask.shape)))
        for reason,(iy,ix) in selected:
            samples.append({'central_cr':center,'selection':reason,'row':int(iy),'column':int(ix),
                            'longitude_deg':float(lon[ix]),'latitude_deg':float(lat[iy]),'mu':float(mu[iy,ix]),
                            'reference_Br_G':float(obs[iy,ix]),
                            **{f'Br_{v}_G':float(f[iy,ix]) for v,f in {**fields,'111_exact':extras['111_exact']}.items()}})
        # Registration control with equal masks and one documented extra linear interpolation.
        yy,xx=np.indices(maps[1].shape)
        reflect=(2*(headers[1]['CRPIX1']-1)-xx)%maps[1].shape[1]
        reflected=map_coordinates(maps[1],[yy,reflect],order=1,mode='grid-wrap')
        rm=mask&np.isfinite(reflected)
        for name,f in (('positive_physical_step',maps[1]),('negative_header_step',reflected)):
            registration.append({'central_cr':center,'orientation':name,**score(f,obs,rm)})
        print(f'CR{center}: executing literal original reconstruction block (no SFT evolution)...',flush=True)
        literal=original_source_run(maps)
        vec=original_grid_vectorized(maps)
        literal_same=bool(np.allclose(literal,vec,atol=1e-9,equal_nan=True))
        if not literal_same: raise AssertionError('Original AST and vectorized equivalent disagree.')
        literal_metrics.append({'central_cr':center,'variant':'literal_original_on_available_HMI',
                                'finite_output_pixels':int(np.isfinite(literal).sum()),
                                'status':'not observationally scoreable on these NaN-containing HMI inputs',
                                **score(literal,obs,mask&np.isfinite(literal))})
        legacy=original_grid_vectorized(maps,omit_incomplete_rows=True)
        old_lat=np.rad2deg(np.arcsin(np.linspace(-1,1,maps[1].shape[0])))
        old_lon=np.linspace(0,360,maps[1].shape[1])
        good=np.isfinite(legacy).all(axis=1)
        spl=RectBivariateSpline(old_lat[good],old_lon,legacy[good])
        ly,lx=np.meshgrid(lat,lon,indexing='ij')
        resampled=spl.ev(ly,lx)
        resampled[(ly<old_lat[good].min())|(ly>old_lat[good].max())]=np.nan
        lm=mask&np.isfinite(resampled)
        legacy_metrics.append({'central_cr':center,'variant':'original_grid_with_explicit_row_omission_then_resampling',
                               **score(resampled,obs,lm),
                               'map_rmse_vs_physical_000_G':score(resampled,fields['000'],lm)['rmse_G'],
                               'max_abs_map_difference_G':float(np.max(abs(resampled[lm]-fields['000'][lm])))})
        # Real chronological check with both FITS and SunPy: increasing CR means later epoch;
        # decreasing longitude in one rotation means later epoch.
        chronological=[]
        for cr in (center-1,center,center+1):
            chronological.append({'cr':cr,'midrotation_utc':carrington_rotation_time(cr+.5).utc.isot})
        timeline=[{'longitude_deg':p,'utc':carrington_rotation_time(center,p*u.deg).utc.isot}
                  for p in (359.,180.,1.)]
        tmid=carrington_rotation_time(center+.5)
        l0_values=[float(L0(tmid+d*u.day).deg) for d in (-.01,0,.01)]
        ev={'synoptic_headers':[dict(h) for h in headers],
            'incomplete_rows':[np.flatnonzero(~np.isfinite(m).all(axis=1)).tolist() for m in maps],
            'observation':obs_ev,'baseline_reproduction':checks,'literal_matches_vectorized':literal_same,
            'chronology_midrotations':chronological,'chronology_within_rotation':timeline,
            'L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d':l0_values,
            'primary_common_pixels':int(mask.sum()),'full_map_common_pixels':int(full.sum()),
            'full_map_common_area_fraction':float(weights[full].sum()),
            'primary_mask_same_as_prior':bool(np.array_equal(mask,cache['mask'])),
            'exact_vs_first_order':{'max_query_difference_deg':float(np.max(abs(run_variant(sampler,lon,lat,'111',exact=True)[1]-runs['111'][1]))),
                                    'full_common_field_difference':score(extras['111_exact'],fields['111'],full&np.isfinite(extras['111_exact']))}}
        evidence[str(center)]=ev
        write_json(OUT/'evidence'/f'cr{center}.json',ev)
        np.savez_compressed(OUT/'arrays'/f'cr{center}.npz',longitude=lon,latitude=lat,reference=obs,mu=mu,
            mask=mask,full_common_mask=full,area_weights=weights,literal_original=literal,
            original_grid_row_omitted=resampled,**{f'field_{v}':f for v,f in {**fields,**extras}.items()},
            **{f'source_{v}':runs[v][2] for v in VARIANTS},**{f'sample_longitude_{v}':runs[v][1] for v in VARIANTS})
        plot_maps(OUT/'plots'/f'cr{center}.png',lon,lat,fields,obs,mask,runs,f'CR{center}; near-center HMI reference only')
        print(f'CR{center}: {mask.sum():,} common pixels; RMSE central/000/111 = '+
              '/'.join(f"{base[v]['rmse_G']:.6f}" for v in ('central','000','111'))+' G',flush=True)
    pbase={}
    for v,(models,observations) in pooled.items():
        m,o=np.concatenate(models),np.concatenate(observations)
        pbase[v]=score(m,o,np.ones(m.shape,bool))
    pooledrows=[improvements({'variant':v,**pbase[v]},pbase) for v in pbase]
    write_csv(OUT/'metrics.csv',metrics)
    write_csv(OUT/'pooled_metrics.csv',pooledrows)
    write_csv(OUT/'sample_br.csv',samples)
    write_csv(OUT/'sensitivity_metrics.csv',sensitivity)
    write_csv(OUT/'longitude_sources.csv',diagnostics)
    write_csv(OUT/'map_differences.csv',mapdiff)
    write_csv(OUT/'factorial_effects.csv',effects)
    write_csv(OUT/'registration_metrics.csv',registration)
    write_csv(OUT/'literal_original_metrics.csv',literal_metrics)
    write_csv(OUT/'original_grid_sensitivity.csv',legacy_metrics)
    print('Running forward-generated synthetic cases and controls...',flush=True)
    synthetic,synthdetails=run_synthetic(OUT,write_csv,plot_maps)
    write_json(OUT/'evidence'/'synthetic_diagnostics.json',synthdetails)
    write_json(OUT/'run_summary.json',{'observational_rows':len(metrics),'synthetic_rows':len(synthetic),
              'centers':[2120,2122,2124],'input_map_count':len(inputs),'variants':list(VARIANTS),
              'synthetic_cases':sorted({r['case'] for r in synthetic})})
    print('Audit calculations complete.',flush=True)


if __name__=='__main__':
    main()
