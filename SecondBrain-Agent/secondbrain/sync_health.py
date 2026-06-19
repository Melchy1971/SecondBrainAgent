from pathlib import Path
from .utils import now_date, now_datetime

SYNC_MARKERS = {
    ".git": "Git",
    ".obsidian": "Obsidian",
}

def write_sync_health(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "sync"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_sync-health.md"

    markers = []
    for marker, label in SYNC_MARKERS.items():
        markers.append((label, (vault / marker).exists()))

    cloud_markers = ["OneDrive", "Syncthing", "Dropbox", "iCloud"]
    path_str = str(vault).lower()
    for marker in cloud_markers:
        markers.append((marker, marker.lower() in path_str))

    lines = [
        f"# Sync Health {now_datetime()}",
        "",
        "| System | Erkannt |",
        "|---|---|"
    ]
    for label, found in markers:
        lines.append(f"| {label} | {'ja' if found else 'nein'} |")

    lines += [
        "",
        "## Bewertung",
        "",
        "- Mehrere Sync-Systeme parallel erhöhen Konfliktrisiko.",
        "- Konfliktbericht regelmäßig prüfen.",
        "- Markdown bleibt Source of Truth.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
