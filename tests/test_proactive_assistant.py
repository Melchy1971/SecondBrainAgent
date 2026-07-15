from datetime import datetime, timezone

from secondbrain.personal_dashboard.models import DashboardConfig
from secondbrain.personal_dashboard.service import Dashboard


def test_proactive_accept_does_not_execute_external_action():
    config = DashboardConfig(enabled=["suggestions"], order=["suggestions"], workspace_id="w1")
    cards = Dashboard().build(config=config, context={"suggestions": [
        {"id": "suggestion-1", "title": "Antwort vorbereiten", "workspace_id": "w1"},
    ]}, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert cards[0].items[0].label == "Antwort vorbereiten"
    result = Dashboard().quick_action(action="send_reply", reference="mail-1", workspace_id="w1")
    assert result["executed"] is False and result["approval_required"] is True
