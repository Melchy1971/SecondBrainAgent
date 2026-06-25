from __future__ import annotations

import json
from pathlib import Path

from secondbrain.gui.bootstrap import bootstrap_status, ensure_env, ensure_runtime_dirs, write_bootstrap_report
from secondbrain.gui.launch import GUI_COMMANDS


def test_bootstrap_repairs_env_and_runtime_dirs(tmp_path: Path) -> None:
    (tmp_path / "launcher.py").write_text("print('x')", encoding="utf-8")
    payload = bootstrap_status(tmp_path, repair=True)
    assert payload["ok"] is True
    assert (tmp_path / ".env").exists()
    assert (tmp_path / "runtime" / "reports").exists()
    assert payload["env"]["SECONDBRAIN_EMBEDDING_PROVIDER"] == "local"


def test_bootstrap_report_written(tmp_path: Path) -> None:
    (tmp_path / "launcher.py").write_text("print('x')", encoding="utf-8")
    payload = write_bootstrap_report(tmp_path, repair=True)
    report = Path(payload["report_path"])
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["schema"] == "secondbrain.bootstrap.v1"
    assert data["version"] == "30.21"


def test_jarvis_alias_registered() -> None:
    assert "jarvis" in GUI_COMMANDS
    assert "gui-bootstrap" in GUI_COMMANDS


def test_env_defaults_are_idempotent(tmp_path: Path) -> None:
    first = ensure_env(tmp_path, repair=True)
    second = ensure_env(tmp_path, repair=True)
    assert first["ok"] is True
    assert second["ok"] is True
    assert second["missing_defaults"] == []


def test_runtime_dirs_are_writable(tmp_path: Path) -> None:
    result = ensure_runtime_dirs(tmp_path, repair=True)
    assert result["ok"] is True
    assert all(item["writable"] for item in result["checks"])
