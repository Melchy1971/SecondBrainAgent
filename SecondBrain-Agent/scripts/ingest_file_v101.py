from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.document_ingestion_v101 import ingest_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\ingest_file_v101.py <datei>")
        raise SystemExit(1)
    print(ingest_file(sys.argv[1]))
