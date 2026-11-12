"""Measure the unchanged observation workflow in an isolated directory.

Run: python run_baseline.py --input-dir PATH_TO_SHARP_FITS
Dependencies: numpy scipy matplotlib astropy psutil; GCC-compatible C compiler.
Use --check-only for preflight. No downloads, installs, or source edits occur.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime


ROOT = Path(__file__).resolve().parent
OBS = 'hmi.sharp_cea_720s.4698.20141022_000000_TAI'


def inventory(path):
    files = [p for p in path.rglob('*') if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=ROOT / OBS)
    parser.add_argument('--compiler', help='GCC-compatible compiler executable (gcc/clang)')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--max-seconds', type=float, default=0,
                        help='Stop measured execution after this wall time; 0 means unlimited')
    parser.add_argument('--sample-seconds', type=float, default=1)
    args = parser.parse_args()
    if args.sample_seconds <= 0 or args.max_seconds < 0:
        parser.error('sample interval must be positive; time limit must be nonnegative')
    stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    report = ROOT / f'baseline_{stamp}.md'
    run = ROOT / f'baseline_run_{stamp}'
    source = ROOT / OBS
    inputs = [args.input_dir.resolve() / f'{OBS}.{c}.fits' for c in ('Bp', 'Bt', 'Br')]
    packages = ('numpy', 'scipy', 'matplotlib', 'astropy', 'psutil')
    missing = [f'Python package: {p}' for p in packages if importlib.util.find_spec(p) is None]
    missing += [f'Input: {p}' for p in inputs if not p.is_file()]
    compiler = shutil.which(args.compiler) if args.compiler else (shutil.which('gcc') or shutil.which('clang'))
    if not compiler:
        missing.append('GCC-compatible C compiler; supply --compiler PATH')
    required = ['fitsdataextraction.py', 'preproc.c', 'plot.py', 'weightfunction.py',
                'Main.py', 'laplace.py', 'vectormath.py']
    missing += [f'Source: {source / name}' for name in required if not (source / name).is_file()]
    state = {'status': 'preflight', 'started': datetime.now().astimezone().isoformat(),
             'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
             'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
             'versions': {p: importlib.metadata.version(p) for p in packages
                          if importlib.util.find_spec(p) is not None},
             'compiler': compiler, 'missing': missing, 'stages': [],
             'input_directory': str(args.input_dir.resolve()), 'run_directory': str(run),
             'sampling_seconds': args.sample_seconds, 'max_seconds': args.max_seconds,
             'environment': {k: v for k, v in os.environ.items()
                             if k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')},
             'initial_disk_free_bytes': shutil.disk_usage(ROOT).free}

    def save():
        report.write_text(
            '# Original workflow performance baseline\n\n'
            f'Status: **{state["status"]}**. Updated: {datetime.now().astimezone().isoformat()}\n\n'
            'Scope: FITS extraction → C preprocessing → boundary packaging → weights → '
            'initial potential field and WSR reconstruction. Optional downstream analyses are excluded.\n\n'
            'Original scientific source, grid (300 × 300 × 150), tolerances, maximum steps '
            '(2,000,001), and checkpoint interval (200) are unchanged. Matplotlib uses Agg '
            'to avoid blocking plot windows; interactive rendering is excluded. Python is unbuffered '
            'and bytecode writes are disabled. No scientific correctness fixes are applied.\n\n'
            'RAM means process-tree resident memory (RSS); shared pages may be counted twice. '
            'Private committed memory is also sampled when available. CPU percent uses 100% '
            'per logical core. CPU time and process I/O are sampled cumulative counters; very '
            'short processes and between-sample peaks can be missed. I/O counters are OS process '
            'counters, not physical device traffic. CSV contains host RAM/swap and free disk '
            'as context; other running tasks can influence them.\n\n'
            'Storage (SSD/HDD, sometimes called ROM) is reported as logical file bytes, '
            'not physical allocated blocks. Each stage records total run-directory bytes and '
            'growth, including logs. Final totals distinguish copied inputs/source from generated '
            'files. Monitoring, hashing, copying and disk scans add overhead. No GPU metrics '
            'are collected because this workflow uses CPU NumPy/SciPy.\n\n'
            'A time-limited, interrupted, failed or blocked run is not a completed full-workflow '
            'runtime. A successful Main.py exit may mean its existing small-dt termination '
            'triggered; inspect Main.log and checkpoints. Current settings can write approximately '
            '3.24 TB of checkpoint fields at the maximum step count.\n\n'
            'Machine-readable measurements and provenance:\n\n```json\n'
            + json.dumps(state, indent=2) + '\n```\n', encoding='utf-8')

    if missing or args.check_only:
        state['status'] = 'blocked: missing prerequisites' if missing else 'preflight passed (not executed)'
        save()
        print(report)
        for item in missing:
            print('Missing:', item)
        return 2 if missing else 0

    import psutil
    state['physical_cpus'] = psutil.cpu_count(logical=False)
    state['host_ram_bytes'] = psutil.virtual_memory().total
    run.mkdir()
    setup_start = time.perf_counter()
    copied = []
    for item in list(source.glob('*.py')) + [source / 'preproc.c'] + inputs:
        target = run / item.name
        shutil.copy2(item, target)
        copied.append({'name': item.name, 'bytes': target.stat().st_size, 'sha256': digest(target)})
    state['copied_files'] = copied
    state['setup_copy_hash_seconds'] = time.perf_counter() - setup_start
    state['compiler_version'] = subprocess.run([compiler, '--version'], capture_output=True,
                                                text=True, errors='replace').stdout
    binary = run / ('preproc.exe' if os.name == 'nt' else 'preproc')
    stages = [('compile', [compiler, '-O3', 'preproc.c', '-lm', '-o', str(binary)]),
              ('extract', [sys.executable, '-u', '-B', 'fitsdataextraction.py']),
              ('preprocess', [str(binary)]),
              ('package_boundary', [sys.executable, '-u', '-B', 'plot.py']),
              ('weights', [sys.executable, '-u', '-B', 'weightfunction.py']),
              ('Main', [sys.executable, '-u', '-B', 'Main.py'])]
    env = dict(os.environ, MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    started = time.perf_counter()
    active = None
    state['status'] = 'running'
    save()
    print(f'Report: {report}\nOutputs: {run}', flush=True)
    try:
        with (run / 'metrics.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['elapsed_s', 'stage', 'rss_bytes', 'private_bytes', 'cpu_seconds',
                             'cpu_percent_one_core', 'read_bytes', 'write_bytes',
                             'host_available_ram_bytes', 'host_swap_used_bytes', 'disk_free_bytes'])
            for name, command in stages:
                before_count, before_bytes = inventory(run)
                row = {'name': name, 'command': command, 'peak_sampled_rss_bytes': 0,
                       'peak_sampled_private_bytes': 0, 'cpu_seconds': 0,
                       'read_bytes': 0, 'write_bytes': 0}
                state['stages'].append(row)
                tick = time.perf_counter()
                seen = {}
                print(f'Running {name}...', flush=True)
                with (run / f'{name}.log').open('wb') as log:
                    active = subprocess.Popen(command, cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT)
                    root_process = psutil.Process(active.pid)
                    last_t, last_cpu = tick, 0
                    while True:
                        now = time.perf_counter()
                        processes = []
                        try:
                            processes = [root_process] + root_process.children(recursive=True)
                        except psutil.Error:
                            pass
                        rss = private = 0
                        for proc in processes:
                            try:
                                mem = proc.memory_info()
                                cpu = proc.cpu_times()
                                io = proc.io_counters()
                                rss += mem.rss
                                private += getattr(mem, 'private', 0)
                                seen[(proc.pid, proc.create_time())] = (cpu.user + cpu.system,
                                                                       io.read_bytes, io.write_bytes)
                            except psutil.Error:
                                continue
                        totals = [sum(v[i] for v in seen.values()) for i in range(3)]
                        writer.writerow([now-started, name, rss, private, totals[0],
                                         100*(totals[0]-last_cpu)/max(now-last_t, 1e-9),
                                         totals[1], totals[2], psutil.virtual_memory().available,
                                         psutil.swap_memory().used, shutil.disk_usage(run).free])
                        stream.flush()
                        last_t, last_cpu = now, totals[0]
                        row['peak_sampled_rss_bytes'] = max(row['peak_sampled_rss_bytes'], rss)
                        row['peak_sampled_private_bytes'] = max(row['peak_sampled_private_bytes'], private)
                        row.update(cpu_seconds=totals[0], read_bytes=totals[1], write_bytes=totals[2],
                                   elapsed_seconds=now-tick)
                        save()
                        if active.poll() is not None:
                            break
                        if args.max_seconds and now-started >= args.max_seconds:
                            raise TimeoutError('Configured total execution time limit reached')
                        time.sleep(args.sample_seconds)
                    row['return_code'] = active.returncode
                active = None
                count, size = inventory(run)
                row.update(elapsed_seconds=time.perf_counter()-tick, files_after=count,
                           disk_bytes_after=size, disk_growth_bytes=size-before_bytes)
                save()
                if row['return_code']:
                    raise RuntimeError(f'{name} failed; see {name}.log')
        state['status'] = 'completed'
    except (KeyboardInterrupt, Exception) as exc:
        state['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'stopped or failed'
        state['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if active is not None and active.poll() is None:
            try:
                parent = psutil.Process(active.pid)
                children = parent.children(recursive=True)
                for proc in children + [parent]:
                    try:
                        proc.terminate()
                    except psutil.Error:
                        pass
                _, alive = psutil.wait_procs(children + [parent], timeout=3)
                for proc in alive:
                    try:
                        proc.kill()
                    except psutil.Error:
                        pass
                active.wait()
            except psutil.Error:
                pass
        state['total_execution_wall_seconds'] = time.perf_counter()-started
        count, size = inventory(run)
        state['final_file_count'] = count
        state['final_run_bytes'] = size
        state['copied_input_source_bytes'] = sum(item['bytes'] for item in copied)
        state['generated_bytes_including_logs_metrics_binary'] = size-state['copied_input_source_bytes']
        state['final_disk_free_bytes'] = shutil.disk_usage(run).free
        save()
        print(f'{state["status"]}: {report}', flush=True)
    return 0 if state['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
