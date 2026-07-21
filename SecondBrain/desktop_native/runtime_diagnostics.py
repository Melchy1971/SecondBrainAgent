from __future__ import annotations

from typing import Any, Callable, Mapping


def safe_status(provider: Callable[[], Mapping[str, Any]]) -> Mapping[str, Any]:
    try:
        return provider()
    except Exception:
        return {}


def runtime_diagnostics(
    *,
    voice: Mapping[str, Any],
    voice_state: str,
    wake: Mapping[str, Any],
    hotkey: Mapping[str, Any],
    tray_running: bool,
    approvals: Mapping[str, Any],
    jobs: Mapping[str, Any],
    approval_config: Mapping[str, Any] | None = None,
    external_actions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stt = voice.get("stt_policy") or {}
    microphone = (voice.get("microphone") or {}).get("inventory") or {}
    components = {
        "voice": {
            "state": voice_state,
            "language": voice.get("language"),
            "stt_ready": bool(voice.get("stt_ready")),
            "tts_ready": bool(voice.get("tts_ready")),
            "listening": bool(voice.get("listening")),
        },
        "stt": {
            "selected_engine": stt.get("selected_engine", "none"),
            "cloud_opt_in": bool(stt.get("cloud_opt_in")),
            "raw_audio_persisted": bool(stt.get("raw_audio_persisted")),
            "model_download_allowed": bool(stt.get("model_download_allowed")),
        },
        "microphone": {
            "available": bool(microphone.get("available")),
            "selected_index": microphone.get("selected_index"),
            "selected_available": bool(microphone.get("selected_available")),
        },
        "wake_word": {
            "enabled": bool(wake.get("enabled")),
            "running": bool(wake.get("running")),
            "local_only": bool(wake.get("local_only")),
            "raw_audio_persisted": bool(wake.get("raw_audio_persisted")),
        },
        "hotkey": {
            "enabled": bool(hotkey.get("enabled")),
            "available": bool(hotkey.get("available")),
            "running": bool(hotkey.get("running")),
            "raw_keys_recorded": bool(hotkey.get("raw_keys_recorded")),
        },
        "tray": {"running": bool(tray_running)},
        "approvals": {
            "available": bool(approvals.get("available", "pending_count" in approvals)),
            "pending_count": int(approvals.get("pending_count", 0)),
            "elevated_count": int(approvals.get("elevated_count", 0)),
            "overdue_count": int(approvals.get("overdue_count", 0)),
            "notifications_enabled": bool((approval_config or {}).get("notifications_enabled", True)),
            "overdue_minutes": int((approval_config or {}).get("overdue_minutes", 15)),
            "refresh_seconds": int((approval_config or {}).get("refresh_seconds", 2)),
        },
        "jobs": {
            "running_count": int(jobs.get("running_count", 0)),
            "blocked_count": int(jobs.get("blocked_count", 0)),
        },
        "external_actions": {
            "provider": str((external_actions or {}).get("provider") or "disabled"),
            "configured": bool((external_actions or {}).get("configured")),
            "authenticated": bool((external_actions or {}).get("authenticated")),
            "calendar_write": bool((external_actions or {}).get("calendar_write")),
            "mail_write": bool((external_actions or {}).get("mail_write")),
            "reason": str((external_actions or {}).get("reason") or "disabled"),
        },
    }
    degraded = not components["voice"]["stt_ready"] or not components["microphone"]["available"]
    return {
        "status": "degraded" if degraded else "ready",
        "components": components,
        "privacy": {
            "secrets_exposed": False,
            "payloads_exposed": False,
            "device_names_exposed": False,
            "local_paths_exposed": False,
        },
    }
