from pathlib import Path
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings

class Handler(BaseHTTPRequestHandler):
    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        settings = load_settings(PROJECT_ROOT)
        vault = Path(settings["vault_path"])
        if self.path == "/api/status":
            self._json({
                "app": "SecondBrain-Agent",
                "version": settings.get("version"),
                "vault": str(vault),
                "markdown_files": len(list(vault.rglob("*.md"))) if vault.exists() else 0
            })
        else:
            self._json({"endpoints": ["/api/status"]})

if __name__ == "__main__":
    print("Web-App Backend läuft: http://localhost:8790/api/status")
    HTTPServer(("localhost", 8790), Handler).serve_forever()
