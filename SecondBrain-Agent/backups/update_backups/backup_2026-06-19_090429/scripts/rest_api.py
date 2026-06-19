from pathlib import Path
import sys
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.service_config import load_service_config

def run_script(script):
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    return {"returncode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]}

class Handler(BaseHTTPRequestHandler):
    def json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        settings = load_settings(PROJECT_ROOT)
        vault = Path(settings["vault_path"])
        inbox = Path(settings["inbox_path"])

        if parsed.path == "/status":
            self.json_response({
                "status": "ok",
                "version": settings.get("version"),
                "vault_exists": vault.exists(),
                "inbox_exists": inbox.exists(),
                "markdown_files": len(list(vault.rglob("*.md"))) if vault.exists() else 0,
                "inbox_files": len([p for p in inbox.rglob("*") if p.is_file()]) if inbox.exists() else 0,
            })
        elif parsed.path == "/run/import":
            self.json_response(run_script("run_once.py"))
        elif parsed.path == "/run/intelligence":
            self.json_response(run_script("run_intelligence_cycle.py"))
        elif parsed.path == "/run/governance":
            self.json_response(run_script("run_governance.py"))
        else:
            self.json_response({"error": "unknown endpoint"}, status=404)

if __name__ == "__main__":
    cfg = load_service_config(PROJECT_ROOT)
    host = "localhost"
    port = int(cfg.get("api_port", 8787))
    print(f"REST API läuft: http://{host}:{port}/status")
    HTTPServer((host, port), Handler).serve_forever()
