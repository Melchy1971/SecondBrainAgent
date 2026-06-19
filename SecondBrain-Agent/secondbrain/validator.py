from pathlib import Path
import sys
import importlib.util

REQUIRED_SETTINGS = [
    "vault_path",
    "inbox_path",
    "system_path",
]

REQUIRED_FOLDERS = [
    "00_Inbox",
    "01_Projekte",
    "02_Wissen",
    "04_Tasks",
    "05_Quellen",
    "06_Journal",
    "07_Graph",
    "90_Templates",
    "99_System",
]

def has_package(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def validate_environment(settings: dict, project_root: Path) -> dict:
    vault = Path(settings.get("vault_path", ""))
    inbox = Path(settings.get("inbox_path", ""))

    checks = []
    checks.append(("python_version", sys.version_info >= (3, 10), "Python 3.10+ erforderlich"))
    checks.append(("project_root", project_root.exists(), str(project_root)))
    checks.append(("vault_path", vault.exists(), str(vault)))
    checks.append(("inbox_path", inbox.exists(), str(inbox)))

    for key in REQUIRED_SETTINGS:
        checks.append((f"setting_{key}", bool(settings.get(key)), f"{key} gesetzt"))

    for folder in REQUIRED_FOLDERS:
        checks.append((f"vault_folder_{folder}", (vault / folder).exists(), str(vault / folder)))

    optional = {
        "pypdf": "PDF-Textextraktion",
        "requests": "Webseitenabruf",
        "bs4": "HTML-Bereinigung",
        "docx": "Word-Import",
        "openpyxl": "Excel-Import",
        "PIL": "Bildverarbeitung",
        "pytesseract": "OCR",
        "watchdog": "Echter Dateiwatcher",
    }

    for package, purpose in optional.items():
        checks.append((f"optional_{package}", has_package(package), purpose))

    ok_required = all(ok for name, ok, _ in checks if not name.startswith("optional_"))

    return {
        "ok": ok_required,
        "checks": checks,
    }
