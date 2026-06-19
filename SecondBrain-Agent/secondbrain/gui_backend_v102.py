from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, quote

ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")
LOG_DIR = ROOT / "logs"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run_script(script: str, *args: str) -> dict:
    p = ROOT / "scripts" / script
    if not p.exists():
        return {"ok": False, "script": script, "output": f"Script nicht gefunden: {p}"}
    result = subprocess.run(
        [sys.executable, str(p), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    output = (result.stdout + "\n" + result.stderr)[-12000:]
    log_event("script.run", {"script": script, "ok": result.returncode == 0})
    return {"ok": result.returncode == 0, "script": script, "output": output}

def log_event(event_type: str, payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {"time": now(), "type": event_type, "payload": payload}
    with (LOG_DIR / "jarvis_gui.log").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def system_status() -> dict:
    return {
        "time": now(),
        "root": str(ROOT),
        "vault": str(VAULT),
        "inbox": str(INBOX),
        "root_exists": ROOT.exists(),
        "vault_exists": VAULT.exists(),
        "inbox_exists": INBOX.exists(),
        "python": sys.version,
        "markdown_files": len(list(VAULT.rglob("*.md"))) if VAULT.exists() else 0,
        "log_exists": (LOG_DIR / "jarvis_gui.log").exists(),
    }

def latest_file(folder: Path) -> str:
    if not folder.exists():
        return ""
    files = sorted(folder.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    return str(files[0]) if files else ""

def dashboard_links() -> dict:
    return {
        "Command Center v10": str(VAULT / "126_CommandCenter" / "SecondBrain_Command_Center_v10.md"),
        "Jarvis Copilot": latest_file(VAULT / "125_JarvisCopilot"),
        "Life Dashboard": str(VAULT / "120_LifeDashboard" / "Life_Dashboard_v10.md"),
        "Knowledge Intelligence": str(VAULT / "119_KnowledgeIntelligenceDashboard" / "Knowledge_Intelligence_Dashboard_v99.md"),
        "v9.5 Control Center": str(VAULT / "98_V95ControlCenter" / "SecondBrain_v9_5_Control_Center.md"),
        "Release Gates": str(VAULT / "95_Operations" / "ReleaseGates"),
    }

def html_page(body: str, title: str = "Jarvis Control Center") -> bytes:
    html = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body{{font-family:Arial, sans-serif; margin:0; background:#111827; color:#e5e7eb;}}
header{{background:#020617; padding:18px 28px; border-bottom:1px solid #334155;}}
main{{padding:24px; max-width:1200px; margin:auto;}}
.card{{background:#1f2937; border:1px solid #374151; border-radius:10px; padding:16px; margin:14px 0;}}
.grid{{display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px;}}
button,a.button{{background:#2563eb; color:white; border:0; padding:10px 14px; border-radius:8px; cursor:pointer; text-decoration:none; display:inline-block; margin:4px;}}
button.warn{{background:#b45309;}}
button.ok{{background:#047857;}}
pre{{background:#020617; padding:14px; border-radius:8px; overflow:auto; max-height:520px;}}
table{{width:100%; border-collapse:collapse;}}
td,th{{border-bottom:1px solid #374151; padding:8px; text-align:left;}}
small{{color:#94a3b8;}}
input{{padding:10px; border-radius:8px; border:1px solid #475569; width:70%;}}
</style>
</head>
<body>
<header><h1>Jarvis Control Center v10.2</h1><small>lokal · review-first · keine Löschaktionen</small></header>
<main>{body}</main>
</body></html>"""
    return html.encode("utf-8")

def render_home(output: str = "") -> bytes:
    status = system_status()
    links = dashboard_links()
    body = ["<div class='grid'>"]
    body.append("<div class='card'><h2>Status</h2><table>")
    for k, v in status.items():
        body.append(f"<tr><th>{k}</th><td>{v}</td></tr>")
    body.append("</table></div>")
    body.append("<div class='card'><h2>Aktionen</h2>")
    actions = [
        ("Import AI Exports", "/run?script=import_ai_exports.py"),
        ("v10 Cycle", "/run?script=run_v10_cycle.py"),
        ("v10.1 Cycle", "/run?script=run_v101_cycle.py"),
        ("Path Check", "/run?script=check_paths_v9.py"),
        ("Release Gate v9", "/run?script=release_gate_v9.py"),
        ("Regression Tests", "/run?script=run_regression_tests_v9.py"),
        ("Production Gate v9.6", "/run?script=production_ready_gate_v96.py"),
        ("Vector RAG Index", "/run?script=build_vector_rag.py"),
    ]
    for label, href in actions:
        body.append(f"<a class='button' href='{href}'>{label}</a>")
    body.append("</div>")
    body.append("</div>")
    body.append("<div class='card'><h2>RAG Frage</h2><form action='/rag' method='get'><input name='q' placeholder='Frage an dein Vault'><button>Fragen</button></form></div>")
    body.append("<div class='card'><h2>Dashboards</h2><table><tr><th>Name</th><th>Pfad</th></tr>")
    for name, path in links.items():
        body.append(f"<tr><td>{name}</td><td><code>{path}</code></td></tr>")
    body.append("</table></div>")
    if output:
        body.append(f"<div class='card'><h2>Ausgabe</h2><pre>{output}</pre></div>")
    body.append("<div class='card'><h2>Logs</h2><a class='button' href='/logs'>jarvis_gui.log öffnen</a></div>")
    return html_page("\n".join(body))

class Handler(BaseHTTPRequestHandler):
    def send_html(self, data: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, data: dict):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/":
            self.send_html(render_home())
        elif parsed.path == "/status":
            self.send_json(system_status())
        elif parsed.path == "/run":
            script = qs.get("script", [""])[0]
            result = run_script(script)
            self.send_html(render_home(result["output"]))
        elif parsed.path == "/rag":
            q = qs.get("q", [""])[0]
            result = run_script("rag_answer.py", q) if q else {"output": "Keine Frage übergeben."}
            self.send_html(render_home(result["output"]))
        elif parsed.path == "/logs":
            log = LOG_DIR / "jarvis_gui.log"
            text = log.read_text(encoding="utf-8", errors="ignore")[-20000:] if log.exists() else "Noch keine Logs."
            self.send_html(html_page(f"<div class='card'><h2>Logs</h2><pre>{text}</pre><a class='button' href='/'>Zurück</a></div>", "Logs"))
        else:
            self.send_response(404)
            self.end_headers()

def start(host: str = "127.0.0.1", port: int = 8850):
    log_event("gui.start", {"host": host, "port": port})
    print(f"Jarvis Control Center: http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
