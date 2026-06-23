from secondbrain.desktop.settings.release.settings_health_report import SettingsHealthReport


def test_health_report_status_rollup():
    assert SettingsHealthReport.from_checks({"a": "PASS"}).status == "PASS"
    assert SettingsHealthReport.from_checks({"a": "WARNING"}).status == "WARNING"
    assert SettingsHealthReport.from_checks({"a": "FAIL"}).status == "FAIL"
