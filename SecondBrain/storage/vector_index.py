"""pgvector index DDL builders (HNSW + optional IVFFLAT). Pure strings, unit-testable.

Dimensionsgrenze
----------------
pgvector indiziert den Typ ``vector`` mit HNSW und IVFFlat nur bis
``MAX_INDEXABLE_VECTOR_DIMENSIONS``. Darueber scheitert ``CREATE INDEX`` mit
"column cannot have more than 2000 dimensions". Verifiziert gegen
PostgreSQL 18.4 / pgvector 0.8.4 am 2026-07-21.

Fuer groessere Dimensionen wird auf ``halfvec`` gecastet, das bis 4000
Dimensionen indizierbar ist. Die Spalte bleibt dabei ``vector`` in voller
Praezision -- nur der Index arbeitet mit halber.

Kritisch: PostgreSQL nutzt einen Ausdrucksindex ausschliesslich dann, wenn die
Abfrage denselben Ausdruck enthaelt. ``distance_expression()`` und
``hnsw_index_sql()`` muessen deshalb immer aus derselben Quelle stammen --
sonst existiert der Index und wird nie benutzt.
"""

from __future__ import annotations

# distance metric -> pgvector operator class je Vektortyp
OPCLASS = {
    "cosine": "vector_cosine_ops",
    "l2": "vector_l2_ops",
    "ip": "vector_ip_ops",
}
HALFVEC_OPCLASS = {
    "cosine": "halfvec_cosine_ops",
    "l2": "halfvec_l2_ops",
    "ip": "halfvec_ip_ops",
}
# distance metric -> pgvector distance operator
OPERATOR = {"cosine": "<=>", "l2": "<->", "ip": "<#>"}

HNSW_INDEX = "idx_embeddings_hnsw_{metric}"
IVFFLAT_INDEX = "idx_embeddings_ivfflat_{metric}"

MAX_INDEXABLE_VECTOR_DIMENSIONS = 2000
MAX_INDEXABLE_HALFVEC_DIMENSIONS = 4000

DEFAULT_DIMENSIONS = 3072


def _opclass(metric: str) -> str:
    if metric not in OPCLASS:
        raise ValueError(f"unsupported metric: {metric}")
    return OPCLASS[metric]


def _halfvec_opclass(metric: str) -> str:
    if metric not in HALFVEC_OPCLASS:
        raise ValueError(f"unsupported metric: {metric}")
    return HALFVEC_OPCLASS[metric]


def requires_halfvec(dimensions: int) -> bool:
    """True, wenn ``dimensions`` nicht direkt als ``vector`` indizierbar ist."""
    return int(dimensions) > MAX_INDEXABLE_VECTOR_DIMENSIONS


def index_expression(*, dimensions: int = DEFAULT_DIMENSIONS, column: str = "embedding") -> str:
    """Der zu indizierende Ausdruck. Identisch mit dem Ausdruck der Abfrage."""
    dims = int(dimensions)
    if not requires_halfvec(dims):
        return column
    if dims > MAX_INDEXABLE_HALFVEC_DIMENSIONS:
        raise ValueError(
            f"{dims} dimensions exceed the halfvec index limit of "
            f"{MAX_INDEXABLE_HALFVEC_DIMENSIONS}; reduce the embedding dimension"
        )
    return f"({column}::halfvec({dims}))"


def distance_expression(*, metric: str = "cosine", dimensions: int = DEFAULT_DIMENSIONS,
                        column: str = "embedding", parameter: str = "%s") -> str:
    """ORDER-BY-Ausdruck, der den Index aus :func:`index_expression` trifft."""
    if metric not in OPERATOR:
        raise ValueError(f"unsupported metric: {metric}")
    operator = OPERATOR[metric]
    dims = int(dimensions)
    if not requires_halfvec(dims):
        return f"{column} {operator} {parameter}::vector"
    return f"{column}::halfvec({dims}) {operator} {parameter}::halfvec({dims})"


def index_opclass(*, metric: str = "cosine", dimensions: int = DEFAULT_DIMENSIONS) -> str:
    """Operatorklasse passend zum Typ, den :func:`index_expression` liefert."""
    return _halfvec_opclass(metric) if requires_halfvec(dimensions) else _opclass(metric)


def hnsw_index_sql(*, metric: str = "cosine", m: int = 16, ef_construction: int = 64,
                   table: str = "embeddings", column: str = "embedding",
                   dimensions: int = DEFAULT_DIMENSIONS, name: str | None = None) -> str:
    index = name or HNSW_INDEX.format(metric=metric)
    expression = index_expression(dimensions=dimensions, column=column)
    opclass = index_opclass(metric=metric, dimensions=dimensions)
    return (
        f"CREATE INDEX IF NOT EXISTS {index} ON {table} "
        f"USING hnsw ({expression} {opclass}) "
        f"WITH (m = {int(m)}, ef_construction = {int(ef_construction)})"
    )


def ivfflat_index_sql(*, metric: str = "cosine", lists: int = 100,
                      table: str = "embeddings", column: str = "embedding",
                      dimensions: int = DEFAULT_DIMENSIONS, name: str | None = None) -> str:
    index = name or IVFFLAT_INDEX.format(metric=metric)
    expression = index_expression(dimensions=dimensions, column=column)
    opclass = index_opclass(metric=metric, dimensions=dimensions)
    return (
        f"CREATE INDEX IF NOT EXISTS {index} ON {table} "
        f"USING ivfflat ({expression} {opclass}) "
        f"WITH (lists = {int(lists)})"
    )


def drop_index_sql(name: str) -> str:
    return f"DROP INDEX IF EXISTS {name}"


def index_name(method: str, metric: str) -> str:
    tmpl = HNSW_INDEX if method == "hnsw" else IVFFLAT_INDEX
    return tmpl.format(metric=metric)
