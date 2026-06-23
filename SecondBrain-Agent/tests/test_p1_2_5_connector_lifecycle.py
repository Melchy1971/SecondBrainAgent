from datetime import datetime, timezone

import pytest

from secondbrain.connectors.adapter_contract import ConnectorItem, ConnectorContractError
from secondbrain.connectors.adapter_lifecycle import ConnectorLifecycleRegistry, ConnectorLifecycleService
from secondbrain.connectors.retry_policy import RetryPolicy
from secondbrain.connectors.sync_state import SyncStatus


class StaticAdapter:
    source = "gmail"

    def __init__(self, items=None):
        self.items = items or []
        self.cursors = []

    def fetch_changed(self, cursor=None):
        self.cursors.append(cursor)
        return self.items


def item(external_id="1", source="gmail", title="hello"):
    return ConnectorItem(
        external_id=external_id,
        source=source,
        title=title,
        content="body",
        updated_at=datetime(2026, 6, 23, 8, 0, tzinfo=timezone.utc),
    )


def test_registry_registers_valid_adapter_and_blocks_duplicates():
    registry = ConnectorLifecycleRegistry()
    record = registry.register(StaticAdapter(), labels=["mail", " inbox "])

    assert record.source == "gmail"
    assert record.labels == ("mail", "inbox")
    assert registry.list()[0].source == "gmail"

    with pytest.raises(ConnectorContractError):
        registry.register(StaticAdapter())


def test_lifecycle_processes_items_commits_cursor_and_reports_health():
    service = ConnectorLifecycleService()
    adapter = StaticAdapter([item("1"), item("2")])
    service.register(adapter)
    processed = []

    run = service.run_one("gmail", lambda connector_item: processed.append(connector_item.external_id) or True)

    assert processed == ["1", "2"]
    assert run.result.status == SyncStatus.SUCCESS
    assert run.result.fetched == 2
    assert run.result.processed == 2
    assert service.cursor_store.get("gmail").value == "2026-06-23T08:00:00+00:00"
    assert run.health.status.value == "healthy"
    assert run.health.fetched == 2


def test_lifecycle_disabled_connector_does_not_fetch():
    service = ConnectorLifecycleService()
    adapter = StaticAdapter([item("1")])
    service.register(adapter, enabled=False)

    run = service.run_one("gmail", lambda connector_item: True)

    assert adapter.cursors == []
    assert run.result.status == SyncStatus.IDLE
    assert run.result.skipped == 1


def test_lifecycle_isolates_item_failure_to_dead_letter_and_partial_status():
    service = ConnectorLifecycleService(retry_policy=RetryPolicy(max_attempts=1))
    service.register(StaticAdapter([item("1"), item("2")]))

    def processor(connector_item):
        if connector_item.external_id == "2":
            raise RuntimeError("boom")
        return True

    run = service.run_one("gmail", processor)

    assert run.result.status == SyncStatus.PARTIAL
    assert run.result.processed == 1
    assert run.result.failed == 1
    assert service.dead_letters.list("gmail")[0].item_id == "2"
    assert run.health.status.value == "degraded"


def test_lifecycle_fetch_failure_keeps_cursor_and_reports_failed_health():
    class BrokenAdapter:
        source = "gmail"

        def fetch_changed(self, cursor=None):
            raise RuntimeError("api down")

    service = ConnectorLifecycleService(retry_policy=RetryPolicy(max_attempts=1))
    service.register(BrokenAdapter())

    run = service.run_one("gmail", lambda connector_item: True)

    assert run.result.status == SyncStatus.FAILED
    assert run.result.cursor_before is None
    assert run.result.cursor_after is None
    assert service.cursor_store.get("gmail") is None
    assert service.dead_letters.list("gmail")[0].code == "fetch_error"
    assert run.health.status.value == "failed"


def test_lifecycle_rejects_source_mismatch_without_processing_item():
    service = ConnectorLifecycleService()
    service.register(StaticAdapter([item("x", source="drive")]))
    processed = []

    run = service.run_one("gmail", lambda connector_item: processed.append(connector_item.external_id) or True)

    assert processed == []
    assert run.result.status == SyncStatus.PARTIAL
    assert run.result.failed == 1
    assert service.dead_letters.list("gmail")[0].code == "source_mismatch"


def test_lifecycle_run_enabled_runs_only_enabled_connectors():
    class DriveAdapter(StaticAdapter):
        source = "drive"

    service = ConnectorLifecycleService()
    service.register(StaticAdapter([item("g")]))
    service.register(DriveAdapter([item("d", source="drive")]), enabled=False)

    runs = service.run_enabled(lambda connector_item: True)

    assert [run.result.connector for run in runs] == ["gmail"]
