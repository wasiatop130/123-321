import socket
import select
import threading

PORT = 1080

class Socks5Server:
    def __init__(self, host="0.0.0.0", port=PORT):
        self.host = host
        self.port = port

    def handle_client(self, client_socket):
        try:
            # 1. Greeting
            version, nmethods = client_socket.recv(2)
            methods = client_socket.recv(nmethods)
            client_socket.sendall(b"\x05\x00") # No authentication

            # 2. Request
            version, cmd, _, address_type = client_socket.recv(4)
            if address_type == 1: # IPv4
                address = socket.inet_ntoa(client_socket.recv(4))
            elif address_type == 3: # Domain name
                domain_length = client_socket.recv(1)[0]
                address = client_socket.recv(domain_length).decode('utf-8')
            port = int.from_bytes(client_socket.recv(2), 'big')

            # 3. Connect to target
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((address, port))
            client_socket.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + (PORT).to_bytes(2, 'big'))

            # 4. Pipe traffic
            self.forward(client_socket, remote_socket)
        except Exception:
            pass
        finally:
            client_socket.close()

    def forward(self, client_socket, remote_socket):
        while True:
            r, w, x = select.select([client_socket, remote_socket], [], [])
            if client_socket in r:
                data = client_socket.recv(4096)
                if not data: break
                remote_socket.sendall(data)
            if remote_socket in r:
                data = remote_socket.recv(4096)
                if not data: break
                client_socket.sendall(data)

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        print(f"✅ SOCKS5 Proxy-Bridge is running on port {self.port}!")
        while True:
            client, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

if __name__ == "__main__":
    Socks5Server().start()
