from datetime import datetime, timezone

import pytest

from secondbrain.connectors.adapter_contract import ConnectorItem
from secondbrain.connectors.adapter_lifecycle import ConnectorLifecycleService
from secondbrain.connectors.import_bridge import (
    ConnectorImportBridge,
    ImportJobStatus,
    InMemoryImportJobSink,
    run_connector_import,
    summarize_import_run,
)
from secondbrain.connectors.sync_state import SyncStatus


class StaticAdapter:
    source = "drive"

    def __init__(self, items):
        self.items = items
        self.cursors = []

    def fetch_changed(self, cursor=None):
        self.cursors.append(cursor)
        return self.items


def item(external_id="doc-1", content="Alpha content", source="drive"):
    return ConnectorItem(
        external_id=external_id,
        source=source,
        title="Alpha",
        content=content,
        updated_at=datetime(2026, 6, 23, 8, 0, tzinfo=timezone.utc),
        uri="https://example.invalid/doc-1",
        mime_type="text/plain",
        metadata={"folder": "inbox"},
    )


def test_build_job_preserves_idempotency_boundaries():
    bridge = ConnectorImportBridge(InMemoryImportJobSink())
    first = bridge.build_job(item())
    second = bridge.build_job(item(content="Changed content"))

    assert first.document_key == second.document_key
    assert first.job_id != second.job_id
    assert first.source == "drive"
    assert first.metadata["connector_external_id"] == "doc-1"
    assert first.status == ImportJobStatus.PENDING


def test_process_item_submits_and_skips_duplicate():
    sink = InMemoryImportJobSink(skip_existing=True)
    bridge = ConnectorImportBridge(sink)
    changed = item()

    assert bridge.process_item(changed) is True
    assert bridge.process_item(changed) is False

    snapshot = bridge.snapshot()
    assert snapshot["imported"] == 1
    assert snapshot["skipped"] == 1
    assert snapshot["failed"] == 0
    assert len(sink.jobs) == 1


def test_item_filter_skips_before_sink_submit():
    sink = InMemoryImportJobSink()
    bridge = ConnectorImportBridge(sink, item_filter=lambda candidate: candidate.mime_type == "application/pdf")

    assert bridge.process_item(item()) is False
    assert bridge.snapshot()["skipped"] == 1
    assert sink.jobs == {}


def test_import_failure_is_isolated_by_lifecycle_dead_letter():
    lifecycle = ConnectorLifecycleService()
    lifecycle.register(StaticAdapter([item("doc-1"), item("doc-2")]))
    sink = InMemoryImportJobSink(fail_on={"doc-2"})

    run, bridge = run_connector_import(lifecycle, "drive", sink)

    assert run.result.status == SyncStatus.PARTIAL
    assert run.result.processed == 1
    assert run.result.failed == 1
    assert bridge.snapshot()["failed"] == 1
    assert lifecycle.dead_letters.list()[0].item_id == "doc-2"


def test_run_summary_is_release_gate_friendly():
    lifecycle = ConnectorLifecycleService()
    lifecycle.register(StaticAdapter([item("doc-1")]))
    sink = InMemoryImportJobSink()

    run, bridge = run_connector_import(lifecycle, "drive", sink)
    summary = summarize_import_run(run, bridge)

    assert summary["connector"] == "drive"
    assert summary["sync_status"] == "success"
    assert summary["fetched"] == 1
    assert summary["imported"] == 1
    assert summary["ok"] is True
    assert "health" in summary


def test_source_mismatch_does_not_submit_import_job():
    lifecycle = ConnectorLifecycleService()
    lifecycle.register(StaticAdapter([item(source="gmail")]))
    sink = InMemoryImportJobSink()

    run, bridge = run_connector_import(lifecycle, "drive", sink)

    assert run.result.status == SyncStatus.PARTIAL
    assert run.result.failed == 1
    assert bridge.snapshot()["total"] == 0
    assert sink.jobs == {}
