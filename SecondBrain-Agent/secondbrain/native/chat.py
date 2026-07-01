from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class NativeChatMessage:
    role: str
    content: str
    ts: float
    source: str = "native_chat"
    command: str = ""
    ok: bool | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["metadata"] = data.get("metadata") or {}
        return data


class NativeChatStore:
    """File-backed native chat history for the desktop Jarvis shell.

    Constraint: local, deterministic, no background web server dependency.
    Storage: runtime/native/chat_history.jsonl.
    """

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.path = self.project_root / "runtime" / "native" / "chat_history.jsonl"

    def append(self, message: NativeChatMessage | dict[str, Any]) -> dict[str, Any]:
        record = message.to_dict() if isinstance(message, NativeChatMessage) else dict(message)
        record.setdefault("ts", time.time())
        record.setdefault("source", "native_chat")
        record.setdefault("metadata", {})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"role": "system", "content": "INVALID_CHAT_RECORD", "raw": line, "ts": 0, "ok": False})
        return rows[-max(1, int(limit)):]

    def status(self, limit: int = 10) -> dict[str, Any]:
        messages = self.list(limit=limit)
        total = 0
        if self.path.exists():
            total = sum(1 for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())
        return {
            "ok": True,
            "schema": "secondbrain.native.chat.v30_29",
            "status": "ready",
            "path": str(self.path),
            "total_messages": total,
            "visible_messages": len(messages),
            "messages": messages,
        }

    def clear(self) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        return {"ok": True, "status": "cleared", "path": str(self.path)}


class NativeChatService:
    """Native chat bridge over existing RAG answer/search launcher commands."""

    def __init__(self, project_root: str | Path | None = None, timeout_seconds: int = 60):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.timeout_seconds = int(timeout_seconds)
        self.store = NativeChatStore(self.project_root)

    def ask(self, text: str, *, limit: int = 5) -> dict[str, Any]:
        question = (text or "").strip()
        if not question:
            return {"ok": False, "status": "empty_question", "error": "Keine Frage angegeben"}
        self.store.append(NativeChatMessage("user", question, time.time(), command="p1-rag-answer"))
        result = self._run_launcher("p1-rag-answer", question, "--limit", str(int(limit)))
        answer_text = self._extract_answer_text(result)
        self.store.append(NativeChatMessage(
            "assistant",
            answer_text,
            time.time(),
            command="p1-rag-answer",
            ok=bool(result.get("ok")),
            metadata={"launcher": result},
        ))
        return {
            "ok": bool(result.get("ok")),
            "status": "answered" if result.get("ok") else "failed",
            "question": question,
            "answer": answer_text,
            "launcher": result,
            "history": self.store.status(limit=12),
        }

    def search(self, text: str, *, limit: int = 5) -> dict[str, Any]:
        query = (text or "").strip()
        if not query:
            return {"ok": False, "status": "empty_query", "error": "Keine Suche angegeben"}
        self.store.append(NativeChatMessage("user", f"Suche: {query}", time.time(), command="p1-rag-hybrid-search"))
        result = self._run_launcher("p1-rag-hybrid-search", query, "--limit", str(int(limit)))
        summary = self._extract_answer_text(result)
        self.store.append(NativeChatMessage(
            "assistant",
            summary,
            time.time(),
            command="p1-rag-hybrid-search",
            ok=bool(result.get("ok")),
            metadata={"launcher": result},
        ))
        return {
            "ok": bool(result.get("ok")),
            "status": "searched" if result.get("ok") else "failed",
            "query": query,
            "summary": summary,
            "launcher": result,
            "history": self.store.status(limit=12),
        }

    def _run_launcher(self, *args: str) -> dict[str, Any]:
        try:
            proc = subprocess.run(
                [sys.executable, "launcher.py", *args],
                cwd=str(self.project_root),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
            )
            raw = (proc.stdout or proc.stderr or "").strip()
            parsed: Any = None
            if raw:
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = None
            ok = proc.returncode == 0 and (not isinstance(parsed, dict) or bool(parsed.get("ok", True)))
            return {"ok": ok, "returncode": proc.returncode, "raw": raw, "json": parsed}
        except subprocess.TimeoutExpired as exc:
            return {"ok": False, "status": "timeout", "error": str(exc)}
        except Exception as exc:  # pragma: no cover
            return {"ok": False, "status": "error", "error": f"{type(exc).__name__}: {exc}"}

    def _extract_answer_text(self, result: dict[str, Any]) -> str:
        if not result.get("ok"):
            return result.get("error") or result.get("raw") or "Befehl fehlgeschlagen."
        data = result.get("json")
        if isinstance(data, dict):
            for key in ("answer", "summary", "text", "output"):
                if data.get(key):
                    return str(data[key])
            if isinstance(data.get("results"), list):
                return json.dumps(data.get("results")[:5], ensure_ascii=False, indent=2, default=str)
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        return result.get("raw") or "OK"


def native_chat_status(project_root: str | Path | None = None, limit: int = 20) -> dict[str, Any]:
    return NativeChatStore(project_root).status(limit=limit)


def native_chat_ask(project_root: str | Path | None, text: str, *, limit: int = 5) -> dict[str, Any]:
    return NativeChatService(project_root).ask(text, limit=limit)


def native_chat_search(project_root: str | Path | None, text: str, *, limit: int = 5) -> dict[str, Any]:
    return NativeChatService(project_root).search(text, limit=limit)
