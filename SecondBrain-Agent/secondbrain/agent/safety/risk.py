"""v30.61 Agent Safety Layer - RiskClassifier.

Maps agent actions to a single canonical risk level. The six levels are the
contract defined by the v30.61 brief; every downstream policy decision keys off
them.

The classifier is deliberately data-driven: an explicit action -> level table
handles the known agent commands, a keyword table handles free-form or unknown
actions, and everything else falls back to ``low`` so that an unclassified
write can never silently execute at ``read`` privilege.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Ordered from least to most dangerous. Order matters: it is used to resolve
# ambiguous keyword matches (the most dangerous match wins) and to compare
# levels numerically.
RISK_LEVELS: tuple[str, ...] = ("read", "low", "medium", "high", "destructive", "external")
RISK_ORDER: dict[str, int] = {level: index for index, level in enumerate(RISK_LEVELS)}

UNKNOWN_ACTION_LEVEL = "low"


def normalize_level(level: str) -> str:
    """Return a known risk level, defaulting unknown strings to ``low``.

    The native queue historically wrote ``risk_level="write"``; map that legacy
    value onto ``medium`` so old records classify consistently.
    """

    value = (level or "").strip().lower()
    if value in RISK_ORDER:
        return value
    if value == "write":
        return "medium"
    if value in {"execute", "system", "critical"}:
        return "destructive"
    return UNKNOWN_ACTION_LEVEL


def level_rank(level: str) -> int:
    return RISK_ORDER[normalize_level(level)]


# Explicit mapping for the canonical agent action verbs. Keys are matched
# exactly (case-insensitive) against the action string.
DEFAULT_ACTION_RISK: dict[str, str] = {
    # read-only
    "read": "read",
    "file.read": "read",
    "list": "read",
    "show": "read",
    "status": "read",
    "search": "read",
    "get": "read",
    # low-impact writes inside the vault
    "note.append": "low",
    "note.create": "low",
    "journal.write": "low",
    "tag.write": "low",
    # file changes -> medium (Dateiaenderungen)
    "file.write": "medium",
    "file.modify": "medium",
    "file.move": "medium",
    "file.rename": "medium",
    # calendar changes (Kalender aendern)
    "calendar.write": "high",
    "calendar.modify": "high",
    "calendar.delete": "high",
    # email (E-Mail senden)
    "email.send": "high",
    "mail.send": "high",
    # index repair (Index-Reparatur)
    "index.repair": "high",
    "index.rebuild": "high",
    # bulk import (Bulk Import)
    "import.bulk": "high",
    "bulk.import": "high",
    # deletions (Loeschaktionen)
    "file.delete": "destructive",
    "delete": "destructive",
    "note.delete": "destructive",
    # database migration (Datenbankmigration)
    "db.migrate": "destructive",
    "database.migrate": "destructive",
    "migration.apply": "destructive",
    # shell commands (Shell Commands)
    "shell.exec": "destructive",
    "shell.run": "destructive",
    "command.run": "destructive",
    # external API calls (externe API-Aufrufe)
    "api.external": "external",
    "http.request": "external",
    "external.call": "external",
    "webhook.send": "external",
}

# Keyword fallback for free-form actions. Checked when the exact action is not
# in the table. Each keyword maps to a level; when several keywords match, the
# highest risk wins.
DEFAULT_KEYWORD_RISK: dict[str, str] = {
    "delete": "destructive",
    "drop": "destructive",
    "purge": "destructive",
    "migrate": "destructive",
    "migration": "destructive",
    "shell": "destructive",
    "exec": "destructive",
    "rm ": "destructive",
    "external": "external",
    "http": "external",
    "https": "external",
    "webhook": "external",
    "api": "external",
    "email": "high",
    "mail": "high",
    "calendar": "high",
    "repair": "high",
    "reindex": "high",
    "bulk": "high",
    "write": "medium",
    "modify": "medium",
    "update": "medium",
    "rename": "medium",
    "move": "medium",
    "append": "low",
    "note": "low",
    "journal": "low",
    "read": "read",
    "list": "read",
    "status": "read",
    "search": "read",
}


@dataclass
class RiskClassifier:
    """Resolve an action string to one of :data:`RISK_LEVELS`."""

    action_risk: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ACTION_RISK))
    keyword_risk: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KEYWORD_RISK))
    default_level: str = UNKNOWN_ACTION_LEVEL

    @classmethod
    def from_config(cls, config: dict | None) -> "RiskClassifier":
        config = config or {}
        classifier = cls()
        classifier.action_risk.update(
            {str(k).lower(): normalize_level(v) for k, v in (config.get("action_risk") or {}).items()}
        )
        classifier.keyword_risk.update(
            {str(k).lower(): normalize_level(v) for k, v in (config.get("keyword_risk") or {}).items()}
        )
        if config.get("default_level"):
            classifier.default_level = normalize_level(config["default_level"])
        return classifier

    def classify(self, action: str, *, hint: str | None = None) -> str:
        """Return the risk level for ``action``.

        ``hint`` is an optional caller-supplied level; when it is a known level
        it takes precedence over the tables, which lets a tool declare its own
        risk explicitly while still being normalized into the contract.
        """

        if hint:
            normalized = normalize_level(hint)
            if (hint or "").strip().lower() in RISK_ORDER or (hint or "").strip().lower() == "write":
                return normalized

        key = (action or "").strip().lower()
        if key in self.action_risk:
            return normalize_level(self.action_risk[key])

        matched: str | None = None
        for keyword, level in self.keyword_risk.items():
            if keyword in key:
                level = normalize_level(level)
                if matched is None or level_rank(level) > level_rank(matched):
                    matched = level
        if matched is not None:
            return matched
        return normalize_level(self.default_level)
