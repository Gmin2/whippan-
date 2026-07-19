#!/usr/bin/env python3
# static file server for the repo plus one endpoint the editor uses to
# write docs back to disk. run from the repo root: python3 scripts/dev-server.py
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_POST(self):
        if self.path != '/save':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        rel = body.get('path', '')
        target = os.path.normpath(os.path.join(ROOT, rel.lstrip('/')))
        if not target.startswith(os.path.join(ROOT, 'docs')) or not target.endswith('.json'):
            self.send_error(403, 'only docs/*.json')
            return
        with open(target, 'w') as f:
            json.dump(body['doc'], f, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8777))
    print(f'whippan dev server on :{port}, root {ROOT}')
    ThreadingHTTPServer(('', port), Handler).serve_forever()
