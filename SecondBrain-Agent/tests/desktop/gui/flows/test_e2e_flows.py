from secondbrain.desktop.gui.flows.e2e_flows import build_default_e2e_registry
from secondbrain.desktop.gui.flows.flow_runner import DesktopFlowRunner


def test_import_index_search_flow_passes():
    result = DesktopFlowRunner(build_default_e2e_registry()).run("import_index_search", {"document_id": "doc-42"})
    assert result.passed
    assert result.context["search_results"] == ["doc-42"]


def test_connector_sync_import_flow_passes():
    result = DesktopFlowRunner(build_default_e2e_registry()).run("connector_sync_import", {"connector_items": 3})
    assert result.passed
    assert result.context["import_jobs"] == 3


def test_settings_restart_flow_passes():
    result = DesktopFlowRunner(build_default_e2e_registry()).run("settings_restart")
    assert result.passed
    assert result.context["startup_ready"] is True
