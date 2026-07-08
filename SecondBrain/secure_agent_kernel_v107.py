from __future__ import annotations

from pathlib import Path
from .agent_kernel_v106 import AgentKernel
from .security_v107 import PolicyEngine, ApprovalStore, AuditLogger, asdict

class SecureAgentKernel(AgentKernel):
    """v10.7 wrapper: applies policy, approval store and audit trail before v10.6 job handlers run."""
    def __init__(self, runtime_dir: str | Path, policy: PolicyEngine | None = None):
        super().__init__(runtime_dir)
        self.policy_v107 = policy or PolicyEngine(max_level=2)
        self.approvals_v107 = ApprovalStore(Path(runtime_dir) / "approvals_v107.json")
        self.audit_v107 = AuditLogger(Path(runtime_dir) / "audit_v107.jsonl")
        self.handler_meta: dict[str, tuple[int | str, int]] = {}

    def register_handler(self, action: str, handler, level: int | str = 1, risk_score: int = 0):
        self.handlers[action] = (handler, level, risk_score)
        self.handler_meta[action] = (level, risk_score)

    def _guarded_handlers(self):
        guarded = {}
        for action, (handler, level, _legacy_risk) in self.handlers.items():
            def make_guard(a, h, l):
                def wrapped(payload):
                    decision = self.policy_v107.evaluate(a, l, payload or {}, (payload or {}).get("approval_id"), self.approvals_v107)
                    self.audit_v107.append("agent_decision", {"action": a, "decision": decision.reason, "risk": asdict(decision.risk), "approval_id": decision.approval_id, "payload": payload or {}})
                    if not decision.allowed:
                        raise PermissionError(decision.reason if not decision.approval_id else f"approval_required:{decision.approval_id}")
                    result = h(payload or {})
                    self.audit_v107.append("agent_executed", {"action": a, "result": result})
                    return result
                return wrapped
            guarded[action] = make_guard(action, handler, level)
        return guarded
