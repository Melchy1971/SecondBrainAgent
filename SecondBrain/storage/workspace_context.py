"""Workspace-Isolation auf Datenbankebene: Sitzungsvariable und RLS-Policy.

Reine SQL-Erzeugung, ohne Datenbankabhaengigkeit -- damit unit-testbar und
versionsunabhaengig. Die Anwendung setzt vor jedem Zugriff die Sitzungsvariable
``app.workspace_id``; die Row-Level-Security-Policy filtert jede Zeile dagegen.

Sicherheitsmodell (siehe docs/specs/workspace_isolation_spec.md):

* ``SET LOCAL`` bindet den Wert an die Transaktion. Ueber Connection-Pooling
  kann er nicht in eine fremde Anfrage lecken.
* ``current_setting('app.workspace_id', true)`` liefert bei fehlender Variable
  ``NULL``. Der Policy-Vergleich ist dann nie wahr -- ohne gesetzten Workspace
  ist die Tabelle leer und nimmt keine Schreibzugriffe an. Fail-closed.
* ``FORCE ROW LEVEL SECURITY`` unterwirft auch den Tabelleneigentuemer.
"""

from __future__ import annotations

import re

SESSION_VARIABLE = "app.workspace_id"
POLICY_NAME = "workspace_isolation"

# Ein Workspace-Bezeichner darf nur diese Zeichen enthalten. Da der Wert per
# SET LOCAL als String-Literal eingesetzt wird, ist die Validierung die
# Absicherung gegen Injection.
_WORKSPACE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class WorkspaceContextError(ValueError):
    """Ungueltiger Workspace-Bezeichner."""


def validate_workspace_id(workspace_id: str) -> str:
    if not isinstance(workspace_id, str) or not _WORKSPACE_ID.match(workspace_id):
        raise WorkspaceContextError("invalid_workspace_id")
    return workspace_id


def set_workspace_sql(workspace_id: str) -> str:
    """SET LOCAL fuer die aktuelle Transaktion.

    Der Bezeichner wird validiert und als einfaches String-Literal gesetzt.
    ``SET LOCAL`` akzeptiert keine Bind-Parameter, deshalb die strikte
    Zeichenklasse in :func:`validate_workspace_id`.
    """
    validate_workspace_id(workspace_id)
    return f"SET LOCAL {SESSION_VARIABLE} = '{workspace_id}'"


def reset_workspace_sql() -> str:
    """Setzt die Variable auf den leeren Wert -- Tabelle wird damit unsichtbar."""
    return f"SET LOCAL {SESSION_VARIABLE} = ''"


def current_workspace_expression() -> str:
    """Der Ausdruck, den die Policy zum Vergleich nutzt. Fail-closed via NULL."""
    return f"current_setting('{SESSION_VARIABLE}', true)"


def enable_rls_statements(table: str) -> tuple[str, ...]:
    """RLS aktivieren und erzwingen. Idempotent aufrufbar."""
    _validate_identifier(table)
    return (
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
    )


def create_policy_statement(table: str) -> str:
    _validate_identifier(table)
    expr = current_workspace_expression()
    return (
        f"CREATE POLICY {POLICY_NAME} ON {table} "
        f"USING (workspace_id = {expr}) "
        f"WITH CHECK (workspace_id = {expr})"
    )


def drop_policy_statement(table: str) -> str:
    _validate_identifier(table)
    return f"DROP POLICY IF EXISTS {POLICY_NAME} ON {table}"


def rls_setup_statements(table: str) -> tuple[str, ...]:
    """Vollstaendige, wiederholbare RLS-Einrichtung fuer ``table``.

    DROP POLICY zuerst, damit ein erneuter Lauf nicht an einer bestehenden
    Policy scheitert -- ``CREATE POLICY`` kennt kein ``IF NOT EXISTS``.
    """
    return (
        *enable_rls_statements(table),
        drop_policy_statement(table),
        create_policy_statement(table),
    )


def _validate_identifier(name: str) -> None:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", name or ""):
        raise WorkspaceContextError("invalid_table_identifier")
