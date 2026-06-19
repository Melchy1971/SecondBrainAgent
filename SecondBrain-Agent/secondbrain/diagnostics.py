from pathlib import Path
from .utils import now_date, now_datetime
from .validator import validate_environment
from .config import load_settings

def write_diagnostics(project_root: Path) -> Path:
    settings = load_settings(project_root)
    result = validate_environment(settings, project_root)

    vault = Path(settings.get("vault_path", project_root))
    target_dir = vault / "99_System" / "diagnostics"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_diagnostics.md"

    lines = [
        f"# Diagnose {now_datetime()}",
        "",
        f"Gesamtstatus: {'OK' if result['ok'] else 'BLOCKIERT'}",
        "",
        "| Check | Status | Hinweis |",
        "|---|---|---|"
    ]

    for name, ok, hint in result["checks"]:
        lines.append(f"| {name} | {'OK' if ok else 'FEHLT'} | {hint} |")

    lines += [
        "",
        "## Maßnahmen",
        "",
        "- Fehlende Pflichtordner anlegen.",
        "- Optionale Pakete über `pip install -r requirements-optional.txt` installieren.",
        "- Pfade in `config/settings.yaml` prüfen.",
    ]

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
