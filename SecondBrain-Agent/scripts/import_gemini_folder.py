from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.gemini_importer.importer import import_gemini_folder


def _imported(report: dict) -> int:
    return int(report.get("imported_count", report.get("imported_chats", 0)) or 0)


def _errors(report: dict) -> int:
    if "error_count" in report:
        return int(report.get("error_count") or 0)
    return 0 if report.get("ok", report.get("status") == "completed") else 1

EXPORTS = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\exports")

if __name__ == "__main__":
    reports = import_gemini_folder(EXPORTS, agent_root=PROJECT_ROOT, update_semantic_search=True)
    print("Gemini Ordnerimport abgeschlossen")
    print("ZIP-Dateien verarbeitet:", len(reports))
    print("Gesamt importiert:", sum(_imported(r) for r in reports))
    print("Gesamt Fehler:", sum(_errors(r) for r in reports))
