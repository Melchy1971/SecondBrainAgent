from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from secondbrain.native.layout_center.service import NativeLayoutService
from secondbrain.native.layout_center.models import LayoutSpec, PanelSpec


def test_layout_defaults_and_status(tmp_path: Path) -> None:
    service = NativeLayoutService(tmp_path)
    created = service.ensure_defaults()
    assert created["ok"] is True
    status = service.status()
    assert status["ok"] is True
    assert status["active"] == "default"
    assert status["layout_count"] >= 5


def test_activate_load_and_history(tmp_path: Path) -> None:
    service = NativeLayoutService(tmp_path)
    activated = service.activate("developer")
    assert activated["ok"] is True
    assert activated["active"] == "developer"
    loaded = service.load()
    assert loaded["ok"] is True
    assert loaded["layout"]["name"] == "developer"
    history = service.history()
    assert history["ok"] is True
    assert history["count"] >= 1


def test_export_import_custom_layout(tmp_path: Path) -> None:
    service = NativeLayoutService(tmp_path)
    custom = LayoutSpec(
        name="custom",
        title="Custom",
        description="Test layout",
        panels=[PanelSpec("one", "One", "dashboard", "center", True, 1, "dashboard-center-status")],
    )
    saved = service.save(custom)
    assert saved["ok"] is True
    target = tmp_path / "custom_export.json"
    exported = service.export("custom", target=target)
    assert exported["ok"] is True
    assert target.exists()

    imported_root = tmp_path / "imported"
    imported = NativeLayoutService(imported_root).import_layout(target, activate=True)
    assert imported["ok"] is True
    assert imported["active"] == "custom"


def test_cli_status_json(tmp_path: Path) -> None:
    code = "from secondbrain.native.layout_center.cli import main; raise SystemExit(main())"
    result = subprocess.run(
        [sys.executable, "-c", code, "layout-status", "--project-root", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["version"] == "v30.41"


def test_workspace_navigation_contains_layout(tmp_path: Path) -> None:
    from secondbrain.native.ai_workspace.service import AIWorkspaceService

    root = tmp_path
    (root / "secondbrain" / "native" / "layout_center").mkdir(parents=True)
    service = AIWorkspaceService(root)
    nav = service.navigation()
    layout = [item for item in nav["navigation"] if item["id"] == "layout"]
    assert layout
    assert layout[0]["command"] == "layout-status"
