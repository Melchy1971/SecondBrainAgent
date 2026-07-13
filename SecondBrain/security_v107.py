from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import time
import uuid

LEVELS = {"read": 1, "write": 2, "execute": 3, "system": 4}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*([^\s]+)"),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
]
PII_PATTERNS = [
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
    re.compile(r"\b(?:\+?49|0)[\s-]?(?:\d[\s-]?){7,}\b"),
]

@dataclass(frozen=True)
class RiskAssessment:
    action: str
    level: int
    score: int
    reasons: list[str] = field(default_factory=list)
    requires_approval: bool = False
    blocked: bool = False

@dataclass(frozen=True)
class SecurityDecision:
    action: str
    allowed: bool
    reason: str
    risk: RiskAssessment
    approval_id: str | None = None

class AuditLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, event_type: str, payload: dict[str, Any]) -> None:
        record = {
            "ts": time.time(),
            "event_type": event_type,
            "payload": sanitize_payload(payload),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def read(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

class ApprovalStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def create(self, action: str, payload: dict[str, Any], risk: RiskAssessment) -> str:
        data = self._load()
        approval_id = uuid.uuid4().hex
        data[approval_id] = {
            "approval_id": approval_id,
            "action": action,
            "payload_hash": stable_hash(sanitize_payload(payload)),
            "risk": asdict(risk),
            "status": "pending",
            "created_at": time.time(),
        }
        self._save(data)
        return approval_id

    def approve(self, approval_id: str) -> None:
        data = self._load()
        if approval_id not in data:
            raise KeyError("unknown_approval_id")
        data[approval_id]["status"] = "approved"
        data[approval_id]["approved_at"] = time.time()
        self._save(data)

    def is_approved(self, approval_id: str | None) -> bool:
        if not approval_id:
            return False
        return self._load().get(approval_id, {}).get("status") == "approved"

    def pending(self) -> list[dict[str, Any]]:
        return [v for v in self._load().values() if v.get("status") == "pending"]

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

class RiskScorer:
    def score(self, action: str, level: int | str, payload: dict[str, Any] | None = None) -> RiskAssessment:
        payload = payload or {}
        numeric_level = LEVELS.get(level.lower(), 4) if isinstance(level, str) else int(level)
        score = numeric_level * 15
        reasons = [f"level:{numeric_level}"]
        action_l = action.lower()
        if any(x in action_l for x in ["delete", "trash", "remove", "exec", "shell", "system"]):
            score += 35; reasons.append("destructive_or_execution_action")
        if any(x in action_l for x in ["send", "email", "calendar.create", "publish"]):
            score += 20; reasons.append("external_side_effect")
        text = json.dumps(payload, ensure_ascii=False)
        if contains_secret(text):
            score += 45; reasons.append("secret_detected")
        if contains_pii(text):
            score += 15; reasons.append("pii_detected")
        score = min(score, 100)
        return RiskAssessment(action=action, level=numeric_level, score=score, reasons=reasons, requires_approval=score >= 60 or numeric_level >= 3, blocked=score >= 95)

class PolicyEngine:
    def __init__(self, *, max_level: int | str = 2, approval_threshold: int = 60, block_threshold: int = 95, blocked_actions: list[str] | None = None):
        self.max_level = LEVELS.get(max_level.lower(), 2) if isinstance(max_level, str) else int(max_level)
        self.approval_threshold = approval_threshold
        self.block_threshold = block_threshold
        self.blocked_actions = set(blocked_actions or [])
        self.scorer = RiskScorer()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PolicyEngine":
        data = data or {}
        return cls(
            max_level=data.get("max_level", 2),
            approval_threshold=int(data.get("approval_threshold", 60)),
            block_threshold=int(data.get("block_threshold", 95)),
            blocked_actions=list(data.get("blocked_actions", []) or []),
        )

    def evaluate(self, action: str, level: int | str, payload: dict[str, Any] | None = None, approval_id: str | None = None, approvals: ApprovalStore | None = None) -> SecurityDecision:
        risk = self.scorer.score(action, level, payload)
        if action in self.blocked_actions:
            return SecurityDecision(action, False, "blocked_action", risk)
        if risk.level > self.max_level:
            return SecurityDecision(action, False, "level_exceeds_policy", risk)
        if risk.score >= self.block_threshold or risk.blocked:
            return SecurityDecision(action, False, "risk_blocked", risk)
        needs_approval = risk.score >= self.approval_threshold or risk.requires_approval
        if needs_approval and not (approvals and approvals.is_approved(approval_id)):
            pending_id = approvals.create(action, payload or {}, risk) if approvals else None
            return SecurityDecision(action, False, "approval_required", risk, pending_id)
        return SecurityDecision(action, True, "allowed", risk, approval_id)

class SecureCommandGateway:
    def __init__(self, runtime_dir: str | Path, policy: PolicyEngine | None = None):
        self.runtime_dir = Path(runtime_dir)
        self.audit = AuditLogger(self.runtime_dir / "audit_v107.jsonl")
        self.approvals = ApprovalStore(self.runtime_dir / "approvals_v107.json")
        self.policy = policy or PolicyEngine()
        self.handlers: dict[str, tuple[Any, int | str]] = {}

    def register(self, action: str, handler, level: int | str = "read") -> None:
        self.handlers[action] = (handler, level)

    def execute(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if action not in self.handlers:
            self.audit.append("blocked", {"action": action, "reason": "missing_handler", "payload": payload})
            return {"ok": False, "reason": "missing_handler"}
        handler, level = self.handlers[action]
        approval_id = payload.get("approval_id")
        decision = self.policy.evaluate(action, level, payload, approval_id, self.approvals)
        self.audit.append("decision", {"action": action, "decision": decision.reason, "risk": asdict(decision.risk), "approval_id": decision.approval_id, "payload": payload})
        if not decision.allowed:
            return {"ok": False, "reason": decision.reason, "risk_score": decision.risk.score, "approval_id": decision.approval_id}
        result = handler(payload)
        self.audit.append("executed", {"action": action, "result": result})
        return {"ok": True, "result": result, "risk_score": decision.risk.score}

def contains_secret(text: str) -> bool:
    return any(p.search(text or "") for p in SECRET_PATTERNS)

def contains_pii(text: str) -> bool:
    return any(p.search(text or "") for p in PII_PATTERNS)

def sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("***REDACTED***" if re.search(r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)", str(k)) else sanitize_payload(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_payload(v) for v in value]
    if isinstance(value, str):
        redacted = value
        for p in SECRET_PATTERNS:
            redacted = p.sub(lambda m: m.group(0).split(m.group(2))[0] + "***REDACTED***" if len(m.groups()) >= 2 else "***REDACTED***", redacted)
        return redacted
    return value

def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
