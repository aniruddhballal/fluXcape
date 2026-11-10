"""Additional resolution and subdegree-registration diagnostics, not fitted fixes."""
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
from audit_core import ROOT, VARIANTS, Sampler, score, existing
from observations import independent_projection
from run_audit import write_csv, plot_maps

OUT=Path(__file__).resolve().parent


def main():
    smooth_rows,registration_rows=[],[]
    for cr in (2120,2122,2124):
        print(f'CR{cr}: detector smoothing and registration sensitivity...',flush=True)
        saved=np.load(OUT/'arrays'/f'cr{cr}.npz')
        ev=json.loads((OUT/'evidence'/f'cr{cr}.json').read_text())
        fields={v:saved['field_'+v] for v in ('central',)+VARIANTS}
        obs={3:saved['reference']}
        meta=ev['observation']['metadata']; header=ev['synoptic_headers'][1]
        image=ROOT/'SFT'/'validation_data'/ev['observation']['saved_report']['observation']['file']
        with fits.open(image,memmap=False) as hdus:
            data=np.asarray(hdus[1].data,dtype=np.float32)
        for sigma in (6,12):
            obs[sigma]=independent_projection(data,meta,header,sigma=sigma)[0]
        mask=saved['mask'].copy()
        for o in obs.values(): mask &= np.isfinite(o)
        for sigma,o in obs.items():
            for v,f in fields.items():
                smooth_rows.append({'central_cr':cr,'sigma_detector_pixels':sigma,'variant':v,
                                    'mask':'intersection primary and all sigma values; mu>=0.8',
                                    **score(f,o,mask)})
        np.savez_compressed(OUT/'arrays'/f'cr{cr}_reference_sensitivity.npz',mask=mask,
                            **{f'reference_sigma_{sigma}':o for sigma,o in obs.items()})
        central=fits.getdata(ROOT/'SFT'/'fits_files'/'720x360'/f'hmi.Synoptic_Mr_small.{cr}.fits')
        sampler=Sampler([central]*3,[header]*3)
        lon,lat=saved['longitude'],saved['latitude']
        shifted_fields={}
        for dl in (-1.,-.5,0.,.5,1.):
            for db in (-.5,0.,.5):
                source=np.ones(central.shape,int)
                query=np.broadcast_to(lon[None,:]+dl,central.shape)
                shifted_fields[dl,db]=sampler.sample(lat+db,source,query)
        rm=saved['mask'].copy()
        for f in shifted_fields.values(): rm &= np.isfinite(f)
        for (dl,db),f in shifted_fields.items():
            registration_rows.append({'central_cr':cr,'source_query_longitude_offset_deg':dl,
                                      'source_query_latitude_offset_deg':db,
                                      'mask':'common all registration offsets and primary mask',
                                      **score(f,saved['reference'],rm)})
        # Re-render persisted primary plots after final visual inspection.
        runs={v:(None,saved['sample_longitude_'+v],saved['source_'+v],None) for v in VARIANTS}
        plot_maps(OUT/'plots'/f'cr{cr}.png',lon,lat,fields,saved['reference'],saved['mask'],runs,
                  f'CR{cr}; near-center HMI reference only')
    write_csv(OUT/'smoothing_sensitivity.csv',smooth_rows)
    write_csv(OUT/'registration_offset_sensitivity.csv',registration_rows)
    # Refresh synthetic plots from saved results as well, without recalculation.
    from synthetic import make_case
    from audit_core import run_variant
    for case in ('seam_features','missing_data'):
        h,lon,lat,rate,truth,maps=make_case(case)
        a=np.load(OUT/'arrays'/f'synthetic_{case}.npz')
        fields={v:a['field_'+v] for v in ('central',)+VARIANTS}
        sampler=Sampler(maps,[h]*3)
        runs={v:run_variant(sampler,lon,lat,v) for v in VARIANTS}
        plot_maps(OUT/'plots'/f'synthetic_{case}.png',lon,lat,fields,truth,a['mask'],runs,case)
    print('Discrepancy diagnostics and final figures complete.',flush=True)


if __name__=='__main__':
    main()
