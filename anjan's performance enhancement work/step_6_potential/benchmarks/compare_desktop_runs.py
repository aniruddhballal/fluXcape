"""Alternating full-step V3/V4 runs, verified against an existing original run."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def progress(run):
    with (run / 'convergence.csv').open() as stream:
        return [(int(row['iteration']), float(row['max_change'])) for row in csv.DictReader(stream)]


def verify(run, reference, baseline):
    data = json.loads((run / 'measurements.json').read_text())
    if data['status'] != 'completed' or not data['expected_outputs_present'] or len(data['outputs']) != 9:
        raise AssertionError('Full step 6 did not complete with nine outputs')
    if [(r['name'], r['sha256']) for r in data['copied_files']] != [(r['name'], r['sha256']) for r in baseline['copied_files']]:
        raise AssertionError('Copied scientific source or inputs differ from original baseline')
    comparisons = []
    for item in baseline['outputs']:
        path = run / item['name']
        if digest(path) != item['sha256'] or digest(reference / item['name']) != item['sha256']:
            raise AssertionError('Output hash differs: ' + item['name'])
        a = np.load(reference / item['name'], mmap_mode='r')
        b = np.load(path, mmap_mode='r')
        if a.shape != b.shape or a.dtype != b.dtype:
            raise AssertionError('Output shape/dtype differs')
        maximum = 0.0
        for start in range(0, a.size, 1_000_000):
            aa, bb = a.reshape(-1)[start:start+1_000_000], b.reshape(-1)[start:start+1_000_000]
            if not np.isfinite(bb).all() or not np.array_equal(aa.view(np.uint64), bb.view(np.uint64)):
                raise AssertionError('Nonfinite or nonidentical output: ' + item['name'])
            maximum = max(maximum, float(np.max(np.abs(aa-bb))))
        comparisons.append({'name': item['name'], 'sha256': item['sha256'],
                            'bit_exact': True, 'maximum_absolute_difference': maximum})
    if progress(run) != progress(reference):
        raise AssertionError('Logged iteration/error values differ')
    return data, comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trials', type=int, default=3)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error('trials must be positive')
    reference = args.reference_run.resolve()
    baseline = json.loads((reference / 'measurements.json').read_text())
    result = {'reference_run': str(reference), 'input_directory': str(args.input_dir.resolve()),
              'workload': 'full step 6, nine arrays', 'jit_and_logging_included': True,
              'trials_per_implementation': args.trials, 'records': []}
    for trial in range(args.trials):
        order = [('optimised-v3', 4), ('optimised-v4', 16)]
        if trial % 2:
            order.reverse()
        for implementation, workers in order:
            command = [sys.executable, str(ROOT/'measure_potential.py'), '--input-dir',
                       str(args.input_dir.resolve()), '--implementation', implementation,
                       '--max-seconds', '0', '--label', f'ubuntu_{implementation}_paired_trial_{trial+1}']
            env = dict(os.environ, NUMBA_NUM_THREADS=str(workers))
            print(f'Starting {implementation}, trial {trial+1}, {workers} workers', flush=True)
            process = subprocess.run(command, env=env, capture_output=True, text=True)
            print(process.stdout, flush=True)
            if process.returncode:
                raise RuntimeError(process.stderr + process.stdout)
            run = Path(next(line.removeprefix('Outputs: ') for line in process.stdout.splitlines() if line.startswith('Outputs: ')))
            data, comparisons = verify(run, reference, baseline)
            record = {'implementation': implementation, 'trial': trial+1, 'workers': workers,
                      'run_id': run.name, 'command': command, 'wall_seconds': data['wall_seconds'],
                      'cpu_seconds': data['cpu_seconds'], 'peak_rss_bytes': data['peak_rss_bytes'],
                      'solver_runtime': data['solver_runtime'], 'output_comparisons': comparisons,
                      'logged_convergence_samples': len(progress(run)), 'convergence_exact': True}
            result['records'].append(record)
            result['summary'] = {}
            for variant in ('optimised-v3', 'optimised-v4'):
                records = [r for r in result['records'] if r['implementation'] == variant]
                if records:
                    result['summary'][variant] = {f'median_{key}': statistics.median(r[key] for r in records)
                                                 for key in ('wall_seconds', 'cpu_seconds', 'peak_rss_bytes')}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2))
            print(f'Verified all nine files and convergence: {run.name}, {data["wall_seconds"]:.3f}s', flush=True)
    print(json.dumps(result['summary'], indent=2), flush=True)


if __name__ == '__main__':
    main()
