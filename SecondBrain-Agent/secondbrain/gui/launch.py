from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

from secondbrain.gui.bootstrap import bootstrap_status, write_bootstrap_report

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8851
GUI_COMMANDS = {"gui", "gui-start", "gui-open", "gui-status", "gui-doctor", "gui-shortcuts", "gui-bootstrap", "jarvis", "desktop-gui", "desktop16-gui"}


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _root(project_root: str | Path | None = None) -> Path:
    return Path(project_root or Path.cwd()).resolve()


def _pidfile(root: Path) -> Path:
    return root / "runtime" / "jarvis_hud.pid"


def _server_script(root: Path) -> Path:
    return root / "scripts" / "start_hud.py"


def _url(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    return f"http://{host}:{port}"


def _port_open(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except PermissionError:
        return True


def read_pid(root: Path) -> int | None:
    try:
        raw = _pidfile(root).read_text(encoding="utf-8").strip()
        return int(raw) if raw else None
    except (OSError, ValueError):
        return None


def gui_status(project_root: str | Path | None = None, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict[str, Any]:
    root = _root(project_root)
    pid = read_pid(root)
    pid_alive = _pid_alive(pid) if pid is not None else False
    port_alive = _port_open(host, port)
    return {
        "ok": pid_alive or port_alive,
        "status": "running" if pid_alive or port_alive else "stopped",
        "project_root": str(root),
        "url": _url(host, port),
        "pid_file": str(_pidfile(root)),
        "pid": pid,
        "pid_alive": pid_alive,
        "port_alive": port_alive,
        "start_script": str(_server_script(root)),
    }


def gui_doctor(project_root: str | Path | None = None) -> dict[str, Any]:
    root = _root(project_root)
    checks: list[dict[str, Any]] = []
    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
    check("launcher", (root / "launcher.py").exists(), "launcher.py vorhanden")
    check("hud_start_script", _server_script(root).exists(), "scripts/start_hud.py vorhanden")
    check("jarvis_bat", (root / "Jarvis.bat").exists(), "Jarvis.bat vorhanden")
    check("gui_ps1", (root / "Start-Jarvis-GUI.ps1").exists(), "Start-Jarvis-GUI.ps1 vorhanden")
    check("shortcut_installer", (root / "Install-Jarvis-Desktop.ps1").exists(), "Install-Jarvis-Desktop.ps1 vorhanden")
    check("python", bool(sys.executable), sys.executable)
    status = gui_status(root)
    bootstrap = bootstrap_status(root, repair=False)
    ok = all(c["ok"] for c in checks) and bootstrap.get("ok", False)
    return {"ok": ok, "status": "pass" if ok else "blocked", "checks": checks, "runtime": status, "bootstrap": bootstrap}


def shortcut_manifest(project_root: str | Path | None = None) -> dict[str, Any]:
    root = _root(project_root)
    return {
        "ok": True,
        "schema": "secondbrain.gui.shortcuts.v1",
        "project_root": str(root),
        "desktop_shortcuts": [
            {"name": "Jarvis GUI", "target": str(root / "Jarvis.bat"), "arguments": "", "starts": "HUD + Browser"},
            {"name": "Jarvis GUI Autostart", "target": str(root / "Jarvis.bat"), "arguments": "/quiet", "starts": "HUD ohne Browser"},
        ],
        "installer": str(root / "Install-Jarvis-Desktop.ps1"),
        "uninstaller": str(root / "uninstall_jarvis.ps1"),
        "manual_start": [
            "python launcher.py gui-open",
            "python launcher.py gui-status",
            "Jarvis.bat",
            "powershell -ExecutionPolicy Bypass -File Start-Jarvis-GUI.ps1",
        ],
    }


def start_gui(project_root: str | Path | None = None, *, open_browser: bool = True, quiet: bool = False, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict[str, Any]:
    root = _root(project_root)
    bootstrap = write_bootstrap_report(root, repair=True)
    if not bootstrap.get("ok"):
        return {"ok": False, "status": "blocked", "error": "bootstrap blocked", "bootstrap": bootstrap}
    status = gui_status(root, host, port)
    if status["ok"]:
        if open_browser and not quiet:
            webbrowser.open(status["url"])
        status.update({"action": "already_running", "opened_browser": bool(open_browser and not quiet)})
        return status
    script = _server_script(root)
    if not script.exists():
        return {"ok": False, "status": "blocked", "error": f"Startskript fehlt: {script}"}
    root.joinpath("runtime").mkdir(parents=True, exist_ok=True)
    python_exe = sys.executable or "python"
    kwargs: dict[str, Any] = {"cwd": str(root), "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    proc = subprocess.Popen([python_exe, str(script)], **kwargs)
    if open_browser and not quiet:
        webbrowser.open(_url(host, port))
    return {"ok": True, "status": "starting", "action": "started", "pid": proc.pid, "url": _url(host, port), "opened_browser": bool(open_browser and not quiet)}


def _normalize_argv(raw: list[str]) -> list[str]:
    for i, item in enumerate(raw):
        if item in GUI_COMMANDS:
            return [item] + raw[:i] + raw[i + 1:]
    return raw


def gui_command(argv: list[str] | None = None) -> int:
    raw = _normalize_argv(list(sys.argv[1:] if argv is None else argv))
    parser = argparse.ArgumentParser(prog="secondbrain gui", description="SecondBrain GUI launcher")
    parser.add_argument("cmd", choices=sorted(GUI_COMMANDS))
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args, _ = parser.parse_known_args(raw)

    if args.cmd in {"gui", "gui-start", "gui-open", "jarvis", "desktop-gui", "desktop16-gui"}:
        payload = start_gui(args.project_root, open_browser=not args.no_browser, quiet=args.quiet, host=args.host, port=args.port)
    elif args.cmd == "gui-status":
        payload = gui_status(args.project_root, args.host, args.port)
    elif args.cmd == "gui-doctor":
        payload = gui_doctor(args.project_root)
    elif args.cmd == "gui-shortcuts":
        payload = shortcut_manifest(args.project_root)
    elif args.cmd == "gui-bootstrap":
        payload = write_bootstrap_report(args.project_root, repair=True)
    else:
        payload = {"ok": False, "status": "unknown_command", "cmd": args.cmd}
    _print(payload)
    return 0 if payload.get("ok") else 1
