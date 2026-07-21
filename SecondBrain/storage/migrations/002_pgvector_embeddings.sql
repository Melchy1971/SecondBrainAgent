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

-- pgvector indiziert den Typ vector mit HNSW und IVFFlat nur bis 2000
-- Dimensionen. Bei vector(3072) scheitert ein direkter Index mit
--   "column cannot have more than 2000 dimensions for hnsw index"
-- Verifiziert gegen PostgreSQL 18.4 / pgvector 0.8.4 am 2026-07-21.
--
-- Die Spalte bleibt daher vector(3072) in voller Praezision; indiziert wird
-- ein Cast auf halfvec, das bis 4000 Dimensionen traegt.
--
-- WICHTIG: Abfragen muessen exakt denselben Ausdruck verwenden, sonst nutzt
-- der Planner diesen Index nicht. Siehe SecondBrain/storage/vector_index.py,
-- distance_expression().
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine
ON embeddings
USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops);
