from secondbrain.desktop.gui.release.gui_rc1_gate import GuiRc1Gate, GuiRc1Input, REQUIRED_ACCESSIBILITY, REQUIRED_FLOWS, REQUIRED_MODULES


def ready_payload() -> GuiRc1Input:
    return GuiRc1Input(
        modules={key: "PASS" for key in REQUIRED_MODULES},
        flows={key: "PASS" for key in REQUIRED_FLOWS},
        accessibility={key: "PASS" for key in REQUIRED_ACCESSIBILITY},
        tests_passed=True,
    )


def test_gate_passes_when_everything_ready():
    report = GuiRc1Gate().evaluate(ready_payload())
    assert report.status == "PASS"
    assert report.blockers == []


def test_gate_blocks_missing_module():
    payload = ready_payload()
    payload.modules.pop("search")
    report = GuiRc1Gate().evaluate(payload)
    assert report.status == "BLOCKED"
    assert any("search" in blocker for blocker in report.blockers)


def test_gate_allows_warning_without_blocking():
    payload = ready_payload()
    payload.accessibility["screenreader_labels"] = "WARNING"
    report = GuiRc1Gate().evaluate(payload)
    assert report.status == "PASS"
    assert any(check.status == "WARNING" for check in report.checks)


def test_gate_blocks_failed_tests():
    payload = ready_payload()
    payload.tests_passed = False
    report = GuiRc1Gate().evaluate(payload)
    assert report.status == "BLOCKED"
