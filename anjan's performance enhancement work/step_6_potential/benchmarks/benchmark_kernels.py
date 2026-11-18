"""Fixed-workload full-grid CPU experiments; not a convergence benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

import numba
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'solvers'))
import optimised_laplace as v1
import optimised_laplace_v2 as v2

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=60)
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--threads', type=int, nargs='+', default=[1, 2, 4, 6, 8, 12])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.steps < 1 or args.trials < 1 or min(args.threads) < 1:
        parser.error('steps, trials and thread counts must be positive')
    initial = np.zeros((300, 300, 150))
    input_path = args.input_dir / 'Preprocessedmagneticfield/Bz.npy'
    initial[:, :, 0] = np.load(input_path)
    dx2, dy2, dz2 = (1471/299)**2, (799/299)**2, (1000/149)**2
    denom = 2/dx2 + 2/dy2 + 2/dz2
    small = np.zeros((4, 4, 4))
    numba.set_num_threads(2)
    for kernel, dtype in ((v1.jacobi_update, np.float64), (v2.jacobi_update, np.uint64)):
        kernel(small, small.copy(), dx2, dy2, dz2, denom, np.empty(2, dtype=dtype))
    result = {'platform': platform.platform(), 'numba': numba.__version__,
              'numpy': np.__version__, 'shape': list(initial.shape), 'steps': args.steps,
              'trials': args.trials, 'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
              'jit_included': False, 'records': []}
    reference = reference_errors = None
    # Alternate implementation order to reduce consistent warm/thermal ordering bias.
    for count in args.threads:
        numba.set_num_threads(count)
        times = {'v1': [], 'v2': []}
        for trial in range(args.trials):
            variants = [('v1', v1, np.float64), ('v2', v2, np.uint64)]
            if trial % 2:
                variants.reverse()
            for name, module, dtype in variants:
                old, new = initial.copy(), initial.copy()
                errors = np.empty(initial.shape[0] - 2, dtype=dtype)
                history = np.empty(args.steps)
                started = time.perf_counter()
                for step in range(args.steps):
                    module.jacobi_update(old, new, dx2, dy2, dz2, denom, errors)
                    old, new = new, old
                    error = np.max(errors)
                    history[step] = error.view(np.float64) if dtype == np.uint64 else error
                elapsed = time.perf_counter() - started
                times[name].append(elapsed)
                if reference is None:
                    reference, reference_errors = old.copy(), history.copy()
                exact = (np.array_equal(old.view(np.uint64), reference.view(np.uint64))
                         and np.array_equal(history.view(np.uint64), reference_errors.view(np.uint64)))
                if not exact:
                    raise AssertionError(f'Kernel mismatch: {name}, {count} threads, trial {trial}')
                print(f'{name}: threads={count}, trial={trial+1}, seconds={elapsed:.6f}, bit_exact={exact}', flush=True)
                del old, new
        for name in times:
            result['records'].append({'implementation': name, 'threads': count,
                                      'wall_seconds': times[name],
                                      'median_seconds': statistics.median(times[name]),
                                      'all_bit_exact': True})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Results: {args.output}', flush=True)


if __name__ == '__main__':
    main()
