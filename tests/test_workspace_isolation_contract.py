"""Vertrag der Workspace-Isolation im Task-/Projekt-Repository.

Repository-Zugriffe muessen explizit an ``workspace_id`` gebunden sein. Das
PostgreSQL-Backend setzt zusaetzlich einen transaktionslokalen Kontext und
erzwingt die Grenze per Row Level Security (RLS).
"""

from __future__ import annotations

import ast
from pathlib import Path

_SB = Path(__file__).resolve().parents[1] / "SecondBrain"
REPOSITORY = _SB / "tasks" / "repository.py"
SERVICE = _SB / "tasks" / "service.py"
JOB_REPOSITORY = _SB / "jobs" / "repository.py"
WORKSPACE_CONTEXT = _SB / "storage" / "workspace_context.py"


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


def test_write_deletes_only_records_in_bound_workspace() -> None:
    source = REPOSITORY.read_text(encoding="utf-8")
    assert "set(current) - desired_ids" in source
    assert 'scope = " AND workspace_id = :workspace_id"' in source
    assert 'f"DELETE FROM {_TABLE} WHERE collection=:collection AND record_id=:record_id{scope}"' in source


def test_service_write_calls_pass_workspace_id() -> None:
    tree = _tree(SERVICE)
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if not (isinstance(target, ast.Attribute) and target.attr == "_write"):
            continue
        if not any(keyword.arg == "workspace_id" for keyword in node.keywords):
            offenders.append(f"Zeile {node.lineno}: workspace_id fehlt")

    assert not offenders, (
        "TaskProjectService._write ohne expliziten Workspace-Kontext:\n"
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


def test_task_repository_read_is_workspace_scoped() -> None:
    tree = _tree(REPOSITORY)
    read = _method(tree, "PostgresTaskRepository", "read")
    names = {a.arg for a in read.args.args} | {a.arg for a in read.args.kwonlyargs}

    assert "workspace_id" in names


def test_row_level_security_is_fail_closed() -> None:
    source = WORKSPACE_CONTEXT.read_text(encoding="utf-8").lower()
    for marker in (
        "enable row level security",
        "force row level security",
        "create policy",
        "current_setting('",
        "with check",
    ):
        assert marker in source
