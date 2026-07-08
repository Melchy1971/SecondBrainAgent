from pathlib import Path

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")

SUPPORTED = [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".csv", ".json", ".zip", ".png", ".jpg", ".jpeg"]

def ingest_file(path: str) -> Path:
    from secondbrain.importing import StreamingImportService
    service = StreamingImportService(Path(__file__).resolve().parents[1])
    service.import_document(path, source="document_ingestion_v101")
    return service.db_path

def write_ingestion_status() -> Path:
    target = VAULT / "130_DocumentIngestion" / "Document_Ingestion_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Document Ingestion v10.1\n\nUnterstützte Typen:\n\n" + "\n".join(f"- {x}" for x in SUPPORTED), encoding="utf-8")
    return target
