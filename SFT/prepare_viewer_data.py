"""Prepare the existing reconstruction for the local React viewer."""
import base64
import json
from pathlib import Path
import numpy as np
from synoptic_reconstruction import (ROTATIONS, load_maps, calculate_coordinates,
    calculate_delta_t, calculate_rotation_rate, calculate_phi_prime,
    select_source_map, interpolate_field)

root = Path(__file__).resolve().parent
maps, headers = load_maps(root / 'fits_files' / '720x360')
longitude, latitude = calculate_coordinates(maps[1], headers[1])
phi_prime = calculate_phi_prime(longitude, calculate_delta_t(longitude), calculate_rotation_rate(latitude))
source, wrapped = select_source_map(phi_prime)
result = interpolate_field(maps, headers, latitude, source, wrapped)
valid = np.isfinite(maps[1]) & np.isfinite(result)
difference = result[valid] - maps[1][valid]

def encode(data):
    return base64.b64encode(np.asarray(data, dtype='<f4').tobytes()).decode('ascii')

header = headers[1]
payload = {
    'rotation': ROTATIONS[1], 'rotations': list(ROTATIONS),
    'width': maps[1].shape[1], 'height': maps[1].shape[0],
    'original': encode(maps[1]), 'reconstructed': encode(result),
    'coordinates': {key: header[key] for key in ('CRPIX1', 'CRVAL1', 'CDELT1', 'CRPIX2', 'CRVAL2', 'CDELT2')},
    'metrics': {'bias': float(np.mean(difference)), 'mae': float(np.mean(np.abs(difference))),
                'rmse': float(np.sqrt(np.mean(difference**2))), 'valid': int(valid.sum()), 'total': int(valid.size)},
}
output = root / 'viewer' / 'public' / 'maps.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, separators=(',', ':')), encoding='utf-8')
print(f'Viewer data prepared: {output}')
