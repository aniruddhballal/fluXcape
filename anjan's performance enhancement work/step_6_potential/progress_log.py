"""Timestamped solver progress; instrumentation changes logging only."""
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
        with self.path.open('w', newline='', encoding='utf-8') as stream:
            csv.writer(stream).writerow([
                'timestamp', 'solver_elapsed_seconds', 'iteration', 'max_change',
                'interval_seconds', 'iterations_since_previous', 'mean_seconds_per_iteration'])

    def record(self, iteration, error):
        now = time.perf_counter()
        interval = count = mean = ''
        if self.previous is not None:
            previous_time, previous_iteration = self.previous
            interval = now - previous_time
            count = iteration - previous_iteration
            mean = interval / count if count else ''
        with self.path.open('a', newline='', encoding='utf-8') as stream:
            csv.writer(stream).writerow([
                datetime.now().astimezone().isoformat(), now - self.started,
                iteration, float(error), interval, count, mean])
        self.previous = now, iteration


def instrument_solver(source):
    """Add a CSV record at the existing progress print; leave arithmetic intact."""
    tree = ast.parse(source)
    original = ast.dump(tree)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'solve_pfss_cartesian_vectorized']
    if len(functions) != 1:
        raise ValueError('Expected one solve_pfss_cartesian_vectorized function')
    function = functions[0]
    matches = []
    for node in ast.walk(function):
        if not isinstance(node, ast.If):
            continue
        if ast.dump(node.test) == ast.dump(ast.parse('verbose and step % 50 == 0', mode='eval').body):
            matches.append(node)
    if len(matches) != 1:
        raise ValueError('Expected the original every-50-iterations progress branch')
    progress = matches[0]
    added = ast.parse('from _step6_progress import ProgressLog\n_step6_progress_writer = ProgressLog()').body
    index = 1 if (function.body and isinstance(function.body[0], ast.Expr)
                  and isinstance(function.body[0].value, ast.Constant)
                  and isinstance(function.body[0].value.value, str)) else 0
    function.body[index:index] = added
    record = ast.parse('_step6_progress_writer.record(step, error)').body[0]
    progress.body.append(record)
    instrumented = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
    # Verify all original statements, equations and stopping rules are unchanged.
    progress.body.pop()
    del function.body[index:index+len(added)]
    if ast.dump(tree) != original:
        raise AssertionError('Logging instrumentation changed the original AST')
    return instrumented
