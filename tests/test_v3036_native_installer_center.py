from __future__ import annotations

import json
from pathlib import Path

from secondbrain.native.installer_center import installer_status, installer_plan, write_installer_artifacts


def _project(tmp_path: Path) -> Path:
    root = tmp_path
    (root / "secondbrain" / "native").mkdir(parents=True)
    (root / "secondbrain" / "native" / "workspace_center.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "native" / "voice_control_center.py").write_text("", encoding="utf-8")
    (root / "launcher.py").write_text("print('jarvis')", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname='secondbrain'\n", encoding="utf-8")
    (root / "requirements-runtime.txt").write_text("", encoding="utf-8")
    (root / "requirements-voice.txt").write_text("", encoding="utf-8")
    (root / "Jarvis.bat").write_text("python launcher.py", encoding="utf-8")
    return root


def test_installer_status_ready(tmp_path: Path) -> None:
    root = _project(tmp_path)
    payload = installer_status(root)
    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert "workspace_center" in payload["native_modules"]
    assert any(c["key"] == "native_voice" for c in payload["checks"])


def test_installer_plan_contains_native_start(tmp_path: Path) -> None:
    root = _project(tmp_path)
    payload = installer_plan(root)
    assert payload["ok"] is True
    assert payload["primary_start"] == "python launcher.py"
    names = {a["name"] for a in payload["artifacts"]}
    assert "Start-Jarvis-Native.bat" in names
    assert "Install-Jarvis-Native.ps1" in names


def test_write_installer_artifacts(tmp_path: Path) -> None:
    root = _project(tmp_path)
    payload = write_installer_artifacts(root)
    assert payload["ok"] is True
    assert "dist/native-installer/Start-Jarvis-Native.bat" in payload["written"]
    assert (root / "dist/native-installer/Install-Jarvis-Native.ps1").exists()
    report = root / "runtime/native/installer/installer_v30_36.json"
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["version"] == "30.36"


def test_installer_status_blocks_missing_launcher(tmp_path: Path) -> None:
    root = tmp_path
    (root / "secondbrain" / "native").mkdir(parents=True)
    payload = installer_status(root)
    assert payload["ok"] is False
    keys = {b["key"] for b in payload["blockers"]}
    assert "launcher" in keys
