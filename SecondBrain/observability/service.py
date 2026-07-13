"""Fassade für Observability: gemeinsamer Einstieg für GUI, CLI und Integrationen."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.observability.audit_store import AuditEventStore
from secondbrain.observability.health_timeline import HealthTimeline
from secondbrain.observability.ids import new_correlation_id
from secondbrain.observability.structured_log import StructuredLogger
from secondbrain.observability.taxonomy import classify_error, group_by_cause

SCHEMA = "secondbrain.observability.snapshot.v1"


class ObservabilityService:
    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root)
        self.log = StructuredLogger(self.project_root)
        self.audit = AuditEventStore(self.project_root)
        self.health = HealthTimeline(self.project_root)

    # ------------------------------------------------------------ Aufzeichnen
    def track_action(
        self,
        actor: str,
        action: str,
        *,
        resource: str = "",
        status: str = "ok",
        error: BaseException | str | None = None,
        correlation_id: str | None = None,
        **id_fields: str,
    ) -> dict[str, Any]:
        """Ein Aufruf, drei Effekte: Audit-Eintrag, Log-Zeile, Health bei Fehlern."""
        correlation = correlation_id or new_correlation_id()
        category = ""
        severity = "info"
        message = ""
        if status != "ok" and error is not None:
            category = classify_error(error)
            severity = "critical" if status == "failed" else "warning"
            message = str(error)
        self.audit.record(
            actor, action, resource=resource, status=status, severity=severity,
            correlation_id=correlation, category=category,
            detail={"message": message} if message else {}, **id_fields)
        self.log.log(
            "error" if status == "failed" else "info",
            action, message or f"{actor}: {action}",
            correlation_id=correlation, category=category or None,
            error_type=type(error).__name__ if isinstance(error, BaseException) else None,
            **{k: v for k, v in id_fields.items() if k in ("job_id", "plan_id", "sync_id")})
        if status == "failed":
            self.health.record(actor, "degraded", detail=message, correlation_id=correlation)
        return {"correlation_id": correlation, "category": category, "status": status}

    # ------------------------------------------------------------------ Sicht
    def snapshot(self, limit: int = 50) -> dict[str, Any]:
        """GUI-Sicht: aktuelle Health, letzte kritische Events, Fehlergruppen."""
        errors = self.log.tail(limit=500, level="error")
        return {
            "schema": SCHEMA,
            "health": self.health.current(),
            "critical_events": self.audit.critical_events(limit=20),
            "recent_events": self.audit.query(limit=limit),
            "error_groups": group_by_cause(errors),
            "paths": {
                "logs": str(self.log.path),
                "audit": str(self.audit.path),
                "health": str(self.health.path),
            },
        }

    def export_json(self, target: str | Path | None = None) -> Path:
        return self.audit.export_json(target)
