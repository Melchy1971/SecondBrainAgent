from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CommandDefinition:
    id: str
    title: str
    description: str
    category: str
    launcher_args: tuple[str, ...]
    risk: str = "read"
    requires_confirmation: bool = False
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["launcher_args"] = list(self.launcher_args)
        payload["aliases"] = list(self.aliases)
        return payload


DEFAULT_COMMANDS: tuple[CommandDefinition, ...] = (
    CommandDefinition(
        id="system.status",
        title="Systemstatus prüfen",
        description="Liest den zentralen Modul- und Runtime-Status.",
        category="System",
        launcher_args=("status", "--runtime"),
        aliases=("status", "jarvis status", "system prüfen"),
    ),
    CommandDefinition(
        id="system.repo_doctor",
        title="RepoDoctor ausführen",
        description="Prüft Repository-Struktur, Startpfade und Runtime-Smokes.",
        category="System",
        launcher_args=("repo-doctor", "--execute-runtime-checks"),
        aliases=("repo doctor", "diagnose", "systemdiagnose"),
    ),
    CommandDefinition(
        id="rag.status",
        title="RAG Status prüfen",
        description="Zeigt Dokument-, Chunk-, Vector- und Store-Status.",
        category="RAG",
        launcher_args=("p1-rag-status",),
        aliases=("rag status", "index status"),
    ),
    CommandDefinition(
        id="rag.production_gate",
        title="Production Gate ausführen",
        description="Prüft Provider, Golden Retrieval und Vector Audit.",
        category="RAG",
        launcher_args=("p1-production",),
        aliases=("production gate", "golden gate", "qualität prüfen"),
    ),
    CommandDefinition(
        id="rag.vector_audit",
        title="Vector Audit ausführen",
        description="Prüft Provider-/Modell-/Dimensionsdrift im Vector Index.",
        category="RAG",
        launcher_args=("p1-vector-provider-audit",),
        aliases=("vector audit", "vektor audit", "index prüfen"),
    ),
    CommandDefinition(
        id="rag.reindex",
        title="Index aktualisieren",
        description="Erzeugt Vektoren neu. Schreibende Aktion mit Bestätigung.",
        category="RAG",
        launcher_args=("p1-rag-reindex", "--write-report"),
        risk="write",
        requires_confirmation=True,
        aliases=("repariere index", "index aktualisieren", "index reparieren"),
    ),
    CommandDefinition(
        id="gui.status",
        title="GUI Status prüfen",
        description="Prüft GUI-Startpfad und Bootstrap-Konfiguration.",
        category="GUI",
        launcher_args=("gui-status",),
        aliases=("gui status", "oberfläche prüfen"),
    ),
    CommandDefinition(
        id="gui.bootstrap",
        title="GUI Bootstrap prüfen",
        description="Erzeugt und prüft Runtime-Defaults für die Desktop-Anwendung.",
        category="GUI",
        launcher_args=("gui-bootstrap",),
        aliases=("bootstrap", "start prüfen"),
    ),
)


class CommandCenter:
    """Native command palette and execution bridge.

    The center is intentionally file-backed. It can be used before a database exists,
    during first-run setup, and inside the native desktop shell.
    """

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.runtime_dir = self.project_root / "runtime" / "native"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.runtime_dir / "command_history.jsonl"
        self.approval_path = self.runtime_dir / "command_approvals.jsonl"
        self.favorites_path = self.runtime_dir / "command_favorites.json"
        self._commands = {command.id: command for command in DEFAULT_COMMANDS}

    def catalog(self) -> list[dict[str, Any]]:
        return [command.to_dict() for command in self._commands.values()]

    def status(self) -> dict[str, Any]:
        by_category: dict[str, int] = {}
        for command in self._commands.values():
            by_category[command.category] = by_category.get(command.category, 0) + 1
        return {
            "ok": True,
            "version": "30.31",
            "mode": "native_command_center",
            "project_root": str(self.project_root),
            "commands": len(self._commands),
            "categories": by_category,
            "history_entries": len(self.history(5000)),
            "pending_approvals": len(self.pending_approvals()),
            "favorites": self.favorites(),
        }

    def palette(self, query: str = "", limit: int = 25) -> dict[str, Any]:
        query_norm = query.strip().lower()
        rows: list[dict[str, Any]] = []
        for command in self._commands.values():
            haystack = " ".join([command.id, command.title, command.description, command.category, *command.aliases]).lower()
            if not query_norm or query_norm in haystack:
                rows.append(command.to_dict())
        return {"ok": True, "query": query, "count": len(rows[:limit]), "commands": rows[:limit]}

    def resolve(self, command_or_text: str) -> CommandDefinition | None:
        key = command_or_text.strip().lower()
        if key in self._commands:
            return self._commands[key]
        for command in self._commands.values():
            values = [command.id, command.title, *command.aliases]
            if any(key == value.lower() for value in values):
                return command
        for command in self._commands.values():
            values = [command.title, command.description, *command.aliases]
            if any(key in value.lower() for value in values):
                return command
        return None

    def run(self, command_or_text: str, *, dry_run: bool = False, confirmed: bool = False, timeout_seconds: int = 30) -> dict[str, Any]:
        command = self.resolve(command_or_text)
        if command is None:
            payload = {"ok": False, "status": "unknown_command", "input": command_or_text, "matches": self.palette(command_or_text, limit=10)["commands"]}
            self._append_history(payload)
            return payload

        if command.requires_confirmation and not confirmed and not dry_run:
            approval = self._enqueue_approval(command)
            payload = {
                "ok": False,
                "status": "approval_required",
                "approval_id": approval["approval_id"],
                "command": command.to_dict(),
                "message": "Schreibende Aktion blockiert. Mit command-approval-run bestätigen.",
            }
            self._append_history(payload)
            return payload

        launcher = self.project_root / "launcher.py"
        process_args = [sys.executable, str(launcher), *command.launcher_args]
        payload: dict[str, Any] = {
            "ok": True,
            "status": "dry_run" if dry_run else "executed",
            "command": command.to_dict(),
            "process_args": process_args,
            "confirmed": confirmed,
        }
        if not dry_run:
            started = time.time()
            completed = subprocess.run(
                process_args,
                cwd=str(self.project_root),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            payload.update(
                {
                    "ok": completed.returncode == 0,
                    "returncode": completed.returncode,
                    "duration_ms": int((time.time() - started) * 1000),
                    "stdout": completed.stdout[-12000:],
                    "stderr": completed.stderr[-12000:],
                }
            )
        self._append_history(payload)
        return payload

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(_read_jsonl(self.history_path))[-limit:]

    def favorites(self) -> list[str]:
        if not self.favorites_path.exists():
            return []
        try:
            data = json.loads(self.favorites_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [str(item) for item in data if str(item) in self._commands]
        return []

    def add_favorite(self, command_id: str) -> dict[str, Any]:
        command = self.resolve(command_id)
        if command is None:
            return {"ok": False, "status": "unknown_command", "input": command_id}
        values = self.favorites()
        if command.id not in values:
            values.append(command.id)
        self.favorites_path.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "favorites": values}

    def pending_approvals(self) -> list[dict[str, Any]]:
        return [item for item in _read_jsonl(self.approval_path) if item.get("status") == "pending"]

    def approve_and_run(self, approval_id: str, *, timeout_seconds: int = 30) -> dict[str, Any]:
        approvals = list(_read_jsonl(self.approval_path))
        selected = None
        for item in approvals:
            if item.get("approval_id") == approval_id and item.get("status") == "pending":
                selected = item
                item["status"] = "approved"
                item["approved_at"] = time.time()
                break
        if selected is None:
            return {"ok": False, "status": "approval_not_found", "approval_id": approval_id}
        _write_jsonl(self.approval_path, approvals)
        return self.run(str(selected["command_id"]), confirmed=True, timeout_seconds=timeout_seconds)

    def reject_approval(self, approval_id: str) -> dict[str, Any]:
        approvals = list(_read_jsonl(self.approval_path))
        changed = False
        for item in approvals:
            if item.get("approval_id") == approval_id and item.get("status") == "pending":
                item["status"] = "rejected"
                item["rejected_at"] = time.time()
                changed = True
        if changed:
            _write_jsonl(self.approval_path, approvals)
        return {"ok": changed, "status": "rejected" if changed else "approval_not_found", "approval_id": approval_id}

    def _append_history(self, payload: dict[str, Any]) -> None:
        row = {"ts": time.time(), **payload}
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def _enqueue_approval(self, command: CommandDefinition) -> dict[str, Any]:
        row = {
            "approval_id": uuid.uuid4().hex[:12],
            "ts": time.time(),
            "status": "pending",
            "command_id": command.id,
            "title": command.title,
            "risk": command.risk,
            "launcher_args": list(command.launcher_args),
        }
        with self.approval_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
