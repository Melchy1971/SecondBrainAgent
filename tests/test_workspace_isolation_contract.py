"""Vertrag der Workspace-Isolation im Task-/Projekt-Repository.

Befund vom 2026-07-21
---------------------
Die Isolation beruht ausschliesslich auf Anwendungslogik. Es gibt im gesamten
Projekt kein ``ENABLE ROW LEVEL SECURITY`` und keine ``CREATE POLICY``.

Konkret in ``SecondBrain/tasks/repository.py``:

* ``PostgresTaskRepository.read(collection)`` hat **keinen**
  ``workspace_id``-Parameter und liefert alle Zeilen aller Workspaces.
  ``TaskService`` filtert erst danach in Python.
* ``write(collection, rows)`` loescht in Zeile 99 jeden Datensatz der
  Collection, der nicht in ``rows`` enthalten ist -- ebenfalls ohne
  Workspace-Bezug.

Heute ist das ungefaehrlich, weil jeder Aufrufer die **vollstaendige,
ungefilterte** Zeilenliste zurueckschreibt (z. B. ``service.py`` in
``update_project``). Der Schutz haengt damit an einer Konvention, die nirgends
erzwungen wird: uebergibt ein einziger Aufrufer je eine gefilterte Teilmenge,
loescht ``write`` stillschweigend die Datensaetze aller anderen Workspaces.

Dieser Test fixiert genau diese Konvention. Er behauptet nicht, dass die
Architektur gut ist -- er verhindert, dass sie unbemerkt kippt.

Vergleich: ``PostgresJobRepository`` fuehrt ``workspace_id`` in nahezu jeder
Signatur und ist damit strukturell sicher. Der Task-Pfad ist es nicht.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SB = Path(__file__).resolve().parents[1] / "SecondBrain"
REPOSITORY = _SB / "tasks" / "repository.py"
SERVICE = _SB / "tasks" / "service.py"
JOB_REPOSITORY = _SB / "jobs" / "repository.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _method(tree: ast.Module, klass: str, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == klass:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    return item
    raise AssertionError(f"{klass}.{name} nicht gefunden")


# --------------------------------------------------------------------------
# Der gefaehrliche Teil: DELETE ohne Workspace-Bezug
# --------------------------------------------------------------------------


def test_write_deletes_records_not_present_in_input() -> None:
    """Dokumentiert das Verhalten, auf dem die Konvention aufsetzt.

    Seit der Haertung traegt der DELETE optional einen Workspace-Scope
    (``{scope}``). Fehlt er (ungebundener Pfad), ist das Loeschverhalten
    unveraendert; ist er gesetzt, bleibt die Loeschung auf den Workspace
    begrenzt.
    """
    source = REPOSITORY.read_text(encoding="utf-8")
    assert "set(current) - desired_ids" in source, (
        "Die Loeschlogik hat sich geaendert. Pruefe, ob die Aufrufer-Konvention "
        "noch gilt -- dieser Test war ihr einziger Waechter."
    )
    assert "DELETE FROM {_TABLE} WHERE collection=:collection AND record_id=:record_id{scope}" in source


def test_service_write_calls_pass_unfiltered_rows() -> None:
    """Kein Aufrufer darf eine gefilterte Teilmenge an _write uebergeben.

    Wuerde er es tun, loescht PostgresTaskRepository.write die Datensaetze
    aller uebrigen Workspaces.
    """
    tree = _tree(SERVICE)
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if not (isinstance(target, ast.Attribute) and target.attr == "_write"):
            continue
        if len(node.args) < 2:
            continue
        payload = node.args[1]
        # Zulaessig ist nur ein schlichter Name (die vollstaendige Liste).
        # Comprehensions und Filterausdrucke sind das Risiko.
        if isinstance(payload, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
            offenders.append(f"Zeile {node.lineno}: Comprehension an _write uebergeben")
        elif not isinstance(payload, ast.Name):
            offenders.append(f"Zeile {node.lineno}: {type(payload).__name__} an _write uebergeben")

    assert not offenders, (
        "Gefilterte Datenmenge an _write uebergeben. PostgresTaskRepository.write "
        "loescht alles, was nicht enthalten ist -- workspace-uebergreifend:\n"
        + "\n".join(f"  SecondBrain/tasks/service.py:{o}" for o in offenders)
    )


# --------------------------------------------------------------------------
# Struktureller Vergleich mit dem sicheren Pfad
# --------------------------------------------------------------------------


def test_job_repository_scopes_row_access_by_workspace() -> None:
    """Referenz: so sieht strukturelle Isolation aus."""
    # Bewusst per AST statt per Import: das Modul verlangt Python 3.11
    # (``enum.StrEnum``), der Vertrag ist aber versionsunabhaengig pruefbar.
    tree = _tree(JOB_REPOSITORY)
    unscoped: list[str] = []

    row_access = {
        "get_job", "list_jobs", "renew_lease", "release_lease", "update_progress",
        "save_checkpoint", "complete_job", "fail_job", "start_job", "pause_job",
        "resume_job", "cancel_job",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "PostgresJobRepository":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name in row_access:
                    names = {a.arg for a in item.args.args} | {a.arg for a in item.args.kwonlyargs}
                    if "workspace_id" not in names:
                        unscoped.append(item.name)

    assert not unscoped, f"Zeilenzugriff ohne workspace_id: {unscoped}"


def test_task_repository_read_is_workspace_bindable() -> None:
    """read() akzeptiert seit der Haertung einen optionalen workspace_id.

    Historie: Zuvor hielt dieser Test fest, dass read() NICHT gebunden war --
    als Vertrag ueber einen Schwachpunkt. Der Schwachpunkt ist behoben, also
    prueft der Test jetzt die Gegenrichtung.
    """
    tree = _tree(REPOSITORY)
    read = _method(tree, "PostgresTaskRepository", "read")
    names = {a.arg for a in read.args.args} | {a.arg for a in read.args.kwonlyargs}
    assert "workspace_id" in names, "read() sollte workspace_id binden koennen"


def test_row_level_security_protects_task_records() -> None:
    """RLS ist der Datenbank-Backstop gegen Raw-SQL-Bypass (Prompt 68 Phase 4).

    Historie: Zuvor stellte dieser Test fest, dass es NIRGENDS RLS gibt. Sie
    wurde eingefuehrt; der Test sichert jetzt ihr Vorhandensein.
    """
    context = (_SB / "storage" / "workspace_context.py").read_text(encoding="utf-8").lower()
    assert "enable row level security" in context
    assert "force row level security" in context
    assert "create policy" in context
    # fail-closed: der zweite Parameter true macht current_setting nullbar.
    assert "current_setting('app.workspace_id', true)" in context

    repository = REPOSITORY.read_text(encoding="utf-8")
    assert "rls_setup_statements" in repository, (
        "ensure_schema richtet keine RLS ein"
    )
