from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class VoiceCommand:
    intent: str
    text: str
    args: dict[str, Any]
    needs_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "text": self.text,
            "args": self.args,
            "needs_confirmation": self.needs_confirmation,
        }


def _norm(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("öffne", "oeffne").replace("ö", "oe").replace("ä", "ae").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"\s+", " ", text)
    for wake in ("jarvis", "second brain", "secondbrain", "assistent"):
        if text.startswith(wake + " "):
            text = text[len(wake) + 1 :].strip()
    return text


def parse_german_voice_command(text: str) -> VoiceCommand:
    raw = text.strip()
    t = _norm(raw)
    if not t:
        return VoiceCommand("empty", raw, {})
    if any(token in t for token in ("status", "systemstatus", "wie ist der stand", "gesundheit", "diagnose")):
        return VoiceCommand("status", raw, {})
    if any(token in t for token in ("produktion", "production gate", "release gate", "gate")):
        return VoiceCommand("production_gate", raw, {})
    if any(token in t for token in ("dokument", "document center", "import center")) and not t.startswith("importiere"):
        return VoiceCommand("open_view", raw, {"view": "documents"})
    if any(token in t for token in ("memory", "gedaechtnis", "erinnerung")):
        return VoiceCommand("open_view", raw, {"view": "memory"})
    if any(token in t for token in ("einstellung", "settings", "konfiguration")):
        return VoiceCommand("open_view", raw, {"view": "settings"})
    if t.startswith(("suche ", "finde ", "recherchiere ")):
        query = re.sub(r"^(suche|finde|recherchiere)\s+", "", t).strip()
        return VoiceCommand("rag_search", raw, {"query": query})
    if t.startswith(("frage ", "beantworte ", "antwort ")):
        query = re.sub(r"^(frage|beantworte|antwort)\s+", "", t).strip()
        return VoiceCommand("rag_answer", raw, {"query": query})
    if t.startswith(("importiere datei ", "datei importieren ")):
        path = re.sub(r"^(importiere datei|datei importieren)\s+", "", raw, flags=re.IGNORECASE).strip().strip('"')
        return VoiceCommand("ingest_file", raw, {"path": path}, needs_confirmation=True)
    if any(token in t for token in ("repariere index", "index reparieren", "vektor index reparieren", "vector index repair")):
        return VoiceCommand("vector_repair", raw, {}, needs_confirmation=True)
    if any(token in t for token in ("stopp", "beenden", "schliessen", "ruhe")):
        return VoiceCommand("stop_listening", raw, {})
    return VoiceCommand("chat", raw, {"message": raw})


class GermanVoiceController:
    """German voice boundary for the native desktop app.

    Dependencies are optional. Without microphone/STT packages the controller still parses
    typed German commands and exposes clear readiness diagnostics.
    """

    def __init__(self, project_root: str | Path | None = None, *, speaker: Callable[[str], None] | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.speaker = speaker
        self.language = os.environ.get("SECONDBRAIN_VOICE_LANGUAGE", "de-DE")
        self._listening = False
        self._thread: threading.Thread | None = None

    def status(self) -> dict[str, Any]:
        modules: dict[str, bool] = {}
        for name in ("speech_recognition", "pyttsx3", "edge_tts", "faster_whisper", "vosk"):
            try:
                __import__(name)
                modules[name] = True
            except Exception:
                modules[name] = False
        return {
            "ok": True,
            "schema": "secondbrain.voice.de.v1",
            "language": self.language,
            "stt_ready": modules["speech_recognition"] or modules["faster_whisper"] or modules["vosk"],
            "tts_ready": modules["pyttsx3"] or modules["edge_tts"],
            "modules": modules,
            "listening": self._listening,
            "supported_intents": [
                "status",
                "production_gate",
                "open_view",
                "rag_search",
                "rag_answer",
                "ingest_file",
                "vector_repair",
                "stop_listening",
                "chat",
            ],
        }

    def parse(self, text: str) -> dict[str, Any]:
        return parse_german_voice_command(text).to_dict()

    def speak(self, text: str) -> dict[str, Any]:
        if self.speaker:
            self.speaker(text)
            return {"ok": True, "engine": "callback"}
        try:
            import pyttsx3
            engine = pyttsx3.init()
            # Keep engine selection deterministic. German voice is used when installed.
            for voice in engine.getProperty("voices") or []:
                blob = " ".join(str(getattr(voice, attr, "")) for attr in ("id", "name", "languages")).lower()
                if "german" in blob or "de_" in blob or "de-de" in blob:
                    engine.setProperty("voice", voice.id)
                    break
            engine.say(text)
            engine.runAndWait()
            return {"ok": True, "engine": "pyttsx3"}
        except Exception as exc:
            return {"ok": False, "engine": "none", "error": str(exc)}

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 8) -> dict[str, Any]:
        try:
            import speech_recognition as sr
        except Exception as exc:
            return {"ok": False, "error": f"speech_recognition nicht installiert: {exc}"}
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            try:
                text = recognizer.recognize_google(audio, language=self.language)
                return {"ok": True, "text": text, "command": self.parse(text), "engine": "google_speech_recognition"}
            except sr.UnknownValueError:
                return {"ok": False, "error": "Sprache nicht verstanden"}
            except sr.RequestError as exc:
                return {"ok": False, "error": f"STT-Service nicht erreichbar: {exc}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def run_launcher_command(self, args: list[str], timeout: int = 60) -> dict[str, Any]:
        cmd = [sys.executable, "launcher.py"] + args
        try:
            proc = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, timeout=timeout)
            payload: Any = None
            try:
                payload = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else None
            except json.JSONDecodeError:
                payload = None
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "command": cmd,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-2000:],
                "json": payload,
            }
        except Exception as exc:
            return {"ok": False, "command": cmd, "error": str(exc)}
