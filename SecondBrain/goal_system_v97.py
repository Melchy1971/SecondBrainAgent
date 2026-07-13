from __future__ import annotations

from pathlib import Path

from .goal_engine import write_goal_map as _write_goal_map
from .v97_common import VAULT

CATEGORIES = {
    "Beruf": ["sap", "prozess", "telekom", "projekt", "management"],
    "Projekte": ["secondbrain", "jarvis", "wissensdatenbank", "code", "release"],
    "Lernen": ["lernen", "kurs", "skill", "ki", "python"],
    "Gesundheit": ["gesundheit", "diabetes", "training", "gewicht"],
    "Verein": ["ttc", "verein", "tischtennis", "turnier"],
    "Privat": ["reise", "familie", "haus", "finanzen"],
}

def write_goal_map(vault: Path = VAULT) -> Path:
    project_root = vault.parent
    settings = {
        "vault_path": str(vault),
        "project_root": str(project_root),
        "incoming_path": str(project_root / "SecondBrain-Inbox"),
        "vault_folders": {},
    }
    return _write_goal_map(project_root, settings)
