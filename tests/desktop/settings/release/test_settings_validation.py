from secondbrain.desktop.settings.release.settings_validation import SettingsRC1Validator


def test_validator_warns_when_schema_version_missing():
    result = SettingsRC1Validator().validate({})
    assert result.status == "WARNING"
    assert any(issue.code == "MISSING_SCHEMA_VERSION" for issue in result.issues)


def test_validator_fails_on_raw_secrets():
    result = SettingsRC1Validator().validate({"schema_version": "1", "secrets": {"x": "y"}})
    assert result.status == "FAIL"
