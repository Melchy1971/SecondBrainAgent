"""Tests für Observability: IDs, Redaction, Taxonomy, Audit Store, Health, Fassade."""

from __future__ import annotations

import json
from pathlib import Path

from secondbrain.observability import (
    AuditEventStore, HealthTimeline, ObservabilityService,
    RedactionMiddleware, StructuredLogger, classify_error, group_by_cause,
    new_correlation_id, new_job_id, new_plan_id, new_sync_id,
)


# --- IDs ---------------------------------------------------------------------

def test_ids_have_stable_prefixes_and_are_unique():
    ids = {new_correlation_id(), new_job_id(), new_plan_id(), new_sync_id()}
    assert len(ids) == 4
    assert new_correlation_id().startswith("cor_")
    assert new_job_id().startswith("job_")
    assert new_plan_id().startswith("plan_")
    assert new_sync_id().startswith("sync_")
    assert new_job_id() != new_job_id()


# --- Redaction ----------------------------------------------------------------

def test_redaction_masks_secret_keys_and_patterns():
    middleware = RedactionMiddleware()
    payload = {
        "database_url": "postgresql://user:pass@host/db",
        "nested": {"api_key": "sk-abcdef1234567890", "harmlos": "wert"},
        "text": "api_key=sk-abcdef1234567890XYZ",
        "liste": [{"password": "geheim123"}],
    }
    redacted = middleware.redact_payload(payload)
    dumped = json.dumps(redacted)
    assert "postgresql://user:pass" not in dumped
    assert "sk-abcdef1234567890" not in dumped
    assert "geheim123" not in dumped
    assert redacted["nested"]["harmlos"] == "wert"


# --- Taxonomy -------------------------------------------------------------------

def test_classify_error_by_type_and_message():
    assert classify_error(PermissionError("denied")) == "permission"
    assert classify_error(TimeoutError("t")) == "timeout"
    assert classify_error("connection refused by host") == "network"
    assert classify_error("missing api key for provider") == "configuration"
    assert classify_error("völlig unbekannt") == "unknown"


def test_group_by_cause_counts_and_samples():
    events = [
        {"message": "connection reset", "ts": "t1", "event": "e1"},
        {"message": "connection refused", "ts": "t2", "event": "e2"},
        {"message": "rate limit exceeded", "ts": "t3", "event": "e3"},
    ]
    groups = group_by_cause(events)
    assert groups["total"] == 3
    assert groups["by_category"]["network"] == 2
    assert groups["by_category"]["provider"] == 1
    assert len(groups["samples"]["network"]) == 2


# --- Structured Log ---------------------------------------------------------------

def test_structured_log_writes_ids_and_redacts(tmp_path: Path):
    logger = StructuredLogger(tmp_path)
    job = new_job_id()
    logger.error("import.failed", "token=abcdefgh1234 secret",
                 job_id=job, category="parsing")
    records = logger.tail()
    assert len(records) == 1
    assert records[0]["job_id"] == job
    assert records[0]["category"] == "parsing"
    assert "abcdefgh1234" not in json.dumps(records[0])


# --- Audit Store --------------------------------------------------------------------

def test_audit_store_append_query_and_export(tmp_path: Path):
    store = AuditEventStore(tmp_path)
    cor = new_correlation_id()
    store.record("import", "import.file", resource="a.pdf", correlation_id=cor)
    store.record("import", "import.file", resource="b.pdf", status="failed",
                 severity="critical", correlation_id=cor, category="parsing")
    store.record("agent", "agent.plan.start", plan_id=new_plan_id())

    assert len(store.query(actor="import")) == 2
    assert len(store.query(correlation_id=cor)) == 2
    assert len(store.query(action_prefix="agent.")) == 1
    critical = store.critical_events()
    assert len(critical) == 1 and critical[0]["resource"] == "b.pdf"

    target = store.export_json(tmp_path / "export.json")
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["count"] == 3
    assert data["events"][0]["schema"].startswith("secondbrain.observability")


def test_audit_store_redacts_detail(tmp_path: Path):
    store = AuditEventStore(tmp_path)
    store.record("connector", "connector.sync", sync_id=new_sync_id(),
                 detail={"api_key": "sk-supersecret123456", "items": 5})
    record = store.query()[0]
    assert "sk-supersecret123456" not in json.dumps(record)
    assert record["detail"]["items"] == 5


# --- Health Timeline ------------------------------------------------------------------

def test_health_timeline_current_reports_worst_status(tmp_path: Path):
    health = HealthTimeline(tmp_path)
    health.record("rag", "ok")
    health.record("import", "ok")
    health.record("import", "degraded", detail="Parserfehler")
    current = health.current()
    assert current["overall"] == "degraded"
    assert current["components"]["import"]["status"] == "degraded"
    assert current["components"]["rag"]["status"] == "ok"


# --- Fassade ---------------------------------------------------------------------------

def test_service_track_action_writes_audit_log_and_health(tmp_path: Path):
    service = ObservabilityService(tmp_path)
    result = service.track_action(
        "import", "import.file", resource="x.pdf",
        status="failed", error=TimeoutError("provider timed out"),
        job_id=new_job_id())
    assert result["category"] == "timeout"
    snapshot = service.snapshot()
    assert snapshot["health"]["overall"] == "degraded"
    assert len(snapshot["critical_events"]) == 1
    assert snapshot["error_groups"]["total"] >= 1


def test_service_snapshot_empty_project_is_safe(tmp_path: Path):
    snapshot = ObservabilityService(tmp_path).snapshot()
    assert snapshot["health"]["overall"] == "unknown"
    assert snapshot["critical_events"] == []
