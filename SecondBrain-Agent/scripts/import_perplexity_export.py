from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.perplexity_importer.importer import import_perplexity_export


def _imported(report: dict) -> int:
    return int(report.get("imported_count", report.get("imported_chats", 0)) or 0)


def _errors(report: dict) -> int:
    if "error_count" in report:
        return int(report.get("error_count") or 0)
    return 0 if report.get("ok", report.get("status") == "completed") else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\import_perplexity_export.py \"C:\\Downloads\\perplexity-export.zip\"")
        raise SystemExit(1)

    report = import_perplexity_export(sys.argv[1], agent_root=PROJECT_ROOT, update_semantic_search=True)
    print("Perplexity Import abgeschlossen")
    print("Importiert:", _imported(report))
    print("Fehler:", _errors(report))
    print("Report:", report.get("report_md", report.get("session_id", "-")))
