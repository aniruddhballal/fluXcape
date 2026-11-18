"""Paired full-grid V2/temporal-tile timings with bit-exact per-update checks."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

import numba
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'solvers'))
from optimised_laplace_v2 import jacobi_update
from optimised_laplace_v3 import temporal_update


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=60)
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--threads', type=int, nargs='+', default=[4])
    parser.add_argument('--tiles', type=int, nargs='+', default=[16, 24, 32, 48])
    parser.add_argument('--depths', type=int, nargs='+', default=[2, 4, 6])
    args = parser.parse_args()
    if min([args.steps, args.trials, *args.threads, *args.tiles, *args.depths]) < 1:
        parser.error('counts and sizes must be positive')
    initial = np.zeros((300, 300, 150))
    path = args.input_dir / 'Preprocessedmagneticfield/Bz.npy'
    initial[:, :, 0] = np.load(path)
    dx2, dy2, dz2 = (1471/299)**2, (799/299)**2, (1000/149)**2
    denom = 2/dx2 + 2/dy2 + 2/dz2
    numba.set_num_threads(2)
    small = np.zeros((4, 4, 4))
    jacobi_update(small, small.copy(), dx2, dy2, dz2, denom, np.empty(2, dtype=np.uint64))
    temporal_update(small, small.copy(), dx2, dy2, dz2, denom, np.empty((1, 2), dtype=np.uint64), 2, 4, 4)
    results = {'steps': args.steps, 'trials': args.trials, 'shape': list(initial.shape),
               'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'jit_included': False, 'records': []}
    for threads in args.threads:
        numba.set_num_threads(threads)
        for tile in args.tiles:
            for depth in args.depths:
                timings = {'v2': [], 'temporal': []}
                for trial in range(args.trials):
                    fields, histories = {}, {}
                    order = ['v2', 'temporal'] if trial % 2 == 0 else ['temporal', 'v2']
                    for name in order:
                        old, new = initial.copy(), initial.copy()
                        history = np.empty(args.steps, dtype=np.uint64)
                        ntiles = ((298+tile-1)//tile)**2
                        errors = np.empty((ntiles, depth), dtype=np.uint64) if name == 'temporal' else np.empty(298, dtype=np.uint64)
                        started = time.perf_counter()
                        if name == 'v2':
                            for step in range(args.steps):
                                jacobi_update(old, new, dx2, dy2, dz2, denom, errors)
                                old, new = new, old
                                history[step] = np.max(errors)
                        else:
                            for step in range(0, args.steps, depth):
                                width = min(depth, args.steps-step)
                                temporal_update(old, new, dx2, dy2, dz2, denom, errors, width, tile, tile)
                                old, new = new, old
                                history[step:step+width] = np.max(errors[:, :width], axis=0)
                        elapsed = time.perf_counter()-started
                        timings[name].append(elapsed)
                        fields[name], histories[name] = old, history
                        del new
                    if not (np.array_equal(fields['v2'].view(np.uint64), fields['temporal'].view(np.uint64))
                            and np.array_equal(histories['v2'], histories['temporal'])):
                        raise AssertionError(f'Non-exact tile={tile} depth={depth} threads={threads}')
                    print(f'threads={threads} tile={tile} depth={depth} trial={trial+1}: v2={timings["v2"][-1]:.6f}s tiled={timings["temporal"][-1]:.6f}s exact=True', flush=True)
                    del fields
                record = {'threads': threads, 'tile': tile, 'depth': depth, 'all_bit_exact': True,
                          'v2_seconds': timings['v2'], 'temporal_seconds': timings['temporal']}
                record['v2_median'] = statistics.median(timings['v2'])
                record['temporal_median'] = statistics.median(timings['temporal'])
                record['speedup'] = record['v2_median']/record['temporal_median']
                results['records'].append(record)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'Results: {args.output}', flush=True)


if __name__ == '__main__':
    main()
