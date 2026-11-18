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
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'solvers'))
from support import progress_log
import measure_potential

SOURCE = ROOT.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI'
spec = importlib.util.spec_from_file_location('laplace', SOURCE / 'laplace.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
sys.modules['laplace'] = original
sys.modules['_step6_progress'] = progress_log
from optimised_laplace import solve_pfss_cartesian_vectorized as optimised
from optimised_laplace_v2 import solve_pfss_cartesian_vectorized as optimised_v2
from optimised_laplace_v3 import solve_pfss_cartesian_vectorized as optimised_v3, temporal_update


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
            for candidate in (optimised, optimised_v2, optimised_v3):
                actual = candidate(field, 1.7, 2.3, 0.8, **options)
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
        for solver in (optimised, optimised_v2, optimised_v3):
            with contextlib.redirect_stdout(io.StringIO()) as candidate_log:
                actual = solver(initial, 1.7, 2.3, 0.8, verbose=True)
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

    def test_v2_subnormals_and_fallbacks(self):
        field = np.random.default_rng(9).normal(size=(9, 8, 7)) * 1e-310
        self.compare(field, tol=0, max_iter=3)
        self.compare(field[::-1], tol=0, max_iter=3)
        self.compare(np.full((9, 8, 7), -0.0), tol=0, max_iter=3)
        narrow = field.astype(np.float32)
        with contextlib.redirect_stdout(io.StringIO()):
            expected = original.solve_pfss_cartesian_vectorized(narrow, 1.7, 2.3, 0.8, max_iter=2)
            actual = optimised_v2(narrow, 1.7, 2.3, 0.8, max_iter=2)
        self.assertEqual(actual.dtype, expected.dtype)
        self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_v2_worker_settings(self):
        field = np.zeros((5, 6, 7))
        with patch.dict(os.environ), contextlib.redirect_stdout(io.StringIO()):
            os.environ.pop('NUMBA_NUM_THREADS', None)
            optimised_v2(field, 1.7, 2.3, 0.8, max_iter=1)
            self.assertEqual(json.loads(Path('solver_runtime.json').read_text())['numba_threads'], 4)
            os.environ['NUMBA_NUM_THREADS'] = '1'
            set_num_threads(1)
            optimised_v2(field, 1.7, 2.3, 0.8, max_iter=1)
            self.assertEqual(json.loads(Path('solver_runtime.json').read_text())['numba_threads'], 1)

    def test_v3_tile_fields_and_each_update_error(self):
        from optimised_laplace_v2 import jacobi_update
        rng = np.random.default_rng(30)
        for shape in ((9, 8, 7), (12, 10, 8), (31, 29, 17)):
            for steps in (1, 2, 3, 4, 6):
                initial = rng.normal(size=shape)
                reference, spare = initial.copy(), initial.copy()
                reference_errors = []
                for _ in range(steps):
                    error = np.empty(shape[0]-2, dtype=np.uint64)
                    jacobi_update(reference, spare, 1.7**2, 2.3**2, 0.8**2, 4.5, error)
                    reference, spare = spare, reference
                    reference_errors.append(error.max())
                for bx, by in ((4, 3), (16, 16)):
                    candidate = initial.copy()
                    ntiles = ((shape[0]-2+bx-1)//bx) * ((shape[1]-2+by-1)//by)
                    errors = np.empty((ntiles, steps), dtype=np.uint64)
                    temporal_update(initial, candidate, 1.7**2, 2.3**2, 0.8**2, 4.5, errors, steps, bx, by)
                    np.testing.assert_array_equal(candidate.view(np.uint64), reference.view(np.uint64))
                    np.testing.assert_array_equal(errors.max(axis=0), reference_errors)

    def test_v3_replays_first_converged_state(self):
        initial = np.zeros((17, 15, 11))
        initial[:, :, 0] = np.random.default_rng(72).normal(size=(17, 15))
        states = [initial]
        with contextlib.redirect_stdout(io.StringIO()):
            for count in range(1, 4):
                states.append(original.solve_pfss_cartesian_vectorized(initial, 1.7, 2.3, 0.8, tol=0, max_iter=count))
            errors = [np.max(np.abs(states[i]-states[i-1])) for i in range(1, 4)]
            self.assertTrue(errors[1] > errors[2])
            tolerance = (errors[1]+errors[2])/2
            expected = original.solve_pfss_cartesian_vectorized(initial, 1.7, 2.3, 0.8, tol=tolerance)
            actual = optimised_v3(initial, 1.7, 2.3, 0.8, tol=tolerance)
        np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))
        runtime = json.loads(Path('solver_runtime.json').read_text())
        self.assertEqual(runtime['final_iteration'], 2)
        self.assertGreater(runtime['unused_speculative_updates'], 0)
        self.assertGreater(runtime['replayed_updates'], 0)
        self.assertEqual(runtime['final_max_change'], errors[2])

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
        (runner_root / 'support').mkdir()
        (runner_root / 'solvers').mkdir()
        shutil.copy2(ROOT / 'support/progress_log.py', runner_root / 'support/progress_log.py')
        for name in ('optimised_laplace.py', 'optimised_laplace_v2.py', 'optimised_laplace_v3.py'):
            shutil.copy2(ROOT / 'solvers' / name, runner_root / 'solvers' / name)
        results = []
        for implementation, first_only in [('original', True), ('optimised', True), ('original', False), ('optimised-v2', True), ('optimised-v3', True)]:
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
            if implementation in ('optimised-v2', 'optimised-v3'):
                self.assertEqual(state['solver_runtime']['numba_threads'], 2)
            self.assertEqual(len(state['outputs']), 3 if first_only else 9)
            results.append((run, state))
        self.assertEqual(results[0][1]['original_prefix_sha256'], results[1][1]['original_prefix_sha256'])
        for name in ('Bx_full', 'By_full', 'Bz_full'):
            paths = [run / 'PFSSmagneticfield/Bfield_full' / f'{name}.npy' for run, _ in results]
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            self.assertEqual(paths[0].read_bytes(), paths[2].read_bytes())
            self.assertEqual(paths[0].read_bytes(), paths[3].read_bytes())
            self.assertEqual(paths[0].read_bytes(), paths[4].read_bytes())
        # Source snapshot was never modified by dispatch.
        self.assertEqual((fixture / 'Main.py').read_text(encoding='utf-8'), source)


if __name__ == '__main__':
    unittest.main()
