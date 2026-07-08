import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


SUPPORTED_EXTENSIONS = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".eml": "message/rfc822",
}


class DocumentUnderstandingRuntime:
    def __init__(self, root=".", db_path=None, registry=None):
        # Compatibility mode for P1.3 parser service tests: when the first
        # argument exposes ingest_text, this runtime acts as a thin parser
        # wrapper around ParsedDocumentIngestionService. Otherwise it keeps the
        # legacy SQLite-backed runtime contract used by earlier tests and UI code.
        if hasattr(root, "ingest_text"):
            from .ingestion_contract import ParsedDocumentIngestionService
            from .parsers import default_parser_registry

            self._service_mode = True
            self.ingestion_runtime = root
            self.registry = registry or default_parser_registry()
            self.service = ParsedDocumentIngestionService(root, self.registry)
            return

        self._service_mode = False
        self.root = Path(root)
        self.data_dir = self.root / "data" / "document_understanding"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "documents.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    path TEXT,
                    mime_type TEXT,
                    status TEXT NOT NULL,
                    text TEXT,
                    metadata_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    token_estimate INTEGER DEFAULT 0,
                    citation TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS extracted_tables (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    title TEXT,
                    rows_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    kind TEXT DEFAULT 'concept',
                    confidence REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_id TEXT,
                    label TEXT NOT NULL,
                    source_path TEXT,
                    location TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path)}

    def status(self):
        if getattr(self, "_service_mode", False):
            return {"version": "16.3", "mode": "parser_service"}
        self.migrate()
        with self.connect() as conn:
            counts = {}
            for table in ["documents", "chunks", "extracted_tables", "entities", "citations"]:
                counts[table] = conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        return {"version": "16.3", "supported_extensions": sorted(SUPPORTED_EXTENSIONS), "counts": counts}

    def detect_mime(self, path):
        suffix = Path(path).suffix.lower()
        return SUPPORTED_EXTENSIONS.get(suffix, "application/octet-stream")

    def read_file_text(self, path):
        p = Path(path)
        suffix = p.suffix.lower()
        if suffix in {".txt", ".md", ".eml"}:
            return p.read_text(encoding="utf-8", errors="ignore"), {"reader": "plain_text"}
        if suffix == ".docx":
            return self._read_docx(p)
        if suffix == ".xlsx":
            return self._read_xlsx(p)
        if suffix == ".pptx":
            return self._read_pptx(p)
        if suffix == ".pdf":
            return self._read_pdf_stub(p)
        return "", {"reader": "unsupported", "warning": "file_type_not_supported"}

    def _read_docx(self, path):
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml")
            root = ET.fromstring(xml)
            texts = [node.text for node in root.iter() if node.text]
            return "\n".join(texts), {"reader": "docx_xml"}
        except Exception as exc:
            return "", {"reader": "docx_xml", "error": str(exc)}

    def _read_xlsx(self, path):
        try:
            import zipfile
            with zipfile.ZipFile(path) as z:
                names = [n for n in z.namelist() if n.startswith("xl/worksheets/")]
            return "\n".join(names), {"reader": "xlsx_zip_manifest", "tables_detected": len(names)}
        except Exception as exc:
            return "", {"reader": "xlsx_zip_manifest", "error": str(exc)}

    def _read_pptx(self, path):
        try:
            import zipfile
            import re
            texts = []
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    if name.startswith("ppt/slides/") and name.endswith(".xml"):
                        raw = z.read(name).decode("utf-8", errors="ignore")
                        texts.extend(re.findall(r"<a:t>(.*?)</a:t>", raw))
            return "\n".join(texts), {"reader": "pptx_xml", "slides_text_fragments": len(texts)}
        except Exception as exc:
            return "", {"reader": "pptx_xml", "error": str(exc)}

    def _read_pdf_stub(self, path):
        try:
            import fitz

            doc = fitz.open(path)
            try:
                text = "\n".join(page.get_text("text") for page in doc)
                return text, {"reader": "pymupdf", "pages": doc.page_count, "path": str(path)}
            finally:
                doc.close()
        except Exception:
            try:
                import pypdf

                reader = pypdf.PdfReader(str(path))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text, {"reader": "pypdf", "pages": len(reader.pages), "path": str(path)}
            except Exception as exc:
                return "", {"reader": "pdf_stub", "warning": "pdf_text_extraction_failed", "error": str(exc), "path": str(path)}

    def chunk_text(self, text, size=900, overlap=120):
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(0, end - overlap)
        return chunks

    def extract_entities(self, text):
        candidates = sorted(set(re.findall(r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,}\b", text or "")))
        return [{"name": c, "kind": "concept", "confidence": 0.55} for c in candidates[:100]]

    def ingest_text(self, title, text, source_path="manual", mime_type="text/plain"):
        self.migrate()
        doc_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        metadata = {"source_path": source_path, "chars": len(text or ""), "ingestion": "text"}
        chunks = self.chunk_text(text)
        entities = self.extract_entities(text)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO documents(id, title, path, mime_type, status, text, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (doc_id, title, source_path, mime_type, "ingested", text, json.dumps(metadata, ensure_ascii=False), now)
            )
            for idx, chunk in enumerate(chunks):
                chunk_id = str(uuid4())
                citation = f"{title}#chunk-{idx}"
                conn.execute(
                    "INSERT INTO chunks(id, document_id, chunk_index, text, token_estimate, citation, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (chunk_id, doc_id, idx, chunk, max(1, len(chunk)//4), citation, now)
                )
                conn.execute(
                    "INSERT INTO citations(id, document_id, chunk_id, label, source_path, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid4()), doc_id, chunk_id, citation, source_path, f"chunk:{idx}", now)
                )
            for ent in entities:
                conn.execute(
                    "INSERT INTO entities(id, document_id, name, kind, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid4()), doc_id, ent["name"], ent["kind"], ent["confidence"], now)
                )
            conn.commit()
        return {"ok": True, "document_id": doc_id, "chunks": len(chunks), "entities": len(entities), "metadata": metadata}

    def ingest_file(self, path):
        if getattr(self, "_service_mode", False):
            return self.service.ingest_file(path).to_dict()
        p = Path(path)
        text, metadata = self.read_file_text(p)
        return self.ingest_text(p.name, text, str(p), self.detect_mime(p)) | {"reader_metadata": metadata}

    def documents(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT id, title, path, mime_type, status, created_at FROM documents ORDER BY created_at DESC").fetchall()]

    def chunks(self, document_id=None):
        self.migrate()
        with self.connect() as conn:
            if document_id:
                rows = conn.execute("SELECT * FROM chunks WHERE document_id=? ORDER BY chunk_index", (document_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM chunks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def search(self, query):
        self.migrate()
        q = f"%{query.lower()}%"
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT c.*, d.title FROM chunks c JOIN documents d ON d.id=c.document_id WHERE lower(c.text) LIKE ? OR lower(d.title) LIKE ? ORDER BY c.created_at DESC",
                (q, q)
            ).fetchall()
        return [dict(r) for r in rows]

    def entities(self, document_id=None):
        self.migrate()
        with self.connect() as conn:
            if document_id:
                rows = conn.execute("SELECT * FROM entities WHERE document_id=? ORDER BY name", (document_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM entities ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def citations(self, document_id=None):
        self.migrate()
        with self.connect() as conn:
            if document_id:
                rows = conn.execute("SELECT * FROM citations WHERE document_id=? ORDER BY location", (document_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM citations ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def answer_stub(self, question):
        results = self.search(question)
        top = results[:3]
        return {
            "question": question,
            "answer": "Antwort-Stub auf Basis der gefundenen Chunks. Ein LLM/RAG-Modell muss hier angeschlossen werden.",
            "citations": [{"citation": r["citation"], "title": r["title"], "chunk_id": r["id"]} for r in top],
            "matches": len(results),
        }
