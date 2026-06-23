from secondbrain.desktop.dashboard import DashboardEventType, DashboardService, WidgetStatus


def test_bootstrap_defaults_registers_standard_widgets(tmp_path):
    service = DashboardService(tmp_path)

    widgets = service.bootstrap_defaults()

    assert len(widgets) == 8
    assert "rag_status" in service.state.enabled_widgets


def test_service_refresh_and_snapshot(tmp_path):
    service = DashboardService(tmp_path, providers={"rag_status": lambda workspace: {"status": "green", "workspace": workspace}})
    service.bootstrap_defaults()
    service.state.selected_workspace = "main"

    widget = service.refresh("rag_status")
    snapshot = service.snapshot()

    assert widget.status == WidgetStatus.READY
    assert widget.data == {"status": "green", "workspace": "main"}
    assert snapshot["workspace"] == "main"
    assert any(item["widget_id"] == "rag_status" for item in snapshot["widgets"])


def test_service_save_emits_event(tmp_path):
    service = DashboardService(tmp_path)
    service.bootstrap_defaults()

    service.save()

    assert service.persistence.load_state().enabled_widgets
    assert service.events.all()[-1].event_type == DashboardEventType.DASHBOARD_SAVED
