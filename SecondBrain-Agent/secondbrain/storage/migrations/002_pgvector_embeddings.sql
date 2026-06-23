-- v30.2 pgvector production schema

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    owner_type TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    embedding vector(3072) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_owner
ON embeddings (owner_type, owner_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_model
ON embeddings (provider, model);

CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine
ON embeddings
USING hnsw (embedding vector_cosine_ops);
