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
    """Dokumentiert das Verhalten, auf dem die Konvention aufsetzt."""
    source = REPOSITORY.read_text(encoding="utf-8")
    assert "set(current) - desired_ids" in source, (
        "Die Loeschlogik hat sich geaendert. Pruefe, ob die Aufrufer-Konvention "
        "noch gilt -- dieser Test war ihr einziger Waechter."
    )
    assert "DELETE FROM task_project_records WHERE collection=:collection AND record_id=:record_id" in source


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


def test_task_repository_read_is_documented_as_unscoped() -> None:
    """Bewusst festgehalten: read() ist nicht workspace-gebunden.

    Faellt dieser Test aus, weil ein workspace_id-Parameter ergaenzt wurde, ist
    das eine Verbesserung -- dann gehoert dieser Test entfernt und die
    Aufrufer-Konvention aus test_service_write_calls_pass_unfiltered_rows
    ebenfalls neu bewertet.
    """
    tree = _tree(REPOSITORY)
    read = _method(tree, "PostgresTaskRepository", "read")
    names = {a.arg for a in read.args.args} | {a.arg for a in read.args.kwonlyargs}

    assert "workspace_id" not in names, (
        "read() ist jetzt workspace-gebunden. Bitte diesen Test und den "
        "Blocker task_repository_isolation_is_application_level_only entfernen."
    )


def test_no_row_level_security_anywhere() -> None:
    """Ohne RLS ist ein Raw-SQL-Bypass nicht verhinderbar.

    Prompt 68 Phase 4 verlangt, dass auch direkter SQL-Zugriff Workspaces nicht
    ueberschreiten kann. Mit rein anwendungsseitiger Filterung ist diese
    Anforderung nicht erfuellbar.
    """
    root = Path(__file__).resolve().parents[1] / "SecondBrain"
    markers = ("enable row level security", "create policy", "force row level security")
    found: list[str] = []

    for suffix in ("*.sql", "*.py"):
        for path in root.rglob(suffix):
            if "__pycache__" in path.parts:
                continue
            try:
                lowered = path.read_text(encoding="utf-8").lower()
            except (UnicodeDecodeError, OSError):
                continue
            if any(marker in lowered for marker in markers):
                found.append(str(path.relative_to(root.parent)))

    if found:
        pytest.fail(
            "Row Level Security ist aufgetaucht in:\n  " + "\n  ".join(found)
            + "\nDas ist eine Verbesserung. Bitte diesen Test und den Blocker "
              "workspace_isolation_without_database_enforcement neu bewerten."
        )
