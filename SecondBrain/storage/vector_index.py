"""pgvector index DDL builders (HNSW + optional IVFFLAT). Pure strings, unit-testable."""

from __future__ import annotations

# distance metric -> pgvector operator class
OPCLASS = {
    "cosine": "vector_cosine_ops",
    "l2": "vector_l2_ops",
    "ip": "vector_ip_ops",
}
# distance metric -> pgvector distance operator
OPERATOR = {"cosine": "<=>", "l2": "<->", "ip": "<#>"}

HNSW_INDEX = "idx_embeddings_hnsw_{metric}"
IVFFLAT_INDEX = "idx_embeddings_ivfflat_{metric}"


def _opclass(metric: str) -> str:
    if metric not in OPCLASS:
        raise ValueError(f"unsupported metric: {metric}")
    return OPCLASS[metric]


def hnsw_index_sql(*, metric: str = "cosine", m: int = 16, ef_construction: int = 64,
                   table: str = "embeddings", column: str = "embedding") -> str:
    name = HNSW_INDEX.format(metric=metric)
    return (
        f"CREATE INDEX IF NOT EXISTS {name} ON {table} "
        f"USING hnsw ({column} {_opclass(metric)}) "
        f"WITH (m = {int(m)}, ef_construction = {int(ef_construction)})"
    )


def ivfflat_index_sql(*, metric: str = "cosine", lists: int = 100,
                      table: str = "embeddings", column: str = "embedding") -> str:
    name = IVFFLAT_INDEX.format(metric=metric)
    return (
        f"CREATE INDEX IF NOT EXISTS {name} ON {table} "
        f"USING ivfflat ({column} {_opclass(metric)}) "
        f"WITH (lists = {int(lists)})"
    )


def drop_index_sql(name: str) -> str:
    return f"DROP INDEX IF EXISTS {name}"


def index_name(method: str, metric: str) -> str:
    tmpl = HNSW_INDEX if method == "hnsw" else IVFFLAT_INDEX
    return tmpl.format(metric=metric)
