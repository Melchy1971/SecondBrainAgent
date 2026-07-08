from secondbrain.mobile.sync_manager import MobileSyncManager
from secondbrain.mobile.install_manager import InstallManager
from secondbrain.gates.p7_completion_report import build_p7_completion_report


def test_sync_manager():
    manager = MobileSyncManager()
    manager.schedule("memory")
    assert manager.jobs() == ["memory"]


def test_install_manager():
    result = InstallManager().check_update("1.0", "1.1")
    assert result["update_available"]


def test_completion_report():
    report = build_p7_completion_report()
    assert report["status"] == "PASS"
    assert report["next_phase"] == "P8_AUTONOMY"
