import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import json
from datetime import datetime
from threading import Thread

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data_parse = urllib.parse.parse_qs(post_data.decode())
        username = data_parse.get('username', [''])[0]
        message = data_parse.get('message', [''])[0]
        self.save_to_json(username, message)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def save_to_json(self, username, message):
        data = {
            "username": username,
            "message": message
        }
        timestamp = datetime.now().isoformat()
        with open('storage/data.json', 'a+') as file:
            try:
                file.seek(0)
                data_json = json.load(file)
            except json.JSONDecodeError:
                data_json = {}
            data_json[timestamp] = data
            file.seek(0)
            json.dump(data_json, file, indent=4)
            file.truncate()
            
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/contact':
            self.send_html_file('contact.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

class SocketServer(Thread):
    def __init__(self):
        super().__init__()
        self.host = 'localhost'
        self.port = 5000

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.bind((self.host, self.port))
            print("Socket server started.")
            while True:
                data, _ = server_socket.recvfrom(1024)
                self.handle_data(data)

    def handle_data(self, data):
        data_dict = json.loads(data.decode())
        timestamp = datetime.now().isoformat()
        with open('storage/data.json', 'a+') as file:
            file.seek(0)
            if file.read(1):
                file.seek(0)
                try:
                    data_json = json.load(file)
                except json.JSONDecodeError as e:
                    print(f"Error loading JSON: {e}")
                    data_json = {}
            else:
                data_json = {}
            data_json[timestamp] = data_dict
            file.seek(0)
            json.dump(data_json, file, indent=4)
            file.truncate()

def run_servers():
    http_server = HTTPServer(('0.0.0.0', 3000), HttpHandler)
    socket_server = SocketServer()
    try:
        thread = Thread(target=http_server.serve_forever)
        thread.start()
        socket_server.start()
        thread.join()
    except KeyboardInterrupt:
        http_server.server_close()
        socket_server.join()

if __name__ == '__main__':
    run_servers()