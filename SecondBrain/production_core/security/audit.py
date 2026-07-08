from datetime import datetime, timezone
from uuid import uuid4


SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "value"}


class AuditTrail:
    def __init__(self, store):
        self.store = store

    def log(self, actor: str, action: str, target: str, metadata: dict | None = None, result: str = "success") -> dict:
        event = {
            "id": str(uuid4()),
            "actor": actor,
            "action": action,
            "target": target,
            "metadata": self._redact(metadata or {}),
            "result": result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("audit_log", event)

    def events(self, limit: int = 100) -> list[dict]:
        return self.store.load("audit_log", [])[-limit:]

    def _redact(self, value):
        if isinstance(value, dict):
            return {k: ("***REDACTED***" if k.lower() in SENSITIVE_KEYS else self._redact(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact(v) for v in value]
        return value
