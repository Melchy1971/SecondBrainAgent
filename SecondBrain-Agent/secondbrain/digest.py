from pathlib import Path
from .utils import now_date

def write_digest(settings: dict, imported_items: list[dict]) -> Path | None:
    if not settings.get("daily_digest", True):
        return None

    vault = Path(settings["vault_path"])
    system_folder = settings.get("vault_folders", {}).get("system", "99_System")
    target_dir = vault / system_folder / "digests"
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / f"{now_date()}_daily-digest.md"
    lines = [
        f"# Daily Digest {now_date()}",
        "",
        "## Importierte Inhalte",
        ""
    ]

    if not imported_items:
        lines.append("- Keine neuen Inhalte.")
    else:
        for item in imported_items:
            lines.append(f"- [[{Path(item['target']).stem}]] | Typ: `{item['type']}` | Quelle: `{item['provider']}`")

    lines += ["", "## Risiken", "", "- Manuelle Prüfung der automatisch klassifizierten Inhalte erforderlich."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
