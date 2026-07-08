from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from secondbrain.native.desktop_health.service import NativeDesktopHealthService


ROOT = Path(__file__).resolve().parents[1]


def test_repository_desktop_health_passes() -> None:
    payload = NativeDesktopHealthService(ROOT).status()
    assert payload["ok"] is True
    assert payload["version"] == "v30.46"
    assert payload["failed_checks"] == []


def test_health_is_blocked_for_incomplete_root(tmp_path: Path) -> None:
    payload = NativeDesktopHealthService(tmp_path).status()
    assert payload["ok"] is False
    assert "launcher" in payload["failed_checks"]
    assert "workspace" in payload["failed_checks"]


def test_report_is_only_written_explicitly(tmp_path: Path) -> None:
    service = NativeDesktopHealthService(tmp_path)
    service.status()
    assert not (tmp_path / "runtime" / "reports").exists()
    payload = service.write_report()
    assert Path(payload["report_path"]).is_file()


def test_health_cli_returns_json() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "launcher.py"), "native-desktop-health", "--project-root", str(ROOT)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["version"] == "v30.46"


def test_job_queue_launcher_alias(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "launcher.py"), "job-queue-status", "--project-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["version"] == "30.44"
