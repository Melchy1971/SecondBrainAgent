from secondbrain.desktop.gui.flows.e2e_flows import build_default_e2e_registry
from secondbrain.desktop.gui.flows.flow_report import flow_result_to_report
from secondbrain.desktop.gui.flows.flow_runner import DesktopFlowRunner


def test_report_contains_status_and_step_summary():
    result = DesktopFlowRunner(build_default_e2e_registry()).run("settings_restart")
    report = flow_result_to_report(result)
    assert report["status"] == "passed"
    assert len(report["steps"]) == 3
    assert "startup_ready" in report["context_keys"]
