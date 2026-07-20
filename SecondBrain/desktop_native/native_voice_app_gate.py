from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .action_registry import build_core_registry
from .lifecycle import WindowStateStore
from .navigation import NAVIGATION_VIEWS, VIEWS
from .runtime_diagnostics import runtime_diagnostics, safe_status
from .stt import LocalSttPolicy
from .voice_runtime import VoiceSession, VoiceState
from .wake_word import WakeWordConfig, WakeWordRuntime
from .windows_startup import WindowsStartupManager


def run_native_voice_app_gate(project_root: str | Path, *, write_report: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve()
    registry = build_core_registry(lambda payload: dict(payload))
    session = VoiceSession(registry, workspace_id="gate-workspace")
    orphan_yes = session.understand("ja")
    mail = session.understand("sende mail", {"recipient": "redacted@example.invalid", "body": "[redacted]"})
    binding = str(mail.get("binding") or "")
    session.workspace_id = "other-workspace"
    workspace_guard = session.approve(binding).get("error") == "approval_binding_mismatch"
    session.workspace_id = "gate-workspace"
    dialog = VoiceSession(registry, workspace_id="gate-workspace")
    first_slot = dialog.understand("erstelle termin")
    second_slot = dialog.continue_dialog("Arzt")
    final_slot = dialog.continue_dialog("morgen um 14 Uhr")
    session.set_speaking(True)
    tts_guard = not session.wake("Jarvis")
    session.set_speaking(False)
    wake_runtime = WakeWordRuntime(session, lambda: "", config=WakeWordConfig(enabled=True))
    wake_ready = wake_runtime.process_phrase("Jarvis")
    stt_policy = LocalSttPolicy(environ={}, module_available=lambda _name: False).status()
    diagnostics = runtime_diagnostics(
        voice={
            "language": "de-DE", "stt_ready": False, "tts_ready": False,
            "stt_policy": stt_policy, "microphone": {"inventory": {"available": False}},
            "secret": "must-not-appear",
        },
        voice_state="IDLE",
        wake=wake_runtime.status(),
        hotkey={"enabled": False, "raw_keys_recorded": False},
        tray_running=False,
        approvals={"pending_count": 0},
        jobs={"running_count": 0, "blocked_count": 0},
    )
    started = time.monotonic()
    aliases_ready = all(registry.resolve_alias(f"öffne {spoken.lower()}") for _id, _view, spoken in NAVIGATION_VIEWS)
    alias_latency = time.monotonic() - started
    restored = WindowStateStore(root).load()
    windows_status = WindowsStartupManager(root, startup_dir=root / "startup-test", platform="nt").status()
    checks = {
        "application_shell": (root / "SecondBrain" / "desktop_native" / "app.py").exists(),
        "service_integration": all(
            registry.get(action_id)
            for action_id in (
                "assistant.ask", "documents.import", "calendar.create",
                "mail.send", "search.query", "index.repair",
            )
        ),
        "voice_input": session.push_to_talk() == VoiceState.LISTENING,
        "voice_output": tts_guard,
        "wake_word": wake_ready and wake_runtime.status()["local_only"],
        "intent_coverage": aliases_ready and registry.get("assistant.ask") is not None,
        "dialog_state": (
            first_slot.get("missing") == ["title", "when"]
            and second_slot.get("missing") == ["when"]
            and final_slot.get("status") == "approval_required"
        ),
        "confirmation": orphan_yes.get("error") == "no_bound_confirmation",
        "approval": registry.get("mail.send").requires_approval and registry.get("calendar.create").requires_approval,
        "privacy": (
            not stt_policy["cloud_opt_in"]
            and not stt_policy["raw_audio_persisted"]
            and not stt_policy["model_download_allowed"]
            and diagnostics["privacy"]["secrets_exposed"] is False
            and "must-not-appear" not in repr(diagnostics)
        ),
        "workspace_isolation": workspace_guard and registry.get("mail.send").requires_workspace,
        "recovery": restored.get("geometry") is None and safe_status(lambda: (_ for _ in ()).throw(RuntimeError())) == {},
        "windows_integration": windows_status["supported"] is True and windows_status["enabled"] is False,
        "accessibility": len(VIEWS) == 18 and aliases_ready,
        "performance": alias_latency < 1.0,
    }
    blocked = [name for name, passed in checks.items() if not passed]
    report = {
        "schema": "secondbrain.native_voice_app_gate.v31_54",
        "status": "PASS" if not blocked else "BLOCKED",
        "checks": [{"name": name, "status": "PASS" if passed else "BLOCKED"} for name, passed in checks.items()],
        "blocked": blocked,
        "privacy": stt_policy,
        "metrics": {"navigation_alias_seconds": round(alias_latency, 6), "navigation_views": len(VIEWS)},
    }
    if write_report:
        path = root / "runtime" / "reports" / "native_voice_app_gate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(path)
    return report
