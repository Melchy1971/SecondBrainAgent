-- P1 v19.0
-- Placeholder queries for similarity search and indexing.
--
-- pgvector indiziert den Typ vector mit ivfflat und hnsw nur bis 2000
-- Dimensionen. Bei der Projektdimension 3072 scheitert
--   USING ivfflat (embedding vector_cosine_ops)
-- mit "column cannot have more than 2000 dimensions for ivfflat index".
-- Verifiziert gegen PostgreSQL 18.4 / pgvector 0.8.4 am 2026-07-21.
--
-- Indiziert wird daher ein halfvec-Cast. Abfragen muessen denselben Ausdruck
-- verwenden, sonst bleibt der Index ungenutzt.
-- Massgeblich ist SecondBrain/storage/vector_index.py.
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
ON embeddings USING ivfflat ((embedding::halfvec(3072)) halfvec_cosine_ops);
