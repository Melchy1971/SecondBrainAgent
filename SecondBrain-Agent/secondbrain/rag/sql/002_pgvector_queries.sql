-- P1 v19.0
-- Placeholder queries for similarity search and indexing.
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
ON embeddings USING ivfflat (embedding vector_cosine_ops);
