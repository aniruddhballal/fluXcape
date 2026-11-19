"""Original/candidate bit equivalence, including rejected attempts and checkpoints."""
import contextlib
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import measure_nlfff as runner

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI'


class MemoryOptimisationTests(unittest.TestCase):
    def test_real_suffix_fields_histories_acceptance_rejection_and_saves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, tooling, fields, weights = [root/name for name in ('source', 'tooling', 'fields', 'weights')]
            source.mkdir(); tooling.mkdir()
            for name in ('progress_log.py', 'memory_optimisation.py'):
                shutil.copy2(HERE/name, tooling/name)
            for name in ('laplace.py', 'vectormath.py'):
                shutil.copy2(SOURCE/name, source/name)
            rng = np.random.default_rng(91)
            for axis in 'xyz':
                value = rng.uniform(1, 2, size=(6, 6, 6))
                for name, array in ((f'PFSSmagneticfield_for_uniform_grid/Bfield_full/B{axis}_full.npy', value),
                                    (f'Preprocessedmagneticfield_interpolated/B{axis}.npy', value[:, :, 0])):
                    path = fields/name; path.parent.mkdir(parents=True, exist_ok=True); np.save(path, array)
            (weights/'weight_function').mkdir(parents=True)
            np.save(weights/'weight_function/W.npy', rng.uniform(.2, 1, size=(6, 6, 6)))
            outcomes = set()
            for dt in ('0.0001', '10000', '100000000'):
                code = (SOURCE/'Main.py').read_text(encoding='utf-8')
                code = code.replace('Nx = 300', 'Nx = 6').replace('Ny = 300', 'Ny = 6').replace('Nz = 150', 'Nz = 6')
                code = code.replace('dt = .0001', f'dt = {dt}').replace('num_steps = 2000001', 'num_steps = 8').replace('save_interval =200', 'save_interval =3')
                (source/'Main.py').write_text(code, encoding='utf-8')
                results = []
                for implementation in ('original', 'memory-v1'):
                    before = set((tooling/'runs').glob('*'))
                    args = ['measure', '--source-dir', str(source), '--input-dir', str(fields),
                            '--weights-dir', str(weights), '--max-attempts', '10', '--no-preserve-restart',
                            '--implementation', implementation]
                    with patch.object(runner, 'ROOT', tooling), patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(runner.main(), 0)
                    run = (set((tooling/'runs').glob('*'))-before).pop()
                    state = json.loads((run/'measurements.json').read_text())
                    self.assertEqual(state['restart_preservation'], 'disabled')
                    with (run/'convergence.csv').open(encoding='utf-8') as stream:
                        history = list(csv.DictReader(stream))
                    outcomes.update(r['event'] for r in history)
                    values = {str(p.relative_to(run)): p.read_bytes() for p in run.glob('Optimizedmagneticfield/**/*.npy')}
                    numerical = [{k: v for k, v in row.items() if k not in
                                  ('timestamp', 'elapsed_seconds', 'interval_seconds', 'seconds_per_attempt')} for row in history]
                    results.append((values, numerical))
                self.assertEqual(results[0], results[1])
            self.assertTrue({'accepted', 'rejected'}.issubset(outcomes))


if __name__ == '__main__':
    unittest.main()
