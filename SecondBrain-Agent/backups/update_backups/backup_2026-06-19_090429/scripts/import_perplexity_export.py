from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.perplexity_importer.importer import import_perplexity_export

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\import_perplexity_export.py \"C:\\Downloads\\perplexity-export.zip\"")
        raise SystemExit(1)

    report = import_perplexity_export(sys.argv[1], agent_root=PROJECT_ROOT, update_semantic_search=True)
    print("Perplexity Import abgeschlossen")
    print("Importiert:", report["imported_count"])
    print("Fehler:", report["error_count"])
    print("Report:", report["report_md"])
