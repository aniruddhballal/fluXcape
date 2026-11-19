"""Attempt caps preserve numerical updates and count rejected work as well."""
import contextlib
import csv
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

import progress_log
from progress_log import instrument_wsr

SOURCE = '''
num_steps = 100
dt = 0.0001
current_dt = dt
L_values = [1000.0]
time = [0.0]
step = 0
iteration = 0
while step < num_steps:
    iteration += 1
    Lnew = L_values[-1] - 1 if iteration % 2 else L_values[-1] + 1
    if Lnew <= L_values[-1]:
        L_values.append(Lnew)
        time.append(time[-1] + current_dt)
        step += 1
        current_dt *= 1.01
    else:
        current_dt /= 2
'''


class AttemptLimitTests(unittest.TestCase):
    def test_caps_count_accepted_and_rejected_updates(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                sys.modules['_wsr_progress'] = progress_log
                for limit in (1, 2, 10, 20):
                    namespace = {}
                    exec(instrument_wsr(SOURCE, max_attempts=limit), namespace)
                    with Path('convergence.csv').open(encoding='utf-8') as stream:
                        rows = list(csv.DictReader(stream))
                    attempts = [r for r in rows if r['event'] in ('accepted', 'rejected')]
                    self.assertEqual(len(attempts), limit)
                    self.assertEqual(namespace['iteration'], limit)
                    self.assertEqual(namespace['step'], (limit+1)//2)
                    self.assertEqual(int(rows[-1]['attempts']), limit)
                    self.assertEqual(int(rows[-1]['rejected_attempts']), limit//2)
                    expected_dt = 0.0001
                    for attempt in range(1, limit+1):
                        expected_dt = expected_dt*1.01 if attempt % 2 else expected_dt/2
                    self.assertEqual(namespace['current_dt'], expected_dt)
            finally:
                os.chdir(previous)

    def test_natural_stop_before_cap_matches_uncapped(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                sys.modules['_wsr_progress'] = progress_log
                original, bounded = {}, {}
                source = SOURCE.replace('num_steps = 100', 'num_steps = 3')
                exec(instrument_wsr(source), original)
                exec(instrument_wsr(source, max_attempts=20), bounded)
                for name in ('step', 'iteration', 'current_dt', 'L_values', 'time'):
                    self.assertEqual(original[name], bounded[name])
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
