"""
Vercel Serverless Function: Health Check
GET /api
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {
            "status": "ok",
            "message": "Property Comparison API is running",
            "endpoints": [
                "GET /api - Health check",
                "GET /api/properties - List sample properties",
                "POST /api/compare-addresses - Compare two properties by address"
            ]
        }
        self.wfile.write(json.dumps(response).encode())

