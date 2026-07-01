from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path("runtime/native")
CONFIG_FILE = RUNTIME_DIR / "voice_config.json"
HISTORY_FILE = RUNTIME_DIR / "voice_command_history.jsonl"

DEFAULT_CONFIG = {
    "language": "de-DE",
    "wake_word": "jarvis",
    "mode": "push_to_talk",
    "stt_provider": "offline_optional",
    "tts_provider": "system_optional",
    "microphone": "default",
    "confirmation_required_for_write_actions": True,
}

@dataclass(frozen=True)
class VoiceCommandResult:
    ok: bool
    intent: str
    action: str
    text: str
    requires_confirmation: bool = False
    message: str = ""


def _ensure_runtime() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def load_voice_config() -> dict[str, Any]:
    _ensure_runtime()
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")
        return dict(DEFAULT_CONFIG)
    try:
        loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        loaded = {}
    merged = dict(DEFAULT_CONFIG)
    merged.update({k: v for k, v in loaded.items() if v is not None})
    return merged


def save_voice_config(config: dict[str, Any]) -> dict[str, Any]:
    _ensure_runtime()
    merged = dict(DEFAULT_CONFIG)
    merged.update(config)
    CONFIG_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return merged


def parse_german_voice_command(text: str) -> VoiceCommandResult:
    raw = (text or "").strip()
    normalized = raw.lower().replace(",", " ").replace("  ", " ")
    if normalized.startswith("jarvis "):
        normalized = normalized[len("jarvis "):].strip()

    write_intents = (
        ("repariere index", "index_repair", "p1-vector-index-repair"),
        ("aktualisiere index", "index_repair", "p1-vector-index-repair"),
        ("importiere datei", "document_import", "document-explorer-import"),
        ("speichere memory", "memory_note", "native-action"),
        ("notiere", "memory_note", "native-action"),
    )
    for prefix, intent, action in write_intents:
        if normalized.startswith(prefix):
            return VoiceCommandResult(True, intent, action, raw, True, "Schreibende Aktion benötigt Freigabe.")

    read_intents = (
        ("status", "status", "native-status"),
        ("öffne dokumente", "open_documents", "document-explorer-gui"),
        ("dokumente", "open_documents", "document-explorer-gui"),
        ("öffne memory", "open_memory", "memory-explorer"),
        ("memory", "open_memory", "memory-explorer"),
        ("öffne agenten", "open_agents", "agent-control-gui"),
        ("agenten", "open_agents", "agent-control-gui"),
        ("öffne chat", "open_chat", "native-chat-status"),
        ("chat", "open_chat", "native-chat-status"),
        ("hilfe", "help", "voice-center-status"),
    )
    for prefix, intent, action in read_intents:
        if normalized == prefix or normalized.startswith(prefix + " "):
            return VoiceCommandResult(True, intent, action, raw, False, "Befehl erkannt.")

    if normalized.startswith("suche "):
        return VoiceCommandResult(True, "search", "document-explorer-search", raw, False, "Suche erkannt.")
    if normalized.startswith("frage "):
        return VoiceCommandResult(True, "chat_question", "native-chat-ask", raw, False, "Frage erkannt.")

    return VoiceCommandResult(False, "unknown", "", raw, False, "Kein bekannter deutscher Sprachbefehl.")


def append_voice_history(result: VoiceCommandResult) -> None:
    _ensure_runtime()
    row = asdict(result)
    row["ts"] = int(time.time())
    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_voice_history(limit: int = 25) -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows[-limit:]


def voice_center_status() -> dict[str, Any]:
    cfg = load_voice_config()
    history = read_voice_history(10)
    return {
        "ok": True,
        "version": "30.35",
        "language": cfg["language"],
        "wake_word": cfg["wake_word"],
        "mode": cfg["mode"],
        "stt_provider": cfg["stt_provider"],
        "tts_provider": cfg["tts_provider"],
        "microphone": cfg["microphone"],
        "history_count": len(history),
        "write_confirmation": bool(cfg.get("confirmation_required_for_write_actions", True)),
    }


def run_voice_command(text: str, *, record: bool = True) -> dict[str, Any]:
    result = parse_german_voice_command(text)
    if record:
        append_voice_history(result)
    return asdict(result)
