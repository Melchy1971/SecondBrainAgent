from pathlib import Path

from secondbrain.desktop_native import app, status
from secondbrain.version import get_version


def test_native_desktop_uses_canonical_version_everywhere():
    canonical = get_version()
    assert app.VERSION == canonical
    assert status.VERSION == canonical
    assert canonical in app.TITLE


def test_status_report_filename_is_derived_and_filesystem_safe():
    assert status._report_name("31.55.0") == "native_desktop_v31_55_0.json"
    assert status._report_name("31.55.0-rc.1+win") == "native_desktop_v31_55_0_rc_1_win.json"


def test_native_desktop_sources_contain_no_obsolete_fixed_version():
    app_source = Path(app.__file__).read_text(encoding="utf-8")
    status_source = Path(status.__file__).read_text(encoding="utf-8")
    assert 'VERSION = "30.25"' not in app_source
    assert 'VERSION = "30.25"' not in status_source
    assert "native_desktop_v30_25.json" not in status_source
