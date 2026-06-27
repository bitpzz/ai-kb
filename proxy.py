"""Simple frontend + API reverse proxy. Run on the same port as frontend."""
import http.server, urllib.request, os, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
API  = "http://127.0.0.1:8000/api"

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=BASE, **kw)

    def do_GET(self):
        if self.path.startswith('/kb/api/'): return self.proxy('GET')
        p = self.path[3:] if self.path.startswith('/kb/') else self.path
        self.path = p if os.path.isfile(os.path.join(BASE, p.lstrip('/'))) else '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/kb/api/'): return self.proxy('POST')
        return super().do_POST()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def proxy(self, method):
        target = API + self.path[7:]
        body = None
        if method == 'POST':
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl) if cl else None
        req = urllib.request.Request(target, data=body, method=method)
        for h in ['Authorization', 'Content-Type']:
            if h in self.headers: req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req) as r:
                self.send_response(r.status)
                for k, v in r.getheaders():
                    if k.lower() in ('transfer-encoding', 'connection'): continue
                    self.send_header(k, v)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                while True:
                    c = r.read(8192)
                    if not c: break
                    self.wfile.write(c)
                    self.wfile.flush()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"AI KB Proxy on http://0.0.0.0:{port}/kb/")
    http.server.HTTPServer(('0.0.0.0', port), H).serve_forever()
