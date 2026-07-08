from pathlib import Path
import sys, json, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parents[1]
VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self.send_json({"status": "ok", "version": "9.0.0", "vault": str(VAULT)})
        elif self.path == "/run/v9":
            p = ROOT / "scripts" / "run_v9_cycle.py"
            result = subprocess.run([sys.executable, str(p)], cwd=str(ROOT), capture_output=True, text=True)
            self.send_json({"ok": result.returncode == 0, "output": (result.stdout + result.stderr)[-4000:]})
        else:
            self.send_json({"endpoints": ["/status", "/run/v9"]})

if __name__ == "__main__":
    print("SecondBrain API Gateway v9: http://localhost:8799/status")
    HTTPServer(("localhost", 8799), Handler).serve_forever()
