from secondbrain.desktop.settings.release.settings_checklist import REQUIRED_SETTINGS_RC1_ITEMS, SettingsChecklist


def test_default_checklist_passes_all_required_items():
    checklist = SettingsChecklist.default()
    assert checklist.status() == "PASS"
    assert len(checklist.items) == len(REQUIRED_SETTINGS_RC1_ITEMS)


def test_checklist_from_missing_keys_fails():
    checklist = SettingsChecklist.from_keys(["settings_foundation"])
    assert checklist.status() == "FAIL"
