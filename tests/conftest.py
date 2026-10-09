import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Temp-Verzeichnisse im Repo statt im System-Temp: dort kann die ACL von
# %TEMP%\pytest-of-<user> defekt sein (WinError 5). Bewusst KEIN festes
# --basetemp: das wird bei jedem Lauf geloescht und kollidiert bei parallelen
# Laeufen. Mit PYTEST_DEBUG_TEMPROOT nutzt pytest seinen Standardmechanismus
# (pytest-of-<user>/pytest-N je Lauf, gesperrt, die letzten 3 bleiben erhalten).
# Ein explizites --basetemp hat weiterhin Vorrang.
_TEMPROOT = ROOT / ".pytest_tmp"
_TEMPROOT.mkdir(exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_TEMPROOT))


@pytest.fixture
def tk_display(capsys):
    """Fuer Tests, die echte Tk-Fenster erzeugen.

    Unter Windows scheitert die Tk-Initialisierung sporadisch ("couldn't read
    file .../init.tcl: No error"), solange pytest stdin/stdout/stderr auf
    Handle-Ebene umleitet (Standard --capture=fd). Die Erfassung wird daher fuer
    den ganzen Test ausgesetzt. Die Display-Pruefung laeuft bewusst hier statt
    in einem skipif zur Sammelzeit: dort griffe dieselbe Umleitung und ein
    sporadischer Fehler wuerde den Test stillschweigend ueberspringen.
    """
    try:
        import tkinter as tk
    except ImportError:
        pytest.skip("tkinter nicht installiert")
    with capsys.disabled():
        try:
            probe = tk.Tk()
        except tk.TclError as exc:
            pytest.skip(f"kein Display verfuegbar: {exc}")
        probe.destroy()
        yield tk


INTEGRATION_DIRS = {
    "integration",
    "connectors_runtime",
}

SLOW_TEST_FILES = {
    "tests/test_jarvis_hud_server.py",
    "tests/test_v3047_document_preview_center.py",
    "tests/test_v3052_parallel_import.py",
}


def _relative_item_path(item: pytest.Item) -> str:
    return Path(str(item.fspath)).resolve().relative_to(ROOT).as_posix()


def _is_integration(path: str) -> bool:
    parts = path.split("/")
    filename = parts[-1]
    return (
        len(parts) > 1 and parts[1] in INTEGRATION_DIRS
        or "integration" in filename
        or path.startswith("tests/storage/test_pg")
        or path.startswith("tests/vision/") and filename.endswith("_integration.py")
        or path.startswith("tests/voice/") and filename.endswith("_integration.py")
        or _is_live(path)
    )


def _is_connector(path: str) -> bool:
    return (
        path.startswith("tests/connectors/")
        or path.startswith("tests/connectors_runtime/")
        or "connector" in path
    )


def _is_live(path: str) -> bool:
    return path == "tests/embeddings/test_live_gated.py"


def _is_release(path: str) -> bool:
    return (
        path.startswith("tests/release/")
        or "/release/" in path
        or path.startswith("tests/version/")
        or path in {
            "tests/test_repo_doctor_v18_7.py",
            "tests/test_dependency_inventory_v18_8.py",
        }
    )


def _is_slow(path: str) -> bool:
    return (
        path in SLOW_TEST_FILES
        or _is_integration(path)
        or path.startswith("tests/vision/")
        or path.startswith("tests/voice/")
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        path = _relative_item_path(item)
        if _is_integration(path):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        if _is_slow(path):
            item.add_marker(pytest.mark.slow)
        if _is_connector(path):
            item.add_marker(pytest.mark.connector)
        if _is_release(path):
            item.add_marker(pytest.mark.release)
        if path.startswith("tests/desktop/") or "gui" in path or path.endswith("test_workspace_gui.py"):
            item.add_marker(pytest.mark.gui)


@pytest.fixture(scope="session")
def testdata_dir() -> Path:
    return ROOT / "tests" / "fixtures" / "data"


@pytest.fixture
def connector_payloads():
    from tests.fixtures.data import CONNECTOR_PAYLOADS

    return CONNECTOR_PAYLOADS


@pytest.fixture
def fake_connector_factory():
    from tests.fakes.connectors import FakeIncrementalConnector

    return FakeIncrementalConnector
