from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


RISKY_KEYWORDS = {
    "lösche", "loesche", "delete", "remove", "entferne", "repariere", "repair",
    "importiere", "import", "migriere", "migrate", "schreibe", "write", "sende", "send",
}


@dataclass(frozen=True)
class AgentTask:
    id: str
    title: str
    intent: str
    status: str
    risk: str
    requires_approval: bool
    created_at: float
    updated_at: float
    source: str = "native"
    result: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentControlCenter:
    """Native orchestration facade for Jarvis agents.

    Scope v30.34:
    - deterministic local task planning
    - approval-aware task queue
    - safe execution bridge to already existing native modules
    - JSONL audit trail for explainable desktop operation
    """

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.runtime_dir = self.project_root / "runtime" / "native"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.task_file = self.runtime_dir / "agent_tasks.jsonl"
        self.log_file = self.runtime_dir / "agent_activity.jsonl"

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"corrupt": True, "raw": line})
        return rows

    def _write_tasks(self, rows: list[dict[str, Any]]) -> None:
        self.task_file.parent.mkdir(parents=True, exist_ok=True)
        with self.task_file.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def _log(self, event: str, payload: dict[str, Any]) -> None:
        self._append_jsonl(self.log_file, {"ts": time.time(), "event": event, **payload})

    def agents(self) -> list[dict[str, Any]]:
        modules = [
            ("jarvis", "Primärer persönlicher Assistent", True),
            ("document_agent", "Dokumentenimport, Vorschau, Tags, OCR-Status", (self.project_root / "secondbrain" / "native" / "document_explorer.py").exists()),
            ("memory_agent", "Memory-Suche, Timeline, Export, Archiv", (self.project_root / "secondbrain" / "native" / "memory_explorer.py").exists()),
            ("command_agent", "Kommando-Palette und Freigaben", (self.project_root / "secondbrain" / "native" / "command_center.py").exists()),
            ("rag_agent", "RAG-Suche, Golden Gate, Vector Audit", (self.project_root / "secondbrain" / "p1_rag_runtime.py").exists()),
            ("voice_agent", "Deutsche Sprachbefehle", (self.project_root / "secondbrain" / "native" / "voice_commands.py").exists()),
        ]
        return [
            {
                "id": agent_id,
                "name": name,
                "available": bool(available),
                "status": "ready" if available else "missing",
            }
            for agent_id, name, available in modules
        ]

    def status(self) -> dict[str, Any]:
        tasks = self.tasks(limit=10_000)
        pending = [t for t in tasks if t.get("status") == "pending"]
        approval = [t for t in tasks if t.get("requires_approval") and t.get("status") == "pending"]
        running = [t for t in tasks if t.get("status") == "running"]
        failed = [t for t in tasks if t.get("status") == "failed"]
        available_agents = [a for a in self.agents() if a.get("available")]
        return {
            "ok": True,
            "status": "ready",
            "version": "v30.34",
            "native_primary": True,
            "agents_total": len(self.agents()),
            "agents_ready": len(available_agents),
            "tasks_total": len(tasks),
            "tasks_pending": len(pending),
            "tasks_running": len(running),
            "tasks_failed": len(failed),
            "tasks_requiring_approval": len(approval),
            "runtime_files": {
                "tasks": str(self.task_file),
                "activity": str(self.log_file),
            },
        }

    def _classify(self, text: str) -> tuple[str, str, bool]:
        lowered = text.lower()
        if any(k in lowered for k in ["dokument", "datei", "pdf", "ordner", "import"]):
            intent = "document"
        elif any(k in lowered for k in ["memory", "erinner", "notiz", "wissen"]):
            intent = "memory"
        elif any(k in lowered for k in ["suche", "frage", "rag", "quelle"]):
            intent = "search"
        elif any(k in lowered for k in ["status", "prüfe", "pruefe", "diagnose"]):
            intent = "diagnostics"
        else:
            intent = "assistant"
        requires_approval = any(k in lowered for k in RISKY_KEYWORDS)
        risk = "write" if requires_approval else "read"
        return intent, risk, requires_approval

    def plan(self, text: str) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "status": "missing_task_text"}
        intent, risk, requires_approval = self._classify(text)
        steps = [
            {"step": 1, "action": "classify", "intent": intent},
            {"step": 2, "action": "select_agent", "agent": self._agent_for_intent(intent)},
            {"step": 3, "action": "approval_gate", "required": requires_approval},
            {"step": 4, "action": "execute", "mode": "native_bridge"},
            {"step": 5, "action": "audit", "target": str(self.log_file)},
        ]
        return {"ok": True, "task": text, "intent": intent, "risk": risk, "requires_approval": requires_approval, "steps": steps}

    def _agent_for_intent(self, intent: str) -> str:
        return {
            "document": "document_agent",
            "memory": "memory_agent",
            "search": "rag_agent",
            "diagnostics": "command_agent",
            "assistant": "jarvis",
        }.get(intent, "jarvis")

    def add_task(self, text: str, source: str = "native") -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "status": "missing_task_text"}
        intent, risk, requires_approval = self._classify(text)
        now = time.time()
        task = AgentTask(
            id="agt_" + uuid.uuid4().hex[:12],
            title=text,
            intent=intent,
            status="pending",
            risk=risk,
            requires_approval=requires_approval,
            created_at=now,
            updated_at=now,
            source=source,
        )
        self._append_jsonl(self.task_file, task.to_dict())
        self._log("task_added", task.to_dict())
        return {"ok": True, "task": task.to_dict(), "approval_required": requires_approval}

    def tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self.task_file)
        rows.sort(key=lambda r: r.get("updated_at", r.get("created_at", 0)), reverse=True)
        return rows[: max(0, limit)]

    def _find_task(self, task_id_or_query: str) -> tuple[int, dict[str, Any] | None, list[dict[str, Any]]]:
        query = (task_id_or_query or "").strip().lower()
        rows = self._read_jsonl(self.task_file)
        for idx, row in enumerate(rows):
            if row.get("id", "").lower() == query:
                return idx, row, rows
        for idx, row in enumerate(rows):
            if query and query in row.get("title", "").lower():
                return idx, row, rows
        return -1, None, rows

    def run_task(self, task_id_or_query: str, *, confirmed: bool = False, dry_run: bool = False) -> dict[str, Any]:
        idx, task, rows = self._find_task(task_id_or_query)
        if not task:
            return {"ok": False, "status": "task_not_found", "query": task_id_or_query}
        if task.get("requires_approval") and not confirmed:
            self._log("task_blocked_for_approval", {"id": task.get("id"), "title": task.get("title")})
            return {"ok": False, "status": "approval_required", "task": task}
        if dry_run:
            return {"ok": True, "status": "dry_run", "task": task, "plan": self.plan(task.get("title", ""))}
        result = self._execute(task)
        task["status"] = "done" if result.get("ok") else "failed"
        task["updated_at"] = time.time()
        task["result"] = result.get("summary", result.get("status", ""))
        rows[idx] = task
        self._write_tasks(rows)
        self._log("task_executed", {"task": task, "result": result})
        return {"ok": result.get("ok", False), "status": "executed", "task": task, "result": result}

    def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        intent = task.get("intent")
        title = task.get("title", "")
        if intent == "diagnostics":
            return {"ok": True, "summary": "Diagnose geplant. Nutze Command Center für vollständige Runtime-Prüfung.", "command": "command-center-status"}
        if intent == "document":
            return {"ok": True, "summary": "Dokumentenaktion an Document Explorer übergeben.", "command": "document-explorer-status"}
        if intent == "memory":
            return {"ok": True, "summary": "Memory-Aktion an Memory Explorer übergeben.", "command": "memory-explorer-status"}
        if intent == "search":
            return {"ok": True, "summary": "Such-/RAG-Aufgabe vorbereitet.", "query": title}
        return {"ok": True, "summary": "Jarvis-Aufgabe lokal erfasst und abgeschlossen."}

    def complete_task(self, task_id_or_query: str) -> dict[str, Any]:
        return self._set_status(task_id_or_query, "done")

    def cancel_task(self, task_id_or_query: str) -> dict[str, Any]:
        return self._set_status(task_id_or_query, "cancelled")

    def _set_status(self, task_id_or_query: str, status: str) -> dict[str, Any]:
        idx, task, rows = self._find_task(task_id_or_query)
        if not task:
            return {"ok": False, "status": "task_not_found", "query": task_id_or_query}
        task["status"] = status
        task["updated_at"] = time.time()
        rows[idx] = task
        self._write_tasks(rows)
        self._log("task_status_changed", {"id": task.get("id"), "status": status})
        return {"ok": True, "task": task}

    def logs(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self.log_file)
        rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
        return rows[: max(0, limit)]
