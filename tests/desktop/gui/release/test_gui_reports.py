from secondbrain.desktop.gui.release.gui_checklist import GuiRc1Checklist
from secondbrain.desktop.gui.release.gui_health_report import GuiHealthReport
from secondbrain.desktop.gui.release.gui_metrics import GuiRc1Metrics
from secondbrain.desktop.gui.release.gui_rc1_gate import GuiRc1Input, REQUIRED_ACCESSIBILITY, REQUIRED_FLOWS, REQUIRED_MODULES
from secondbrain.desktop.gui.release.gui_validation import validate_gui_rc1


def test_health_report_computes_readiness_ratio():
    report = GuiHealthReport(modules_ready=2, modules_total=4, flows_ready=1, flows_total=1)
    assert report.readiness_ratio == 0.6
    assert report.to_dict()["readiness_ratio"] == 0.6


def test_checklist_detects_missing_required_items():
    missing = GuiRc1Checklist().missing_required({"desktop_foundation", "tests"})
    assert any(item.key == "dashboard" for item in missing)


def test_metrics_validate_negative_values():
    metrics = GuiRc1Metrics(startup_ms=-1)
    assert metrics.validate() == ["startup_ms must not be negative"]


def test_validation_facade_returns_gate_report():
    report = validate_gui_rc1(
        GuiRc1Input(
            modules={key: "PASS" for key in REQUIRED_MODULES},
            flows={key: "PASS" for key in REQUIRED_FLOWS},
            accessibility={key: "PASS" for key in REQUIRED_ACCESSIBILITY},
        )
    )
    assert report.to_dict()["status"] == "PASS"
