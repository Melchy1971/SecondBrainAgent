from pathlib import Path
from .utils import now_date

AREAS = ["CRM", "DMS", "Projects", "Finance", "Health", "Verein"]

def write_personal_erp_indexes(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    base = vault / "33_PersonalERP"
    created = []
    for area in AREAS:
        folder = base / area
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{area}_Index.md"
        if not target.exists():
            target.write_text(f"# {area} Index\n\nAktualisiert: {now_date()}\n\n## Datensätze\n\n## Aufgaben\n\n## Risiken\n", encoding="utf-8")
        created.append(target)
    return created
