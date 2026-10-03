"""Projektweiter Schutz gegen nicht anlegbare und gegen ungenutzte Vektorindizes.

Zwei Fehlerklassen, beide am 2026-07-21 gegen PostgreSQL 18.4 / pgvector 0.8.4
belegt:

1. **Laut.** ``USING hnsw (embedding vector_cosine_ops)`` auf ``vector(3072)``
   scheitert mit "column cannot have more than 2000 dimensions". Dasselbe gilt
   fuer ivfflat.

2. **Still.** Wird der Index als Ausdruck auf ``halfvec`` angelegt, die Abfrage
   aber weiterhin als ``embedding <=> $1::vector`` formuliert, existiert der
   Index und PostgreSQL benutzt ihn nie. Jede Suche degradiert zum Sequential
   Scan, ohne Fehlermeldung.

``tests/test_pgvector_dimension_contract.py`` prueft die bekannten Stellen.
Dieser Test sucht den gesamten Baum ab und faengt damit auch neue.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pytest

from secondbrain.storage import vector_index as vi

SOURCE_ROOT = "SecondBrain"
SKIP_PARTS = {"__pycache__", "_archive_starters", "OUTPUTS", "backups", "archive", "node_modules"}

# vector_index.py waehlt Ausdruck und Operatorklasse dimensionsabhaengig und
# ist damit die einzige Stelle, die beide Varianten nennen darf.
BUILDER = "SecondBrain/storage/vector_index.py"

# Begruendete Ausnahmen. Jeder Eintrag braucht einen Grund -- eine Ausnahmeliste
# ohne Begruendung hoehlt die Regel aus.
ALLOWED = {
    BUILDER: "waehlt Ausdruck und Operatorklasse dimensionsabhaengig",
    "SecondBrain/release/postgres_live_gate.py": (
        "legt den direkten Index absichtlich an, um nachzuweisen, dass pgvector "
        "ihn oberhalb von 2000 Dimensionen ablehnt (Pruefung "
        "vector_index_limit_as_documented)"
    ),
}

VECTOR_OPCLASS = re.compile(r"\bvector_(cosine|l2|ip)_ops\b")
INDEX_METHOD = re.compile(r"using\s+(hnsw|ivfflat)\s*\(", re.IGNORECASE)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _relative(path: Path) -> str:
    return str(path.relative_to(_root())).replace("\\", "/")


@lru_cache(maxsize=1)
def _sources() -> tuple[tuple[str, str], ...]:
    """(relativer Pfad, Inhalt) fuer jede Quelldatei -- Baum wird einmal gelesen."""
    root = _root() / SOURCE_ROOT
    items: list[tuple[str, str]] = []
    for suffix in ("*.py", "*.sql"):
        for path in root.rglob(suffix):
            if SKIP_PARTS & set(path.parts):
                continue
            try:
                items.append((_relative(path), path.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, OSError):
                continue
    return tuple(sorted(items))


def _is_comment(line: str, path: str) -> bool:
    stripped = line.strip()
    if path.endswith(".sql"):
        return stripped.startswith("--")
    return stripped.startswith("#")


def _code_lines(text: str, path: str):
    """Nur Codezeilen. Erklaerende Kommentare duerfen den Fehlerfall benennen."""
    for number, line in enumerate(text.splitlines(), start=1):
        if not _is_comment(line, path):
            yield number, line


# --------------------------------------------------------------------------
# Fehlerklasse 1: nicht anlegbare Indizes
# --------------------------------------------------------------------------


def test_no_hardcoded_vector_opclass_index_outside_builder() -> None:
    """Kein fest verdrahtetes DDL darf eine vector-Operatorklasse verwenden."""
    offenders: list[str] = []

    for rel, text in _sources():
        if rel in ALLOWED:
            continue
        for number, line in _code_lines(text, rel):
            if VECTOR_OPCLASS.search(line) and "halfvec" not in line:
                offenders.append(f"{rel}:{number}: {line.strip()}")

    assert not offenders, (
        "Direkte vector-Operatorklasse gefunden. Bei der Projektdimension 3072 "
        "laesst sich ein solcher Index nicht anlegen.\n"
        "Beziehe das DDL aus secondbrain.storage.vector_index:\n\n"
        + "\n".join(offenders)
    )


def test_every_index_ddl_matches_a_known_construction() -> None:
    """Jede HNSW-/IVFFlat-DDL nennt entweder halfvec oder stammt aus dem Builder."""
    offenders: list[str] = []

    for rel, text in _sources():
        if rel in ALLOWED:
            continue
        code = "\n".join(line for _, line in _code_lines(text, rel))
        if not INDEX_METHOD.search(code):
            continue
        # Entweder halfvec explizit, oder das DDL kommt aus dem Builder.
        if "halfvec" in code or "index_sql" in code:
            continue
        offenders.append(rel)

    assert not offenders, (
        "Vektorindex-DDL ohne halfvec-Bezug und ohne Builder-Aufruf:\n"
        + "\n".join(f"  {o}" for o in offenders)
    )


# --------------------------------------------------------------------------
# Fehlerklasse 2: Abfrage trifft den Index nicht
# --------------------------------------------------------------------------


@pytest.mark.parametrize("dimensions", [1536, 3072])
def test_builder_expression_and_opclass_agree(dimensions: int) -> None:
    expression = vi.index_expression(dimensions=dimensions)
    opclass = vi.index_opclass(dimensions=dimensions)
    query = vi.distance_expression(dimensions=dimensions)

    uses_halfvec = vi.requires_halfvec(dimensions)
    assert ("halfvec" in expression) is uses_halfvec
    assert opclass.startswith("halfvec_") is uses_halfvec
    assert ("halfvec" in query) is uses_halfvec


def test_p3_rag_store_query_is_dimension_aware() -> None:
    """Der P3-Store baut seinen Distanzausdruck aus der Anfragedimension."""
    from types import SimpleNamespace

    from secondbrain.p3_rag_store import PgVectorRagStore

    # Nur der SQL-Aufbau wird geprueft; keine Verbindung noetig.
    store = PgVectorRagStore.__new__(PgVectorRagStore)
    store.config = SimpleNamespace(schema_name="secondbrain", table_prefix="p1")
    build = PgVectorRagStore.build_vector_search_sql

    small = build(store, dimensions=1536)
    large = build(store, dimensions=3072)

    assert "halfvec" not in small
    assert "halfvec(3072)" in large
    # Score-Ausdruck und ORDER BY muessen identisch sein.
    assert large.count("halfvec(3072)") >= 4, (
        "Score und ORDER BY muessen denselben Cast tragen, je zweimal"
    )


def test_pgvector_foundation_schema_is_dimension_aware() -> None:
    """Das P3-Foundation-Schema darf bei 3072 keinen direkten vector-Index bauen."""
    from secondbrain.p3_pgvector_foundation import PgVectorConfig, build_pgvector_schema_sql

    config = PgVectorConfig.__new__(PgVectorConfig)
    object.__setattr__(config, "schema_name", "secondbrain")
    object.__setattr__(config, "table_prefix", "p1")
    object.__setattr__(config, "vector_dimensions", 3072)

    sql = build_pgvector_schema_sql(config)
    assert "halfvec" in sql
    assert not VECTOR_OPCLASS.search(sql), "direkte vector-Operatorklasse im Schema"


def test_pgvector_search_sql_stays_recognizable_to_existing_test_double() -> None:
    """Kopplung zwischen Produktions-SQL und einem Test-Double festhalten.

    ``tests/test_v191_p3_rag_store.py`` verwendet einen ``_FakeCursor``, der
    seine Antwort am Vorkommen des Literals ``"embedding <=>"`` in der Abfrage
    festmacht. Unterhalb von 2001 Dimensionen erzeugt der Store genau diese
    Form; ab 3072 lautet der Ausdruck ``embedding::halfvec(3072) <=>`` und das
    Literal verschwindet.

    Heute ist das folgenlos, weil jener Test mit dreidimensionalen Vektoren
    arbeitet. Wird die Dimension dort je hochgezogen, liefert der Fake
    stillschweigend keine Treffer und der Test scheitert an ``hit_count == 0``
    -- ohne Hinweis auf die eigentliche Ursache. Dieser Test macht den
    Zusammenhang sichtbar.
    """
    from types import SimpleNamespace

    from secondbrain.p3_rag_store import PgVectorRagStore

    store = PgVectorRagStore.__new__(PgVectorRagStore)
    store.config = SimpleNamespace(schema_name="secondbrain", table_prefix="p1")
    build = PgVectorRagStore.build_vector_search_sql

    assert "embedding <=>" in build(store, dimensions=3), (
        "Der Fake in tests/test_v191_p3_rag_store.py erkennt die Abfrage nicht mehr"
    )
    assert "embedding <=>" not in build(store, dimensions=3072), (
        "Ab 3072 Dimensionen muss der halfvec-Cast im Ausdruck stehen"
    )


def test_pgvector_foundation_keeps_plain_index_below_limit() -> None:
    from secondbrain.p3_pgvector_foundation import PgVectorConfig, build_pgvector_schema_sql

    config = PgVectorConfig.__new__(PgVectorConfig)
    object.__setattr__(config, "schema_name", "secondbrain")
    object.__setattr__(config, "table_prefix", "p1")
    object.__setattr__(config, "vector_dimensions", 1536)

    sql = build_pgvector_schema_sql(config)
    assert "halfvec" not in sql
    assert VECTOR_OPCLASS.search(sql)
