"""Benchmark only FITS extraction/resampling; preserve original source and inputs."""
import argparse
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

ROOT = Path(__file__).resolve().parent
OBS = 'hmi.sharp_cea_720s.4698.20141022_000000_TAI'
ORIGINAL = ROOT.parent / OBS


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ORIGINAL / 'fitsdataextraction.py')
    parser.add_argument('--input-dir', type=Path, default=ORIGINAL)
    parser.add_argument('--label', default='original')
    parser.add_argument('--max-seconds', type=float, default=600,
                        help='Measured execution limit; 0 means unlimited (default: 600)')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.max_seconds < 0:
        parser.error('time limit must be nonnegative')
    packages = ['numpy', 'scipy', 'matplotlib', 'astropy']
    linux = sys.platform.startswith('linux') and Path('/usr/bin/time').is_file()
    if linux:
        linux = 'GNU' in subprocess.run(['/usr/bin/time', '--version'], capture_output=True, text=True).stdout
    if not linux:
        packages.append('psutil')
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    inputs = [args.input_dir / f'{OBS}.{component}.fits' for component in ('Bp', 'Bt', 'Br')]
    missing += [str(p) for p in [args.source, *inputs] if not p.is_file()]
    if missing:
        parser.exit(2, 'Missing prerequisites: ' + ', '.join(missing) + '\n'
                    'Use a Python environment with numpy scipy matplotlib astropy; '
                    'Windows/non-GNU platforms also need psutil.\n')
    if args.check_only:
        print('Step 2 prerequisites available; no extraction performed.')
        return 0
    stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    run = ROOT / 'runs' / stamp
    run.mkdir(parents=True)
    copied = []
    for item in [args.source, *inputs]:
        target = run / item.name
        shutil.copy2(item, target)
        copied.append({'name': item.name, 'bytes': target.stat().st_size, 'sha256': digest(target)})
    command = [sys.executable, '-u', '-B', str(run / args.source.name)]
    state = {'label': args.label, 'status': 'running', 'started': datetime.now().astimezone().isoformat(),
             'platform': platform.platform(), 'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
             'python': sys.version, 'versions': {p: importlib.metadata.version(p) for p in packages},
             'command': command, 'copied_files': copied, 'run_directory': str(run),
             'max_seconds': args.max_seconds, 'backend': 'GNU time' if linux else 'sampled psutil',
             'thread_environment': {k: os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS') if k in os.environ}}
    report = ROOT / f'extraction_{stamp}.md'
    metrics_path = run / 'time.txt'
    launch = ['/usr/bin/time', '-f', 'METRICS %U %S %M', '-o', str(metrics_path), *command] if linux else command
    proc = None
    start = time.perf_counter()
    print(f'Outputs: {run}\nTime limit: {args.max_seconds}s (0 = unlimited)', flush=True)
    try:
        with (run / 'extraction.log').open('wb') as log:
            proc = subprocess.Popen(launch, cwd=run, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=os.name != 'nt',
                                    env=dict(os.environ, MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1'))
            peak = 0
            seen = {}
            if not linux:
                import psutil
                root_process = psutil.Process(proc.pid)
            while proc.poll() is None:
                if args.max_seconds and time.perf_counter()-start >= args.max_seconds:
                    raise TimeoutError('Extraction time limit reached')
                if not linux:
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
                time.sleep(0.02)
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
        state['wall_seconds'] = time.perf_counter()-start
        outputs = sorted(run.glob('*.dat'))
        state['outputs'] = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in outputs]
        state['generated_data_bytes'] = sum(p.stat().st_size for p in outputs)
        state['expected_outputs_present'] = all((run / name).is_file() for axis in 'xyz'
            for name in (f'outputB{axis}.dat', f'interpolated_dataB{axis}.dat'))
        (run / 'measurements.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        report.write_text('# Step 2: FITS extraction/resampling\n\n'
            'One trial of the selected source; no preprocessing or Main.py execution. '
            'Originals are copied and hashed before timing; output hashing is outside timing. '
            'A timeout is a partial measurement, not completed runtime.\n\n'
            'GNU time RSS is the largest individual process peak, not simultaneous tree total. '
            'psutil RSS is sampled tree total (20 ms), can double-count shared pages and miss short peaks; '
            'its CPU counters may miss brief processes. A killed GNU time run may have no CPU/RAM result. '
            'Wall time includes launch/monitoring/termination overhead. No numerical equivalence is asserted. '
            'Output presence/hashes are provenance, not scientific validation.\n\n```json\n'
            + json.dumps(state, indent=2) + '\n```\n', encoding='utf-8')
        print(f'{state["status"]}: {report}', flush=True)
    return 0 if state['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
