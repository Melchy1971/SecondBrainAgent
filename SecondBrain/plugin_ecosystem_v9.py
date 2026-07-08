from pathlib import Path
from .v9_common import now_date, ensure

PLUGINS = [
    "Dashboard Plugin",
    "Meeting Plugin",
    "Project Plugin",
    "Decision Plugin",
    "Learning Plugin",
    "Voice Plugin",
    "AI Import Plugin",
]

def write_plugin_ecosystem(vault: Path) -> Path:
    folder = ensure(vault / "85_PluginEcosystem")
    target = folder / "Plugin_Ecosystem.md"
    lines = ["# Plugin Ecosystem", "", f"Aktualisiert: {now_date()}", "", "| Plugin | Status |", "|---|---|"]
    for p in PLUGINS:
        status = "active" if p == "Dashboard Plugin" else "prepared"
        lines.append(f"| {p} | {status} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
