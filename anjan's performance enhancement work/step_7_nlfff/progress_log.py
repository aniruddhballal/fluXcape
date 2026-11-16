"""Record WSR progress without changing original numerical statements."""
import ast
import csv
from datetime import datetime
from pathlib import Path
import time


class ProgressLog:
    def __init__(self, path='convergence.csv'):
        self.path = Path(path)
        self.started = time.perf_counter()
        self.previous = None
        self.initial_L = None
        self.attempts = self.rejected = 0
        with self.path.open('w', newline='', encoding='utf-8') as stream:
            csv.writer(stream).writerow([
                'timestamp', 'elapsed_seconds', 'event', 'attempts', 'accepted_steps',
                'rejected_attempts', 'L', 'L_normalised', 'trial_L', 'next_dt',
                'relaxation_time', 'interval_seconds', 'seconds_per_attempt'])

    def record(self, event, accepted_steps, L, next_dt, relaxation_time, trial_L=None):
        now = time.perf_counter()
        if event == 'initial':
            self.initial_L = float(L)
        if event in ('accepted', 'rejected'):
            self.attempts += 1
        if event == 'rejected':
            self.rejected += 1
        interval = now - self.previous if self.previous is not None else ''
        duration = interval if event in ('accepted', 'rejected') else ''
        normalised = float(L) / self.initial_L if self.initial_L else ''
        with self.path.open('a', newline='', encoding='utf-8') as stream:
            csv.writer(stream).writerow([
                datetime.now().astimezone().isoformat(), now - self.started,
                event, self.attempts, int(accepted_steps), self.rejected,
                float(L), normalised, '' if trial_L is None else float(trial_L),
                float(next_dt), float(relaxation_time), interval, duration])
        self.previous = now


def instrument_wsr(source):
    tree = ast.parse(source)
    original = ast.dump(tree)
    added = []

    def insert(body, index, code):
        nodes = ast.parse(code).body
        body[index:index] = nodes
        added.extend((body, node) for node in nodes)

    def assigns(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)

    initial = next(i for i, node in enumerate(tree.body) if assigns(node, 'step'))
    insert(tree.body, initial + 1,
           '_wsr_progress.record("initial", step, L_values[-1], current_dt, time[-1])')
    loops = [n for n in tree.body if isinstance(n, ast.While)
             and ast.dump(n.test) == ast.dump(ast.parse('step < num_steps', mode='eval').body)]
    if len(loops) != 1:
        raise ValueError('Expected the original WSR loop')
    decisions = [n for n in loops[0].body if isinstance(n, ast.If)
                 and ast.dump(n.test) == ast.dump(ast.parse('Lnew <= L_values[-1]', mode='eval').body)]
    if len(decisions) != 1:
        raise ValueError('Expected the original WSR acceptance condition')
    decision = decisions[0]
    for branch, op, event in ((decision.body, ast.Mult, 'accepted'),
                              (decision.orelse, ast.Div, 'rejected')):
        updates = [i for i, n in enumerate(branch) if isinstance(n, ast.AugAssign)
                   and isinstance(n.target, ast.Name) and n.target.id == 'current_dt'
                   and isinstance(n.op, op)]
        if len(updates) != 1:
            raise ValueError('Expected the original timestep update')
        insert(branch, updates[0] + 1,
               f'_wsr_progress.record("{event}", step, L_values[-1], current_dt, time[-1], Lnew)')
    insert(tree.body, len(tree.body),
           '_wsr_progress.record("finished", step, L_values[-1], current_dt, time[-1])')
    first = next(i for i, n in enumerate(tree.body) if not isinstance(n, (ast.Import, ast.ImportFrom)))
    insert(tree.body, first, 'from _wsr_progress import ProgressLog\n_wsr_progress = ProgressLog()')
    result = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
    for body, node in reversed(added):
        body.remove(node)
    if ast.dump(tree) != original:
        raise AssertionError('WSR instrumentation changed original statements')
    return result
