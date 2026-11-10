"""Isolated reconstruction switches; existing SFT code is imported read-only.

Angles are degrees, rates degrees/day, and epoch offsets days. Sources are
0=previous CR, 1=current CR, 2=next CR. No SFT evolution is executed.
"""
from __future__ import annotations
import ast
import importlib.util
from pathlib import Path
import sys

import numpy as np
from scipy.interpolate import RectBivariateSpline

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'SFT'))
import synoptic_reconstruction as existing

VARIANTS = ('000', '100', '010', '001', '110', '101', '011', '111')


def rotation_rate(latitude, fix_latitude=False):
    f = np.sin if fix_latitude else np.cos
    q = f(np.deg2rad(latitude)) ** 2
    return 0.18 - 2.3 * q - 1.62 * q ** 2


def sample_longitudes(longitude, rate, invert=False, exact=False, omega0=13.2, reference=180.):
    """Backward sample an unwrapped, time-ordered three-CR synoptic mosaic.

    Exact inverse solves s = phi + rate*(reference-s)/omega0, where
    t_obs(s)-t_ref=(reference-s)/omega0. Exact is a separate sensitivity,
    not silently included in the three-switch first-order factorial.
    """
    phi = np.asarray(longitude)[None, :]
    a = np.asarray(rate)[:, None] / omega0
    if exact:
        if not invert:
            raise ValueError('Exact inverse requires invert=True.')
        if np.any(np.abs(1+a) < 1e-10):
            raise ValueError('Degenerate trajectory parallel to observing meridian.')
        return reference + (phi-reference)/(1+a)
    return phi + (-1 if invert else 1) * a * (phi-reference)


def select_sources(shifted, reverse=False):
    """Keep exactly 0 and 360 in current CR, matching original strict tests.

    With HMI pixel centers neither endpoint is supported by the spline. Such
    queries stay NaN, rather than extrapolate or fill the gap periodically.
    """
    s = np.asarray(shifted)
    low, high = s < 0, s > 360
    source = np.where(low, 2 if reverse else 0, np.where(high, 0 if reverse else 2, 1))
    wrapped = np.where(low, s+360, np.where(high, s-360, s))
    if np.any((wrapped < 0) | (wrapped > 360)):
        raise ValueError('Three-map reconstruction supports at most one wrap.')
    return source, wrapped


class Sampler:
    """Same cubic RectBivariateSpline and whole-incomplete-row policy as SFT.

    Splines are cached per run to reuse infrastructure without rebuilding
    the identical three splines for every switch combination.
    """
    def __init__(self, maps, headers, degree=3):
        self.parts = []
        for data, header in zip(maps, headers):
            lon, lat = existing.calculate_coordinates(data, header)
            good = np.isfinite(data).all(axis=1) & np.isfinite(lat)
            order = np.argsort(lon)
            x, y = lat[good], lon[order]
            if len(x) <= degree or len(y) <= degree:
                self.parts.append(None)
                continue
            spline = RectBivariateSpline(x, y, data[good][:, order], kx=degree, ky=degree, s=0)
            self.parts.append((spline, x.min(), x.max(), y.min(), y.max()))

    def sample(self, latitude, source, wrapped):
        field = np.full(source.shape, np.nan)
        lat = np.broadcast_to(np.asarray(latitude)[:, None], source.shape)
        for index, part in enumerate(self.parts):
            if part is None:
                continue
            spline, xmin, xmax, ymin, ymax = part
            use = ((source == index) & np.isfinite(lat) & np.isfinite(wrapped)
                   & (lat >= xmin) & (lat <= xmax) & (wrapped >= ymin) & (wrapped <= ymax))
            field[use] = spline.ev(lat[use], wrapped[use])
        return field


def reconstruct(sampler, longitude, latitude, fix_latitude=False,
                invert_sample_shift=False, reverse_cr_seam=False, exact=False,
                omega0=13.2, reference=180.):
    rate = rotation_rate(latitude, fix_latitude)
    shifted = sample_longitudes(longitude, rate, invert_sample_shift, exact, omega0, reference)
    source, wrapped = select_sources(shifted, reverse_cr_seam)
    return sampler.sample(latitude, source, wrapped), shifted, source, wrapped


def run_variant(sampler, longitude, latitude, variant, **kwargs):
    if variant not in VARIANTS:
        raise ValueError(variant)
    return reconstruct(sampler, longitude, latitude, *(c == '1' for c in variant), **kwargs)


def score(model, reference, mask, weights=None):
    m, r = model[mask], reference[mask]
    if not len(m):
        return {'count': 0, 'bias_G': None, 'mae_G': None, 'rmse_G': None, 'pearson_r': None,
                'median_abs_G': None, 'p95_abs_G': None}
    if not np.isfinite(m).all() or not np.isfinite(r).all():
        raise ValueError('Nonfinite value in evaluation mask.')
    d = m-r
    return {'count': len(m), 'bias_G': float(np.mean(d)), 'mae_G': float(np.mean(abs(d))),
            'rmse_G': float(np.sqrt(np.mean(d*d))),
            'pearson_r': float(np.corrcoef(m, r)[0, 1]) if np.std(m)>0 and np.std(r)>0 else None,
            'median_abs_G': float(np.median(abs(d))), 'p95_abs_G': float(np.percentile(abs(d), 95))}


def area_weights(header):
    """Cell area / 4 pi R^2 from sine-latitude edges; clip tiny rounded poles."""
    ny, nx = int(header['NAXIS2']), int(header['NAXIS1'])
    edges = np.clip(header['CRVAL2'] + (np.arange(ny+1)+.5-header['CRPIX2'])*header['CDELT2'], -1, 1)
    row = np.abs(np.diff(edges)) * abs(header['CDELT1']) / 720.
    return np.broadcast_to(row[:, None], (ny, nx))


def original_source_run(maps):
    """Execute ONLY original omega and pre-SFT reconstruction AST nodes, verbatim.

    Supplies three arrays in place of the unavailable hard-coded MDI files.
    Coordinates, units, splines, strict seam tests and loop remain unchanged.
    """
    path = ROOT / 'ananya_research_work-main' / 'SFT' / 'SFT.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'omega')
             or 83 <= n.lineno <= 117]
    ns = {'np': np, 'RectBivariateSpline': RectBivariateSpline,
          'B_prev': maps[0], 'B_curr': maps[1], 'B_next': maps[2]}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns['B_day106']


def original_grid_vectorized(maps, omit_incomplete_rows=False):
    """Audit equivalent on original dimension-derived grid, radians and all.

    Row omission is an explicitly separate diagnostic; it is never the literal
    original reference. Returns its native result plus a physical-grid sampler.
    """
    ny, nx = maps[1].shape
    lon = np.linspace(0, 2*np.pi, nx)
    lat = np.arcsin(np.linspace(-1, 1, ny))
    rate = rotation_rate(np.rad2deg(lat), False)
    s = lon[None, :] + (np.deg2rad(rate)[:, None]/np.deg2rad(13.2))*(lon[None, :]-np.pi)
    src = np.where(s<0, 0, np.where(s>2*np.pi, 2, 1))
    wrap = np.where(s<0, s+2*np.pi, np.where(s>2*np.pi, s-2*np.pi, s))
    result = np.full((ny, nx), np.nan)
    for k, data in enumerate(maps):
        good = np.isfinite(data).all(axis=1) if omit_incomplete_rows else np.ones(ny, bool)
        spl = RectBivariateSpline(lat[good], lon, data[good])
        latgrid = np.broadcast_to(lat[:, None], result.shape)
        use = (src==k) & (latgrid>=lat[good].min()) & (latgrid<=lat[good].max())
        result[use] = spl.ev(latgrid[use], wrap[use])
    return result
