from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


_GEOMETRY = re.compile(r"^(\d{3,5})x(\d{3,5})([+-]\d{1,6})([+-]\d{1,6})$")


class InstanceAlreadyRunning(RuntimeError):
    pass


class SingleInstanceLock:
    def __init__(self, project_root: str | Path) -> None:
        self.path = Path(project_root).resolve() / "runtime" / "native" / "desktop.pid"
        self._owned = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _attempt in range(2):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    os.write(fd, str(os.getpid()).encode("ascii"))
                finally:
                    os.close(fd)
                self._owned = True
                return
            except FileExistsError:
                if self._owner_alive():
                    raise InstanceAlreadyRunning(f"Jarvis Desktop läuft bereits (PID {self._read_pid()})")
                self.path.unlink(missing_ok=True)
        raise InstanceAlreadyRunning("Jarvis Desktop konnte die Instanzsperre nicht übernehmen")

    def release(self) -> None:
        if self._owned:
            self.path.unlink(missing_ok=True)
            self._owned = False

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()

    def _read_pid(self) -> int:
        try:
            return int(self.path.read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            return -1

    def _owner_alive(self) -> bool:
        pid = self._read_pid()
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True


class WindowStateStore:
    def __init__(self, project_root: str | Path) -> None:
        self.path = Path(project_root).resolve() / "runtime" / "native" / "window_state.json"

    def load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        geometry = str(payload.get("geometry") or "")
        view = str(payload.get("view") or "Dashboard")
        return {"geometry": geometry, "view": view} if self.valid_geometry(geometry) else {"view": view}

    def save(self, *, geometry: str, view: str) -> None:
        if not self.valid_geometry(geometry):
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({"schema": "secondbrain.desktop.window.v31_40", "geometry": geometry, "view": view}, indent=2), encoding="utf-8")
        temp.replace(self.path)

    @staticmethod
    def valid_geometry(value: str) -> bool:
        match = _GEOMETRY.fullmatch(str(value or ""))
        if not match:
            return False
        width, height = int(match.group(1)), int(match.group(2))
        return 640 <= width <= 10000 and 480 <= height <= 10000
