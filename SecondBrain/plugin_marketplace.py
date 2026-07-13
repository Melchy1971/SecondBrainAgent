from pathlib import Path
from .path import from_settings_mapping
from .utils import now_date

PLUGINS = ["SAP Connector", "Outlook Connector", "YouTube Connector", "TTR Connector", "myGEKKO Connector", "Home Assistant Connector", "Cisco Connector"]

def write_plugin_marketplace(settings: dict) -> Path:
    vault = from_settings_mapping(settings).vault
    folder = vault / "37_MCPHub"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Plugin_Marketplace.md"

    lines = ["# Plugin Marketplace", "", f"Aktualisiert: {now_date()}", "", "| Plugin | Status | Nutzen |", "|---|---|---|"]
    for p in PLUGINS:
        lines.append(f"| {p} | geplant | Integration vorbereiten |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
