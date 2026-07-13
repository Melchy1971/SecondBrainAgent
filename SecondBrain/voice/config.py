"""Voice Control v20 - zentrale Konfiguration.

Eine einzige Quelle der Wahrheit fuer alle Voice-Komponenten. Laedt aus
``runtime/voice/settings.json`` und faellt auf sichere Defaults zurueck.
Pfade werden aus ``secondbrain.hud_core`` abgeleitet, damit Voice-Control und
HUD garantiert dasselbe Vault/Repo verwenden.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:  # Pfade aus dem Kernmodul wiederverwenden (HUD/Voice teilen sich Vault).
    from secondbrain.hud_core import ROOT, VAULT  # type: ignore
except Exception:  # pragma: no cover - Fallback ohne installiertes Paket
    ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
    VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

INBOX = VAULT.parent / "SecondBrain-Inbox"
SETTINGS_FILE = ROOT / "runtime" / "voice" / "settings.json"

# Erlaubte Werte je Provider. Reihenfolge = Praeferenz beim Auto-Fallback.
STT_PROVIDERS = ("faster_whisper", "whisper", "manual")
TTS_PROVIDERS = ("pyttsx3", "sapi", "console")
MODES = ("wake_word", "push_to_talk", "always_on")


@dataclass
class VoiceConfig:
    """Laufzeitkonfiguration der Sprachsteuerung."""

    wake_word: str = "jarvis"
    mode: str = "wake_word"
    language: str = "de"

    stt_provider: str = "faster_whisper"
    stt_model: str = "small"            # tiny|base|small|medium|large-v3
    tts_provider: str = "pyttsx3"
    tts_rate: int = 185                 # Woerter/Minute (pyttsx3)

    sample_rate: int = 16000
    silence_threshold: float = 0.012    # RMS-Schwelle der Energie-VAD
    silence_duration: float = 1.0       # Sek. Stille -> Aufnahme-Ende
    max_utterance_seconds: float = 20.0

    hud_url: str = "http://127.0.0.1:8851"
    hud_timeout: float = 8.0

    dictation_dir: Path = field(default_factory=lambda: INBOX / "Voice" / "Dictation")
    sessions_log: Path = field(default_factory=lambda: ROOT / "runtime" / "voice" / "sessions.json")

    # Sicherheit (entspricht voice_layer_v103.safety + CLAUDE.md):
    # destruktive Aktionen aus, Skriptausfuehrung nur ueber HUD-Allowlist.
    allow_system_actions: bool = False

    # --- Persistenz ----------------------------------------------------------
    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceConfig":
        path = Path(path) if path else SETTINGS_FILE
        cfg = cls()
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                raw = {}
            cfg = cls._merge(cfg, raw)
        return cfg.normalised()

    @staticmethod
    def _merge(cfg: "VoiceConfig", raw: dict) -> "VoiceConfig":
        # Akzeptiert sowohl neue Keys als auch die alten settings.json-Keys.
        alias = {
            "stt_provider": "stt_provider",
            "tts_provider": "tts_provider",
            "wake_word": "wake_word",
            "mode": "mode",
            "allow_system_actions": "allow_system_actions",
        }
        data = asdict(cfg)
        for key, value in (raw or {}).items():
            target = alias.get(key, key)
            if target in data:
                data[target] = value
        # Pfadfelder zurueck zu Path.
        for pf in ("dictation_dir", "sessions_log"):
            data[pf] = Path(data[pf])
        return VoiceConfig(**data)

    def normalised(self) -> "VoiceConfig":
        if self.mode not in MODES:
            self.mode = "wake_word"
        if self.stt_provider not in STT_PROVIDERS:
            self.stt_provider = "faster_whisper"
        if self.tts_provider not in TTS_PROVIDERS:
            self.tts_provider = "pyttsx3"
        self.wake_word = (self.wake_word or "jarvis").lower().strip()
        return self

    def save(self, path: Path | None = None) -> Path:
        path = Path(path) if path else SETTINGS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data["dictation_dir"] = str(self.dictation_dir)
        data["sessions_log"] = str(self.sessions_log)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
