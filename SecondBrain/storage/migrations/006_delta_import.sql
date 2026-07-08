-- v30.56 delta/version audit inside the existing RAG database.
CREATE TABLE IF NOT EXISTS document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(document_id, version_number)
);
CREATE INDEX IF NOT EXISTS idx_document_versions_document ON document_versions(document_id, version_number);

CREATE TABLE IF NOT EXISTS import_delta_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    action TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_import_delta_session ON import_delta_entries(session_id, action);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
