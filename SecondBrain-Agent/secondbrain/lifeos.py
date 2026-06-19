from pathlib import Path
from .utils import now_date

AREAS = ["Gesundheit", "Finanzen", "Reisen", "Verein"]

def write_lifeos_indexes(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    base = vault / settings.get("vault_folders", {}).get("lifeos", "14_LifeOS")
    created = []
    for area in AREAS:
        folder = base / area
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{area}_Index.md"
        if not target.exists():
            target.write_text(
                f"# {area} Index\n\nAktualisiert: {now_date()}\n\n## Aktuelle Themen\n\n## Aufgaben\n\n## Quellen\n",
                encoding="utf-8"
            )
        created.append(target)
    return created
