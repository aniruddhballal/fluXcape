"""Small restart equivalence tests; never run the real observation workflow."""
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
import preserve_restart
from restart_state import read_checkpoint

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI'


class ResumeTests(unittest.TestCase):
    def test_continuation_and_second_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tooling = root / 'tooling'
            tooling.mkdir()
            for name in ('progress_log.py','restart_state.py','preserve_restart.py'):
                shutil.copy2(HERE / name, tooling / name)
            source = root / 'source'
            source.mkdir()
            code = (SOURCE / 'Main.py').read_text().replace('Nx = 300','Nx = 4').replace('Ny = 300','Ny = 4').replace('Nz = 150','Nz = 4').replace('num_steps = 2000001','num_steps = 4').replace('save_interval =200','save_interval =1')
            (source / 'Main.py').write_text(code)
            for name in ('laplace.py','vectormath.py'):
                shutil.copy2(SOURCE / name, source / name)
            inputs, weights = root / 'fields', root / 'weights'
            rng = np.random.default_rng(42)
            for axis in 'xyz':
                values = rng.uniform(1,2,size=(4,4,4))
                for name, array in ((f'PFSSmagneticfield_for_uniform_grid/Bfield_full/B{axis}_full.npy',values),
                                    (f'Preprocessedmagneticfield_interpolated/B{axis}.npy',values[:,:,0])):
                    path = inputs / name
                    path.parent.mkdir(parents=True,exist_ok=True)
                    np.save(path,array)
            (weights / 'weight_function').mkdir(parents=True)
            np.save(weights / 'weight_function/W.npy',np.ones((4,4,4)))
            def run(args, expected=0):
                before = set((tooling / 'runs').glob('*'))
                with patch.object(runner,'ROOT',tooling), patch.object(sys,'argv',['measure',*args]), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.main(),expected)
                return (set((tooling / 'runs').glob('*')) - before).pop()
            original = run(['--source-dir',str(source),'--input-dir',str(inputs),'--weights-dir',str(weights)])
            self.assertEqual(json.loads((original/'restart_checkpoints/latest.json').read_text())['step'],4)
            self.assertEqual(json.loads((original/'measurements.json').read_text())['restart_preservation_return_code'],0)
            reference = original / 'Optimizedmagneticfield/step_4'
            for step in (3,4):
                (original / f'Optimizedmagneticfield/step_{step}').rename(original / f'hidden_{step}')
            with contextlib.redirect_stdout(io.StringIO()):
                bundle = preserve_restart.save_latest(original)
            _, state = read_checkpoint(bundle)
            self.assertEqual(state['step'],2)
            resumed = run(['--resume',str(bundle)])
            final = resumed / 'Optimizedmagneticfield/step_4'
            for name in ('Bx.npy','By.npy','Bz.npy','L_values.npy'):
                self.assertTrue(np.array_equal(np.load(final/name),np.load(original/'hidden_4'/name)),name)
            with (original / 'convergence.csv').open() as f:
                before = list(csv.DictReader(f))
            with (resumed / 'convergence.csv').open() as f:
                after = list(csv.DictReader(f))
            self.assertEqual([r['accepted_steps'] for r in after if r['event']=='accepted'],['1','2','3','4'])
            self.assertEqual(after[-1]['attempts'],before[-1]['attempts'])
            self.assertEqual(after[-1]['next_dt'],before[-1]['next_dt'])
            self.assertEqual(after[-1]['relaxation_time'],before[-1]['relaxation_time'])
            self.assertEqual(after[-1]['L_normalised'],before[-1]['L_normalised'])
            self.assertEqual(next(r['accepted_steps'] for r in after if r['event']=='resumed'),'2')
            self.assertEqual(json.loads((resumed/'measurements.json').read_text())['start_accepted_step'],2)
            # A resumed run can itself be preserved and resumed again.
            (resumed/'Optimizedmagneticfield/step_4').rename(resumed/'hidden_4')
            with contextlib.redirect_stdout(io.StringIO()):
                second_bundle = preserve_restart.save_latest(resumed)
            self.assertEqual(json.loads((second_bundle/'state.json').read_text())['step'],3)
            second = run(['--resume',str(second_bundle)])
            for name in ('Bx.npy','By.npy','Bz.npy','L_values.npy'):
                self.assertTrue(np.array_equal(np.load(second/'Optimizedmagneticfield/step_4'/name),np.load(original/'hidden_4'/name)),name)
            # Damaged state must be rejected before launch.
            with (second_bundle/'divB.npy').open('ab') as f:
                f.write(b'corrupt')
            with self.assertRaises(ValueError):
                read_checkpoint(second_bundle)
            # A time-capped worker must still finish preservation before the runner returns.
            (source / 'Main.py').write_text(code.replace('num_steps = 4', 'num_steps = 100000'))
            limited = run(['--source-dir',str(source),'--input-dir',str(inputs),
                           '--weights-dir',str(weights),'--max-seconds','3'], expected=1)
            measurement = json.loads((limited/'measurements.json').read_text())
            self.assertIn('TimeoutError',measurement['error'])
            self.assertEqual(measurement['restart_preservation_return_code'],0)
            latest = json.loads((limited/'restart_checkpoints/latest.json').read_text())
            _, restored = read_checkpoint(limited/'restart_checkpoints'/latest['checkpoint'])
            self.assertEqual(restored['step'],latest['step'])


if __name__ == '__main__':
    unittest.main()
