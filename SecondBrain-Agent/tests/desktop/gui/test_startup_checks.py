from secondbrain.desktop.gui.startup_checks import StartupChecks, StartupCheck

def test_startup_checks_pass_by_default():
    checks = StartupChecks()
    results = checks.run()
    assert all(result.status == "PASS" for result in results)
    assert checks.is_blocked(results) is False

def test_required_failed_check_blocks_startup():
    checks = StartupChecks([StartupCheck("settings", True, lambda: False)])
    results = checks.run()
    assert checks.is_blocked(results) is True
