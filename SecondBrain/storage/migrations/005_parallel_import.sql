-- v30.52 transient payloads in the existing RAG database; jobs stay in JobQueueService.
CREATE TABLE IF NOT EXISTS import_stage_records (
    document_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES import_sessions(session_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_import_stage_records_session ON import_stage_records(session_id, state);
