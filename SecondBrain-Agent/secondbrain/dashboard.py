from pathlib import Path
import json
from .utils import now_date, now_datetime

def _safe_count(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return len([p for p in path.rglob(pattern) if p.is_file()])

def write_dashboard(settings: dict, project_root: Path, imported_items: list[dict]) -> Path | None:
    if not settings.get("dashboard_enabled", True):
        return None

    vault = Path(settings["vault_path"])
    inbox = Path(settings["inbox_path"])
    system_folder = settings.get("vault_folders", {}).get("system", "99_System")
    target_dir = vault / system_folder / "dashboard"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "SecondBrain-Agent Dashboard.md"

    cache_file = project_root / "cache" / "processed_files.json"
    processed_count = 0
    if cache_file.exists():
        try:
            processed_count = len(json.loads(cache_file.read_text(encoding="utf-8")))
        except Exception:
            processed_count = 0

    lines = [
        "# SecondBrain-Agent Dashboard",
        "",
        f"Aktualisiert: {now_datetime()}",
        "",
        "## Status",
        "",
        f"- Neue Imports im letzten Lauf: {len(imported_items)}",
        f"- Insgesamt verarbeitete Dateien: {processed_count}",
        f"- Dateien aktuell in Inbox: {_safe_count(inbox)}",
        f"- Archivierte Dateien: {_safe_count(project_root / 'archive' / 'processed')}",
        f"- Fehlerhafte Dateien: {_safe_count(project_root / 'archive' / 'failed')}",
        "",
        "## Letzter Import",
        ""
    ]

    if imported_items:
        for item in imported_items:
            lines.append(f"- [[{Path(item['target']).stem}]] | `{item['type']}` | `{item['provider']}`")
    else:
        lines.append("- Keine neuen Dateien.")

    lines += [
        "",
        "## Betriebsrisiken",
        "",
        "- Automatische Klassifikation kann falsch liegen.",
        "- PDF-OCR ist noch nicht vollständig.",
        "- Webseiten können unvollständig extrahiert werden.",
        "- Review Queue regelmäßig prüfen.",
        "",
        "## Relevante Systemdateien",
        "",
        "- [[../reports/" + now_date() + "_import-report]]",
        "- [[../claude_review/" + now_date() + "_review-queue]]",
    ]

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
