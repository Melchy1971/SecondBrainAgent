from datetime import datetime, timezone

from secondbrain.personal_dashboard.models import DashboardConfig
from secondbrain.personal_dashboard.service import Dashboard


def test_snapshot_is_workspace_scoped():
    config = DashboardConfig(enabled=["tasks"], order=["tasks"], workspace_id="w1")
    snapshot = Dashboard().snapshot(config=config, context={"tasks": [
        {"id": "mine", "title": "Mine", "workspace_id": "w1"},
        {"id": "other", "title": "Other", "workspace_id": "w2"},
    ]}, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert [item.label for item in snapshot.cards[0].items] == ["Mine"]
