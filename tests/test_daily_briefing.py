from datetime import datetime, timezone

from secondbrain.personal_dashboard.models import DashboardConfig
from secondbrain.personal_dashboard.service import Dashboard


def test_daily_briefing_is_read_only_and_evidence_based():
    config = DashboardConfig(enabled=["next_up"], order=["next_up"], workspace_id="w1")
    cards = Dashboard().build(config=config, context={"tasks": [
        {"id": "task-1", "title": "Konzept", "workspace_id": "w1", "due": "2026-01-02"},
    ]}, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert cards[0].items[0].reference == "task-1"
