"""
NEXORA AI - Frontend Development Server
Serves static frontend files on http://127.0.0.1:5500 and maps /storage to backend/storage
"""
import os
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 5500
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
STORAGE_DIR = BASE_DIR / "backend" / "storage"

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def translate_path(self, path):
        clean_path = path.split("?")[0]
        if clean_path.startswith("/storage/"):
            rel = clean_path[len("/storage/"):]
            target = STORAGE_DIR / rel
            return str(target)
        return super().translate_path(clean_path)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

class FastThreadingServer(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True

def run_server():
    os.chdir(FRONTEND_DIR)
    server_address = ("127.0.0.1", PORT)
    httpd = FastThreadingServer(server_address, CORSRequestHandler)
    print("==================================================")
    print(f"NEXORA AI Frontend Server Running")
    print(f"URL: http://127.0.0.1:{PORT}")
    print(f"Serving Directory: {FRONTEND_DIR}")
    print(f"Storage Directory: {STORAGE_DIR}")
    print("==================================================")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down frontend server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
