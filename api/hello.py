from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'message': 'Hello from NCU Food Map!',
            'status': 'Python runtime working',
            'framework': 'Django (via WSGI)',
            'current_directory': os.getcwd(),
            'python_path': os.sys.path[:3]
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        return 