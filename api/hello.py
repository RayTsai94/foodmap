from http.server import BaseHTTPRequestHandler
import json
import os
import sys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'message': 'Hello from NCU Food Map!',
            'status': 'Python runtime working on Vercel',
            'framework': 'Django (via WSGI)',
            'current_directory': os.getcwd(),
            'python_version': sys.version,
            'python_path': sys.path[:5],
            'environment_vars': {
                'DJANGO_SETTINGS_MODULE': os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set'),
                'VERCEL': os.environ.get('VERCEL', 'Not set'),
                'VERCEL_ENV': os.environ.get('VERCEL_ENV', 'Not set')
            }
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
        return
        
    def do_POST(self):
        self.do_GET() 