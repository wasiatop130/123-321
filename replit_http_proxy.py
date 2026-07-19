import http.server
import socketserver
import socket
import select

PORT = 9000

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Forward HTTP GET requests
        url = self.path
        try:
            # We construct a request to forward
            import urllib.request
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for k, v in response.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                import shutil
                shutil.copyfileobj(response, self.wfile)
        except Exception as e:
            self.send_error(500, str(e))

    def do_CONNECT(self):
        # Forward HTTPS CONNECT tunnel (essential for HTTPS traffic)
        address = self.path.split(":")
        host = address[0]
        port = int(address[1])
        try:
            target = socket.create_connection((host, port))
            self.send_response(200, "Connection Established")
            self.end_headers()
            
            # Bidirectional pipe
            inputs = [self.connection, target]
            while True:
                readable, _, _ = select.select(inputs, [], [])
                if self.connection in readable:
                    data = self.connection.recv(4096)
                    if not data: break
                    target.sendall(data)
                if target in readable:
                    data = target.recv(4096)
                    if not data: break
                    self.connection.sendall(data)
        except Exception as e:
            self.send_error(500, str(e))

with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"✅ HTTP Proxy Bridge is running on port {PORT}!")
    httpd.serve_forever()
