import json
import time
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class Store:
    def __init__(self, root="."):
        self.base = Path(root) / "data" / "service_runtime"
        self.base.mkdir(parents=True, exist_ok=True)

    def load(self, name, default):
        path = self.base / f"{name}.json"
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name, value):
        (self.base / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

    def append(self, name, item):
        items = self.load(name, [])
        items.append(item)
        self.save(name, items)
        return item


class ServiceRuntime:
    def __init__(self, root="."):
        self.root = Path(root)
        self.store = Store(root)

    def log(self, level, message, component="service", **fields):
        event = {
            "id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "component": component,
            "message": message,
            "fields": fields,
        }
        return self.store.append("logs", event)

    def logs(self, limit=100):
        return self.store.load("logs", [])[-limit:]

    def start(self):
        state = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat(), "heartbeat": datetime.now(timezone.utc).isoformat()}
        self.store.save("runtime", state)
        self.log("info", "runtime started")
        return state

    def stop(self):
        state = self.store.load("runtime", {})
        state.update({"status": "stopped", "stopped_at": datetime.now(timezone.utc).isoformat()})
        self.store.save("runtime", state)
        self.log("info", "runtime stopped")
        return state

    def tick(self):
        state = self.store.load("runtime", {"status": "stopped"})
        if state.get("status") != "running":
            self.log("warning", "tick rejected: runtime stopped")
            return {"ok": False, "status": "stopped"}
        state["heartbeat"] = datetime.now(timezone.utc).isoformat()
        self.store.save("runtime", state)
        self.log("debug", "heartbeat")
        return {"ok": True, "heartbeat": state["heartbeat"]}

    def status(self):
        return {
            "version": "15.1",
            "runtime": self.store.load("runtime", {"status": "stopped"}),
            "logs": len(self.store.load("logs", [])),
            "service": self.store.load("windows_service", {"status": "not_installed"}),
        }

    def health(self):
        running = self.status()["runtime"].get("status") == "running"
        return {"status": "healthy" if running else "degraded", "runtime": self.status()["runtime"]}

    def ready(self):
        return {"ready": self.health()["status"] == "healthy", "health": self.health()}

    def metrics(self):
        logs = self.store.load("logs", [])
        return {
            "runtime_status": self.status()["runtime"].get("status"),
            "logs": len(logs),
            "warnings": len([l for l in logs if l["level"] == "WARNING"]),
            "errors": len([l for l in logs if l["level"] == "ERROR"]),
        }

    def service_manifest(self, service_name="SecondBrainOS"):
        manifest = {
            "service_name": service_name,
            "display_name": "SecondBrain OS Runtime",
            "methods": ["pywin32", "nssm"],
            "entrypoint": "python launcher.py svc-run",
            "autostart": True,
        }
        self.store.save("windows_service_manifest", manifest)
        return manifest

    def generate_service_script(self, service_name="SecondBrainOS"):
        scripts = self.root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        script = scripts / "secondbrain_service.py"
        script.write_text(f"""
# pywin32 Windows Service scaffold for {service_name}
# Install:
#   pip install pywin32
#   python scripts\\secondbrain_service.py install
#   python scripts\\secondbrain_service.py start

import subprocess
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    subprocess.call(["python", "launcher.py", "svc-run"], cwd=str(root))
""".strip() + "\n", encoding="utf-8")
        return {"path": str(script), "service_name": service_name}

    def nssm_commands(self, service_name="SecondBrainOS"):
        root = str(self.root.resolve())
        return {
            "service_name": service_name,
            "commands": [
                f'nssm install {service_name} python "{root}\\launcher.py" svc-run',
                f'nssm set {service_name} AppDirectory "{root}"',
                f'nssm set {service_name} Start SERVICE_AUTO_START',
                f'nssm start {service_name}',
            ],
        }

    def http_manifest(self, host="127.0.0.1", port=8765):
        return {"host": host, "port": port, "endpoints": ["/health", "/ready", "/metrics", "/status"]}

    def http_start(self, host="127.0.0.1", port=8765):
        runtime = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, payload, status=200):
                body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/health":
                    self._send(runtime.health())
                elif self.path == "/ready":
                    self._send(runtime.ready())
                elif self.path == "/metrics":
                    self._send(runtime.metrics())
                elif self.path == "/status":
                    self._send(runtime.status())
                else:
                    self._send({"error": "not_found"}, 404)

            def log_message(self, *args):
                return

        server = HTTPServer((host, port), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        state = {"status": "running", "host": host, "port": port, "endpoints": self.http_manifest(host, port)["endpoints"]}
        self.store.save("http_server", state)
        self.log("info", "http health server started", "http", host=host, port=port)
        return state

    def run(self, ticks=3):
        self.start()
        for _ in range(ticks):
            self.tick()
            time.sleep(0.05)
        return self.status()
