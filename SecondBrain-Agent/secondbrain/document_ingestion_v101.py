from pathlib import Path
from datetime import datetime
import shutil

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")

SUPPORTED = [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".csv", ".json", ".zip", ".png", ".jpg", ".jpeg"]

def ingest_file(path: str) -> Path:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(str(src))
    target_dir = INBOX / "Documents" / "imports"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / src.name
    if target.exists():
        target = target_dir / f"{src.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{src.suffix}"
    shutil.copy2(src, target)

    report_dir = VAULT / "130_DocumentIngestion"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_document-ingestion.md"
    report.write_text(f"""# Document Ingestion v10.1

Quelle: `{src}`
Ziel: `{target}`
Typ: `{src.suffix.lower()}`
Status: vorbereitet

Hinweis:
- Datei wurde in die Inbox kopiert.
- Fachparser/OCR laufen in späterer Ausbaustufe.
""", encoding="utf-8")
    return report

def write_ingestion_status() -> Path:
    target = VAULT / "130_DocumentIngestion" / "Document_Ingestion_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Document Ingestion v10.1\n\nUnterstützte Typen:\n\n" + "\n".join(f"- {x}" for x in SUPPORTED), encoding="utf-8")
    return target
