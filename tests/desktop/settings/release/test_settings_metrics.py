from secondbrain.desktop.settings.release.settings_metrics import SettingsMetrics


def test_metrics_records_timing_and_failure_counts():
    metrics = SettingsMetrics()
    value = metrics.record_timing("load", lambda: "ok")
    metrics.mark_validation_failed()
    metrics.mark_corruption_detected(2)
    data = metrics.to_dict()
    assert value == "ok"
    assert data["load_time_ms"] >= 0
    assert data["failed_validations"] == 1
    assert data["corrupted_settings_detected"] == 2
