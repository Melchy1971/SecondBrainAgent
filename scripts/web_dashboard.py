from pathlib import Path
import sys
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings

ACTIONS = {
    "/action/import": "run_once.py",
    "/action/intelligence": "run_intelligence_cycle.py",
    "/action/governance": "run_governance.py",
    "/action/quality": "run_quality_report.py",
    "/action/conflicts": "run_conflict_report.py",
    "/action/sync": "run_sync_health.py",
}

def run_script(script):
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    return result.returncode, result.stdout[-2000:], result.stderr[-2000:]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ACTIONS:
            code, out, err = run_script(ACTIONS[parsed.path])
            body = f"<html><body><h1>Aktion ausgeführt</h1><pre>{out}\n{err}</pre><p><a href='/'>zurück</a></p></body></html>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        settings = load_settings(PROJECT_ROOT)
        vault = Path(settings["vault_path"])
        inbox = Path(settings["inbox_path"])
        md_count = len(list(vault.rglob("*.md"))) if vault.exists() else 0
        inbox_count = len([p for p in inbox.rglob("*") if p.is_file()]) if inbox.exists() else 0

        html = f"""
        <html>
        <head>
          <title>SecondBrain-Agent</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .card {{ border: 1px solid #ccc; padding: 16px; margin: 12px 0; border-radius: 8px; }}
            a.button {{ display:inline-block; padding:8px 12px; border:1px solid #333; margin:4px; text-decoration:none; }}
          </style>
        </head>
        <body>
        <h1>SecondBrain-Agent Dashboard v3.2</h1>
        <div class="card">
          <h2>Status</h2>
          <ul>
            <li>Vault: {vault}</li>
            <li>Markdown-Dateien: {md_count}</li>
            <li>Inbox-Dateien: {inbox_count}</li>
            <li>Agent: {PROJECT_ROOT}</li>
          </ul>
        </div>
        <div class="card">
          <h2>Aktionen</h2>
          <a class="button" href="/action/import">Import</a>
          <a class="button" href="/action/intelligence">Intelligence Cycle</a>
          <a class="button" href="/action/governance">Governance</a>
          <a class="button" href="/action/quality">Quality Report</a>
          <a class="button" href="/action/conflicts">Conflict Report</a>
          <a class="button" href="/action/sync">Sync Health</a>
        </div>
        </body>
        </html>
        """
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    print(f"Dashboard läuft: http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
