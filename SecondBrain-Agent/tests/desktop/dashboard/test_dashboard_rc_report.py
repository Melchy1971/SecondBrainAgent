import json

from secondbrain.desktop.dashboard.rc_gate import DashboardRCGate
from secondbrain.desktop.dashboard.rc_report import dashboard_rc_markdown, write_dashboard_rc_markdown, write_dashboard_rc_report

def full_snapshot():
    from secondbrain.desktop.dashboard.rc_gate import DashboardRCSnapshot

    widgets = {
        "recent_imports": {"enabled": True},
        "running_jobs": {"enabled": True},
        "connector_health": {"enabled": True},
        "rag_status": {"enabled": True},
        "system_health": {"enabled": True},
        "recent_errors": {"enabled": True},
        "workspace_summary": {"enabled": True},
    }
    layout = {f"slot_{idx}": {"widget_id": widget_id, "x": idx, "y": 0, "w": 1, "h": 1} for idx, widget_id in enumerate(widgets)}
    actions = {"refresh_widget": {"enabled": True}, "open_widget_details": {"enabled": True}, "disable_widget": {"enabled": True}}
    services = {"dashboard_service": True, "widget_registry": True, "widget_manager": True, "refresh_scheduler": True, "dashboard_persistence": True}
    return DashboardRCSnapshot(widgets=widgets, layout=layout, actions=actions, services=services, tests={"passed": 20, "failed": 0})


def test_write_dashboard_rc_json_report(tmp_path):
    report = DashboardRCGate().evaluate(full_snapshot())
    path = write_dashboard_rc_report(report, tmp_path / "dashboard_rc.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "PASS"
    assert data["score"] == 100


def test_dashboard_rc_markdown_contains_status_and_score(tmp_path):
    report = DashboardRCGate().evaluate(full_snapshot())
    text = dashboard_rc_markdown(report)
    assert "Status: PASS" in text
    assert "Score: 100" in text
    path = write_dashboard_rc_markdown(report, tmp_path / "dashboard_rc.md")
    assert path.read_text(encoding="utf-8").startswith("# Dashboard RC1 Gate")
