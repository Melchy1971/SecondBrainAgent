"""Resolve the Jarvis user-data home and scaffold its layout.

Installed builds must keep all writable data out of the (replaceable) program
directory so an update cannot destroy user data. This module is the single source
of truth for that location:

    JARVIS_HOME env  >  %APPDATA%\\Jarvis (Windows)  >  ~/.jarvis (other)

Program code should treat ``project_root()`` as the working root instead of a
path relative to the executable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

APP_NAME = "Jarvis"
ENV_HOME = "JARVIS_HOME"

# Writable state is grouped by purpose and never mixed with program files.
DATA_SUBDIRS = ("config", "database", "vault", "logs", "backups", "cache", "updates", "runtime", "data")


def resolve_home(env: Mapping[str, str] | None = None) -> Path:
    src = os.environ if env is None else env
    explicit = str(src.get(ENV_HOME, "")).strip()
    if explicit:
        return Path(explicit).expanduser()
    appdata = str(src.get("APPDATA", "")).strip()
    if appdata:
        return Path(appdata) / APP_NAME
    return Path(src.get("HOME", str(Path.home()))).expanduser() / ".jarvis"


def resolve_portable_home(program_dir: str | Path, env: Mapping[str, str] | None = None) -> Path:
    """Portable state is colocated explicitly and never leaks into AppData."""
    src = os.environ if env is None else env
    explicit = str(src.get(ENV_HOME, "")).strip()
    return Path(explicit).expanduser() if explicit else Path(program_dir) / "JarvisData"


def resolve_local_home(env: Mapping[str, str] | None = None) -> Path:
    """Machine-local, disposable state (cache, logs, downloads)."""
    src = os.environ if env is None else env
    local = str(src.get("LOCALAPPDATA", "")).strip()
    return (Path(local) / APP_NAME) if local else resolve_home(src) / "local"


def ensure_layout(home: str | Path) -> Path:
    home_path = Path(home)
    home_path.mkdir(parents=True, exist_ok=True)
    for sub in DATA_SUBDIRS:
        (home_path / sub).mkdir(parents=True, exist_ok=True)
    return home_path


def project_root(env: Mapping[str, str] | None = None) -> Path:
    """The root the installed app should use for config/data/logs/runtime."""
    return ensure_layout(resolve_home(env))
