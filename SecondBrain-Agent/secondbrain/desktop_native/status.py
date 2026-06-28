from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from secondbrain.gui.bootstrap import bootstrap_status, write_bootstrap_report

SCHEMA = "secondbrain.native_desktop.status.v1"
VERSION = "30.25"


def _optional_module(name: str) -> dict[str, Any]:
    try:
        __import__(name)
        return {"name": name, "available": True}
    except Exception as exc:
        return {"name": name, "available": False, "error": str(exc)}


def _project_root(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def native_desktop_status(project_root: str | Path | None = None, *, repair: bool = False) -> dict[str, Any]:
    root = _project_root(project_root)
    bootstrap = bootstrap_status(root, repair=repair)
    voice_modules = {
        "speech_recognition": _optional_module("speech_recognition"),
        "pyttsx3": _optional_module("pyttsx3"),
        "edge_tts": _optional_module("edge_tts"),
        "sounddevice": _optional_module("sounddevice"),
        "faster_whisper": _optional_module("faster_whisper"),
        "vosk": _optional_module("vosk"),
    }
    blockers = []
    if sys.version_info < (3, 11):
        blockers.append({"name": "python", "detail": "Python >= 3.11 erforderlich"})
    if not (root / "launcher.py").exists():
        blockers.append({"name": "project_root", "detail": "launcher.py fehlt"})
    return {
        "ok": not blockers and bool(bootstrap.get("ok")),
        "schema": SCHEMA,
        "version": VERSION,
        "mode": "native_desktop",
        "web_primary": False,
        "project_root": str(root),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
        "bootstrap": bootstrap,
        "voice": {
            "language": "de-DE",
            "wake_words": ["jarvis", "second brain", "assistent"],
            "offline_first": True,
            "modules": voice_modules,
            "ready": voice_modules["speech_recognition"]["available"] or voice_modules["faster_whisper"]["available"] or voice_modules["vosk"]["available"],
            "tts_ready": voice_modules["pyttsx3"]["available"] or voice_modules["edge_tts"]["available"],
        },
        "blockers": blockers,
    }


def write_native_status_report(project_root: str | Path | None = None) -> dict[str, Any]:
    root = _project_root(project_root)
    write_bootstrap_report(root, repair=True)
    payload = native_desktop_status(root, repair=True)
    path = root / "runtime" / "reports" / "native_desktop_v30_25.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["report_path"] = str(path)
    return payload
