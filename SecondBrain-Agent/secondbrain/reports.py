from pathlib import Path
from .utils import now_date, now_datetime

def write_import_report(settings: dict, imported_items: list[dict], project_root: Path) -> Path:
    vault = Path(settings["vault_path"])
    system_folder = settings.get("vault_folders", {}).get("system", "99_System")
    target_dir = vault / system_folder / "reports"
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / f"{now_date()}_import-report.md"

    lines = [
        f"# Import Report {now_datetime()}",
        "",
        "## Kennzahlen",
        "",
        f"- Neue Dateien: {len(imported_items)}",
        "",
        "## Dateien",
        ""
    ]

    if not imported_items:
        lines.append("- Keine neuen Dateien importiert.")
    else:
        for item in imported_items:
            lines.append(f"- Quelle: `{item['source']}`")
            lines.append(f"  - Ziel: `[[{Path(item['target']).stem}]]`")
            lines.append(f"  - Typ: `{item['type']}`")
            lines.append(f"  - Provider: `{item['provider']}`")
            lines.append(f"  - Tags: `{', '.join(item.get('tags', []))}`")
            lines.append("")

    lines += [
        "",
        "## Prüfhinweise",
        "",
        "- Automatische Klassifikation stichprobenartig prüfen.",
        "- PDF-Dateien ohne extrahierten Text benötigen OCR.",
        "- Webseiten können gekürzte oder fehlerhafte Inhalte enthalten.",
    ]

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
