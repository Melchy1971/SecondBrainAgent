"""Support/diagnostic center delta (v31.00).

The support bundle, recursive redaction and diagnostics collectors already
exist (``support/bundle.py``, ``support/redaction.py``, ``diagnostics.py``).
This module adds the missing pieces from the v31.00 brief without rebuilding
them:

* a **redaction report** listing which field paths were removed (values never
  shown), reusing the existing redactor;
* **stable error codes** and known-error detection so recurring failures get a
  consistent, greppable identifier and a remediation hint;
* **repair actions** where any writing/destructive repair produces an approval
  request instead of running, never auto-deletes data, and is audited;
* a **bundle validator** that fails if any residual secret/PII survived, run
  before export.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
from uuid import uuid4

from secondbrain.support.redaction import REDACTED, is_sensitive_key, redact_text

__all__ = [
    "RedactionReport", "build_redaction_report", "classify_error", "detect_known_errors",
    "RepairAction", "REPAIR_ACTIONS", "RepairCenter", "validate_bundle", "KNOWN_ERRORS",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- redaction report -------------------------------------------------------

@dataclass
class RedactionReport:
    removed_fields: list[str] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.removed_fields)

    def to_dict(self) -> dict[str, Any]:
        return {"removed_fields": list(self.removed_fields), "reasons": dict(self.reasons),
                "count": self.count}


def build_redaction_report(data: Any, *, _path: str = "", _report: RedactionReport | None = None) -> RedactionReport:
    """Walk a *pre-redaction* structure and list field paths that would be
    removed. Never records the sensitive value itself - only its path and the
    reason (key-based or value-based)."""
    report = _report or RedactionReport()
    if isinstance(data, Mapping):
        for key, value in data.items():
            path = f"{_path}.{key}" if _path else str(key)
            if is_sensitive_key(str(key)):
                report.removed_fields.append(path)
                report.reasons[path] = "sensitive_key"
            else:
                build_redaction_report(value, _path=path, _report=report)
    elif isinstance(data, (list, tuple)):
        for i, item in enumerate(data):
            build_redaction_report(item, _path=f"{_path}[{i}]", _report=report)
    elif isinstance(data, str):
        if redact_text(data) != data:
            report.removed_fields.append(_path or "<root>")
            report.reasons[_path or "<root>"] = "secret_value"
    return report


# --- stable error codes -----------------------------------------------------

# (code, compiled pattern, remediation). Codes are stable identifiers - never
# renumber an existing one.
KNOWN_ERRORS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("SB-DB-001", re.compile(r"(?i)connection refused|could not connect.*postgres|database is not available"),
     "PostgreSQL prüfen (Dienst, DSN, Netzwerk)."),
    ("SB-DB-002", re.compile(r"(?i)pgvector|vector extension|index.*corrupt"),
     "pgvector-Extension/Index prüfen, ggf. reindex."),
    ("SB-MIG-001", re.compile(r"(?i)migration.*(failed|pending|mismatch)"),
     "Migrationsstand prüfen, Migration ausführen."),
    ("SB-PROV-001", re.compile(r"(?i)provider.*(unavailable|timeout|429|rate limit)"),
     "Provider-Status/Rate-Limit prüfen."),
    ("SB-CONN-001", re.compile(r"(?i)oauth|token expired|unauthorized|invalid_grant"),
     "Connector neu authentifizieren."),
    ("SB-QUEUE-001", re.compile(r"(?i)queue.*(stuck|growing|backlog|deadlock)"),
     "Queue/Worker prüfen, ggf. Recovery."),
    ("SB-DISK-001", re.compile(r"(?i)no space left|disk full|quota exceeded"),
     "Speicherplatz freigeben."),
)
_UNKNOWN = "SB-GEN-000"


def classify_error(text: str) -> dict[str, str]:
    """Return a stable error code + remediation for a message. Unmatched errors
    get the generic ``SB-GEN-000`` so every error still has a code."""
    safe = redact_text(str(text or ""))
    for code, pattern, remediation in KNOWN_ERRORS:
        if pattern.search(safe):
            return {"code": code, "remediation": remediation}
    return {"code": _UNKNOWN, "remediation": "Support Bundle erzeugen und prüfen."}


def detect_known_errors(recent_errors: Iterable[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for err in recent_errors:
        classified = classify_error(err)
        out.append({"message": redact_text(str(err))[:200], **classified})
    return out


# --- repair actions (approval-gated, audited) -------------------------------

@dataclass(frozen=True)
class RepairAction:
    action_id: str
    title: str
    writing: bool               # mutates state -> needs approval
    destructive: bool = False   # deletes data -> never auto, always approval

    def to_dict(self) -> dict[str, Any]:
        return {"action_id": self.action_id, "title": self.title,
                "writing": self.writing, "destructive": self.destructive}


REPAIR_ACTIONS: dict[str, RepairAction] = {
    "validate_index": RepairAction("validate_index", "Index validieren", writing=False),
    "check_queue": RepairAction("check_queue", "Queue prüfen", writing=False),
    "validate_config": RepairAction("validate_config", "Konfiguration validieren", writing=False),
    "check_migration": RepairAction("check_migration", "Migrationstatus prüfen", writing=False),
    "check_backup": RepairAction("check_backup", "Backupstatus prüfen", writing=False),
    "clear_cache": RepairAction("clear_cache", "Cache leeren", writing=True),
    "reauth_connector": RepairAction("reauth_connector", "Connector neu authentifizieren", writing=True),
}


class RepairCenter:
    """Proposes repair actions. Read-only checks run immediately; writing or
    destructive repairs return an approval request and are never executed here.
    Every proposal is audited."""

    def __init__(self) -> None:
        self._audit: list[dict[str, Any]] = []

    def propose(self, action_id: str, *, workspace_id: str = "") -> dict[str, Any]:
        action = REPAIR_ACTIONS.get(action_id)
        if action is None:
            raise KeyError(f"unknown_repair_action:{action_id}")
        needs_approval = action.writing or action.destructive
        record = {
            "at": _now(), "action_id": action.action_id, "workspace_id": workspace_id,
            "requires_approval": needs_approval, "executed": False,
            "auto_delete": False,  # repairs never auto-delete data
            "correlation_id": uuid4().hex,
        }
        self._audit.append(record)
        return {
            "action": action.to_dict(),
            "requires_approval": needs_approval,
            "executed": False,
            "route": "approval_inbox" if needs_approval else "run_readonly",
            "correlation_id": record["correlation_id"],
        }

    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit)


# --- bundle validation ------------------------------------------------------

def validate_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Fail if any residual secret/PII survived redaction. Returns ok + the
    field paths that still look sensitive (paths only, never values)."""
    residual = build_redaction_report(bundle)
    ok = residual.count == 0
    return {"ok": ok, "residual_fields": residual.removed_fields, "count": residual.count}
