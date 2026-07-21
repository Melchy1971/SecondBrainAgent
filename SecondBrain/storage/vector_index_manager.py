"""v30.2 - vector index management.

Das DDL wird nicht mehr lokal formuliert, sondern aus
:mod:`secondbrain.storage.vector_index` bezogen. Eine zweite Formulierung
wuerde bei Dimensionen ueber 2000 eine andere Operatorklasse waehlen als der
Suchpfad und den Index damit unbenutzbar machen.
"""

from __future__ import annotations

from secondbrain.storage.vector_index import DEFAULT_DIMENSIONS, hnsw_index_sql


class VectorIndexManager:
    def __init__(self, database, *, dimensions: int = DEFAULT_DIMENSIONS):
        self.database = database
        self.dimensions = int(dimensions)

    def ensure_hnsw_index(self) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(text(hnsw_index_sql(metric="cosine", dimensions=self.dimensions)))

    def analyze(self) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(text("ANALYZE embeddings"))
