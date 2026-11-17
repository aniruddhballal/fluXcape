"""Package completed accepted-step checkpoints without touching a live solver."""
import argparse
import ast
import csv
from datetime import datetime
import hashlib
import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import platform
import shutil
import sys
import time


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
    temporary.replace(path)


def configuration(run):
    tree = ast.parse((run / '_step7_original.py').read_text())
    def assigns(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    boundary = next(i for i, n in enumerate(tree.body) if assigns(n, 'BxC'))
    grid = [n for n in tree.body[:boundary] if not isinstance(n, (ast.Import, ast.ImportFrom))]
    # This prefix only defines the reconstruction grid; never execute the loop.
    if not all(isinstance(n, ast.Assign) for n in grid):
        raise ValueError('Unexpected grid setup; refusing to execute arbitrary setup statements')
    import numpy as np
    scope = {'np': np}
    exec(compile(ast.Module(body=grid, type_ignores=[]), '<checkpoint grid>', 'exec'), scope)
    settings = {}
    for name in ('dt', 'num_steps', 'save_interval'):
        node = next(n for n in tree.body if assigns(n, name))
        settings[name] = ast.literal_eval(node.value)
    return scope, settings


def save_latest(run):
    import numpy as np
    grid, settings = configuration(run)
    destination = run / 'restart_checkpoints'
    destination.mkdir(exist_ok=True)
    text = (run / 'convergence.csv').read_text()
    text = text[:text.rfind('\n')+1]  # Ignore a currently incomplete CSV row.
    records = list(csv.DictReader(io.StringIO(text)))
    accepted = [r for r in records if r['event'] in ('initial', 'accepted')]
    by_step = {int(r['accepted_steps']): r for r in accepted}
    checkpoints = sorted((p for p in (run / 'Optimizedmagneticfield').glob('step_*')
                          if p.is_dir() and p.name[5:].isdigit()),
                         key=lambda p: int(p.name[5:]), reverse=True)
    last_error = None
    for checkpoint in checkpoints:
        step = int(checkpoint.name[5:])
        # Periodic checkpoints are reached immediately after an accepted step.
        if step % settings['save_interval'] or step not in by_step:
            continue
        final = destination / checkpoint.name
        if (final / 'state.json').is_file():
            return final
        staging = destination / (checkpoint.name + '.building')
        try:
            field = [np.load(checkpoint / f'B{axis}.npy', mmap_mode='r') for axis in 'xyz']
            shape = (grid['Nx'], grid['Ny'], grid['Nz'])
            if any(a.shape != shape for a in field):
                raise ValueError('Checkpoint field shapes do not match the recorded grid')
            history = np.load(checkpoint / 'L_values.npy')
            prior = [r for r in accepted if int(r['accepted_steps']) <= step]
            if len(prior) != step+1 or len(history) != step+1:
                raise ValueError('Checkpoint history/CSV is incomplete')
            if not np.array_equal(history, np.array([float(r['L']) for r in prior]), equal_nan=True):
                raise ValueError('Checkpoint objective history does not match CSV')
            if staging.exists():
                shutil.rmtree(staging)
            staging.mkdir()
            for subdir in ('field', 'boundary_reference', 'weight_function', 'source'):
                (staging / subdir).mkdir()
            reference_dir = run / '_restart/boundary_reference' if (run / '_restart/boundary_reference').is_dir() else run / 'Optimizedmagneticfield/step_0'
            for axis in 'xyz':
                shutil.copy2(checkpoint / f'B{axis}.npy', staging / 'field' / f'B{axis}.npy')
                shutil.copy2(reference_dir / f'B{axis}.npy',
                             staging / 'boundary_reference' / f'B{axis}.npy')
            shutil.copy2(checkpoint / 'L_values.npy', staging / 'L_values.npy')
            np.save(staging / 'time.npy', np.array([float(r['relaxation_time']) for r in prior]))
            weights = run / 'weight_function/W.npy'
            if not weights.is_file():
                weights = run / '_restart/weight_function/W.npy'
            shutil.copy2(weights, staging / 'weight_function/W.npy')
            for name in ('Main.py', 'laplace.py', 'vectormath.py', '_step7.py', '_step7_original.py', '_wsr_progress.py'):
                shutil.copy2(run / name, staging / 'source' / name)
            np.savez(staging / 'coordinates.npz', X1=grid['X1'], Y1=grid['Y1'], Z1=grid['Z1'])
            spec = importlib.util.spec_from_file_location('_restart_vector_math', staging / 'source/vectormath.py')
            helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            saved = [np.load(staging / 'field' / f'B{a}.npy', mmap_mode='r') for a in 'xyz']
            # At an accepted checkpoint divB is the divergence of that saved field.
            divergence = helper.compute_divergence_nonuniform(*saved, grid['X1'], grid['Y1'], grid['Z1'])
            np.save(staging / 'divB.npy', divergence)
            row = by_step[step]
            state = {'schema': 1, 'created': datetime.now().astimezone().isoformat(),
                     'source_run': str(run), 'checkpoint_step': step, 'step': step,
                     'current_dt': float(row['next_dt']), 'initial_dt': settings['dt'],
                     'num_steps': settings['num_steps'], 'save_interval': settings['save_interval'],
                     'attempts': int(row['attempts']), 'rejected_attempts': int(row['rejected_attempts']),
                     'relaxation_time': float(row['relaxation_time']), 'L': float(row['L']),
                     'checkpoint_timestamp': row['timestamp'],
                     'source_elapsed_seconds': float(row['elapsed_seconds']),
                     'python': sys.version, 'platform': platform.platform(),
                     'versions': {p: importlib.metadata.version(p) for p in ('numpy','scipy','matplotlib')},
                     'divB_origin': 'recomputed from a completed accepted-step field using the copied original helper',
                     'resume_boundary': 'after this accepted checkpoint, before the next trial; later attempts must be repeated'}
            with (staging / 'progress_to_checkpoint.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(r for r in records if int(r['attempts']) <= int(row['attempts']))
            state['files'] = [{'path': str(p.relative_to(staging)), 'bytes': p.stat().st_size, 'sha256': digest(p)}
                              for p in sorted(staging.rglob('*')) if p.is_file()]
            # Verify copied current/reference fields against their completed sources.
            for axis in 'xyz':
                if digest(staging / 'field' / f'B{axis}.npy') != digest(checkpoint / f'B{axis}.npy'):
                    raise ValueError('Checkpoint changed during copying; retry later')
                if digest(staging / 'boundary_reference' / f'B{axis}.npy') != digest(reference_dir / f'B{axis}.npy'):
                    raise ValueError('Initial boundary reference changed during copying')
            atomic_json(staging / 'state.json', state)
            staging.rename(final)
            atomic_json(destination / 'latest.json', {'checkpoint': final.name, 'step': step,
                                                     'state': str(final / 'state.json')})
            print(f'Preserved restart state: {final} (accepted step {step})', flush=True)
            return final
        except (OSError, ValueError, EOFError) as exc:
            last_error = str(exc)
            if staging.exists():
                shutil.rmtree(staging)
            continue
    raise ValueError('No complete periodic checkpoint available: ' + str(last_error))


def is_active(run):
    import psutil
    script = str(run / '_step7.py')
    for process in psutil.process_iter(['cmdline','status']):
        try:
            if process.info['status'] != psutil.STATUS_ZOMBIE and script in (process.info['cmdline'] or []):
                return True
        except psutil.Error:
            pass
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--watch', action='store_true', help='Keep capturing new periodic checkpoints until this run stops')
    parser.add_argument('--worker-pid', type=int, help='Runner-managed worker PID; avoids a startup race when watching')
    args = parser.parse_args()
    run = args.run_dir.resolve()
    while True:
        if args.watch and args.worker_pid:
            import psutil
            try:
                worker = psutil.Process(args.worker_pid)
                active = worker.is_running() and worker.status() != psutil.STATUS_ZOMBIE
            except psutil.Error:
                active = False
        else:
            active = is_active(run) if args.watch else False
        try:
            final = save_latest(run)
        except (OSError, ValueError) as exc:
            if not active:
                parser.exit(2, str(exc)+'\n')
            print('Waiting for a complete checkpoint: '+str(exc), flush=True)
        if not args.watch or not active:
            print('Preservation complete. Source solver was not modified or interrupted.', flush=True)
            return 0
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())
