"""Zentrale Runtime-Konfiguration.

Prioritäten (hoch -> niedrig):
    1. os.environ
    2. <workspace>/.env
    3. <workspace>/config.json            (Workspace-Konfiguration)
    4. <AppData-Home>/config/config.json  (Benutzer-Konfiguration, via install.app_home)
    5. <workspace>/runtime/gui/settings.json (Legacy-GUI-Settings, nur lesend)
    6. dokumentierte Defaults (schema.py)

Secrets werden in JSON-Dateien ausschließlich als Referenzen gespeichert
({"ref": "ENV_NAME"}); Werte kommen nur aus os.environ oder .env.
"""

from .schema import CONFIG_KEYS, ConfigKey, KEYS_BY_NAME, SECTIONS
from .service import RuntimeConfig, runtime_config_status

__all__ = ["CONFIG_KEYS", "ConfigKey", "KEYS_BY_NAME", "SECTIONS", "RuntimeConfig", "runtime_config_status"]
