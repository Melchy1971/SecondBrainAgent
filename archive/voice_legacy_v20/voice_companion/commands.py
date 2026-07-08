class VoiceCommandRouter:
    SAFE_COMMANDS = {
        "status": "os.status",
        "zeige status": "os.status",
        "briefing": "assistant.briefing",
        "notiz": "capture.note",
        "suche": "knowledge.search",
        "hilfe": "voice.help",
    }

    RISKY_KEYWORDS = ["lösche", "delete", "sende", "send", "kaufe", "execute", "system"]

    def parse(self, text: str) -> dict:
        lower = text.lower().strip()
        risky = any(k in lower for k in self.RISKY_KEYWORDS)
        target = None
        for phrase, command in self.SAFE_COMMANDS.items():
            if phrase in lower:
                target = command
                break
        return {
            "text": text,
            "target": target or "conversation.reply",
            "requires_approval": risky,
            "risk": "high" if risky else "low",
        }

    def execute(self, parsed: dict) -> dict:
        if parsed.get("requires_approval"):
            return {"ok": False, "status": "approval_required", "parsed": parsed}
        return {"ok": True, "status": "executed", "target": parsed["target"], "result": f"Executed {parsed['target']}"}
