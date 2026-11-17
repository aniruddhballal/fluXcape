"""Measure only WSR / NLFFF reconstruction (step 7), using saved fields and weights."""
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
from progress_log import instrument_wsr
from restart_state import read_checkpoint, resume_script

ROOT = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_wsr(text):
    """Preserve the original WSR suffix and import statements; exclude the solve."""
    tree = ast.parse(text)
    def assigns(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    boundary = next(i for i, node in enumerate(tree.body) if assigns(node, 'BxC'))
    start = max(i for i, node in enumerate(tree.body[:boundary]) if assigns(node, 'Nx'))
    lines = text.splitlines(keepends=True)
    imports = [node for node in tree.body[:start] if isinstance(node, (ast.Import, ast.ImportFrom))]
    script = ''.join(''.join(lines[n.lineno-1:n.end_lineno]) for n in imports) + '\n' + ''.join(lines[tree.body[start].lineno-1:])
    expected = ast.Module(body=imports + tree.body[start:], type_ignores=[])
    if ast.dump(ast.parse(script)) != ast.dump(expected):
        raise ValueError('Step 7 extraction changed the original statements')
    if not any(isinstance(node, ast.While) for node in ast.walk(ast.parse(script))):
        raise ValueError('Expected the WSR reconstruction loop')
    return script, tree.body[start].lineno


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=ROOT.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI')
    parser.add_argument('--input-dir', type=Path, help='Completed step 6 run directory')
    parser.add_argument('--weights-dir', type=Path, help='Step 5 run directory containing weight_function/W.npy')
    parser.add_argument('--resume', type=Path, help='Preserved restart package directory or state.json')
    parser.add_argument('--label', default='original')
    parser.add_argument('--max-seconds', type=float, default=600,
                        help='Measured execution limit; 0 means unlimited (default: 600)')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.max_seconds < 0:
        parser.error('time limit must be nonnegative')
    if args.resume and (args.input_dir or args.weights_dir):
        parser.error('--resume uses its package; omit --input-dir and --weights-dir')
    if not args.resume and (not args.input_dir or not args.weights_dir):
        parser.error('Fresh runs need --input-dir and --weights-dir; otherwise use --resume')
    packages = ['numpy', 'scipy', 'matplotlib', 'psutil']
    linux = sys.platform.startswith('linux') and Path('/usr/bin/time').is_file()
    if linux:
        linux = 'GNU' in subprocess.run(['/usr/bin/time', '--version'], capture_output=True, text=True).stdout
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    restart = restart_info = None
    if args.resume:
        if missing:
            parser.error('Missing packages: '+', '.join(missing))
        try:
            restart, restart_info = read_checkpoint(args.resume)
        except (OSError, ValueError, KeyError) as exc:
            parser.error(str(exc))
        sources = [restart / 'source' / name for name in ('Main.py','laplace.py','vectormath.py')]
        inputs = [(p, Path('_restart') / p.relative_to(restart)) for p in sorted(restart.rglob('*')) if p.is_file()]
    else:
        sources = [args.source_dir / name for name in ('Main.py','laplace.py','vectormath.py')]
        field_names = [f'PFSSmagneticfield_for_uniform_grid/Bfield_full/B{axis}_full.npy' for axis in 'xyz']
        boundary_names = [f'Preprocessedmagneticfield_interpolated/B{axis}.npy' for axis in 'xyz']
        inputs = [(args.input_dir / name, Path(name)) for name in field_names + boundary_names]
        inputs.append((args.weights_dir / 'weight_function/W.npy', Path('weight_function/W.npy')))
    missing += [str(p) for p in [*sources, *(p for p, _ in inputs)] if not p.is_file()]
    if missing:
        parser.exit(2, 'Missing prerequisites: ' + ', '.join(missing) + '\n'
                    'Windows/non-GNU platforms also need psutil.\n')
    if args.check_only:
        print(f'Step 7 prerequisites available; resume step: {restart_info["step"] if restart_info else 0}. Reconstruction not started.')
        return 0
    stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    run = ROOT / 'runs' / stamp
    run.mkdir(parents=True)
    copied = []
    for item, relative in [(p, Path(p.name)) for p in sources] + inputs:
        target = run / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied.append({'name': str(relative), 'bytes': target.stat().st_size, 'sha256': digest(target)})
    script, first_line = extract_wsr((run / 'Main.py').read_text())
    stage_script = run / '_step7.py'
    (run / '_step7_original.py').write_text(script)
    if restart:
        read_checkpoint(run / '_restart')  # Verify the isolated copy before launching.
        script = resume_script(script)
        shutil.copy2(ROOT / 'restart_state.py', run / '_restart_state.py')
    stage_script.write_text(instrument_wsr(script, resume=bool(restart)), encoding='utf-8')
    shutil.copy2(ROOT / 'progress_log.py', run / '_wsr_progress.py')
    command = [sys.executable, '-u', '-B', str(stage_script)]
    state = {'label': args.label, 'status': 'running', 'started': datetime.now().astimezone().isoformat(),
             'platform': platform.platform(), 'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
             'python': sys.version, 'versions': {p: importlib.metadata.version(p) for p in packages},
             'command': command, 'copied_files': copied, 'run_directory': str(run),
             'max_seconds': args.max_seconds, 'main_start_line': first_line,
             'resumed_from': str(restart) if restart else None,
             'start_accepted_step': restart_info['step'] if restart_info else 0,
             'progress_elapsed_offset_seconds': restart_info['source_elapsed_seconds'] if restart_info else 0,
             'original_wsr_sha256': digest(run / '_step7_original.py'),
             'executed_wsr_sha256': digest(stage_script),
             'progress_helper_sha256': digest(run / '_wsr_progress.py'),
             'progress_csv': str(run / 'convergence.csv'), 'backend': 'GNU time' if linux else 'sampled psutil',
             'thread_environment': {k: os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS') if k in os.environ}}
    report = ROOT / f'nlfff_{stamp}.md'
    metrics_path = run / 'time.txt'
    launch = ['/usr/bin/time', '-f', 'METRICS %U %S %M', '-o', str(metrics_path), *command] if linux else command
    proc = None
    peak = 0
    seen = {}
    start = time.perf_counter()
    if restart_info:
        print(f'Resuming accepted step {restart_info["step"]}; original total budget {restart_info["num_steps"]}.', flush=True)
    print(f'Outputs: {run}\nTime limit: {args.max_seconds}s (0 = unlimited)', flush=True)
    try:
        with (run / 'nlfff.log').open('wb') as log:
            proc = subprocess.Popen(launch, cwd=run, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=os.name != 'nt',
                                    env=dict(os.environ, MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1'))
            peak = 0
            seen = {}
            import psutil
            root_process = psutil.Process(proc.pid)
            while proc.poll() is None:
                if args.max_seconds and time.perf_counter()-start >= args.max_seconds:
                    raise TimeoutError('Step 7 time limit reached')
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
        outputs = sorted(p for p in (run / 'Optimizedmagneticfield').rglob('*') if p.is_file())
        final_step_dirs = [p for p in (run / 'Optimizedmagneticfield').glob('step_*') if p.is_dir() and p.name[5:].isdigit()]
        state['highest_saved_step'] = max((int(p.name[5:]) for p in final_step_dirs), default=None)
        state['checkpoint_count'] = len(final_step_dirs)
        state['last_log_lines'] = (run / 'nlfff.log').read_text(errors='replace').splitlines()[-8:] if (run / 'nlfff.log').exists() else []
        state['outputs'] = [{'name': str(p.relative_to(run)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in outputs]
        state['generated_data_bytes'] = sum(p.stat().st_size for p in outputs)
        state['saved_checkpoint_files_present'] = bool(outputs)
        state['final_save_message_seen'] = any('Final step complete.' in line for line in state['last_log_lines'])
        (run / 'measurements.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        report.write_text('# Step 7: WSR / NLFFF reconstruction baseline\n\n'
            'Only the original Main.py reconstruction suffix and its imports execute. '
            'Uses saved step 6 fields/boundary and step 5 weights; no earlier stage runs. '
            'Original equations, grid, 2,000,001 accepted-step budget, timestep rules and '
            '200-step checkpoint interval are unchanged. The original small-dt stop remains in place. '
            'A successful process exit means the original code finished; it does not necessarily '
            'mean the full accepted-step budget was reached. Check nlfff.log.\n\n'
            'Copying and hashing are outside timing; runtime includes array loading, reconstruction, '
            'checkpoint I/O and figure generation with Agg (no interactive display). '
            'GNU time RSS is the largest individual process peak. Independently sampled '
            'tree RSS and CPU counters (100 ms) remain available on interruption; shared memory '
            'can be double-counted and short-lived activity missed. A timeout is partial, not '
            'completed runtime. Output size counts generated checkpoints/plots only. '
            'On timeout a last checkpoint may be incomplete; output existence is not a restart guarantee. '
            'Resume runs restore preserved state and retain the original loop and total accepted-step budget. '
            'Their wall/CPU measurements cover this invocation only; CSV elapsed time continues from '
            'the checkpoint offset and retains its prior history. The time limit restarts for this invocation. '
            'Logging-only instrumentation records full-precision L, accepted/rejected attempts, next dt, '
            'numerical relaxation time and elapsed wall time in convergence.csv. Its overhead is included; '
            'the original arithmetic, acceptance conditions and stopping rules are unchanged.\n\n```json\n'
            + json.dumps(state, indent=2) + '\n```\n', encoding='utf-8')
        print(f'{state["status"]}: {report}', flush=True)
    return 0 if state['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
