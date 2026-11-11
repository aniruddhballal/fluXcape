"""Prepare the existing reconstruction for the local React viewer."""
import base64
import hashlib
import json
from pathlib import Path
import numpy as np
from synoptic_reconstruction import (FITS_FOLDER, ROTATIONS, load_maps, calculate_coordinates,
    calculate_delta_t, calculate_rotation_rate, calculate_ananya_rotation_rate, calculate_phi_prime,
    select_source_map, interpolate_field)

root = Path(__file__).resolve().parent
maps, headers = load_maps()
longitude, latitude = calculate_coordinates(maps[1], headers[1])
delta_t = calculate_delta_t(longitude)


def reconstruct(rate):
    phi_prime = calculate_phi_prime(longitude, delta_t, rate)
    source, wrapped = select_source_map(phi_prime)
    return interpolate_field(maps, headers, latitude, source, wrapped)

def encode(data):
    return base64.b64encode(np.asarray(data, dtype='<f4').tobytes()).decode('ascii')


def package_result(result):
    valid = np.isfinite(maps[1]) & np.isfinite(result)
    difference = result[valid] - maps[1][valid]
    return {'data': encode(result), 'metrics': {
        'bias': float(np.mean(difference)), 'mae': float(np.mean(np.abs(difference))),
        'rmse': float(np.sqrt(np.mean(difference**2))), 'valid': int(valid.sum()),
        'total': int(valid.size),
    }}


ananya = reconstruct(calculate_ananya_rotation_rate(latitude))
fixed = reconstruct(calculate_rotation_rate(latitude))
header = headers[1]
validation_file = root / 'validation_data' / f'cr{ROTATIONS[1]}_observational_metrics.json'
validation = None
if validation_file.exists():
    candidate = json.loads(validation_file.read_text(encoding='utf-8'))
    paths = [root / 'synoptic_reconstruction.py', root / 'prepare_viewer_data.py', root / 'validate_observations.py']
    paths += [FITS_FOLDER / '720x360' / f'hmi.Synoptic_Mr_small.{n}.fits' for n in ROTATIONS]
    # Use the same logical labels as the validator, independent of data location.
    fingerprints = {str(p.relative_to(root if p.suffix == '.py' else FITS_FOLDER.parent)).replace('\\', '/'): hashlib.sha256(
        p.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode('utf-8')
        if p.suffix == '.py' else p.read_bytes()).hexdigest() for p in paths}
    if candidate.get('cr') == ROTATIONS[1] and candidate.get('input_sha256') == fingerprints:
        validation = candidate
    else:
        print('Observational validation is stale; rerun "my work/SFT/validate_observations.py".')
payload = {
    'rotation': ROTATIONS[1], 'rotations': list(ROTATIONS),
    'width': maps[1].shape[1], 'height': maps[1].shape[0],
    'original': encode(maps[1]),
    'reconstructions': {'ananya': package_result(ananya), 'fixed': package_result(fixed)},
    'coordinates': {key: header[key] for key in ('CRPIX1', 'CRVAL1', 'CDELT1', 'CRPIX2', 'CRVAL2', 'CDELT2')},
    'observational_validation': validation,
}
# Export the physical longitude convention used for reconstruction and validation.
payload['coordinates']['CDELT1'] = abs(payload['coordinates']['CDELT1'])
output = root / 'viewer' / 'public' / 'maps.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, separators=(',', ':')), encoding='utf-8')
print(f'Viewer data prepared: {output}')
