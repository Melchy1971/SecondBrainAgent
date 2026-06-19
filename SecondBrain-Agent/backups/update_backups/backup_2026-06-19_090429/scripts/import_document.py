from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.document_connectors import import_document_to_inbox

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\import_document.py <Dateipfad>")
        raise SystemExit(1)
    settings = load_settings(PROJECT_ROOT)
    target = import_document_to_inbox(settings, sys.argv[1])
    print(f"Dokument importiert: {target}")
