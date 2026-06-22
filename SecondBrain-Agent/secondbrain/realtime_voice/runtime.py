import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


RISKY_KEYWORDS = ["lösche", "delete", "sende", "send", "kaufe", "purchase", "terminal", "shell", "system"]
SAFE_INTENTS = {
    "status": "system.status",
    "hilfe": "voice.help",
    "notiz": "capture.note",
    "suche": "rag.search",
    "briefing": "assistant.briefing",
}


class RealtimeVoiceRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "realtime_voice"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "voice.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_turns (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_text TEXT NOT NULL,
                    intent TEXT,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assistant_text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_memory (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path)}

    def status(self):
        self.migrate()
        with self.connect() as conn:
            sessions = conn.execute("SELECT COUNT(*) c FROM voice_sessions").fetchone()["c"]
            turns = conn.execute("SELECT COUNT(*) c FROM voice_turns").fetchone()["c"]
            events = conn.execute("SELECT COUNT(*) c FROM voice_events").fetchone()["c"]
            memory = conn.execute("SELECT COUNT(*) c FROM voice_memory").fetchone()["c"]
        return {
            "version": "16.8",
            "sessions": sessions,
            "turns": turns,
            "events": events,
            "memory": memory,
            "adapters": ["wake_word_stub", "manual_stream_stt", "console_tts"],
        }

    def start_session(self, title="Voice Session"):
        self.migrate()
        session = {
            "id": str(uuid4()),
            "title": title,
            "status": "active",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": None,
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO voice_sessions(id, title, status, started_at, ended_at) VALUES (:id, :title, :status, :started_at, :ended_at)",
                session
            )
            conn.commit()
        self.event(session["id"], "session.started", {"title": title})
        return session

    def active_session(self):
        self.migrate()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM voice_sessions WHERE status='active' ORDER BY started_at DESC LIMIT 1").fetchone()
        return dict(row) if row else self.start_session()

    def stop_session(self):
        session = self.active_session()
        with self.connect() as conn:
            conn.execute(
                "UPDATE voice_sessions SET status='stopped', ended_at=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), session["id"])
            )
            conn.commit()
        self.event(session["id"], "session.stopped", {})
        return {"ok": True, "session_id": session["id"], "status": "stopped"}

    def event(self, session_id, event_type, payload):
        item = {
            "id": str(uuid4()),
            "session_id": session_id,
            "event_type": event_type,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO voice_events(id, session_id, event_type, payload_json, created_at) VALUES (:id, :session_id, :event_type, :payload_json, :created_at)",
                item
            )
            conn.commit()
        return item

    def wake_detect(self, text, wake_words=None):
        wake_words = wake_words or ["jarvis", "secondbrain"]
        lower = text.lower().strip()
        for word in wake_words:
            if lower.startswith(word):
                return {"detected": True, "wake_word": word, "command_text": lower[len(word):].strip()}
        return {"detected": False, "wake_word": None, "command_text": text}

    def transcribe(self, chunks):
        text = " ".join([c.strip() for c in chunks if c.strip()])
        return {"engine": "manual_stream_stt", "chunks": len(chunks), "text": text}

    def synthesize(self, text):
        return {"engine": "console_tts", "text": text, "audio_ref": f"voice://tts/{abs(hash(text))}", "status": "ready"}

    def parse_intent(self, text):
        lower = text.lower()
        risk = "high" if any(k in lower for k in RISKY_KEYWORDS) else "low"
        intent = "conversation.reply"
        for key, value in SAFE_INTENTS.items():
            if key in lower:
                intent = value
                break
        requires_approval = risk == "high"
        return {"text": text, "intent": intent, "risk": risk, "requires_approval": requires_approval}

    def remember(self, text, kind="utterance"):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "text": text,
            "kind": kind,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO voice_memory(id, text, kind, created_at) VALUES (:id, :text, :kind, :created_at)",
                item
            )
            conn.commit()
        return item

    def recall(self, query):
        self.migrate()
        q = f"%{query.lower()}%"
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM voice_memory WHERE lower(text) LIKE ? OR lower(kind) LIKE ? ORDER BY created_at DESC",
                (q, q)
            ).fetchall()
        return [dict(r) for r in rows]

    def handle_text(self, text):
        session = self.active_session()
        parsed = self.parse_intent(text)
        if parsed["requires_approval"]:
            assistant = "Freigabe erforderlich."
            status = "approval_required"
        elif parsed["intent"] == "system.status":
            assistant = "Systemstatus verfügbar."
            status = "executed"
        elif parsed["intent"] == "capture.note":
            self.remember(text, "voice_note")
            assistant = "Notiz gespeichert."
            status = "executed"
        elif parsed["intent"] == "rag.search":
            assistant = "Suche vorbereitet."
            status = "executed"
        elif parsed["intent"] == "assistant.briefing":
            assistant = "Briefing vorbereitet."
            status = "executed"
        else:
            assistant = f"Verstanden: {text}"
            status = "executed"
        turn = {
            "id": str(uuid4()),
            "session_id": session["id"],
            "user_text": text,
            "intent": parsed["intent"],
            "risk": parsed["risk"],
            "status": status,
            "assistant_text": assistant,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO voice_turns(id, session_id, user_text, intent, risk, status, assistant_text, created_at) VALUES (:id, :session_id, :user_text, :intent, :risk, :status, :assistant_text, :created_at)",
                turn
            )
            conn.commit()
        self.event(session["id"], "turn.completed", turn)
        tts = self.synthesize(assistant)
        return {"turn": turn, "parsed": parsed, "tts": tts}

    def wake_and_handle(self, text):
        wake = self.wake_detect(text)
        if not wake["detected"]:
            return {"ok": False, "reason": "wake_word_not_detected", "wake": wake}
        result = self.handle_text(wake["command_text"])
        return {"ok": True, "wake": wake, "result": result}

    def interrupt(self, reason="user_stop"):
        session = self.active_session()
        event = self.event(session["id"], "interrupt", {"reason": reason})
        return {"ok": True, "event": event}

    def sessions(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM voice_sessions ORDER BY started_at DESC").fetchall()]

    def turns(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM voice_turns ORDER BY created_at DESC").fetchall()]

    def events(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM voice_events ORDER BY created_at DESC").fetchall()]
