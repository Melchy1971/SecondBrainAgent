import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
