from __future__ import annotations

from pathlib import Path

from secondbrain.native.dashboard_center.service import NativeDashboardService
from secondbrain.native.ai_workspace.service import AIWorkspaceService
import secondbrain.native.dashboard_center.service as dashboard_service_module


def test_dashboard_status_contains_core_cards(tmp_path: Path) -> None:
    (tmp_path / "secondbrain" / "native" / "dashboard_center").mkdir(parents=True)
    service = NativeDashboardService(tmp_path)
    payload = service.status()
    ids = {card["id"] for card in payload["cards"]}
    assert payload["ok"] is True
    assert {"desktop", "database", "embeddings", "security", "runtime"}.issubset(ids)


def test_dashboard_records_activity(tmp_path: Path) -> None:
    service = NativeDashboardService(tmp_path)
    result = service.record_activity("test_event", {"x": 1})
    activity = service.activity()
    assert result["ok"] is True
    assert activity["count"] == 1
    assert activity["items"][0]["event"] == "test_event"


def test_dashboard_detects_missing_native_modules(tmp_path: Path) -> None:
    service = NativeDashboardService(tmp_path)
    snap = service.snapshot().to_dict()
    assert any(card["id"] == "chat" and card["status"] == "blocked" for card in snap["cards"])
    assert any(blocker.startswith("missing_module:") for blocker in snap["blockers"])


def test_workspace_navigation_includes_dashboard(tmp_path: Path) -> None:
    (tmp_path / "secondbrain" / "native" / "dashboard_center").mkdir(parents=True)
    nav = AIWorkspaceService(tmp_path).navigation()
    ids = {item["id"] for item in nav["navigation"]}
    assert "dashboard" in ids


def test_dashboard_security_blocks_when_approval_disabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SECONDBRAIN_APPROVAL_REQUIRED", "false")
    service = NativeDashboardService(tmp_path)
    cards = {card["id"]: card for card in service.snapshot().to_dict()["cards"]}
    assert cards["security"]["status"] == "blocked"
    assert "approval_required_disabled" in cards["security"]["blockers"]


def test_dashboard_database_card_uses_degraded_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        dashboard_service_module,
        "evaluate_db_pgvector_production_status",
        lambda _root: {"status": "degraded_sqlite", "reason": "database_url_missing"},
    )
    service = NativeDashboardService(tmp_path)
    cards = {card["id"]: card for card in service.snapshot().to_dict()["cards"]}
    assert cards["database"]["status"] == "warning"
    assert cards["database"]["value"] == "degraded_sqlite"


def test_dashboard_database_card_uses_blocked_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        dashboard_service_module,
        "evaluate_db_pgvector_production_status",
        lambda _root: {"status": "blocked_missing_pgvector", "reason": "pgvector_extension_missing"},
    )
    service = NativeDashboardService(tmp_path)
    cards = {card["id"]: card for card in service.snapshot().to_dict()["cards"]}
    assert cards["database"]["status"] == "blocked"
    assert cards["database"]["value"] == "blocked_missing_pgvector"
