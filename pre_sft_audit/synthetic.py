"""Analytic forward-generated time-tagged observations; no fit to audit outputs."""
from __future__ import annotations
import numpy as np
from audit_core import (Sampler, VARIANTS, existing, rotation_rate, run_variant,
                        sample_longitudes, select_sources, score, area_weights)


def mock_header(ny=181, nx=720):
    return {'NAXIS1': nx, 'NAXIS2': ny, 'CRVAL1': 180., 'CRPIX1': (nx+1)/2,
            'CDELT1': -360/nx, 'CRVAL2': 0., 'CRPIX2': (ny+1)/2, 'CDELT2': 2/ny}


def analytic_field(lon, lat, localized=False):
    p, b = np.deg2rad(lon), np.deg2rad(lat)
    smooth = 35*np.cos(b)**2*np.sin(3*p+.7*np.sin(b))+18*np.cos(7*p-2*b)*np.cos(b)**3
    if not localized:
        return smooth+12*np.sin(2*b)
    # Several latitudes and both longitude seams, with opposite polarities.
    result = smooth*.25
    for lp, bp, amp, width in [(2.,0.,120.,4.),(357.,55.,-110.,6.),
                               (4.,-55.,90.,5.),(180.,25.,-140.,7.),(240.,-25.,70.,5.)]:
        dl = (lon-lp+180)%360-180
        result = result+amp*np.exp(-.5*((dl*np.cos(np.deg2rad(bp))/width)**2+((lat-bp)/width)**2))
    return result


def make_case(case):
    h = mock_header()
    lon, lat = existing.calculate_coordinates(np.empty((h['NAXIS2'],h['NAXIS1'])),h)
    l, b = np.meshgrid(lon,lat)
    rate = rotation_rate(lat,True)
    if case=='stationary_control':
        rate = np.zeros_like(rate)
    elif case=='opposite_rotation_control':
        rate = -rate
    localized = case in ('seam_features','missing_data','evolving_control')
    truth = analytic_field(l,b,localized)
    maps = []
    for k in (-1,0,1):
        t = (180-l)/13.2+k*360/13.2
        # Explicit feature evolution F(l,t)=F0(l-rate*t), independent of inverse.
        field = analytic_field(l-rate[:,None]*t,b,localized)
        if case=='evolving_control':
            # Uniform time tag cannot be removed by longitudinal advection.
            field = field+.4*t*np.cos(np.deg2rad(b))
        if case=='missing_data':
            field = field.copy()
            field[0,:] = np.nan
            field[-1,:] = np.nan
            field[h['NAXIS2']//3, 100:106] = np.nan
        maps.append(field)
    return h, lon, lat, rate, truth, maps


def run_synthetic(out, write_csv, plot_function):
    records, details = [], []
    cases = ('smooth_rotation','seam_features','missing_data','stationary_control',
             'opposite_rotation_control','evolving_control')
    for case in cases:
        h, lon, lat, true_rate, truth, maps = make_case(case)
        sampler = Sampler(maps,[h]*3)
        fields = {'central': maps[1]}
        runs = {}
        for v in VARIANTS:
            runs[v] = run_variant(sampler,lon,lat,v)
            fields[v] = runs[v][0]
        exact = run_variant(sampler,lon,lat,'111',exact=True)
        fields['111_exact'] = exact[0]
        # Known-rate oracle checks convention even for stationary/opposite-rate controls.
        s = sample_longitudes(lon,true_rate,True,True)
        source, wrapped = select_sources(s,True)
        fields['known_rate_exact'] = sampler.sample(lat,source,wrapped)
        mask = np.isfinite(truth)
        for f in fields.values():
            mask &= np.isfinite(f)
        weights = area_weights(h)
        base = {v:score(f,truth,mask) for v,f in fields.items()}
        for v,f in fields.items():
            row = {'case':case, 'variant':v, 'mask':'common all variants, exact, oracle, central; full mock sphere',
                   'surface_area_fraction':float(weights[mask].sum()), **base[v]}
            for bname in ('000','central'):
                row[f'rmse_improvement_vs_{bname}_pct'] = 100*(1-base[v]['rmse_G']/base[bname]['rmse_G']) if base[bname]['rmse_G'] else None
            records.append(row)
        d = exact[1]-runs['111'][1]
        details.append({'case':case,'common_pixels':int(mask.sum()),
                        'first_order_vs_exact_max_shift_deg':float(np.max(abs(d))),
                        'first_order_vs_exact_field_rmse_G':score(exact[0],fields['111'],mask)['rmse_G']})
        np.savez_compressed(out/'arrays'/f'synthetic_{case}.npz',longitude=lon,latitude=lat,
                            truth=truth,mask=mask,true_rate_deg_day=true_rate,
                            input_previous=maps[0],input_current=maps[1],input_next=maps[2],
                            time_current_days=(180-lon)/13.2,
                            rotation_period_days=360/13.2,
                            **{f'field_{v}':f for v,f in fields.items()})
        if case in ('seam_features','missing_data'):
            plot_function(out/'plots'/f'synthetic_{case}.png', lon,lat,fields,truth,mask,runs,case)
    write_csv(out/'synthetic_metrics.csv',records)
    return records, details
