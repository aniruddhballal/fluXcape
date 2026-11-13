"""Measure C compilation only. Run: python measure_compile.py

GCC-compatible compiler required. Linux uses GNU time; Windows requires psutil.
No FITS inputs, preprocessing execution, downloads or installs are performed.
"""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'hmi.sharp_cea_720s.4698.20141022_000000_TAI' / 'preproc.c'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_process(command, log, interval):
    """Fallback: sampled simultaneous process-tree RSS and cumulative counters."""
    import psutil
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    root = psutil.Process(process.pid)
    peak = 0
    seen = {}
    while True:
        try:
            processes = [root] + root.children(recursive=True)
        except psutil.Error:
            processes = []
        rss = 0
        for member in processes:
            try:
                rss += member.memory_info().rss
                cpu = member.cpu_times()
                seen[(member.pid, member.create_time())] = cpu.user + cpu.system
            except psutil.Error:
                pass
        peak = max(peak, rss)
        if process.poll() is not None:
            break
        time.sleep(interval)
    return {'return_code': process.returncode, 'peak_rss_bytes': peak,
            'cpu_seconds': sum(seen.values()),
            'memory_method': 'sampled simultaneous process-tree RSS; shared pages may be counted twice',
            'cpu_method': 'sampled process counters; short-lived processes may be missed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', help='GCC-compatible compiler executable or path')
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--flags', default='-O3', help='Example: --flags="-O3 -fopenmp"')
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--label', default='baseline')
    parser.add_argument('--sample-seconds', type=float, default=0.01)
    args = parser.parse_args()
    if args.trials < 1 or args.sample_seconds <= 0:
        parser.error('trials and sampling interval must be positive')
    compiler = shutil.which(args.compiler) if args.compiler else (shutil.which('gcc') or shutil.which('clang'))
    if not compiler:
        parser.error('GCC-compatible compiler not found; use --compiler PATH')
    if not args.source.is_file():
        parser.error(f'Source not found: {args.source}')
    gnu_time = None
    if sys.platform.startswith('linux') and Path('/usr/bin/time').is_file():
        probe = subprocess.run(['/usr/bin/time', '--version'], capture_output=True, text=True)
        if 'GNU' in probe.stdout:
            gnu_time = '/usr/bin/time'
    if not gnu_time and importlib.util.find_spec('psutil') is None:
        parser.error('This platform needs psutil: python -m pip install psutil')
    version = subprocess.run([compiler, '--version'], capture_output=True, text=True, errors='replace')
    if version.returncode:
        parser.error('Cannot query compiler version')
    stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    run = ROOT / 'runs' / stamp
    run.mkdir(parents=True)
    copied_source = run / 'preproc.c'
    shutil.copy2(args.source, copied_source)
    report = ROOT / f'compile_{stamp}.md'
    state = {'label': args.label, 'started': datetime.now().astimezone().isoformat(),
             'status': 'running', 'platform': platform.platform(), 'machine': platform.machine(),
             'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
             'python': sys.version, 'compiler': compiler, 'compiler_version': version.stdout.strip(),
             'flags': shlex.split(args.flags), 'source': str(args.source.resolve()),
             'source_sha256': sha256(copied_source), 'source_bytes': copied_source.stat().st_size,
             'sampling_seconds': None if gnu_time else args.sample_seconds,
             'backend': 'GNU time' if gnu_time else 'psutil', 'run_directory': str(run), 'trials': []}

    def save():
        (run / 'measurements.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        lines = ['# Step 1: C compilation measurements', '', f'Label: {args.label}. Status: **{state["status"]}**.', '',
                 'Compilation only: the resulting preprocessor is not executed. Original source is unchanged.', '',
                 '| Trial | Wall seconds | CPU seconds | Peak RSS (MiB) | Executable bytes | Exit |',
                 '| --- | ---: | ---: | ---: | ---: | ---: |']
        for row in state['trials']:
            lines.append(f'| {row["trial"]} | {row["wall_seconds"]:.6f} | {row.get("cpu_seconds", 0):.4f} | '
                         f'{row.get("peak_rss_bytes", 0)/2**20:.3f} | {row.get("executable_bytes", 0)} | {row["return_code"]} |')
        lines += ['', 'GNU time reports the largest individual process RSS in the compilation tree, '
                  'not the simultaneous sum of compiler processes. Its CPU time includes waited-for children. '
                  'The psutil fallback samples simultaneous tree RSS and CPU counters, may count shared pages twice '
                  'and may miss brief processes/peaks. These backends are not interchangeable memory measurements.', '',
                  'Wall time includes launching the measurement wrapper and compilation; excludes copying, '
                  'hashing, compiler-version lookup and report writing. Repeated builds may benefit from OS cache; '
                  'these are consecutive trials, not controlled cold-cache runs. No GPU metrics are measured.', '',
                  'Commands, hashes, environment, summaries and log locations:', '', '```json',
                  json.dumps(state, indent=2), '```', '']
        report.write_text('\n'.join(lines), encoding='utf-8')

    try:
        for trial in range(1, args.trials + 1):
            binary = run / f'preproc_trial_{trial}{".exe" if os.name == "nt" else ""}'
            log_path = run / f'compile_trial_{trial}.log'
            command = [compiler, *state['flags'], str(copied_source), '-lm', '-o', str(binary)]
            started = time.perf_counter()
            with log_path.open('wb') as log:
                if gnu_time:
                    metrics = run / f'time_trial_{trial}.txt'
                    fmt = 'METRICS %U %S %M %x'
                    result = subprocess.run([gnu_time, '-f', fmt, '-o', str(metrics), *command],
                                            stdout=log, stderr=subprocess.STDOUT)
                    data = next(l for l in metrics.read_text().splitlines() if l.startswith('METRICS ')).split()
                    measured = {'return_code': result.returncode,
                                'cpu_seconds': float(data[1]) + float(data[2]),
                                'user_seconds': float(data[1]), 'system_seconds': float(data[2]),
                                'peak_rss_bytes': int(data[3]) * 1024,
                                'memory_method': 'GNU time: largest individual process RSS in compilation tree'}
                else:
                    measured = sample_process(command, log, args.sample_seconds)
            measured.update(trial=trial, command=command, wall_seconds=time.perf_counter()-started,
                            executable_bytes=binary.stat().st_size if binary.exists() else 0,
                            log=str(log_path))
            state['trials'].append(measured)
            save()
            print(f'Trial {trial}: {measured["wall_seconds"]:.3f}s, '
                  f'{measured["peak_rss_bytes"]/2**20:.2f} MiB peak RSS, exit {measured["return_code"]}', flush=True)
            if measured['return_code']:
                state['status'] = 'failed'
                break
        else:
            state['status'] = 'completed'
            rows = state['trials']
            state['summary'] = {'median_wall_seconds': statistics.median(r['wall_seconds'] for r in rows),
                                'min_wall_seconds': min(r['wall_seconds'] for r in rows),
                                'max_wall_seconds': max(r['wall_seconds'] for r in rows),
                                'maximum_peak_rss_bytes': max(r['peak_rss_bytes'] for r in rows),
                                'median_cpu_seconds': statistics.median(r['cpu_seconds'] for r in rows)}
    except (KeyboardInterrupt, Exception) as exc:
        state['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        state['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        state['original_source_unchanged'] = sha256(args.source) == state['source_sha256']
        save()
        print(f'Report: {report}')
    return 0 if state['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
