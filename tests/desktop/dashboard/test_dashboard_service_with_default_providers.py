from secondbrain.desktop.dashboard import DashboardService, WidgetStatus
from secondbrain.desktop.dashboard.widget_providers import default_widget_providers


def test_dashboard_service_bootstraps_with_concrete_default_providers(tmp_path):
    providers = default_widget_providers(
        jobs=lambda workspace: [{"id": "j1", "state": "running"}],
        rag=lambda workspace: {"indexed_documents": 2, "pending_documents": 0, "errors": 0},
    )
    service = DashboardService(tmp_path, providers=providers)
    service.bootstrap_defaults()

    widgets = service.refresh_all()
    by_id = {widget.widget_id: widget for widget in widgets}

    assert by_id["running_jobs"].status == WidgetStatus.READY
    assert by_id["running_jobs"].data["running"] == 1
    assert by_id["rag_status"].data["status"] == "green"
