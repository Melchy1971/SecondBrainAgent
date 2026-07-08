from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from secondbrain.gui.bootstrap import bootstrap_status
from secondbrain.gui.p1_control_panel import P1ControlPanel
from secondbrain.gui.settings_center import SettingsCenter
from secondbrain.native.voice_de import GermanVoiceCommandParser
from secondbrain.native.approval import native_audit_status
from secondbrain.native.chat import native_chat_status


def _safe_call(fn, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        value = fn()
        return value if isinstance(value, dict) else {"ok": True, "value": value}
    except Exception as exc:  # pragma: no cover - defensive runtime boundary
        result = dict(fallback)
        result.update({"ok": False, "error": type(exc).__name__, "detail": str(exc)})
        return result


def _latest_report(root: Path, name: str) -> dict[str, Any]:
    path = root / "runtime" / "reports" / name
    if not path.exists():
        return {"ok": False, "status": "missing", "path": str(path)}
    try:
        return {"ok": True, "path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))}
    except Exception as exc:
        return {"ok": False, "status": "invalid", "path": str(path), "error": str(exc)}


def _rag_status(root: Path) -> dict[str, Any]:
    def call() -> dict[str, Any]:
        from secondbrain.p1_rag_runtime import P1RagRuntime
        rt = P1RagRuntime(root)
        return rt.status()
    return _safe_call(call, {"status": "unavailable"})


def _provider_status(root: Path) -> dict[str, Any]:
    def call() -> dict[str, Any]:
        from secondbrain.p1_rag_runtime import P1RagRuntime
        from secondbrain.p1_provider_health import evaluate_embedding_provider_health
        rt = P1RagRuntime(root)
        return evaluate_embedding_provider_health(rt, production=True, write_report=False)
    return _safe_call(call, {"status": "unavailable"})


def _memory_status(root: Path) -> dict[str, Any]:
    candidates = [
        root / "runtime" / "reports" / "memory_center_latest.json",
        root / "runtime" / "reports" / "memory_status_latest.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                return {"ok": True, "status": "report", "path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))}
            except Exception as exc:
                return {"ok": False, "status": "invalid", "path": str(path), "error": str(exc)}
    return {
        "ok": False,
        "status": "not_initialized",
        "privacy_mode_visible": True,
        "secret_encryption_visible": True,
        "data_classification_visible": True,
        "blockers": ["memory_runtime_report_missing"],
    }


def _production_status(root: Path) -> dict[str, Any]:
    return _latest_report(root, "p1_production_latest.json")


def _action_surface() -> dict[str, Any]:
    return {
        "schema": "secondbrain.native.actions.v30_29",
        "mode": "voice_button_dispatch_with_audit_and_approval_queue",
        "confirmation_required_for": ["p1-rag-ingest-file", "p1-vector-index-repair", "memory-note"],
        "direct_actions": ["native-status", "native-chat-ask", "native-chat-search", "p1-rag-hybrid-search", "p1-rag-answer", "p1-production", "open-tab"],
        "audit_log": "runtime/native/action_audit.jsonl",
        "approval_queue": "runtime/native/approval_queue.jsonl",
        "german_examples": [
            "Jarvis Status",
            "Öffne Dokumente",
            "Suche Rechnung Telekom",
            "Frage was fehlt noch",
            "Repariere Index",
            "Merke Projektstand prüfen",
        ],
    }


def build_native_view_model(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd()).resolve()
    bootstrap = bootstrap_status(base, repair=False)
    rag = _rag_status(base)
    provider = _provider_status(base)
    production = _production_status(base)
    memory = _memory_status(base)
    p1_panel = P1ControlPanel().render(provider if isinstance(provider, dict) else {})
    settings = SettingsCenter().render_embedding_settings()
    voice_examples = _action_surface()["german_examples"]
    parser = GermanVoiceCommandParser()
    audit = native_audit_status(base, limit=10)
    chat = native_chat_status(base, limit=12)
    return {
        "schema": "secondbrain.native.view_model.v30_29",
        "ok": bool(bootstrap.get("ok")),
        "version": "30.29",
        "project_root": str(base),
        "python": sys.version.split()[0],
        "mode": "native_desktop_primary",
        "web_hud": "secondary_only",
        "bootstrap": bootstrap,
        "rag": rag,
        "provider": provider,
        "production": production,
        "memory": memory,
        "p1_control": p1_panel,
        "settings": settings,
        "actions": _action_surface(),
        "audit": audit,
        "chat": chat,
        "voice": {
            "language": "de-DE",
            "offline_intent_parser": True,
            "stt_tts_optional": True,
            "action_dispatcher": True,
            "examples": voice_examples,
            "sample_intents": [parser.parse(item).to_dict() for item in voice_examples],
        },
        "environment": {
            "DATABASE_URL": bool(os.environ.get("DATABASE_URL")),
            "SECONDBRAIN_EMBEDDING_PROVIDER": os.environ.get("SECONDBRAIN_EMBEDDING_PROVIDER", ""),
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        },
    }
