"""Migrate existing local Jarvis data into the AppData home.

Runs on every launch. It copies known data directories from a source location
(a previous portable/dev checkout) into the home ONLY when the target is missing
or empty, so a re-run or an in-place update never overwrites newer user data.
A marker file records what was migrated and when.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.install.app_home import ensure_layout

# Directories to lift into the home. Vault directories use the app's default names.
MIGRATE_DIRS = ("config", "data", "logs", "runtime", "SecondBrain", "SecondBrain-Inbox")
MARKER = ".jarvis_migrated.json"


def _is_empty(path: Path) -> bool:
    return not path.exists() or not any(path.iterdir())


def migrate_local_data(
    source_root: str | Path,
    home: str | Path,
    *,
    version: str = "",
    overwrite: bool = False,
) -> dict[str, Any]:
    source = Path(source_root)
    home_path = ensure_layout(home)
    migrated: list[str] = []
    skipped: list[str] = []

    for name in MIGRATE_DIRS:
        src = source / name
        if not src.exists() or not src.is_dir():
            continue
        dst = home_path / name
        if dst.exists() and not _is_empty(dst) and not overwrite:
            skipped.append(name)  # preserve existing user data (update safety)
            continue
        if dst.exists() and overwrite:
            shutil.rmtree(dst)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        migrated.append(name)

    marker_path = home_path / MARKER
    history: list[dict[str, Any]] = []
    if marker_path.exists():
        try:
            history = json.loads(marker_path.read_text(encoding="utf-8")).get("history", [])
        except Exception:  # noqa: BLE001 - a broken marker must not block startup
            history = []
    history.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "migrated": migrated,
        "skipped": skipped,
        "source": str(source),
    })
    marker_path.write_text(json.dumps({"schema": "jarvis.migration.v1", "history": history},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    return {"migrated": migrated, "skipped": skipped, "home": str(home_path), "marker": str(marker_path)}
