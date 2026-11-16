"""Read-only local convergence viewer. No simulation is started or modified."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path == '/data.csv':
                body = self.server.csv_path.read_bytes()
                kind = 'text/csv; charset=utf-8'
            elif path == '/info':
                body = json.dumps({'csv': str(self.server.csv_path)}).encode()
                kind = 'application/json'
            elif path in ('/', '/index.html', '/viewer.js'):
                asset = 'viewer.js' if path == '/viewer.js' else 'index.html'
                body = (ROOT / asset).read_bytes()
                kind = 'application/javascript' if asset.endswith('.js') else 'text/html; charset=utf-8'
            else:
                self.send_error(404)
                return
        except OSError:
            self.send_error(503, 'CSV or viewer file temporarily unavailable')
            return
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Avoid printing a request every two seconds while monitoring.
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, help='CSV path; default: newest convergence.csv at startup')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    csv_path = args.csv
    if csv_path is None:
        candidates = list((ROOT.parent / 'runs').glob('*/convergence.csv'))
        if not candidates:
            parser.error('No convergence.csv found; start the solver or pass --csv PATH')
        csv_path = max(candidates, key=lambda p: p.stat().st_mtime)
    csv_path = csv_path.resolve()
    if not csv_path.is_file():
        parser.error(f'CSV not found: {csv_path}')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as exc:
        parser.exit(2, f'Cannot start viewer: {exc}. Try --port 8766\n')
    server.csv_path = csv_path
    print(f'CSV: {csv_path}\nOpen in Firefox: http://127.0.0.1:{server.server_port}/\n'
          'Refreshes every 2 seconds. Ctrl+C stops only this viewer.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
