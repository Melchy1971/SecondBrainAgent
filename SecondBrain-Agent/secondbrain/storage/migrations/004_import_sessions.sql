-- v30.51 resumable enterprise imports in the existing RAG database
CREATE TABLE IF NOT EXISTS import_sessions (
    session_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    source TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_mtime_ns INTEGER NOT NULL DEFAULT 0,
    bytes_processed INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL DEFAULT 0,
    imported_chats INTEGER NOT NULL DEFAULT 0,
    chunks INTEGER NOT NULL DEFAULT 0,
    embeddings INTEGER NOT NULL DEFAULT 0,
    new_documents INTEGER NOT NULL DEFAULT 0,
    updated_documents INTEGER NOT NULL DEFAULT 0,
    skipped_documents INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    control_state TEXT NOT NULL DEFAULT 'running',
    error TEXT NOT NULL DEFAULT '',
    batch_size INTEGER NOT NULL DEFAULT 500,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_import_sessions_file ON import_sessions(file_path, updated_at);
CREATE INDEX IF NOT EXISTS idx_import_sessions_status ON import_sessions(status);
