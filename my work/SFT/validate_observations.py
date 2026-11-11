"""Validate CR 2120 reconstructions against an independent HMI 45-second image.

Run from the repository root using the project virtual environment.
Synoptic inputs are in my work/fits_files. The source image is cached in
my work/SFT/validation_data and downloaded from JSOC if absent.
"""
from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, urlretrieve

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from sunpy.coordinates.frames import HeliographicCarrington, HeliographicStonyhurst, Helioprojective
from sunpy.coordinates.sun import carrington_rotation_time

from synoptic_reconstruction import (FITS_FOLDER, ROTATIONS, load_maps, calculate_coordinates,
    calculate_delta_t, calculate_rotation_rate, calculate_ananya_rotation_rate,
    calculate_phi_prime, select_source_map, interpolate_field)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'validation_data'
JSOC = 'http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info'
MIN_MU = 0.8
SMOOTH_SIGMA_PIXELS = 3.0
SERIES = 'hmi.M_45s'


def query(**params):
    with urlopen(JSOC + '?' + urlencode(params), timeout=60) as response:
        result = json.load(response)
    if result.get('status') != 0:
        raise RuntimeError(f'JSOC query failed: {result}')
    return result


def parse_tai(value):
    """Parse a JSOC TAI timestamp without mistaking it for UTC."""
    date, clock, scale = value.split('_')
    if scale != 'TAI':
        raise ValueError(f'Expected TAI timestamp: {value}')
    return Time(date.replace('.', '-') + 'T' + clock, format='isot', scale='tai')


def record_values(result):
    return {item['name']: item['values'] for item in result['keywords']}


def reference_and_record(header):
    """Bracket the observed 180-degree CMP using 45-second JSOC records."""
    nominal = parse_tai(header['T_ROT'])
    start = (nominal - 12 * u.min).tai.strftime('%Y.%m.%d_%H:%M:%S_TAI')
    result = query(op='rs_list', ds=f'{SERIES}[{start}/24m]',
                   key='T_REC,T_OBS,CRLN_OBS,QUALITY', seg='magnetogram')
    values = record_values(result)
    records = []
    for rec, obs, lon, quality, segment in zip(values['T_REC'], values['T_OBS'],
            values['CRLN_OBS'], values['QUALITY'], result['segments'][0]['values']):
        if quality != '0x00000000' or not segment.startswith('/SUM'):
            continue
        records.append({'rec': rec, 'obs': obs, 'time': parse_tai(obs),
                        'longitude': float(lon), 'segment': segment})
    records.sort(key=lambda r: r['time'].tai.jd)
    for before, after in zip(records, records[1:]):
        if before['longitude'] >= 180 >= after['longitude']:
            fraction = (before['longitude'] - 180) / (before['longitude'] - after['longitude'])
            crossing = before['time'] + fraction * (after['time'] - before['time'])
            closest = min(records, key=lambda r: abs((r['time'] - crossing).to_value(u.s)))
            return nominal, crossing, before, after, closest
    raise RuntimeError('Could not bracket the 180-degree central-meridian crossing.')


def observation(record):
    """Download the original compressed JSOC segment and its separate metadata."""
    OUTPUT.mkdir(exist_ok=True)
    tag = record['rec'].replace('.', '').replace(':', '')
    image = OUTPUT / f'{SERIES}.{tag}.magnetogram.fits'
    meta_file = OUTPUT / f'{SERIES}.{tag}.jsoc.json'
    meta = query(op='rs_list', ds=f"{SERIES}[{record['rec']}]", key='**ALL**', seg='magnetogram')
    if meta['count'] != 1:
        raise RuntimeError('Expected exactly one magnetogram record.')
    meta_file.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    url = 'https://jsoc1.stanford.edu' + meta['segments'][0]['values'][0]
    if not image.exists():
        partial = image.with_suffix('.fits.part')
        try:
            urlretrieve(url, partial)
            with fits.open(partial) as hdus:
                if hdus[1].data.shape != (4096, 4096):
                    raise ValueError('Unexpected magnetogram shape.')
            partial.replace(image)
        finally:
            partial.unlink(missing_ok=True)
    values = {item['name']: item['values'][0] for item in meta['keywords']}
    if values['QUALITY'] != '0x00000000':
        raise ValueError('Magnetogram does not have QUALITY=0.')
    with fits.open(image, memmap=False) as hdus:
        data = np.asarray(hdus[1].data, dtype=np.float32)
    if data.shape != (4096, 4096):
        raise ValueError('Unexpected magnetogram shape.')
    return image, values, data, url


def project_observation(data, meta, synoptic_header):
    """Sample smoothed LOS pixels onto the physical Carrington grid as radial field."""
    time = parse_tai(meta['T_OBS'])
    dsun = float(meta['DSUN_OBS'])
    rsun = float(meta['RSUN_REF'])
    obs_lat = float(meta['CRLT_OBS'])
    obs_lon = float(meta['CRLN_OBS'])

    # Build an observer whose Carrington coordinates agree with this HMI record.
    earth_meridian = SkyCoord(0*u.deg, obs_lat*u.deg, dsun*u.m,
                             frame=HeliographicStonyhurst, obstime=time)
    sunpy_lon = earth_meridian.transform_to(HeliographicCarrington(observer=earth_meridian)).lon.deg
    hgs_offset = (obs_lon - sunpy_lon + 180) % 360 - 180
    observer = SkyCoord(hgs_offset*u.deg, obs_lat*u.deg, dsun*u.m,
                        frame=HeliographicStonyhurst, obstime=time)
    actual_lon = observer.transform_to(HeliographicCarrington(observer=observer)).lon.deg
    if abs((actual_lon - obs_lon + 180) % 360 - 180) > 1e-6:
        raise ValueError('Observer longitude does not match the HMI record.')

    ny, nx = int(synoptic_header['NAXIS2']), int(synoptic_header['NAXIS1'])
    # Use the exact same HMI longitude/latitude grid as the reconstruction.
    longitude, latitude = calculate_coordinates(np.empty((ny, nx)), synoptic_header)
    lon_grid, lat_grid = np.meshgrid(longitude, latitude)
    angle = (np.sin(np.radians(lat_grid))*np.sin(np.radians(obs_lat))
             + np.cos(np.radians(lat_grid))*np.cos(np.radians(obs_lat))
             * np.cos(np.radians(lon_grid - obs_lon)))
    # Angle between the outward surface normal and the finite-distance LOS.
    ratio = rsun / dsun
    mu = (angle - ratio) / np.sqrt(1 - 2*ratio*angle + ratio**2)
    selected = np.isfinite(mu) & (mu >= MIN_MU)

    carr = SkyCoord(lon_grid[selected]*u.deg, lat_grid[selected]*u.deg, rsun*u.m,
                    frame=HeliographicCarrington, obstime=time, observer=observer)
    image_coords = carr.transform_to(Helioprojective(observer=observer, obstime=time, rsun=rsun*u.m))
    h = fits.Header()
    for key in ('CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2', 'CRPIX1', 'CRPIX2',
                'CRVAL1', 'CRVAL2', 'CDELT1', 'CDELT2', 'CROTA2'):
        h[key] = float(meta[key]) if key.startswith(('CRPIX', 'CRVAL', 'CDELT', 'CROTA')) else meta[key]
    wcs = WCS(h)
    px, py = wcs.world_to_pixel_values(image_coords.Tx.to_value(u.deg), image_coords.Ty.to_value(u.deg))

    # A small Gaussian reduces high-resolution snapshot aliasing before sampling.
    # Missing detector pixels are tracked separately, not replaced by measurements.
    finite = np.isfinite(data)
    weight = gaussian_filter(finite.astype(np.float32), SMOOTH_SIGMA_PIXELS, mode='constant', cval=0)
    smoothed = gaussian_filter(np.where(finite, data, 0).astype(np.float32), SMOOTH_SIGMA_PIXELS, mode='constant', cval=0)
    inside = np.isfinite(px) & np.isfinite(py) & (px >= 0) & (px <= data.shape[1]-1) & (py >= 0) & (py <= data.shape[0]-1)
    observed = np.full((ny, nx), np.nan, dtype=np.float64)
    coords = np.vstack((py[inside], px[inside]))
    sampled = map_coordinates(smoothed, coords, order=1, mode='constant', cval=np.nan)
    weights = map_coordinates(weight, coords, order=1, mode='constant', cval=0)
    radial = np.full(px.shape, np.nan)
    valid_samples = (weights >= 0.999) & np.isfinite(sampled)
    good = inside.copy()
    good[inside] = valid_samples
    radial[good] = (sampled[valid_samples] / weights[valid_samples]) / mu[selected][good]
    observed[selected] = radial
    return observed, mu, longitude, latitude


def reconstruction(maps, headers, longitude, latitude, rate):
    phi_prime = calculate_phi_prime(longitude, calculate_delta_t(longitude), rate)
    source, wrapped = select_source_map(phi_prime)
    return interpolate_field(maps, headers, latitude, source, wrapped)


def metrics(model, observation, mask):
    residual = model[mask] - observation[mask]
    return {'count': int(mask.sum()), 'bias_gauss': float(np.mean(residual)),
            'mae_gauss': float(np.mean(np.abs(residual))),
            'rmse_gauss': float(np.sqrt(np.mean(residual**2))),
            'pearson_r': float(np.corrcoef(model[mask], observation[mask])[0, 1])}


def input_fingerprints(rotations=ROTATIONS):
    """Identify the reconstruction code and input maps used for a report."""
    paths = [ROOT / 'synoptic_reconstruction.py', ROOT / 'prepare_viewer_data.py', ROOT / 'validate_observations.py']
    paths += [FITS_FOLDER / '720x360' / f'hmi.Synoptic_Mr_small.{n}.fits' for n in rotations]
    # Keep the existing logical input labels even though data now live outside SFT.
    return {str(p.relative_to(ROOT if p.suffix == '.py' else FITS_FOLDER.parent)).replace('\\', '/'): hashlib.sha256(
        p.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode('utf-8')
        if p.suffix == '.py' else p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rotation', type=int, default=ROTATIONS[1], help='central Carrington rotation')
    center = parser.parse_args().rotation
    rotations = (center - 1, center, center + 1)
    maps, headers = load_maps(rotations=rotations)
    if [h.get('CAR_ROT') for h in headers] != list(rotations):
        raise ValueError('The FITS headers must identify the requested consecutive rotations.')
    nominal, crossing, before, after, record = reference_and_record(headers[1])
    sunpy_earth_crossing = carrington_rotation_time(center + 0.5)
    image, meta, data, source_url = observation(record)
    observed, mu, physical_longitude, physical_latitude = project_observation(data, meta, headers[1])
    model_lon, model_lat = calculate_coordinates(maps[1], headers[1])
    if not (np.allclose(model_lon, physical_longitude, equal_nan=True) and
            np.allclose(model_lat, physical_latitude, equal_nan=True)):
        raise ValueError('Reconstruction and observational coordinate grids differ.')
    ananya = reconstruction(maps, headers, model_lon, model_lat, calculate_ananya_rotation_rate(model_lat))
    fixed = reconstruction(maps, headers, model_lon, model_lat, calculate_rotation_rate(model_lat))
    # The intersection is identical for both: visible, finite observation and both models.
    mask = np.isfinite(observed) & np.isfinite(ananya) & np.isfinite(fixed) & np.isfinite(maps[1]) & (mu >= MIN_MU)
    if mask.sum() < 10:
        raise ValueError('Too few common pixels for comparison.')
    # Registration control: sample the original map as if the negative header
    # sign were physical. The signed and physical orientations share a mask.
    rows, columns = np.indices(maps[1].shape)
    reflected_columns = (2 * (headers[1]['CRPIX1'] - 1) - columns) % maps[1].shape[1]
    negative_orientation = map_coordinates(maps[1], [rows, reflected_columns],
                                           order=1, mode='grid-wrap')
    registration_mask = mask & np.isfinite(negative_orientation)
    sensitivity = {}
    for cutoff in (0.8, 0.9, 0.95):
        common = mask & (mu >= cutoff)
        sensitivity[str(cutoff)] = {'original': metrics(maps[1], observed, common),
                                    'ananya': metrics(ananya, observed, common),
                                    'fixed': metrics(fixed, observed, common)}
    results = {'cr': center, 'input_rotations': list(rotations), 'input_sha256': input_fingerprints(rotations),
        'reference': {'definition': 'Observed HMI central meridian longitude 180 degrees, linearly interpolated between adjacent quality-zero 45-second records',
                      'crossing_tai': crossing.tai.isot, 'crossing_utc': crossing.utc.isot,
                      'header_T_ROT_tai': nominal.tai.isot,
                      'sunpy_earth_midrotation_tai': sunpy_earth_crossing.tai.isot,
                      'sunpy_earth_midrotation_utc': sunpy_earth_crossing.utc.isot,
                      'bracketing_records': [{'T_REC': r['rec'], 'T_OBS': r['obs'], 'CRLN_OBS_deg': r['longitude']} for r in (before, after)]},
        'observation': {'series': SERIES, 'T_REC': record['rec'], 'T_OBS': record['obs'],
                        'T_OBS_utc': record['time'].utc.isot, 'offset_seconds': float((record['time'] - crossing).to_value(u.s)),
                        'QUALITY': meta['QUALITY'], 'CRLN_OBS_deg': float(meta['CRLN_OBS']),
                        'CRLT_OBS_deg': float(meta['CRLT_OBS']), 'source_url': source_url,
                        'file': image.name, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest()},
        'method': {'mu_min': MIN_MU, 'smoothing_sigma_detector_pixels': SMOOTH_SIGMA_PIXELS,
                   'interpolation': 'bilinear detector sampling; LOS divided by mu',
                   'synoptic_longitude_step': 'absolute FITS CDELT1, per SunPy HMI synoptic-map convention',
                   'mask': 'finite observation, original and both reconstructions; mu >= 0.8; finite smoothed observation neighborhood'},
        'scores': {'original': metrics(maps[1], observed, mask), 'ananya': metrics(ananya, observed, mask), 'fixed': metrics(fixed, observed, mask)},
        'sensitivity_mu': sensitivity,
        'diagnostics': {'original_vs_observation_same_mask': metrics(maps[1], observed, mask & np.isfinite(maps[1])),
                        'registration_control': {
                            'positive_orientation': metrics(maps[1], observed, registration_mask),
                            'negative_header_orientation': metrics(negative_orientation, observed, registration_mask),
                        },
                        'header_CDELT1': float(headers[1]['CDELT1'])}}
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT/f'cr{center}_observational_metrics.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    np.savez_compressed(OUTPUT/f'cr{center}_observational_arrays.npz', observation=observed, ananya=ananya, fixed=fixed,
                        mu=mu, mask=mask, longitude=physical_longitude, latitude=physical_latitude)
    fig, axes = plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    for ax, field, title in zip(axes.flat, (observed, ananya, fixed, fixed-observed),
                                ('HMI 45 s radial estimate','Ananya reconstruction','Fixed reconstruction','Fixed minus observation')):
        plotted = np.where(mask, field, np.nan)
        im = ax.imshow(plotted,origin='lower',cmap='RdBu_r',vmin=-100,vmax=100)
        ax.set_title(title); ax.set_xlabel('Map column'); ax.set_ylabel('Map row')
    fig.colorbar(im,ax=axes,label='Gauss',shrink=.8,extend='both')
    fig.savefig(OUTPUT/f'cr{center}_observational_comparison.png',dpi=150)
    plt.close(fig)
    print(json.dumps(results,indent=2))


if __name__ == '__main__':
    main()
