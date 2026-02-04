# viewer_server.py
import http.server
import socketserver

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    # Serve files relative to this script's directory
    pass

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving viewer at http://localhost:{PORT}")
        httpd.serve_forever()
