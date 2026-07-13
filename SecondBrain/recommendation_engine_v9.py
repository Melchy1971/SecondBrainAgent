from __future__ import annotations

from pathlib import Path

from .recommendations import write_recommendations as _write_recommendations


def write_recommendations(vault: Path) -> Path:
    settings = {
        "vault_path": str(vault),
        "project_root": str(vault.parent),
        "incoming_path": str(vault.parent / "SecondBrain-Inbox"),
        "vault_folders": {"recommendations": "09_Recommendations", "projects": "01_Projekte", "tasks": "04_Tasks"},
    }
    return _write_recommendations(settings)
