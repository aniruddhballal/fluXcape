"""Measure only the initial-field/preparation section of Main.py (step 6)."""
import argparse
import ast
from datetime import datetime
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time
from progress_log import instrument_solver

ROOT = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=ROOT.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI')
    parser.add_argument('--input-dir', type=Path, required=True, help='Step 4 run directory containing Preprocessedmagneticfield/')
    parser.add_argument('--label', default='original')
    parser.add_argument('--implementation', choices=('original', 'optimised'), default='original',
                        help='Solver implementation; original remains the default')
    parser.add_argument('--first-field-only', action='store_true',
                        help='Stop after the first three field files; exclude interpolation')
    parser.add_argument('--max-seconds', type=float, default=600,
                        help='Measured execution limit; 0 means unlimited (default: 600)')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.max_seconds < 0:
        parser.error('time limit must be nonnegative')
    packages = ['numpy', 'scipy', 'matplotlib', 'psutil']
    if args.implementation == 'optimised':
        packages.append('numba')
    linux = sys.platform.startswith('linux') and Path('/usr/bin/time').is_file()
    if linux:
        linux = 'GNU' in subprocess.run(['/usr/bin/time', '--version'], capture_output=True, text=True).stdout
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    sources = [args.source_dir / name for name in ('Main.py', 'laplace.py', 'vectormath.py')]
    inputs = [args.input_dir / 'Preprocessedmagneticfield' / f'B{axis}.npy' for axis in 'xyz']
    missing += [str(p) for p in [*sources, *inputs] if not p.is_file()]
    if missing:
        parser.exit(2, 'Missing prerequisites: ' + ', '.join(missing) + '\n'
                    'Windows/non-GNU platforms also need psutil.\n')
    if args.check_only:
        print('Step 6 prerequisites available; no calculation performed.')
        return 0
    stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    run = ROOT / 'runs' / stamp
    run.mkdir(parents=True)
    copied = []
    for item in [*sources, *inputs]:
        relative = Path('Preprocessedmagneticfield') / item.name if item in inputs else Path(item.name)
        target = run / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied.append({'name': str(relative), 'bytes': target.stat().st_size, 'sha256': digest(target)})
    text = (run / 'Main.py').read_text(encoding='utf-8')
    tree = ast.parse(text)
    def assigns(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    boundary = next(i for i, node in enumerate(tree.body) if assigns(node, 'BxC'))
    start_node = max(i for i, node in enumerate(tree.body[:boundary]) if assigns(node, 'Nx'))
    prefix = ''.join(text.splitlines(keepends=True)[:tree.body[start_node].lineno - 1])
    expected = tree.body[:start_node]
    assert ast.dump(ast.parse(prefix)) == ast.dump(ast.Module(body=expected, type_ignores=[]))
    assert not any(isinstance(n, ast.While) for n in ast.walk(ast.parse(prefix)))
    if args.first_field_only:
        # Stop after the exact first group's third save, retaining all prior code.
        saves = [node for node in ast.parse(prefix).body
                 if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Attribute)
                 and isinstance(node.value.func.value, ast.Name)
                 and node.value.func.value.id == 'np' and node.value.func.attr == 'save']
        if len(saves) != 9:
            raise ValueError('Expected nine original saves; review source boundaries')
        prefix = ''.join(prefix.splitlines(keepends=True)[:saves[2].end_lineno])
    original_prefix = prefix
    if args.implementation == 'optimised':
        shutil.copy2(ROOT / 'optimised_laplace.py', run / 'optimised_laplace.py')
        # Override only the active solver after imports. Original source is untouched.
        nodes = ast.parse(prefix).body
        setup = next(node for node in nodes if assigns(node, 'Nx'))
        lines = prefix.splitlines(keepends=True)
        lines.insert(setup.lineno - 1,
                     'from optimised_laplace import solve_pfss_cartesian_vectorized\n')
        prefix = ''.join(lines)
    stage_script = run / '_step6.py'
    stage_script.write_text(prefix, encoding='utf-8')
    # Instrument only the isolated solver copy; retain original provenance.
    shutil.copy2(run / 'laplace.py', run / 'laplace_original.py')
    (run / 'laplace.py').write_text(instrument_solver((run / 'laplace.py').read_text(encoding='utf-8')), encoding='utf-8')
    shutil.copy2(ROOT / 'progress_log.py', run / '_step6_progress.py')
    command = [sys.executable, '-u', '-B', str(stage_script)]
    state = {'label': args.label, 'status': 'running', 'started': datetime.now().astimezone().isoformat(),
             'implementation': args.implementation, 'first_field_only': args.first_field_only,
             'original_prefix_sha256': hashlib.sha256(original_prefix.encode()).hexdigest(),
             'optimised_solver_sha256': digest(run / 'optimised_laplace.py') if args.implementation == 'optimised' else None,
             'platform': platform.platform(), 'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
             'python': sys.version, 'versions': {p: importlib.metadata.version(p) for p in packages},
             'command': command, 'copied_files': copied, 'run_directory': str(run),
             'max_seconds': args.max_seconds, 'main_stop_before_line': len(original_prefix.splitlines()) + 1,
             'executed_prefix_sha256': digest(stage_script), 'backend': 'GNU time' if linux else 'sampled psutil',
             'progress_csv': str(run / 'convergence.csv'),
             'instrumented_solver_sha256': digest(run / 'laplace.py'),
             'progress_helper_sha256': digest(run / '_step6_progress.py'),
             'thread_environment': {k: os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS') if k in os.environ}}
    report = ROOT / f'potential_{stamp}.md'
    metrics_path = run / 'time.txt'
    launch = ['/usr/bin/time', '-f', 'METRICS %U %S %M', '-o', str(metrics_path), *command] if linux else command
    proc = None
    peak = 0
    seen = {}
    start = time.perf_counter()
    print(f'Outputs: {run}\nTime limit: {args.max_seconds}s (0 = unlimited)', flush=True)
    try:
        with (run / 'potential.log').open('wb') as log:
            proc = subprocess.Popen(launch, cwd=run, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=os.name != 'nt',
                                    env=dict(os.environ, MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1',
                                             PYTHONIOENCODING='utf-8'))
            peak = 0
            seen = {}
            import psutil
            root_process = psutil.Process(proc.pid)
            while proc.poll() is None:
                if args.max_seconds and time.perf_counter()-start >= args.max_seconds:
                    raise TimeoutError('Step 6 time limit reached')
                try:
                    members = [root_process] + root_process.children(recursive=True)
                except psutil.Error:
                    members = []
                rss = 0
                for member in members:
                    try:
                        rss += member.memory_info().rss
                        cpu = member.cpu_times()
                        seen[(member.pid, member.create_time())] = cpu.user + cpu.system
                    except psutil.Error:
                        pass
                peak = max(peak, rss)
                time.sleep(0.1)
            state['return_code'] = proc.returncode
            state['status'] = 'completed' if proc.returncode == 0 else 'failed'
            if linux and metrics_path.exists():
                row = next(line for line in metrics_path.read_text().splitlines() if line.startswith('METRICS ')).split()
                state.update(cpu_seconds=float(row[1])+float(row[2]), peak_rss_bytes=int(row[3])*1024)
            elif not linux:
                state.update(peak_rss_bytes=peak, cpu_seconds=sum(seen.values()))
    except (KeyboardInterrupt, Exception) as exc:
        state['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'partial or failed'
        state['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if proc is not None and proc.poll() is None:
            if os.name != 'nt':
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                import psutil
                try:
                    parent = psutil.Process(proc.pid)
                    for member in parent.children(recursive=True) + [parent]:
                        try:
                            member.kill()
                        except psutil.Error:
                            pass
                except psutil.Error:
                    pass
            proc.wait()
        state['peak_sampled_tree_rss_bytes'] = peak if proc is not None else 0
        state['sampled_cpu_seconds'] = sum(seen.values()) if proc is not None else 0
        state['wall_seconds'] = time.perf_counter()-start
        expected_outputs = [f'{folder}/{name}.npy' for folder, names in (
            ('PFSSmagneticfield/Bfield_full', ('Bx_full','By_full','Bz_full')),
            ('PFSSmagneticfield_for_uniform_grid/Bfield_full', ('Bx_full','By_full','Bz_full')),
            ('Preprocessedmagneticfield_interpolated', ('Bx','By','Bz'))) for name in names]
        if args.first_field_only:
            expected_outputs = expected_outputs[:3]
        outputs = [run / name for name in expected_outputs if (run / name).is_file()]
        state['outputs'] = [{'name': str(p.relative_to(run)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in outputs]
        state['generated_data_bytes'] = sum(p.stat().st_size for p in outputs)
        state['expected_outputs_present'] = len(outputs) == len(expected_outputs)
        (run / 'measurements.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        report.write_text('# Step 6: initial potential field measurement\n\n'
            f'Implementation: {args.implementation}. First field only: {args.first_field_only}. '
            'The selected Main.py prefix executes; original source is unchanged. '
            'Uses saved step 4 arrays; no prior stages, weights or WSR run. Original grid, tolerance '
            'and solver iteration limit are preserved. Copying/hashing are outside timing.\n\n'
            'A timeout is a partial measurement, not completed stage runtime. GNU time gives '
            'largest individual process RSS on successful runs. Independently sampled process-tree '
            'RSS and cumulative CPU counters (100 ms) are retained even on timeout; sampling may miss '
            'peaks or brief processes and double-count shared pages. Wall time includes launch, '
            'monitoring and termination. Agg disables GUI waiting. Output hashes record provenance. '
            'convergence.csv records timestamps, solver elapsed time, iteration and full-precision '
            'maximum change at labels 0, 50, 100, etc. Interval timing is a per-block average, '
            'not individual iteration timing. Only the isolated solver copy is instrumented; '
            'the original stopping rules are preserved. The optimised path uses a separate float64 '
            'parallel Jacobi kernel with fast-math disabled; gradients and scaling are unchanged. '
            'CSV logging and any JIT compilation overhead are included.\n\n```json\n'
            + json.dumps(state, indent=2) + '\n```\n', encoding='utf-8')
        print(f'{state["status"]}: {report}', flush=True)
    return 0 if state['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
