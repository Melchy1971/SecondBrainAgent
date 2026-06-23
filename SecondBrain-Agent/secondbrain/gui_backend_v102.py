"""Alte Control-Center-GUI (v10.2) - nur noch Praesentationsschicht.

Seit Phase 2 liegt die GUI-neutrale Logik (Pfade, Logging, Skript-Runner,
Status, Dashboard-Links) in secondbrain.hud_core. Diese Datei haelt nur noch
die HTML-Darstellung und den Server auf Port 8850. Sie wird nicht mehr als
Standard-GUI gestartet (start_gui.py leitet auf das HUD um), bleibt aber als
Fallback lauffaehig. Single Source of Truth fuer die Logik ist hud_core.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from secondbrain.hud_core import (
    LOG_DIR,
    dashboard_links,
    log_event,
    run_script,
    system_status,
)


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
