from secondbrain.desktop.settings.release import SettingsRC1Gate, SettingsMetrics


def test_settings_rc1_gate_passes_with_safe_snapshot():
    result = SettingsRC1Gate().run({"schema_version": "1", "privacy_mode": True})
    assert result.status == "PASS"
    assert result.blockers == []
    assert result.checklist["status"] == "PASS"


def test_settings_rc1_gate_blocks_raw_secrets():
    result = SettingsRC1Gate().run({"schema_version": "1", "secrets": {"api_key": "plain"}})
    assert result.status == "BLOCKED"
    assert "SETTINGS_VALIDATION_FAILED" in result.blockers


def test_settings_rc1_gate_includes_metrics_snapshot():
    metrics = SettingsMetrics(snapshot_count=3, migration_count=2)
    result = SettingsRC1Gate().run({"schema_version": "1"}, metrics=metrics)
    assert result.metrics["snapshot_count"] == 3
    assert result.metrics["migration_count"] == 2


def test_settings_rc1_gate_result_is_serializable():
    result = SettingsRC1Gate().run({"schema_version": "1"})
    data = result.to_dict()
    assert data["status"] == "PASS"
    assert set(data) == {"status", "checklist", "validation", "metrics", "health", "blockers"}
