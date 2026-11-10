"""Read-only repository census and preservation checks. Writes only below this folder."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
EXCLUDE = {'.git', '.venv', 'node_modules', 'pre_sft_audit', '__pycache__', 'dist'}


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def census():
    rows = []
    for parent, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE)
        for name in sorted(files):
            p = Path(parent) / name
            item = {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                    'sha256': sha256(p)}
            if p.suffix in {'.py', '.md', '.txt', '.tsx', '.ts', '.css', '.json', '.html'}:
                content = p.read_text(encoding='utf-8-sig', errors='replace')
                item['lines'] = len(content.splitlines())
                if p.suffix == '.py':
                    try:
                        tree = ast.parse(content)
                    except SyntaxError as exc:
                        item['parse_error'] = str(exc)
                        rows.append(item)
                        continue
                    item['functions'] = [{'name': n.name, 'line': n.lineno}
                                         for n in ast.walk(tree)
                                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    item['imports'] = sorted({ast.unparse(n) for n in ast.walk(tree)
                                              if isinstance(n, (ast.Import, ast.ImportFrom))})
            rows.append(item)
    return rows


def main():
    before = OUT / 'original_manifest.json'
    current = census()
    if '--verify' in sys.argv:
        saved = json.loads(before.read_text(encoding='utf-8'))
        old = {r['path']: r['sha256'] for r in saved}
        new = {r['path']: r['sha256'] for r in current}
        changes = [p for p in old if new.get(p) != old[p]]
        added = sorted(set(new) - set(old))
        result = {'original_files_checked': len(old), 'changed_or_missing': changes,
                  'added_outside_audit': added,
                  'protected_research_files': sum(p.startswith('ananya_research_work-main/') for p in old)}
        (OUT / 'preservation_check.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
        if changes or added:
            raise SystemExit(1)
    else:
        if before.exists():
            raise RuntimeError('Initial manifest already exists; use --verify.')
        before.write_text(json.dumps(current, indent=2)+'\n', encoding='utf-8')
        print(f'Inventoried and hashed {len(current)} existing files.')
        print(json.dumps([r for r in current if r['path'].endswith('AGENTS.md')]))


if __name__ == '__main__':
    main()
