"""SQL-Erzeugung fuer Workspace-Isolation. Ohne Datenbank pruefbar.

Die tatsaechliche RLS-Durchsetzung wird im PostgreSQL-Live-Gate gegen echtes
Postgres nachgewiesen. Hier geht es um die Korrektheit und Sicherheit der
erzeugten Anweisungen.
"""

from __future__ import annotations

import pytest

from secondbrain.storage import workspace_context as wc


# --------------------------------------------------------------------------
# Validierung: die einzige Injection-Barriere fuer SET LOCAL
# --------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["ws-a", "workspace_1", "a.b:c-d", "A" * 128, "ws--b"])
def test_valid_workspace_ids_pass(value: str) -> None:
    # "ws--b" ist gueltig: innerhalb des Stringliterals ist "--" kein Kommentar.
    assert wc.validate_workspace_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "A" * 129,
        "ws a",              # Leerzeichen
        "ws';DROP TABLE x;--",
        "ws'",
        "ws\"",
        "ws;",
        "ws\nb",
        123,                 # falscher Typ
        None,
    ],
)
def test_invalid_workspace_ids_are_rejected(value) -> None:
    with pytest.raises(wc.WorkspaceContextError):
        wc.validate_workspace_id(value)  # type: ignore[arg-type]


def test_set_workspace_sql_rejects_injection() -> None:
    with pytest.raises(wc.WorkspaceContextError):
        wc.set_workspace_sql("x'; DROP TABLE task_project_records; --")


def test_set_workspace_sql_shape() -> None:
    sql = wc.set_workspace_sql("ws-a")
    assert sql == "SET LOCAL app.workspace_id = 'ws-a'"
    assert "SET LOCAL" in sql  # transaktionsgebunden, kein Leck ueber den Pool


def test_reset_workspace_makes_table_invisible() -> None:
    # Leerer Wert -> Policy-Vergleich nie wahr -> keine Zeilen sichtbar.
    assert wc.reset_workspace_sql() == "SET LOCAL app.workspace_id = ''"


# --------------------------------------------------------------------------
# Policy: fail-closed und erzwungen
# --------------------------------------------------------------------------


def test_policy_uses_nullable_current_setting() -> None:
    """Der zweite Parameter true macht current_setting fail-closed statt Fehler."""
    stmt = wc.create_policy_statement("task_project_records")
    assert "current_setting('app.workspace_id', true)" in stmt
    assert "USING (workspace_id = current_setting('app.workspace_id', true))" in stmt
    assert "WITH CHECK (workspace_id = current_setting('app.workspace_id', true))" in stmt


def test_rls_is_forced() -> None:
    """Ohne FORCE umginge der Tabelleneigentuemer die Policy."""
    statements = wc.enable_rls_statements("task_project_records")
    assert any("ENABLE ROW LEVEL SECURITY" in s for s in statements)
    assert any("FORCE ROW LEVEL SECURITY" in s for s in statements)


def test_setup_is_repeatable() -> None:
    """DROP POLICY vor CREATE POLICY -- sonst scheitert der zweite Lauf."""
    statements = wc.rls_setup_statements("task_project_records")
    drop_index = next(i for i, s in enumerate(statements) if s.startswith("DROP POLICY"))
    create_index = next(i for i, s in enumerate(statements) if s.startswith("CREATE POLICY"))
    assert drop_index < create_index


def test_setup_targets_the_named_table_only() -> None:
    for stmt in wc.rls_setup_statements("task_project_records"):
        assert "task_project_records" in stmt


@pytest.mark.parametrize("table", ["1abc", "a b", "a;b", "a'b", "", "a-b"])
def test_invalid_table_identifiers_are_rejected(table: str) -> None:
    with pytest.raises(wc.WorkspaceContextError):
        wc.rls_setup_statements(table)
