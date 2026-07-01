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
from secondbrain.native.runtime_snapshot import build_native_view_model

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8851
NATIVE_COMMANDS = {"gui", "gui-start", "gui-open", "jarvis", "native-gui", "desktop-gui", "desktop16-gui"}
WEB_COMMANDS = {"hud", "gui-web", "web-hud"}
GUI_COMMANDS = NATIVE_COMMANDS | WEB_COMMANDS | {"gui-status", "gui-doctor", "gui-shortcuts", "gui-bootstrap", "native-status", "voice-parse", "voice-run", "native-action", "native-action-audit", "native-approval-list", "native-approval-run", "native-approval-reject", "native-chat-status", "native-chat-ask", "native-chat-search", "native-chat-clear"}


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
    native = build_native_view_model(root)
    return {
        "ok": bool(native.get("schema")) or pid_alive or port_alive,
        "status": "native_ready" if native.get("ok") else ("web_running" if pid_alive or port_alive else "native_degraded"),
        "primary_mode": "native_desktop_chat_action_bridge_with_audit",
        "web_mode": "secondary_only",
        "project_root": str(root),
        "native": {
            "schema": native.get("schema"),
            "version": native.get("version"),
            "voice_language": native.get("voice", {}).get("language"),
            "bootstrap_status": native.get("bootstrap", {}).get("status"),
            "rag_status": native.get("rag", {}).get("status"),
            "provider": native.get("provider", {}).get("provider"),
        },
        "web_hud": {
            "url": _url(host, port),
            "pid_file": str(_pidfile(root)),
            "pid": pid,
            "pid_alive": pid_alive,
            "port_alive": port_alive,
            "start_script": str(_server_script(root)),
        },
    }


def gui_doctor(project_root: str | Path | None = None) -> dict[str, Any]:
    root = _root(project_root)
    checks: list[dict[str, Any]] = []
    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
    check("launcher", (root / "launcher.py").exists(), "launcher.py vorhanden")
    check("native_package", (root / "secondbrain" / "native" / "app.py").exists(), "secondbrain/native/app.py vorhanden")
    check("native_voice_de", (root / "secondbrain" / "native" / "voice_de.py").exists(), "deutsche Sprachsteuerung vorhanden")
    check("jarvis_bat", (root / "Jarvis.bat").exists(), "Jarvis.bat vorhanden")
    check("gui_ps1", (root / "Start-Jarvis-GUI.ps1").exists(), "Start-Jarvis-GUI.ps1 vorhanden")
    check("shortcut_installer", (root / "Install-Jarvis-Desktop.ps1").exists(), "Install-Jarvis-Desktop.ps1 vorhanden")
    check("python", bool(sys.executable), sys.executable)
    bootstrap = bootstrap_status(root, repair=False)
    native = build_native_view_model(root)
    ok = all(c["ok"] for c in checks) and bootstrap.get("ok", False)
    return {"ok": ok, "status": "pass" if ok else "blocked", "checks": checks, "bootstrap": bootstrap, "native": native}


def shortcut_manifest(project_root: str | Path | None = None) -> dict[str, Any]:
    root = _root(project_root)
    return {
        "ok": True,
        "schema": "secondbrain.gui.shortcuts.v30_29",
        "project_root": str(root),
        "primary_mode": "native_desktop_chat_action_bridge_with_audit",
        "desktop_shortcuts": [
            {"name": "Jarvis", "target": str(root / "Jarvis.bat"), "arguments": "", "starts": "Native Desktop App"},
            {"name": "Jarvis Autostart", "target": str(root / "Jarvis.bat"), "arguments": "/quiet", "starts": "Native Desktop App"},
        ],
        "web_hud_secondary": ["python launcher.py hud", "python launcher.py gui-web"],
        "installer": str(root / "Install-Jarvis-Desktop.ps1"),
        "manual_start": [
            "python launcher.py",
            "python launcher.py jarvis",
            "python launcher.py native-gui",
            "Jarvis.bat",
            "powershell -ExecutionPolicy Bypass -File Start-Jarvis-GUI.ps1",
        ],
    }


def start_web_hud(project_root: str | Path | None = None, *, open_browser: bool = True, quiet: bool = False, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict[str, Any]:
    root = _root(project_root)
    bootstrap = write_bootstrap_report(root, repair=True)
    if not bootstrap.get("ok"):
        return {"ok": False, "status": "blocked", "error": "bootstrap blocked", "bootstrap": bootstrap}
    pid = read_pid(root)
    if (pid is not None and _pid_alive(pid)) or _port_open(host, port):
        if open_browser and not quiet:
            webbrowser.open(_url(host, port))
        return {"ok": True, "status": "web_running", "action": "already_running", "url": _url(host, port)}
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
    return {"ok": True, "status": "web_starting", "action": "started", "pid": proc.pid, "url": _url(host, port), "opened_browser": bool(open_browser and not quiet)}


def start_native_gui(project_root: str | Path | None = None, *, dry_run: bool = False) -> dict[str, Any]:
    root = _root(project_root)
    bootstrap = write_bootstrap_report(root, repair=True)
    native = build_native_view_model(root)
    payload = {
        "ok": bool(bootstrap.get("ok")),
        "status": "native_ready" if bootstrap.get("ok") else "blocked",
        "action": "native_desktop_primary",
        "project_root": str(root),
        "bootstrap": bootstrap,
        "native": {
            "schema": native.get("schema"),
            "version": native.get("version"),
            "voice_language": native.get("voice", {}).get("language"),
            "web_hud": native.get("web_hud"),
        },
    }
    if dry_run or not payload["ok"]:
        return payload
    try:
        from secondbrain.native.app import run_native_app
        code = run_native_app(root)
        payload.update({"status": "closed", "exit_code": code})
        return payload
    except Exception as exc:
        return {"ok": False, "status": "blocked", "error": type(exc).__name__, "detail": str(exc), "bootstrap": bootstrap}


def _normalize_argv(raw: list[str]) -> list[str]:
    for i, item in enumerate(raw):
        if item in GUI_COMMANDS:
            return [item] + raw[:i] + raw[i + 1:]
    return raw


def gui_command(argv: list[str] | None = None) -> int:
    raw = _normalize_argv(list(sys.argv[1:] if argv is None else argv))
    parser = argparse.ArgumentParser(prog="secondbrain gui", description="SecondBrain native GUI launcher")
    parser.add_argument("cmd", choices=sorted(GUI_COMMANDS))
    parser.add_argument("text", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args, _ = parser.parse_known_args(raw)

    if args.cmd in NATIVE_COMMANDS:
        payload = start_native_gui(args.project_root, dry_run=args.dry_run)
    elif args.cmd in WEB_COMMANDS:
        payload = start_web_hud(args.project_root, open_browser=not args.no_browser, quiet=args.quiet, host=args.host, port=args.port)
    elif args.cmd in {"gui-status", "native-status"}:
        payload = gui_status(args.project_root, args.host, args.port)
    elif args.cmd == "gui-doctor":
        payload = gui_doctor(args.project_root)
    elif args.cmd == "gui-shortcuts":
        payload = shortcut_manifest(args.project_root)
    elif args.cmd == "gui-bootstrap":
        payload = write_bootstrap_report(args.project_root, repair=True)
    elif args.cmd == "voice-parse":
        from secondbrain.native.voice_de import GermanVoiceCommandParser
        payload = GermanVoiceCommandParser().parse(" ".join(args.text)).to_dict()
        payload["ok"] = True
        payload["language"] = "de-DE"
    elif args.cmd in {"voice-run", "native-action"}:
        from secondbrain.native.actions import NativeActionDispatcher
        dispatcher = NativeActionDispatcher(args.project_root)
        payload = dispatcher.parse_and_dispatch(" ".join(args.text), confirmed=False, dry_run=args.dry_run).to_dict()
        payload["language"] = "de-DE"
        payload["project_root"] = str(_root(args.project_root))
    elif args.cmd == "native-chat-status":
        from secondbrain.native.chat import native_chat_status
        payload = native_chat_status(args.project_root, limit=30)
    elif args.cmd == "native-chat-clear":
        from secondbrain.native.chat import NativeChatStore
        payload = NativeChatStore(args.project_root).clear()
    elif args.cmd == "native-chat-ask":
        from secondbrain.native.chat import native_chat_ask
        payload = native_chat_ask(args.project_root, " ".join(args.text), limit=5)
    elif args.cmd == "native-chat-search":
        from secondbrain.native.chat import native_chat_search
        payload = native_chat_search(args.project_root, " ".join(args.text), limit=5)
    elif args.cmd == "native-action-audit":
        from secondbrain.native.approval import native_audit_status
        payload = native_audit_status(args.project_root)
    elif args.cmd == "native-approval-list":
        from secondbrain.native.approval import NativeApprovalQueue, native_audit_status
        root = _root(args.project_root)
        payload = native_audit_status(root)
        payload["approvals"] = NativeApprovalQueue(root).list(status="pending")
    elif args.cmd in {"native-approval-run", "native-approval-reject"}:
        from secondbrain.native.actions import NativeActionDispatcher
        from secondbrain.native.approval import NativeApprovalQueue
        root = _root(args.project_root)
        approval_id = " ".join(args.text).strip()
        queue = NativeApprovalQueue(root)
        approval = queue.get(approval_id) if approval_id else None
        if not approval:
            payload = {"ok": False, "status": "approval_not_found", "approval_id": approval_id}
        elif args.cmd == "native-approval-reject":
            payload = {"ok": True, "status": "rejected", "approval": queue.mark(approval_id, "rejected")}
        else:
            dispatcher = NativeActionDispatcher(root)
            payload = dispatcher.parse_and_dispatch(str(approval.get("text", "")), confirmed=True, dry_run=args.dry_run).to_dict()
            if payload.get("ok"):
                queue.mark(approval_id, "executed")
            payload["approval_id"] = approval_id
            payload["language"] = "de-DE"
            payload["project_root"] = str(root)
    else:
        payload = {"ok": False, "status": "unknown_command", "cmd": args.cmd}
    _print(payload)
    return 0 if payload.get("ok") else 1
