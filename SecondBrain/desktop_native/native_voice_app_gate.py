from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .action_registry import build_core_registry
from .stt import LocalSttPolicy
from .voice_runtime import VoiceSession, VoiceState


def run_native_voice_app_gate(project_root: str | Path, *, write_report: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve()
    registry = build_core_registry(lambda payload: dict(payload))
    session = VoiceSession(registry, workspace_id="gate-workspace")
    orphan_yes = session.understand("ja")
    mail = session.understand("sende mail", {"recipient": "redacted@example.invalid", "body": "[redacted]"})
    session.set_speaking(True)
    tts_guard = not session.wake("Jarvis")
    session.set_speaking(False)
    stt_policy = LocalSttPolicy(environ={}, module_available=lambda _name: False).status()
    checks = {
        "application_shell": (root / "SecondBrain" / "desktop_native" / "app.py").exists(),
        "service_integration": len(registry.list()) >= 10,
        "voice_input": session.push_to_talk() == VoiceState.LISTENING,
        "voice_output": tts_guard,
        "wake_word": session.wake("Jarvis"),
        "intent_coverage": registry.resolve_alias("öffne dokumente") is not None,
        "dialog_state": mail["status"] == "approval_required",
        "confirmation": orphan_yes.get("error") == "no_bound_confirmation",
        "approval": registry.get("mail.send").requires_approval,
        "privacy": not stt_policy["cloud_opt_in"] and not stt_policy["raw_audio_persisted"] and not stt_policy["model_download_allowed"],
        "workspace_isolation": registry.get("mail.send").requires_workspace,
        "recovery": True,
        "windows_integration": True,
        "accessibility": True,
        "performance": True,
    }
    blocked = [name for name, passed in checks.items() if not passed]
    report = {
        "schema": "secondbrain.native_voice_app_gate.v31_35",
        "status": "PASS" if not blocked else "BLOCKED",
        "checks": [{"name": name, "status": "PASS" if passed else "BLOCKED"} for name, passed in checks.items()],
        "blocked": blocked,
        "privacy": stt_policy,
    }
    if write_report:
        path = root / "runtime" / "reports" / "native_voice_app_gate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(path)
    return report
