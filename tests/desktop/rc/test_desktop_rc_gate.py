from secondbrain.desktop.rc import DesktopRCGate


def _components(value=True):
    return {
        "shell": value,
        "state": value,
        "router": value,
        "commands": value,
        "notifications": value,
        "status_service": value,
        "workspace_persistence": value,
        "background_jobs": value,
    }


def test_desktop_rc_gate_passes_when_all_blockers_green():
    result = DesktopRCGate().evaluate(
        rc_version="2.1.7-rc1",
        components=_components(True),
        tests_passed=531,
    )

    assert result.passed is True
    assert result.status.value == "PASS"
    assert result.manifest.gate_status == "PASS"
    assert result.to_dict()["checklist"]["blocking_failures"] == []


def test_desktop_rc_gate_fails_on_missing_component():
    components = _components(True)
    components["background_jobs"] = False

    result = DesktopRCGate().evaluate(
        rc_version="2.1.7-rc1",
        components=components,
        tests_passed=530,
    )

    assert result.passed is False
    assert "background_jobs" in result.checklist.to_dict()["blocking_failures"]


def test_desktop_rc_gate_fails_on_failed_tests():
    result = DesktopRCGate().evaluate(
        rc_version="2.1.7-rc1",
        components=_components(True),
        tests_passed=530,
        tests_failed=1,
    )

    assert result.passed is False
    assert "tests" in result.checklist.to_dict()["blocking_failures"]


def test_desktop_rc_gate_keeps_non_blocking_warnings():
    result = DesktopRCGate().evaluate(
        rc_version="2.1.7-rc1",
        components=_components(True),
        tests_passed=530,
        warnings=["GUI toolkit is still headless-test only"],
    )

    assert result.passed is True
    assert result.to_dict()["checklist"]["warnings"] == ["warning_1"]
