from secondbrain.desktop.dashboard.rc_gate import (
    DashboardRCGate,
    DashboardRCSnapshot,
    DashboardRCStatus,
)


def full_snapshot() -> DashboardRCSnapshot:
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
    actions = {
        "refresh_widget": {"enabled": True},
        "open_widget_details": {"enabled": True},
        "disable_widget": {"enabled": True},
    }
    services = {
        "dashboard_service": True,
        "widget_registry": True,
        "widget_manager": True,
        "refresh_scheduler": True,
        "dashboard_persistence": True,
    }
    return DashboardRCSnapshot(widgets=widgets, layout=layout, actions=actions, services=services, tests={"passed": 20, "failed": 0})


def test_dashboard_rc_gate_passes_complete_snapshot():
    report = DashboardRCGate().evaluate(full_snapshot())
    assert report.status == DashboardRCStatus.PASS
    assert report.score == 100
    assert report.blockers == ()


def test_dashboard_rc_gate_fails_missing_required_widget():
    snapshot = full_snapshot()
    widgets = dict(snapshot.widgets)
    widgets.pop("rag_status")
    report = DashboardRCGate().evaluate(DashboardRCSnapshot(widgets=widgets, layout=snapshot.layout, actions=snapshot.actions, services=snapshot.services, tests=snapshot.tests))
    assert report.status == DashboardRCStatus.FAIL
    assert any(f.code == "DASHBOARD_MISSING_WIDGETS" for f in report.blockers)


def test_dashboard_rc_gate_conditional_pass_for_missing_recommended_action():
    snapshot = full_snapshot()
    actions = dict(snapshot.actions)
    actions.pop("disable_widget")
    report = DashboardRCGate().evaluate(DashboardRCSnapshot(widgets=snapshot.widgets, layout=snapshot.layout, actions=actions, services=snapshot.services, tests=snapshot.tests))
    assert report.status == DashboardRCStatus.CONDITIONAL_PASS
    assert report.warnings


def test_dashboard_rc_gate_fails_orphan_layout_entry():
    snapshot = full_snapshot()
    layout = dict(snapshot.layout)
    layout["orphan"] = {"widget_id": "missing_widget", "x": 0, "y": 2, "w": 1, "h": 1}
    report = DashboardRCGate().evaluate(DashboardRCSnapshot(widgets=snapshot.widgets, layout=layout, actions=snapshot.actions, services=snapshot.services, tests=snapshot.tests))
    assert report.status == DashboardRCStatus.FAIL
    assert any(f.code == "DASHBOARD_LAYOUT_ORPHANS" for f in report.blockers)


def test_dashboard_rc_report_serializes_to_dict():
    report = DashboardRCGate().evaluate(full_snapshot())
    payload = report.to_dict()
    assert payload["status"] == "PASS"
    assert payload["summary"]["widgets_present"] == 7
