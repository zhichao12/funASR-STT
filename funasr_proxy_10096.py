import http.server
import socketserver
import urllib.request


TARGET = "http://127.0.0.1:10095"
PORT = 10096


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def forward(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        url = TARGET + self.path
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in ("host", "connection", "content-length")
        }
        request = urllib.request.Request(url, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(data)
        except Exception as exc:
            message = str(exc).encode("utf-8", errors="replace")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}", flush=True)


class ReuseServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReuseServer(("0.0.0.0", PORT), ProxyHandler) as httpd:
        print(f"proxy listening on 0.0.0.0:{PORT} -> {TARGET}", flush=True)
        httpd.serve_forever()
