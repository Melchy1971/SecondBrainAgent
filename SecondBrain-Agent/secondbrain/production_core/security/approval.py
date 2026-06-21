from datetime import datetime, timezone
from uuid import uuid4


class ApprovalWorkflow:
    def __init__(self, store, audit):
        self.store = store
        self.audit = audit

    def request(self, actor: str, action: str, risk: str, payload: dict | None = None) -> dict:
        request = {
            "id": str(uuid4()),
            "actor": actor,
            "action": action,
            "risk": risk,
            "payload": payload or {},
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.append("approval_requests", request)
        self.audit.log(actor, "approval.request", action, {"risk": risk})
        return request

    def decide(self, request_id: str, decision: str, decided_by: str = "user") -> dict:
        requests = self.store.load("approval_requests", [])
        result = None
        updated = []
        for req in requests:
            if req["id"] == request_id:
                req = {**req, "status": decision, "decided_by": decided_by, "decided_at": datetime.now(timezone.utc).isoformat()}
                result = req
            updated.append(req)
        self.store.save("approval_requests", updated)
        self.audit.log(decided_by, "approval.decide", request_id, {"decision": decision}, result="success" if result else "not_found")
        return result or {"ok": False, "error": "approval_not_found"}

    def list(self) -> list[dict]:
        return self.store.load("approval_requests", [])
