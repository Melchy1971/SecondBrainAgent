from dataclasses import dataclass, field
from typing import Iterable

LEVELS = {"read": 1, "write": 2, "execute": 3, "system": 4}

@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    level: int
    action: str
    reason: str
    requires_approval: bool = False
    risk_score: int = 0

@dataclass
class PermissionPolicy:
    max_level: int = 1
    require_approval_from_level: int = 3
    blocked_actions: set[str] = field(default_factory=set)
    allowed_actions: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: dict | None) -> "PermissionPolicy":
        data = data or {}
        max_level = data.get("max_level", data.get("permission_level", 1))
        if isinstance(max_level, str):
            max_level = LEVELS.get(max_level.lower(), 1)
        approval = data.get("require_approval_from_level", 3)
        if isinstance(approval, str):
            approval = LEVELS.get(approval.lower(), 3)
        return cls(
            max_level=int(max_level),
            require_approval_from_level=int(approval),
            blocked_actions=set(data.get("blocked_actions", []) or []),
            allowed_actions=set(data.get("allowed_actions", []) or []),
        )

    def evaluate(self, action: str, level: int | str, risk_score: int = 0) -> PermissionDecision:
        if isinstance(level, str):
            level = LEVELS.get(level.lower(), 4)
        if action in self.blocked_actions:
            return PermissionDecision(False, int(level), action, "blocked_action", False, risk_score)
        if self.allowed_actions and action not in self.allowed_actions:
            return PermissionDecision(False, int(level), action, "not_in_allowlist", False, risk_score)
        if int(level) > self.max_level:
            return PermissionDecision(False, int(level), action, "level_exceeds_policy", False, risk_score)
        approval = int(level) >= self.require_approval_from_level or risk_score >= 70
        return PermissionDecision(True, int(level), action, "allowed", approval, risk_score)
