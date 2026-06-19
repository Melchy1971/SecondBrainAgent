from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.perplexity_importer.importer import import_perplexity_folder

EXPORTS = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\Perplexity\exports")

if __name__ == "__main__":
    reports = import_perplexity_folder(EXPORTS, agent_root=PROJECT_ROOT, update_semantic_search=True)
    print("Perplexity Ordnerimport abgeschlossen")
    print("ZIP-Dateien verarbeitet:", len(reports))
    print("Gesamt importiert:", sum(r["imported_count"] for r in reports))
    print("Gesamt Fehler:", sum(r["error_count"] for r in reports))
