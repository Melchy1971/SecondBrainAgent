from datetime import datetime

from secondbrain.desktop_native.runtime_info import (
    calendar_month,
    release_blocker_count,
    runtime_log_level,
    topbar_status_labels,
)


def test_calendar_month_uses_current_month_and_full_year() -> None:
    assert calendar_month(datetime(2026, 7, 20)) == "Juli 2026"
    assert calendar_month(datetime(2025, 3, 1)) == "März 2025"


def test_log_level_is_allowlisted_and_has_explicit_default() -> None:
    assert runtime_log_level({}) == "INFO (default)"
    assert runtime_log_level({"SECONDBRAIN_LOG_LEVEL": "warning"}) == "WARNING"
    assert runtime_log_level({"LOG_LEVEL": "ERROR"}) == "ERROR"
    assert runtime_log_level({"LOG_LEVEL": "secret-value"}) == "Unknown"


def test_topbar_projects_health_and_blockers() -> None:
    assert topbar_status_labels(
        {"database": "PostgreSQL", "embedding": "Ollama / Ready"}, blocker_count=2
    ) == {
        "release_gate": "BLOCKING 2",
        "embedding": "Ollama / Ready",
        "postgresql": "Configured",
    }
    assert topbar_status_labels(
        {"database": "Local fallback", "embedding": "Local / Ready"}, blocker_count=0
    )["release_gate"] == "READY"


def test_release_blockers_include_native_and_bootstrap_sources() -> None:
    assert release_blocker_count(
        {"blockers": [{"name": "native"}], "bootstrap": {"blockers": [{"name": "env"}, {"name": "db"}]}}
    ) == 3
    assert release_blocker_count({}) == 0


def test_topbar_does_not_forward_database_details() -> None:
    result = topbar_status_labels(
        {"database": "postgresql://user:secret@host/db", "embedding": "Unknown"},
        blocker_count="invalid",
    )
    assert result["postgresql"] == "Unknown"
    assert "secret" not in str(result)
