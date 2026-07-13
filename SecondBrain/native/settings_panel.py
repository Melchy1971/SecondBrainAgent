"""GUI-Adapter über der zentralen RuntimeConfig.

Enthält keine eigene Persistenz- oder Validierungslogik mehr: GUI und CLI
nutzen dieselbe Konfiguration (secondbrain.runtime_config). Der Adapter
liefert die maskierte Sektionssicht für den Einstellungen-Tab und reicht
Änderungen an RuntimeConfig durch (Nicht-Secrets -> config.json,
Secrets -> .env, maskierte Secrets werden übersprungen).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.runtime_config import RuntimeConfig
from secondbrain.runtime_config.service import SECRET_MASK

SCHEMA = "secondbrain.native.settings_panel.v2"

__all__ = ["NativeSettingsPanel", "SECRET_MASK", "SCHEMA"]


class NativeSettingsPanel:
    def __init__(self, project_root: str | Path | None = None):
        self.config = RuntimeConfig(project_root)

    def render(self) -> dict[str, Any]:
        """Gegliederte, maskierte Sektionssicht inkl. Startvalidierung."""
        snapshot = self.config.snapshot()
        snapshot["panel_schema"] = SCHEMA
        return snapshot

    def save(self, values: dict[str, str], scope: str = "workspace") -> dict[str, Any]:
        return self.config.set_values(values, scope=scope)

    def startup_status(self) -> dict[str, Any]:
        return self.config.startup_status()
