from pathlib import Path
from .utils import now_date

def build_vault_index(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    system_folder = settings.get("vault_folders", {}).get("system", "99_System")
    target_dir = vault / system_folder / "indexes"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "vault_index.md"

    notes = []
    for p in vault.rglob("*.md"):
        if ".obsidian" in p.parts:
            continue
        rel = p.relative_to(vault)
        notes.append(rel)

    lines = [
        "# Vault Index",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        f"Dateien: {len(notes)}",
        ""
    ]

    current_folder = None
    for rel in sorted(notes, key=lambda x: str(x).lower()):
        folder = str(rel.parent)
        if folder != current_folder:
            current_folder = folder
            lines.append(f"\n## {folder}\n")
        lines.append(f"- [[{rel.stem}]]")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
