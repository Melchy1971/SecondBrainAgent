"""Produktive Observability: strukturierte Logs, Audit Events, Health Timeline.

Bausteine:
- ids: Correlation-/Job-/Plan-/Sync-IDs mit stabilen Präfixen
- redaction: Middleware, die Secrets in Strings und Payloads maskiert
- taxonomy: Fehlerklassifikation nach Ursache (gruppierbar)
- structured_log: JSONL-Logger mit ID-Feldern (runtime/observability/logs.jsonl)
- audit_store: Append-only Audit Event Store mit Query + JSON-Export
- health_timeline: Komponenten-Status über die Zeit, letzte kritische Events
- service: Fassade für GUI (Audit Viewer) und Integrationen
"""

from .ids import new_correlation_id, new_job_id, new_plan_id, new_sync_id
from .redaction import RedactionMiddleware
from .taxonomy import ERROR_CATEGORIES, classify_error, group_by_cause
from .structured_log import StructuredLogger
from .audit_store import AuditEvent, AuditEventStore
from .health_timeline import HealthTimeline
from .service import ObservabilityService

__all__ = [
    "AuditEvent", "AuditEventStore", "ERROR_CATEGORIES", "HealthTimeline",
    "ObservabilityService", "RedactionMiddleware", "StructuredLogger",
    "classify_error", "group_by_cause",
    "new_correlation_id", "new_job_id", "new_plan_id", "new_sync_id",
]
