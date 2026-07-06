"""v30.61 Agent Safety Layer - SafetyPolicy.

The policy is the single place that decides, for a given (action, risk level),
whether the action may run unattended, needs human approval, or is hard-blocked.
It has no side effects and does not touch the queue - it only returns a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .risk import RISK_LEVELS, level_rank, normalize_level

# Possible policy verdicts.
ALLOW = "allow"
REQUIRE_APPROVAL = "require_approval"
BLOCK = "block"


@dataclass(frozen=True)
class PolicyVerdict:
    action: str
    risk_level: str
    outcome: str  # one of ALLOW / REQUIRE_APPROVAL / BLOCK
    reason: str

    @property
    def allowed(self) -> bool:
        return self.outcome == ALLOW

    @property
    def requires_approval(self) -> bool:
        return self.outcome == REQUIRE_APPROVAL

    @property
    def blocked(self) -> bool:
        return self.outcome == BLOCK

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "risk_level": self.risk_level,
            "outcome": self.outcome,
            "reason": self.reason,
        }


@dataclass
class SafetyPolicy:
    """Rule set governing which risk levels need approval.

    Defaults implement the v30.61 brief: ``read`` and ``low`` run unattended,
    everything at ``medium`` and above requires approval, nothing is hard-blocked
    unless explicitly configured. All of it is overridable via ``from_config``.
    """

    auto_allow_levels: set[str] = field(default_factory=lambda: {"read", "low"})
    approval_levels: set[str] = field(
        default_factory=lambda: {"medium", "high", "destructive", "external"}
    )
    blocked_levels: set[str] = field(default_factory=set)
    blocked_actions: set[str] = field(default_factory=set)
    allowlist_actions: set[str] = field(default_factory=set)

    @classmethod
    def from_config(cls, config: dict | None) -> "SafetyPolicy":
        config = config or {}
        policy = cls()
        if "auto_allow_levels" in config:
            policy.auto_allow_levels = {normalize_level(x) for x in config["auto_allow_levels"]}
        if "approval_levels" in config:
            policy.approval_levels = {normalize_level(x) for x in config["approval_levels"]}
        if "blocked_levels" in config:
            policy.blocked_levels = {normalize_level(x) for x in config["blocked_levels"]}
        policy.blocked_actions = {str(x).lower() for x in config.get("blocked_actions", [])}
        policy.allowlist_actions = {str(x).lower() for x in config.get("allowlist_actions", [])}
        return policy

    def evaluate(self, action: str, risk_level: str) -> PolicyVerdict:
        act = (action or "").strip().lower()
        level = normalize_level(risk_level)

        if act in self.blocked_actions:
            return PolicyVerdict(action, level, BLOCK, "action_on_blocklist")
        if self.allowlist_actions and act not in self.allowlist_actions:
            return PolicyVerdict(action, level, BLOCK, "action_not_on_allowlist")
        if level in self.blocked_levels:
            return PolicyVerdict(action, level, BLOCK, f"risk_level_blocked:{level}")

        if level in self.auto_allow_levels:
            return PolicyVerdict(action, level, ALLOW, f"auto_allowed:{level}")
        if level in self.approval_levels:
            return PolicyVerdict(action, level, REQUIRE_APPROVAL, f"approval_required:{level}")

        # Any level neither explicitly auto-allowed nor approval-listed is
        # treated as approval-required: safe-by-default. This also covers a
        # misconfigured policy that forgot a level.
        return PolicyVerdict(action, level, REQUIRE_APPROVAL, f"default_requires_approval:{level}")

    def to_dict(self) -> dict:
        return {
            "risk_levels": list(RISK_LEVELS),
            "auto_allow_levels": sorted(self.auto_allow_levels, key=level_rank),
            "approval_levels": sorted(self.approval_levels, key=level_rank),
            "blocked_levels": sorted(self.blocked_levels, key=level_rank),
            "blocked_actions": sorted(self.blocked_actions),
            "allowlist_actions": sorted(self.allowlist_actions),
        }
