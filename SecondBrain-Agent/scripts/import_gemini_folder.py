from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.gemini_importer.importer import import_gemini_folder

EXPORTS = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\exports")

if __name__ == "__main__":
    reports = import_gemini_folder(EXPORTS, agent_root=PROJECT_ROOT, update_semantic_search=True)
    print("Gemini Ordnerimport abgeschlossen")
    print("ZIP-Dateien verarbeitet:", len(reports))
    print("Gesamt importiert:", sum(r["imported_count"] for r in reports))
    print("Gesamt Fehler:", sum(r["error_count"] for r in reports))
