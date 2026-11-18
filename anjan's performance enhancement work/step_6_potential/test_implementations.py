"""Equivalence and dispatch checks on small fixtures, not a full-data benchmark."""
import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from numba import set_num_threads
import progress_log
import measure_potential

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI'
spec = importlib.util.spec_from_file_location('laplace', SOURCE / 'laplace.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
sys.modules['laplace'] = original
sys.modules['_step6_progress'] = progress_log
from optimised_laplace import solve_pfss_cartesian_vectorized as optimised


class Implementations(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        set_num_threads(2)

    def tearDown(self):
        os.chdir(self.previous)
        self.temp.cleanup()

    def compare(self, field, **options):
        before = field.copy()
        with contextlib.redirect_stdout(io.StringIO()):
            expected = original.solve_pfss_cartesian_vectorized(field, 1.7, 2.3, 0.8, **options)
            actual = optimised(field, 1.7, 2.3, 0.8, **options)
        np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))
        np.testing.assert_array_equal(field.view(np.uint64), before.view(np.uint64))

    def test_exact_iterations_and_boundaries(self):
        rng = np.random.default_rng(42)
        for count in (0, 1, 2, 101):
            for initial in (rng.normal(size=(12, 10, 8)), np.zeros((12, 10, 8))):
                self.compare(initial, tol=0, max_iter=count, verbose=True)

    def test_convergence_and_progress(self):
        initial = np.zeros((12, 10, 8))
        initial[:, :, 0] = np.random.default_rng(12).normal(size=(12, 10))
        namespace = {}
        exec(progress_log.instrument_solver((SOURCE / 'laplace.py').read_text(encoding='utf-8')), namespace)
        with contextlib.redirect_stdout(io.StringIO()) as baseline_log:
            expected = namespace['solve_pfss_cartesian_vectorized'](initial, 1.7, 2.3, 0.8, verbose=True)
        with Path('convergence.csv').open(encoding='utf-8') as stream:
            baseline = list(csv.DictReader(stream))
        with contextlib.redirect_stdout(io.StringIO()) as candidate_log:
            actual = optimised(initial, 1.7, 2.3, 0.8, verbose=True)
        with Path('convergence.csv').open(encoding='utf-8') as stream:
            candidate = list(csv.DictReader(stream))
        np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))
        self.assertEqual([(r['iteration'], r['max_change']) for r in baseline],
                         [(r['iteration'], r['max_change']) for r in candidate])
        self.assertEqual(re.findall(r'Converged in (\d+)', baseline_log.getvalue()),
                         re.findall(r'Converged in (\d+)', candidate_log.getvalue()))

    def test_nonfinite_fallback(self):
        for value in (np.nan, np.inf, -np.inf):
            field = np.zeros((5, 6, 7))
            field[0, 0, 0] = value
            with np.errstate(invalid='ignore'):
                self.compare(field, tol=0, max_iter=3)

    def test_overflow_and_single_thread(self):
        field = np.full((5, 6, 7), 1e308)
        with np.errstate(over='ignore', invalid='ignore'):
            self.compare(field, tol=0, max_iter=3)
        set_num_threads(1)
        self.compare(np.random.default_rng(21).normal(size=(9, 8, 7)), tol=0, max_iter=17)

    def test_runner_dispatch_and_output_scope(self):
        fixture = Path('source').resolve()
        fixture.mkdir()
        source = (SOURCE / 'Main.py').read_text(encoding='utf-8')
        for name, size in [('Nx', 12), ('Ny', 10), ('Nz', 8), ('Nx_new', 12), ('Ny_new', 10)]:
            source = re.sub(rf'\b{name} = (300|150)', f'{name} = {size}', source)
        source = source.replace('max_iter=100000', 'max_iter=101')
        (fixture / 'Main.py').write_text(source, encoding='utf-8')
        for name in ('laplace.py', 'vectormath.py'):
            shutil.copy2(SOURCE / name, fixture / name)
        inputs = Path('inputs/Preprocessedmagneticfield').resolve()
        inputs.mkdir(parents=True)
        for axis in 'xyz':
            np.save(inputs / f'B{axis}.npy', np.random.default_rng(ord(axis)).normal(size=(12, 10)))
        runner_root = Path('runner').resolve()
        runner_root.mkdir()
        for name in ('progress_log.py', 'optimised_laplace.py'):
            shutil.copy2(ROOT / name, runner_root / name)
        results = []
        for implementation, first_only in [('original', True), ('optimised', True), ('original', False)]:
            argv = ['measure_potential.py', '--source-dir', str(fixture), '--input-dir', str(inputs.parent),
                    '--max-seconds', '120']
            if first_only:
                argv.extend(['--implementation', implementation])
            if first_only:
                argv.append('--first-field-only')
            with patch.object(measure_potential, 'ROOT', runner_root), patch.object(sys, 'argv', argv), \
                    patch.dict(os.environ, NUMBA_NUM_THREADS='2'):
                self.assertEqual(measure_potential.main(), 0)
            run = max((runner_root / 'runs').iterdir())
            state = json.loads((run / 'measurements.json').read_text())
            self.assertTrue(state['expected_outputs_present'])
            self.assertEqual(state['implementation'], implementation)
            self.assertEqual(len(state['outputs']), 3 if first_only else 9)
            results.append((run, state))
        self.assertEqual(results[0][1]['original_prefix_sha256'], results[1][1]['original_prefix_sha256'])
        for name in ('Bx_full', 'By_full', 'Bz_full'):
            paths = [run / 'PFSSmagneticfield/Bfield_full' / f'{name}.npy' for run, _ in results]
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            self.assertEqual(paths[0].read_bytes(), paths[2].read_bytes())
        # Source snapshot was never modified by dispatch.
        self.assertEqual((fixture / 'Main.py').read_text(encoding='utf-8'), source)


if __name__ == '__main__':
    unittest.main()
