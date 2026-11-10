"""Offline HMI observation projection and independent geometry checks."""
from __future__ import annotations
import json
from pathlib import Path

import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from astropy.utils import iers
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from audit_core import ROOT, existing
from inventory import sha256
import validate_observations as validator

iers.conf.auto_download = False


def independent_projection(data, meta, header, sigma=3.):
    """Direct finite-distance sphere -> tangent-plane -> detector projection.

    Uses HMI's stated observer B0/L0 directly, without SunPy frame transforms.
    The WCS and detector smoothing deliberately match the primary comparison.
    """
    lon, lat = existing.calculate_coordinates(np.empty((header['NAXIS2'], header['NAXIS1'])), header)
    l, b = np.meshgrid(np.deg2rad(lon-float(meta['CRLN_OBS'])), np.deg2rad(lat))
    b0 = np.deg2rad(float(meta['CRLT_OBS']))
    r, d = float(meta['RSUN_REF']), float(meta['DSUN_OBS'])
    c = np.sin(b)*np.sin(b0)+np.cos(b)*np.cos(b0)*np.cos(l)
    x = r*np.cos(b)*np.sin(l)
    y = r*(np.sin(b)*np.cos(b0)-np.cos(b)*np.cos(l)*np.sin(b0))
    z = d-r*c
    tx = np.rad2deg(np.arctan2(x, z))
    ty = np.rad2deg(np.arctan2(y, np.sqrt(z*z+x*x)))
    mu = (d*c-r)/np.sqrt(d*d+r*r-2*d*r*c)
    h = fits.Header()
    for key in ('CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2', 'CRPIX1', 'CRPIX2',
                'CRVAL1', 'CRVAL2', 'CDELT1', 'CDELT2', 'CROTA2'):
        h[key] = float(meta[key]) if key.startswith(('CRPIX','CRVAL','CDELT','CROTA')) else meta[key]
    px, py = WCS(h).world_to_pixel_values(tx, ty)
    good = (mu>=.8) & np.isfinite(px) & np.isfinite(py) & (px>=0) & (py>=0) & (px<=data.shape[1]-1) & (py<=data.shape[0]-1)
    finite = np.isfinite(data)
    w = gaussian_filter(finite.astype(np.float32), sigma, mode='constant', cval=0)
    v = gaussian_filter(np.where(finite, data, 0).astype(np.float32), sigma, mode='constant', cval=0)
    coords = np.array([py[good], px[good]])
    weights = map_coordinates(w, coords, order=1, mode='constant', cval=0)
    sampled = map_coordinates(v, coords, order=1, mode='constant', cval=np.nan)
    br = np.full(mu.shape, np.nan)
    valid = (weights>=.999) & np.isfinite(sampled)
    samples = np.full(len(sampled), np.nan)
    samples[valid] = sampled[valid]/weights[valid]/mu[good][valid]
    br[good] = samples
    return br, mu


def load_and_project(center, header):
    folder = ROOT/'SFT'/'validation_data'
    saved = json.loads((folder/f'cr{center}_observational_metrics.json').read_text())
    image = folder/saved['observation']['file']
    meta_path = image.with_name(image.name.replace('.magnetogram.fits','.jsoc.json'))
    full_meta = json.loads(meta_path.read_text())
    meta = {r['name']: r['values'][0] for r in full_meta['keywords']}
    if meta['QUALITY'] != '0x00000000':
        raise ValueError('Observation QUALITY is not zero.')
    if sha256(image) != saved['observation']['sha256']:
        raise ValueError('Cached observation hash mismatch.')
    if meta['T_REC'] != saved['observation']['T_REC'] or meta['T_OBS'] != saved['observation']['T_OBS']:
        raise ValueError('Metadata and selected record mismatch.')
    with fits.open(image, memmap=False, checksum=True) as hdus:
        data = np.asarray(hdus[1].data, dtype=np.float32)
        image_headers = [dict(h.header) for h in hdus]
    observed, mu, lon, lat = validator.project_observation(data, meta, header)
    manual, manual_mu = independent_projection(data, meta, header)
    common = np.isfinite(manual)&np.isfinite(observed)
    projection_check = {'common_count': int(common.sum()),
                        'max_abs_mu_difference': float(np.nanmax(abs(mu-manual_mu))),
                        'max_abs_Br_difference_G': float(np.max(abs(manual[common]-observed[common]))),
                        'rmse_Br_difference_G': float(np.sqrt(np.mean((manual[common]-observed[common])**2))),
                        'same_finite_mask': bool(np.array_equal(np.isfinite(manual),np.isfinite(observed)))}
    cache = np.load(folder/f'cr{center}_observational_arrays.npz')
    cm = np.isfinite(cache['observation'])&np.isfinite(observed)
    cache_check = {'same_finite_mask': bool(np.array_equal(np.isfinite(cache['observation']), np.isfinite(observed))),
                   'max_abs_observation_difference_G': float(np.max(abs(cache['observation'][cm]-observed[cm])))}
    brackets = saved['reference']['bracketing_records']
    tb, ta = [validator.parse_tai(r['T_OBS']) for r in brackets]
    lb, la = [r['CRLN_OBS_deg'] for r in brackets]
    crossing = tb+(lb-180)/(lb-la)*(ta-tb)
    local_omega0 = (lb-la)/(ta-tb).to_value(u.day)
    obs_time = validator.parse_tai(meta['T_OBS'])
    timing = {'derived_crossing_utc': crossing.utc.isot,
              'stored_crossing_utc': saved['reference']['crossing_utc'],
              'bracket_seconds': float((ta-tb).to_value(u.s)),
              'derived_CM_rate_deg_day': float(local_omega0),
              'observation_minus_crossing_s': float((obs_time-crossing).to_value(u.s)),
              'observation_minus_header_T_ROT_s': float((obs_time-validator.parse_tai(header['T_ROT'])).to_value(u.s)),
              'brackets_are_saved_metadata_not_requeried': True}
    evidence = {'saved_report': saved, 'metadata': meta, 'raw_fits_headers': image_headers,
                'image_sha256': sha256(image), 'metadata_sha256': sha256(meta_path),
                'independent_projection': projection_check, 'cache_check': cache_check,
                'timing': timing}
    return observed, mu, lon, lat, evidence
