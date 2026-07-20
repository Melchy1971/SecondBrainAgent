from pathlib import Path

import pytest

from secondbrain.desktop_native.windows_startup import WindowsStartupManager


def manager(tmp_path: Path, *, platform: str = "nt") -> WindowsStartupManager:
    root = tmp_path / "project with spaces"
    root.mkdir()
    (root / "launcher.py").write_text("", encoding="utf-8")
    return WindowsStartupManager(
        root,
        startup_dir=tmp_path / "Startup",
        platform=platform,
        python_executable=tmp_path / "Python Folder" / "python.exe",
    )


def test_startup_is_opt_in_and_reversible(tmp_path: Path):
    startup = manager(tmp_path)
    assert startup.status()["enabled"] is False
    assert startup.enable()["enabled"] is True
    content = startup.path.read_text(encoding="utf-8")
    assert f'cd /d "{startup.project_root}"' in content
    assert '"native-gui"' not in content
    assert " native-gui" in content
    assert startup.disable()["enabled"] is False


def test_enable_is_idempotent_and_does_not_duplicate_files(tmp_path: Path):
    startup = manager(tmp_path)
    startup.enable()
    first = startup.path.read_bytes()
    startup.enable()
    assert startup.path.read_bytes() == first
    assert list(startup.startup_dir.iterdir()) == [startup.path]


def test_non_windows_platform_is_blocked(tmp_path: Path):
    startup = manager(tmp_path, platform="posix")
    assert startup.status()["supported"] is False
    with pytest.raises(RuntimeError, match="nur unter Windows"):
        startup.enable()


def test_missing_launcher_is_rejected(tmp_path: Path):
    startup = manager(tmp_path)
    (startup.project_root / "launcher.py").unlink()
    with pytest.raises(FileNotFoundError):
        startup.enable()
