"""Vertrag zwischen Embedding-Dimension, Indexausdruck und Suchausdruck.

Hintergrund
-----------
``storage/migrations/002_pgvector_embeddings.sql`` legte ``vector(3072)`` an und
darauf einen direkten HNSW-Index. pgvector indiziert ``vector`` mit HNSW und
IVFFlat aber nur bis 2000 Dimensionen. Die Migration konnte gegen echtes
PostgreSQL nie laufen -- gegen SQLite fiel es nicht auf.

Belegt am 2026-07-21 gegen PostgreSQL 18.4 / pgvector 0.8.4:

    hnsw_vector             -> column cannot have more than 2000 dimensions
    ivfflat_vector          -> column cannot have more than 2000 dimensions
    hnsw_halfvec_expression -> ok
    hnsw_halfvec_column     -> ok
    hnsw_vector_1536        -> ok

Zweiter, subtilerer Fehler: ein Ausdrucksindex wird nur genutzt, wenn die
Abfrage denselben Ausdruck traegt. Laufen DDL und Query auseinander, existiert
der Index und jede Suche degradiert still zum Sequential Scan. Genau das
prueft dieser Test mit.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from secondbrain.storage import vector_index as vi

MIGRATION = Path(__file__).resolve().parents[1] / "SecondBrain" / "storage" / "migrations" / "002_pgvector_embeddings.sql"


# --------------------------------------------------------------------------
# Grenzwerte
# --------------------------------------------------------------------------


def test_documented_limits_match_pgvector() -> None:
    assert vi.MAX_INDEXABLE_VECTOR_DIMENSIONS == 2000
    assert vi.MAX_INDEXABLE_HALFVEC_DIMENSIONS == 4000


@pytest.mark.parametrize(
    "dimensions,expected",
    [(384, False), (1536, False), (2000, False), (2001, True), (3072, True)],
)
def test_requires_halfvec_threshold(dimensions: int, expected: bool) -> None:
    assert vi.requires_halfvec(dimensions) is expected


def test_dimensions_beyond_halfvec_limit_are_rejected() -> None:
    with pytest.raises(ValueError, match="halfvec index limit"):
        vi.index_expression(dimensions=4001)


# --------------------------------------------------------------------------
# Kernregel: kein direkter Index oberhalb der Grenze
# --------------------------------------------------------------------------


@pytest.mark.parametrize("builder", [vi.hnsw_index_sql, vi.ivfflat_index_sql])
def test_no_direct_vector_index_above_limit(builder) -> None:
    sql = builder(dimensions=3072)
    assert "halfvec" in sql, f"{builder.__name__} erzeugt keinen halfvec-Index fuer 3072 Dimensionen"
    assert "vector_cosine_ops" not in sql, (
        f"{builder.__name__} verwendet vector_cosine_ops auf 3072 Dimensionen -- "
        "das schlaegt auf echtem pgvector fehl"
    )


@pytest.mark.parametrize("builder", [vi.hnsw_index_sql, vi.ivfflat_index_sql])
def test_small_dimensions_keep_plain_vector_index(builder) -> None:
    """Unterhalb der Grenze darf kein unnoetiger Cast entstehen."""
    sql = builder(dimensions=1536)
    assert "halfvec" not in sql
    assert "vector_cosine_ops" in sql


# --------------------------------------------------------------------------
# Index und Abfrage muessen denselben Ausdruck tragen
# --------------------------------------------------------------------------


@pytest.mark.parametrize("dimensions", [384, 1536, 3072])
def test_query_expression_matches_index_expression(dimensions: int) -> None:
    index_sql = vi.hnsw_index_sql(dimensions=dimensions)
    query = vi.distance_expression(dimensions=dimensions)

    if vi.requires_halfvec(dimensions):
        cast = f"halfvec({dimensions})"
        assert cast in index_sql, "Indexausdruck ohne halfvec-Cast"
        assert cast in query, "Abfrageausdruck ohne halfvec-Cast - der Index wird nicht genutzt"
    else:
        assert "halfvec" not in index_sql
        assert "halfvec" not in query


def test_repository_distance_matches_vector_index_module() -> None:
    """Das Repository darf keine eigene, abweichende Distanzformel bauen."""
    from secondbrain.storage.pgvector_repository import _distance_sql

    for dimensions in (1536, 3072):
        repo_sql = _distance_sql(dimensions)
        if vi.requires_halfvec(dimensions):
            assert f"halfvec({dimensions})" in repo_sql
            assert repo_sql.count(f"halfvec({dimensions})") == 2, (
                "Sowohl Spalte als auch Parameter muessen gecastet werden"
            )
        else:
            assert "halfvec" not in repo_sql
        assert "<=>" in repo_sql


# --------------------------------------------------------------------------
# Die Migration selbst
# --------------------------------------------------------------------------


def test_migration_declares_vector_column_in_full_precision() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert re.search(r"embedding\s+vector\(3072\)", sql), (
        "Die Speicherspalte soll vector(3072) bleiben - nur der Index nutzt halfvec"
    )


def test_migration_index_is_halfvec_based() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    hnsw = [line for line in sql.splitlines() if "USING hnsw" in line]
    assert hnsw, "Kein HNSW-Index in der Migration"
    for line in hnsw:
        assert "halfvec" in line, (
            f"HNSW-Index ohne halfvec-Cast: {line.strip()!r} - "
            "schlaegt auf echtem pgvector mit 3072 Dimensionen fehl"
        )


def test_migration_has_no_direct_vector_ops_index() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in sql.splitlines()
        if "vector_cosine_ops" in line or "vector_l2_ops" in line or "vector_ip_ops" in line
    ]
    assert not offenders, (
        "Direkter vector-Operatorklassen-Index auf 3072 Dimensionen:\n" + "\n".join(offenders)
    )
