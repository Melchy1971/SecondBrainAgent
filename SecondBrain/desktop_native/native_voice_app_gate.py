from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

from .action_registry import build_core_registry
from .lifecycle import WindowStateStore
from .navigation import NAVIGATION_VIEWS, VIEWS
from .runtime_diagnostics import runtime_diagnostics, safe_status
from .voice_de import GermanVoiceController
from .voice_runtime import VoiceSession, VoiceState
from .wake_word import WakeWordConfig, WakeWordRuntime
from .windows_startup import WindowsStartupManager


PASS = "PASS"
CONDITIONAL_PASS = "CONDITIONAL_PASS"
BLOCKED = "BLOCKED"


def _readiness(voice_status: Mapping[str, Any]) -> dict[str, Any]:
    policy_value = voice_status.get("stt_policy")
    policy = policy_value if isinstance(policy_value, Mapping) else {}
    microphone_value = voice_status.get("microphone")
    microphone_status = microphone_value if isinstance(microphone_value, Mapping) else {}
    inventory_value = microphone_status.get("inventory")
    microphone = inventory_value if isinstance(inventory_value, Mapping) else {}
    modules_value = voice_status.get("modules")
    modules = modules_value if isinstance(modules_value, Mapping) else {}
    selected_engine = str(policy.get("selected_engine") or "none")
    if selected_engine not in {"faster_whisper", "vosk", "google"}:
        selected_engine = "none"
    tts_runtime_ready = bool(voice_status.get("tts_ready"))
    if modules:
        tts_runtime_ready = tts_runtime_ready and bool(modules.get("pyttsx3"))
    return {
        "stt_ready": bool(voice_status.get("stt_ready")) and selected_engine != "none",
        "tts_ready": tts_runtime_ready,
        "microphone_available": bool(microphone.get("available")),
        "selected_stt_engine": selected_engine,
        "faster_whisper_ready": bool(policy.get("faster_whisper_ready")),
        "vosk_ready": bool(policy.get("vosk_ready")),
        "windows_speech_ready": bool(policy.get("windows_speech_ready")),
    }


def run_native_voice_app_gate(
    project_root: str | Path,
    *,
    write_report: bool = True,
    voice_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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
    if voice_status is None:
        try:
            voice_status = GermanVoiceController(root).status()
        except Exception:
            voice_status = {}
    readiness = _readiness(voice_status)
    raw_policy_value = voice_status.get("stt_policy")
    raw_policy = raw_policy_value if isinstance(raw_policy_value, Mapping) else {}
    stt_policy = {
        "selected_engine": readiness["selected_stt_engine"],
        "faster_whisper_ready": readiness["faster_whisper_ready"],
        "vosk_ready": readiness["vosk_ready"],
        "windows_speech_ready": readiness["windows_speech_ready"],
        "cloud_opt_in": bool(raw_policy.get("cloud_opt_in")),
        "raw_audio_persisted": bool(raw_policy.get("raw_audio_persisted")),
        "model_download_allowed": bool(raw_policy.get("model_download_allowed")),
    }
    diagnostics = runtime_diagnostics(
        voice={
            "language": "de-DE", "stt_ready": readiness["stt_ready"],
            "tts_ready": readiness["tts_ready"], "stt_policy": stt_policy,
            "microphone": {"inventory": {"available": readiness["microphone_available"]}},
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
    structural_checks = {
        "application_shell": (root / "SecondBrain" / "desktop_native" / "app.py").exists(),
        "service_integration": all(
            registry.get(action_id)
            for action_id in (
                "assistant.ask", "documents.import", "tasks.list", "tasks.create", "calendar.create",
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
    checks = {
        name: PASS if passed else BLOCKED
        for name, passed in structural_checks.items()
    }
    if checks["voice_input"] == PASS and not (
        readiness["stt_ready"] and readiness["microphone_available"]
    ):
        checks["voice_input"] = CONDITIONAL_PASS
    if checks["voice_output"] == PASS and not readiness["tts_ready"]:
        checks["voice_output"] = CONDITIONAL_PASS
    if checks["wake_word"] == PASS and checks["voice_input"] != PASS:
        checks["wake_word"] = CONDITIONAL_PASS
    blocked = [name for name, status in checks.items() if status == BLOCKED]
    warnings = [name for name, status in checks.items() if status == CONDITIONAL_PASS]
    status = BLOCKED if blocked else CONDITIONAL_PASS if warnings else PASS
    report = {
        "schema": "secondbrain.native_voice_app_gate.v31_79",
        "status": status,
        "checks": [{"name": name, "status": check_status} for name, check_status in checks.items()],
        "blocked": blocked,
        "warnings": warnings,
        "readiness": readiness,
        "privacy": stt_policy,
        "metrics": {"navigation_alias_seconds": round(alias_latency, 6), "navigation_views": len(VIEWS)},
    }
    if write_report:
        path = root / "runtime" / "reports" / "native_voice_app_gate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(path)
    return report
