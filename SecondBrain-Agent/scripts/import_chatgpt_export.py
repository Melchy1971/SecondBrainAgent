from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.chatgpt_importer.importer import import_chatgpt_zip

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\import_chatgpt_export.py \"C:\\Downloads\\chatgpt-export.zip\"")
        raise SystemExit(1)

    report = import_chatgpt_zip(
        zip_path=sys.argv[1],
        agent_root=PROJECT_ROOT,
        update_semantic_search=True,
        update_secondbrain_os=False,
    )

    print("ChatGPT Import abgeschlossen")
    print("Importiert:", report["imported_count"])
    print("Fehler:", report["error_count"])
    print("Report:", report["report_md"])
