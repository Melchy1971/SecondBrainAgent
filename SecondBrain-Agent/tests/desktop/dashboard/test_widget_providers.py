from secondbrain.desktop.dashboard.widget_providers import (
    ConnectorHealthProvider,
    HealthColor,
    RagStatusProvider,
    RecentErrorsProvider,
    RecentImportsProvider,
    RunningJobsProvider,
    StorageUsageProvider,
    SystemHealthProvider,
    WorkspaceSummaryProvider,
    default_widget_providers,
)


def test_recent_imports_provider_sorts_and_limits():
    provider = RecentImportsProvider(
        lambda workspace: [
            {"id": "old", "created_at": "2026-01-01T00:00:00"},
            {"id": "new", "created_at": "2026-02-01T00:00:00"},
        ],
        limit=1,
    )

    payload = provider("w1")

    assert payload["workspace"] == "w1"
    assert payload["count"] == 1
    assert payload["items"][0]["id"] == "new"


def test_running_jobs_provider_counts_active_and_failed_jobs():
    provider = RunningJobsProvider(lambda _: [{"state": "running"}, {"state": "queued"}, {"state": "failed"}])

    payload = provider("w1")

    assert payload["running"] == 2
    assert payload["failed"] == 1
    assert payload["status"] == HealthColor.YELLOW.value


def test_connector_health_provider_escalates_to_red():
    provider = ConnectorHealthProvider(lambda _: [{"name": "a", "status": "green"}, {"name": "b", "status": "red"}])

    payload = provider("w1")

    assert payload["status"] == HealthColor.RED.value
    assert payload["red"] == 1


def test_rag_status_provider_reports_pending_as_yellow():
    provider = RagStatusProvider(lambda _: {"indexed_documents": 10, "pending_documents": 2, "errors": 0, "embedding_provider": "ollama"})

    payload = provider("w1")

    assert payload["status"] == HealthColor.YELLOW.value
    assert payload["embedding_provider"] == "ollama"


def test_system_health_provider_aggregates_checks():
    provider = SystemHealthProvider(lambda _: {"database": "green", "ocr": "yellow"})

    payload = provider("w1")

    assert payload["status"] == HealthColor.YELLOW.value
    assert payload["checks"]["database"] == "green"


def test_storage_usage_provider_uses_thresholds():
    provider = StorageUsageProvider(lambda _: {"used_bytes": 96, "total_bytes": 100})

    payload = provider("w1")

    assert payload["status"] == HealthColor.RED.value
    assert payload["usage_ratio"] == 0.96


def test_recent_errors_provider_returns_warning_when_errors_exist():
    provider = RecentErrorsProvider(lambda _: [{"message": "x", "created_at": "2026-02-01"}])

    payload = provider("w1")

    assert payload["count"] == 1
    assert payload["status"] == HealthColor.YELLOW.value


def test_workspace_summary_provider_applies_defaults():
    provider = WorkspaceSummaryProvider(lambda _: {"documents": 3}, defaults={"connectors": 2})

    payload = provider("w1")

    assert payload == {"connectors": 2, "documents": 3, "jobs": 0, "workspace": "w1"}


def test_default_widget_providers_contains_all_dashboard_widgets():
    providers = default_widget_providers()

    assert set(providers) == {
        "recent_imports",
        "running_jobs",
        "connector_health",
        "rag_status",
        "system_health",
        "storage_usage",
        "recent_errors",
        "workspace_summary",
    }
