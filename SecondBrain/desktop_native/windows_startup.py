from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


class WindowsStartupManager:
    FILE_NAME = "JarvisSecondBrain.cmd"

    def __init__(
        self,
        project_root: str | Path,
        *,
        startup_dir: str | Path | None = None,
        platform: str | None = None,
        python_executable: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.platform = platform or os.name
        self.python_executable = Path(python_executable or sys.executable).resolve()
        self.startup_dir = Path(startup_dir).resolve() if startup_dir else self._default_startup_dir()
        self.path = self.startup_dir / self.FILE_NAME

    def status(self) -> dict[str, Any]:
        supported = self.platform == "nt"
        return {
            "schema": "secondbrain.desktop.windows_startup.v31_42",
            "supported": supported,
            "enabled": supported and self.path.is_file(),
            "path": str(self.path),
            "project_root": str(self.project_root),
        }

    def enable(self) -> dict[str, Any]:
        self._require_windows()
        launcher = self.project_root / "launcher.py"
        if not launcher.is_file():
            raise FileNotFoundError(f"launcher.py fehlt: {launcher}")
        self.startup_dir.mkdir(parents=True, exist_ok=True)
        content = (
            "@echo off\r\n"
            f'cd /d "{self.project_root}"\r\n'
            f'start "Jarvis SecondBrain" /min "{self.python_executable}" "{launcher}" native-gui\r\n'
        )
        temp = self.path.with_suffix(".tmp")
        temp.write_text(content, encoding="utf-8", newline="")
        temp.replace(self.path)
        return self.status()

    def disable(self) -> dict[str, Any]:
        self._require_windows()
        self.path.unlink(missing_ok=True)
        return self.status()

    def _require_windows(self) -> None:
        if self.platform != "nt":
            raise RuntimeError("Windows-Autostart ist nur unter Windows verfügbar")

    @staticmethod
    def _default_startup_dir() -> Path:
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return Path("__windows_startup_unavailable__")
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
