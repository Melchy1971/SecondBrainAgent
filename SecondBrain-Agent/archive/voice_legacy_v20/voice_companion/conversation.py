from datetime import datetime, timezone
from uuid import uuid4


class RealtimeConversation:
    def __init__(self, store, memory, router, tts):
        self.store = store
        self.memory = memory
        self.router = router
        self.tts = tts

    def start_session(self, title: str = "Voice Session") -> dict:
        session = {
            "id": str(uuid4()),
            "title": title,
            "status": "active",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.save("active_session", session)
        return self.store.append("sessions", session)

    def handle_text(self, text: str) -> dict:
        session = self.store.load("active_session", None) or self.start_session()
        self.memory.remember(text, "user_utterance")
        parsed = self.router.parse(text)
        execution = self.router.execute(parsed)
        reply_text = "Freigabe erforderlich." if execution["status"] == "approval_required" else execution["result"]
        speech = self.tts.synthesize(reply_text)
        turn = {
            "id": str(uuid4()),
            "session_id": session["id"],
            "user_text": text,
            "parsed": parsed,
            "execution": execution,
            "reply": reply_text,
            "speech": speech,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.append("turns", turn)
        self.memory.remember(reply_text, "assistant_reply")
        return turn

    def interrupt(self, reason: str = "user_stop") -> dict:
        event = {
            "id": str(uuid4()),
            "type": "interrupt",
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.save("active_session", {})
        return self.store.append("events", event)

    def sessions(self) -> list[dict]:
        return self.store.load("sessions", [])

    def turns(self) -> list[dict]:
        return self.store.load("turns", [])
