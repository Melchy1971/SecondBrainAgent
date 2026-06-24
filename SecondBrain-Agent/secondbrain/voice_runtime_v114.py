from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable
import json
import time
import uuid


@dataclass
class VoiceCommand:
    command_id: str
    raw_text: str
    intent: str
    confidence: float
    args: dict[str, Any]
    requires_approval: bool = False


@dataclass
class VoiceTurn:
    turn_id: str
    role: str
    text: str
    timestamp: float
    metadata: dict[str, Any]


@dataclass
class VoiceSession:
    session_id: str
    created_at: float
    updated_at: float
    turns: list[dict[str, Any]]
    status: str = "open"


class VoiceStateStore:
    def __init__(self, runtime_dir: str | Path):
        self.base = Path(runtime_dir) / "voice"
        self.base.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.base / "sessions.json"
        self.settings_file = self.base / "settings.json"
        if not self.sessions_file.exists():
            self.sessions_file.write_text("{}", encoding="utf-8")
        if not self.settings_file.exists():
            self.settings_file.write_text(json.dumps({
                "wake_word": "jarvis",
                "mode": "push_to_talk",
                "stt_provider": "manual",
                "tts_provider": "console",
                "allow_system_actions": False,
            }, indent=2), encoding="utf-8")

    def load_sessions(self) -> dict[str, Any]:
        return json.loads(self.sessions_file.read_text(encoding="utf-8"))

    def save_sessions(self, sessions: dict[str, Any]) -> None:
        tmp = self.sessions_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.sessions_file)

    def load_settings(self) -> dict[str, Any]:
        return json.loads(self.settings_file.read_text(encoding="utf-8"))

    def save_settings(self, settings: dict[str, Any]) -> None:
        tmp = self.settings_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.settings_file)


class ManualSTT:
    name = "manual"
    def transcribe(self, text: str) -> str:
        return text.strip()


class ConsoleTTS:
    name = "console"
    def speak(self, text: str) -> dict[str, Any]:
        return {"provider": self.name, "text": text, "spoken": True}


class VoiceCommandRouter:
    def __init__(self):
        self.intent_map: list[tuple[str, str, dict[str, Any], bool]] = [
            ("status", "runtime.status", {}, False),
            ("health", "runtime.health", {}, False),
            ("diagnose", "runtime.diagnose", {}, False),
            ("metriken", "runtime.metrics", {}, False),
            ("metrics", "runtime.metrics", {}, False),
            ("notiz", "capture.note", {}, False),
            ("capture", "capture.note", {}, False),
            ("suche", "rag.search", {}, False),
            ("search", "rag.search", {}, False),
            ("frage", "ai.ask", {}, False),
            ("ask", "ai.ask", {}, False),
            ("agent", "agent.run", {}, True),
            ("workflow", "workflow.run", {}, True),
            ("shutdown", "runtime.down", {}, True),
            ("beenden", "runtime.down", {}, True),
        ]

    def parse(self, raw_text: str) -> VoiceCommand:
        text = raw_text.strip()
        low = text.lower()
        for marker, intent, defaults, approval in self.intent_map:
            if marker in low:
                args = dict(defaults)
                remainder = text
                if marker in low:
                    idx = low.find(marker)
                    remainder = text[idx + len(marker):].strip(" :,-")
                if intent == "capture.note":
                    args["text"] = remainder or text
                    args["title"] = "Voice Capture"
                elif intent == "rag.search":
                    args["query"] = remainder or text
                    args["limit"] = 5
                elif intent == "ai.ask":
                    args["prompt"] = remainder or text
                    args["task"] = "voice"
                elif intent == "agent.run":
                    args["objective"] = remainder or text
                    args["max_steps"] = 5
                elif intent == "workflow.run":
                    args["name"] = "voice_workflow"
                    args["objective"] = remainder or text
                return VoiceCommand(str(uuid.uuid4()), text, intent, 0.82, args, approval)
        return VoiceCommand(str(uuid.uuid4()), text, "ai.ask", 0.55, {"prompt": text, "task": "voice"}, False)


class VoiceRuntime:
    def __init__(self, runtime_dir: str | Path, executor: Callable[[VoiceCommand], Any] | None = None):
        self.store = VoiceStateStore(runtime_dir)
        self.router = VoiceCommandRouter()
        self.stt = ManualSTT()
        self.tts = ConsoleTTS()
        self.executor = executor

    def status(self) -> dict[str, Any]:
        sessions = self.store.load_sessions()
        settings = self.store.load_settings()
        return {
            "version": "11.4",
            "wake_word": settings.get("wake_word", "jarvis"),
            "mode": settings.get("mode", "push_to_talk"),
            "stt_provider": settings.get("stt_provider", self.stt.name),
            "tts_provider": settings.get("tts_provider", self.tts.name),
            "sessions": len(sessions),
            "open_sessions": len([s for s in sessions.values() if s.get("status") == "open"]),
        }

    def configure(self, **updates: Any) -> dict[str, Any]:
        settings = self.store.load_settings()
        allowed = {"wake_word", "mode", "stt_provider", "tts_provider", "allow_system_actions"}
        for key, value in updates.items():
            if key in allowed and value is not None:
                settings[key] = value
        self.store.save_settings(settings)
        return settings

    def open_session(self) -> dict[str, Any]:
        sessions = self.store.load_sessions()
        now = time.time()
        session = VoiceSession(str(uuid.uuid4()), now, now, [])
        sessions[session.session_id] = asdict(session)
        self.store.save_sessions(sessions)
        return asdict(session)

    def append_turn(self, session_id: str, role: str, text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        sessions = self.store.load_sessions()
        if session_id not in sessions:
            raise KeyError(f"unknown voice session: {session_id}")
        turn = VoiceTurn(str(uuid.uuid4()), role, text, time.time(), metadata or {})
        sessions[session_id]["turns"].append(asdict(turn))
        sessions[session_id]["updated_at"] = turn.timestamp
        self.store.save_sessions(sessions)
        return asdict(turn)

    def list_sessions(self) -> list[dict[str, Any]]:
        return list(self.store.load_sessions().values())

    def parse(self, text: str) -> dict[str, Any]:
        command = self.router.parse(self.stt.transcribe(text))
        return asdict(command)

    def say(self, text: str) -> dict[str, Any]:
        return self.tts.speak(text)

    def handle_text(self, text: str, session_id: str | None = None, auto_execute: bool = True) -> dict[str, Any]:
        if not session_id:
            session_id = self.open_session()["session_id"]
        self.append_turn(session_id, "user", text)
        command = self.router.parse(self.stt.transcribe(text))
        result: Any = None
        executed = False
        blocked = False
        if auto_execute and self.executor:
            settings = self.store.load_settings()
            if command.requires_approval and not settings.get("allow_system_actions", False):
                blocked = True
                result = {"status": "approval_required", "intent": command.intent, "args": command.args}
            else:
                result = self.executor(command)
                executed = True
        response_text = self._summarize_result(command, result, blocked)
        self.append_turn(session_id, "assistant", response_text, {"command": asdict(command), "executed": executed, "blocked": blocked})
        return {
            "session_id": session_id,
            "command": asdict(command),
            "executed": executed,
            "blocked": blocked,
            "result": result,
            "response": response_text,
        }

    def _summarize_result(self, command: VoiceCommand, result: Any, blocked: bool) -> str:
        if blocked:
            return f"Freigabe erforderlich: {command.intent}"
        if result is None:
            return f"Erkannt: {command.intent}"
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            if "status" in result:
                return f"{command.intent}: {result.get('status')}"
            if "answer" in result:
                return str(result["answer"])
        return f"{command.intent} ausgeführt"

# === DEPRECATED (Voice Control v20) =============================
# Dieses Modul ist abgeloest durch das konsolidierte Paket secondbrain.voice.
# Nutze: from secondbrain.voice import VoiceController, VoiceConfig
# Belassen, weil noch von Launchern/Skripten referenziert. Nicht erweitern.
# Siehe docs/VOICE_CONTROL_v20.md
# ===============================================================
