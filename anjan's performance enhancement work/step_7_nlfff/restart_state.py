"""Validate preserved WSR state and generate a continuation using original equations."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time


def read_checkpoint(path, verify=True):
    import numpy as np
    path = Path(path).resolve()
    if path.name == 'state.json':
        path = path.parent
    state = json.loads((path / 'state.json').read_text())
    if state.get('schema') != 1:
        raise ValueError('Unsupported restart schema')
    if state['step'] >= state['num_steps']:
        raise ValueError('This checkpoint already reached the original accepted-step budget')
    if sys.version_info[:2] != tuple(map(int, state['python'].split()[0].split('.')[:2])):
        raise ValueError('Use the same Python major/minor version as the preserved run')
    for package, version in state['versions'].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f'Use the recorded {package} version: {version}')
    if verify:
        for item in state['files']:
            file = (path / item['path']).resolve()
            if not file.is_relative_to(path):
                raise ValueError('Restart file path escapes its package')
            if file.stat().st_size != item['bytes']:
                raise ValueError(f'Incomplete restart file: {item["path"]}')
            h = hashlib.sha256()
            with file.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            if h.hexdigest() != item['sha256']:
                raise ValueError(f'Restart hash mismatch: {item["path"]}')
    with np.load(path / 'coordinates.npz') as coords:
        shape = tuple(len(coords[k]) for k in ('X1','Y1','Z1'))
    for folder in ('field','boundary_reference'):
        for axis in 'xyz':
            if np.load(path / folder / f'B{axis}.npy', mmap_mode='r').shape != shape:
                raise ValueError('Restart field shape mismatch')
    for name in ('divB.npy','weight_function/W.npy'):
        if np.load(path / name, mmap_mode='r').shape != shape:
            raise ValueError(f'Restart array shape mismatch: {name}')
    L = np.load(path / 'L_values.npy', mmap_mode='r')
    times = np.load(path / 'time.npy', mmap_mode='r')
    if len(L) != state['step']+1 or len(times) != len(L):
        raise ValueError('Restart history length mismatch')
    if float(L[-1]) != state['L'] or float(times[-1]) != state['relaxation_time']:
        raise ValueError('Restart scalar state disagrees with saved histories')
    return path, state


def load_runtime(path):
    import numpy as np
    started = time.perf_counter()
    path, state = read_checkpoint(path, verify=False)  # Parent verified the isolated copy.
    values = {}
    for name in ('Bx','By','Bz'):
        values[name] = np.load(path / 'field' / f'{name}.npy')
        values[name+'I'] = np.load(path / 'boundary_reference' / f'{name}.npy')
    with np.load(path / 'coordinates.npz') as coords:
        values.update({name:coords[name].copy() for name in ('X1','Y1','Z1')})
    values.update(w=np.load(path / 'weight_function/W.npy'), divB=np.load(path / 'divB.npy'),
                  L_values=np.load(path / 'L_values.npy').tolist(), time=np.load(path / 'time.npy').tolist(),
                  step=state['step'], current_dt=state['current_dt'], dt=state['initial_dt'],
                  num_steps=state['num_steps'], save_interval=state['save_interval'])
    for size, coords, diff, spacing in (('Nx','X1','dx_arr','dx'),('Ny','Y1','dy_arr','dy'),('Nz','Z1','dz_arr','dz')):
        values[size]=len(values[coords]);values[diff]=np.diff(values[coords]);values[spacing]=values[diff][0]
    values['_resume_state'] = {**state, 'initial_L':values['L_values'][0],
                               '_session_started':started, '_progress_history':str(path / 'progress_to_checkpoint.csv')}
    return values


def resume_script(original):
    tree = ast.parse(original)
    indices = [i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=='step' for t in n.targets)]
    if len(indices) != 1:
        raise ValueError('Expected original step initialisation')
    start = indices[0]
    imports = [n for n in tree.body[:start] if isinstance(n,(ast.Import,ast.ImportFrom))]
    startup = ast.parse('from pathlib import Path as _RestartPath\n'
                        'from _restart_state import load_runtime as _load_restart\n'
                        'globals().update(_load_restart(_RestartPath("_restart")))\n'
                        'step = _resume_state["step"]').body
    # Retain the original initial checkpoint save, loop, and final save verbatim in AST.
    result = ast.Module(body=imports+startup+tree.body[start+1:],type_ignores=[])
    original_loop = next(n for n in tree.body if isinstance(n,ast.While))
    new_loop = next(n for n in result.body if isinstance(n,ast.While))
    if ast.dump(original_loop) != ast.dump(new_loop):
        raise AssertionError('Resume altered the reconstruction loop')
    return ast.unparse(ast.fix_missing_locations(result))+'\n'
