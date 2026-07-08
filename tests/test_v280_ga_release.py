from secondbrain.ga.installer_manager import InstallerManager
from secondbrain.ga.e2e_system_suite import EndToEndSystemSuite
from secondbrain.ga.version_manifest import MANIFEST


def test_installer():
    assert InstallerManager().build("windows")["status"] == "PASS"


def test_e2e_suite():
    result = EndToEndSystemSuite().run(["p1", "p2", "p3"])
    assert result["modules"] == 3


def test_manifest():
    assert MANIFEST["version"] == "1.0.0"
