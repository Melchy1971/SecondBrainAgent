"""Append-only Audit Event Store mit Query und JSON-Export.

Jede Agent-/Connector-/Import-Aktion erhält hier ihren Audit-Eintrag.
Pfad: runtime/observability/audit_events.jsonl. Alle Einträge sind redacted.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.observability.redaction import RedactionMiddleware

SCHEMA = "secondbrain.observability.audit_event.v1"


@dataclass(frozen=True)
class AuditEvent:
    actor: str            # z.B. "agent", "connector:m365", "import", "user", "gui"
    action: str           # z.B. "import.file", "agent.plan.start", "connector.sync"
    resource: str = ""    # betroffene Ressource (Pfad, Dokument-ID, ...)
    status: str = "ok"    # ok | failed | denied | pending
    severity: str = "info"  # info | warning | critical
    correlation_id: str = ""
    job_id: str = ""
    plan_id: str = ""
    sync_id: str = ""
    category: str = ""    # Fehlerkategorie (taxonomy), nur bei status=failed
    detail: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        record = {"schema": SCHEMA, "ts": datetime.now(timezone.utc).isoformat(), **asdict(self)}
        return {key: value for key, value in record.items() if value not in ("", None, {})}


class AuditEventStore:
    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root)
        self.path = self.project_root / "runtime" / "observability" / "audit_events.jsonl"
        self.redaction = RedactionMiddleware()

    def append(self, event: AuditEvent) -> dict[str, Any]:
        record = self.redaction.redact_payload(event.to_record())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def record(self, actor: str, action: str, **kwargs: Any) -> dict[str, Any]:
        return self.append(AuditEvent(actor=actor, action=action, **kwargs))

    def _iter(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def query(
        self,
        *,
        actor: str | None = None,
        action_prefix: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        correlation_id: str | None = None,
        job_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        result = []
        for record in self._iter():
            if actor and record.get("actor") != actor:
                continue
            if action_prefix and not str(record.get("action", "")).startswith(action_prefix):
                continue
            if status and record.get("status") != status:
                continue
            if severity and record.get("severity") != severity:
                continue
            if correlation_id and record.get("correlation_id") != correlation_id:
                continue
            if job_id and record.get("job_id") != job_id:
                continue
            result.append(record)
        return result[-limit:]

    def critical_events(self, limit: int = 20) -> list[dict[str, Any]]:
        records = [r for r in self._iter()
                   if r.get("severity") == "critical" or r.get("status") == "failed"]
        return records[-limit:]

    def export_json(self, target: str | Path | None = None, **query_kwargs: Any) -> Path:
        records = self.query(limit=10_000, **query_kwargs) if query_kwargs else self._iter()
        if target is None:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            target = self.project_root / "runtime" / "exports" / f"audit_events_{stamp}.json"
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "schema": "secondbrain.observability.audit_export.v1",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "count": len(records),
            "events": records,
        }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return target
