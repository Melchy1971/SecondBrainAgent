from __future__ import annotations

import json
import argparse
import hashlib
import os
import re
import shutil
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Any, Iterable, Iterator

from secondbrain.providers.base.provider_models import ChatMessage, CompletionRequest, StreamChunk
from secondbrain.utils import atomic_replace


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
    """Compatibility facade over the canonical conversation store.

    The legacy JSONL file remains read-compatible, but all new writes use
    ``ConversationStore`` under ``runtime/chat``.
    """

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.path = self.project_root / "runtime" / "native" / "chat_history.jsonl"

    def append(self, message: NativeChatMessage | dict[str, Any]) -> dict[str, Any]:
        record = message.to_dict() if isinstance(message, NativeChatMessage) else dict(message)
        record.setdefault("ts", time.time())
        record.setdefault("source", "native_chat")
        record.setdefault("metadata", {})
        conversation = self._compat_conversation()
        stored = self._conversation_store().append_message(
            conversation["id"],
            str(record.get("role") or "system"),
            str(record.get("content") or ""),
            metadata={
                **dict(record.get("metadata") or {}),
                "source": record.get("source"),
                "command": record.get("command"),
                "ok": record.get("ok"),
            },
        )
        return {**record, "id": stored["id"], "created": stored["created"]}

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for conversation in self._conversation_store().list(include_archived=True):
            for message in self._conversation_store().messages(str(conversation["id"])):
                metadata = dict(message.get("metadata") or {})
                rows.append({
                    "role": message.get("role"),
                    "content": message.get("content"),
                    "ts": message.get("created"),
                    "source": metadata.get("source", "chat_engine"),
                    "command": metadata.get("command", ""),
                    "ok": metadata.get("ok"),
                    "metadata": metadata,
                    "conversation_id": conversation["id"],
                })
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    rows.append({"role": "system", "content": "INVALID_CHAT_RECORD", "raw": line, "ts": 0, "ok": False})
        return rows[-max(1, int(limit)):]

    def status(self, limit: int = 10) -> dict[str, Any]:
        messages = self.list(limit=limit)
        total = len(self.list(limit=1_000_000))
        return {
            "ok": True,
            "schema": "secondbrain.native.chat.v30_29",
            "status": "ready",
            "path": str(self._conversation_store().root),
            "total_messages": total,
            "visible_messages": len(messages),
            "messages": messages,
        }

    def clear(self) -> dict[str, Any]:
        store = self._conversation_store()
        deleted = 0
        for conversation in store.list(include_archived=True):
            if store.delete(str(conversation["id"])).get("ok"):
                deleted += 1
        if self.path.exists():
            self.path.write_text("", encoding="utf-8")
        return {"ok": True, "status": "cleared", "path": str(store.root), "deleted_conversations": deleted}

    def _conversation_store(self) -> "ConversationStore":
        return ConversationStore(self.project_root)

    def _compat_conversation(self) -> dict[str, Any]:
        store = self._conversation_store()
        current = next((row for row in store.list() if row.get("workspace") == "legacy-native-chat"), None)
        return current or store.create("Native Chat", workspace="legacy-native-chat")


@dataclass(frozen=True, slots=True)
class Conversation:
    id: str
    title: str
    workspace: str
    provider: str
    model: str
    created: str
    updated: str
    pinned: bool = False
    favorite: bool = False
    archived: bool = False
    parent_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConversationStore:
    """Conversation-aware persistence backing the existing native chat service."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.root = self.project_root / "runtime" / "chat"

    def create(
        self,
        title: str,
        *,
        workspace: str = "chat",
        provider: str = "ollama",
        model: str = "llama3.2",
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        conversation_id = str(uuid.uuid4())
        now = _utc_now()
        conversation = Conversation(
            id=conversation_id,
            title=(title or "Neue Unterhaltung").strip()[:120],
            workspace=(workspace or "chat").strip(),
            provider=(provider or "ollama").strip().lower(),
            model=(model or "llama3.2").strip(),
            created=now,
            updated=now,
            parent_id=parent_id,
        )
        directory = self._directory(conversation_id)
        (directory / "attachments").mkdir(parents=True, exist_ok=True)
        (directory / "exports").mkdir(parents=True, exist_ok=True)
        (directory / "messages.jsonl").touch()
        self._write_conversation(conversation)
        return conversation.to_dict()

    def get(self, conversation_id: str) -> dict[str, Any] | None:
        path = self._directory(conversation_id) / "conversation.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def list(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for path in self.root.glob("*/conversation.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and (include_archived or not row.get("archived")):
                rows.append(row)
        return sorted(rows, key=lambda row: (bool(row.get("pinned")), str(row.get("updated", ""))), reverse=True)

    def messages(self, conversation_id: str) -> list[dict[str, Any]]:
        path = self._directory(conversation_id) / "messages.jsonl"
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        conversation = self.get(conversation_id)
        if conversation is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        row = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "created": _utc_now(),
            "metadata": metadata or {},
        }
        path = self._directory(conversation_id) / "messages.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        self.update(conversation_id, updated=row["created"])
        return row

    def update(self, conversation_id: str, **changes: Any) -> dict[str, Any]:
        current = self.get(conversation_id)
        if current is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        allowed = {"title", "workspace", "provider", "model", "updated", "pinned", "favorite", "archived"}
        current.update({key: value for key, value in changes.items() if key in allowed})
        current["updated"] = str(current.get("updated") or _utc_now())
        conversation = Conversation(**{key: current.get(key) for key in Conversation.__dataclass_fields__})
        self._write_conversation(conversation)
        return conversation.to_dict()

    def version(self, conversation_id: str, *, provider: str, model: str) -> dict[str, Any]:
        current = self.get(conversation_id)
        if current is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        created = self.create(
            str(current.get("title") or "Unterhaltung") + " (Provider-Version)",
            workspace=str(current.get("workspace") or "chat"),
            provider=provider,
            model=model,
            parent_id=conversation_id,
        )
        for message in self.messages(conversation_id):
            self.append_message(
                created["id"],
                str(message.get("role") or "system"),
                str(message.get("content") or ""),
                metadata={**dict(message.get("metadata") or {}), "copied_from": message.get("id")},
            )
        return self.get(created["id"]) or created

    def search(self, query: str) -> list[dict[str, Any]]:
        needle = (query or "").strip().lower()
        if not needle:
            return self.list(include_archived=True)
        results: list[dict[str, Any]] = []
        for conversation in self.list(include_archived=True):
            messages = self.messages(str(conversation["id"]))
            haystack = " ".join([str(conversation.get("title", "")), *(str(item.get("content", "")) for item in messages)]).lower()
            if needle in haystack:
                results.append({**conversation, "match_count": haystack.count(needle)})
        return results

    def export(self, conversation_id: str, *, format: str = "json") -> dict[str, Any]:
        conversation = self.get(conversation_id)
        if conversation is None:
            return {"ok": False, "status": "not_found", "conversation_id": conversation_id}
        messages = self.messages(conversation_id)
        exports = self._directory(conversation_id) / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        if format == "md":
            path = exports / "conversation.md"
            body = [f"# {conversation['title']}", ""]
            for message in messages:
                body.extend([f"## {str(message.get('role', '')).title()}", "", str(message.get("content", "")), ""])
            path.write_text("\n".join(body), encoding="utf-8")
        elif format == "json":
            path = exports / "conversation.json"
            path.write_text(json.dumps({"conversation": conversation, "messages": messages}, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            return {"ok": False, "status": "unsupported_format", "format": format}
        return {"ok": True, "status": "exported", "path": str(path), "format": format}

    def delete(self, conversation_id: str) -> dict[str, Any]:
        directory = self._directory(conversation_id)
        if not directory.exists():
            return {"ok": False, "status": "not_found", "conversation_id": conversation_id}
        shutil.rmtree(directory)
        return {"ok": True, "status": "deleted", "conversation_id": conversation_id}

    def attachment_dir(self, conversation_id: str) -> Path:
        if self.get(conversation_id) is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        path = self._directory(conversation_id) / "attachments"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _directory(self, conversation_id: str) -> Path:
        try:
            normalized = str(uuid.UUID(str(conversation_id)))
        except ValueError as exc:
            raise ValueError("invalid conversation id") from exc
        return self.root / normalized

    def _write_conversation(self, conversation: Conversation) -> None:
        path = self._directory(conversation.id) / "conversation.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(conversation.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        atomic_replace(temporary, path)


class AttachmentManager:
    SUPPORTED = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".png", ".jpg", ".jpeg", ".json", ".md"}

    def __init__(self, project_root: str | Path, store: ConversationStore) -> None:
        self.project_root = Path(project_root).resolve()
        self.store = store

    def attach(self, conversation_id: str, source_path: str | Path) -> dict[str, Any]:
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            return {"ok": False, "status": "source_not_found", "path": str(source)}
        if source.suffix.lower() not in self.SUPPORTED:
            return {"ok": False, "status": "unsupported_type", "extension": source.suffix.lower()}
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest_path = self.store.attachment_dir(conversation_id) / f"{digest}.json"
        if manifest_path.exists():
            return {"ok": True, "status": "duplicate", **json.loads(manifest_path.read_text(encoding="utf-8"))}
        from secondbrain.native.document_explorer import DocumentExplorer

        imported = DocumentExplorer(self.project_root).import_file(str(source), copy=False)
        if not imported.get("ok"):
            return imported
        manifest = {
            "id": digest,
            "name": source.name,
            "path": str(source),
            "extension": source.suffix.lower(),
            "size": source.stat().st_size,
            "import": imported,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "status": "attached", **manifest}

    def list(self, conversation_id: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in self.store.attachment_dir(conversation_id).glob("*.json"):
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return rows


class ChatContextBuilder:
    """Kompatibilitaets-Fassade ueber die eine Context Pipeline (v30.46.2).

    Implementierung: secondbrain.chat.context.ContextBuilder
    (Prompt -> Conversation -> Working -> Semantic -> Documents ->
    Hybrid Search -> Context -> LLM). Vertrag von build()/citations()
    bleibt unveraendert.
    """

    def __init__(
        self,
        project_root: str | Path,
        *,
        rag_runtime: Any = None,
        memory_explorer: Any = None,
        attachments: Any = None,
    ) -> None:
        from secondbrain.chat.context import ContextBuilder

        self.project_root = Path(project_root).resolve()
        self._builder = ContextBuilder(
            self.project_root,
            rag_runtime=rag_runtime,
            memory_explorer=memory_explorer,
            attachments=attachments,
        )

    def build(
        self,
        prompt: str,
        history: list[dict[str, Any]],
        *,
        selected_sources: Iterable[str] = ("documents", "memory"),
        selected_documents: Iterable[str] = (),
        limit: int = 5,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        return self._builder.build(
            prompt,
            history,
            selected_sources=selected_sources,
            selected_documents=selected_documents,
            limit=limit,
            conversation_id=conversation_id,
        )

    def citations(self, hits: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._builder.citations(hits)


class ChatEngine:
    """Canonical chat engine used by every project surface."""

    VERSION = "30.46.1"

    DEFAULT_MODELS = {
        "openai": "gpt-4.1-mini",
        "ollama": "llama3.2",
        "gemini": "gemini-2.0-flash",
        "anthropic": "claude-3-5-sonnet-latest",
        "claude": "claude-3-5-sonnet-latest",
    }

    def __init__(
        self,
        project_root: str | Path | None = None,
        timeout_seconds: int = 60,
        *,
        provider_manager: Any = None,
        rag_runtime: Any = None,
        memory_explorer: Any = None,
    ):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.timeout_seconds = int(timeout_seconds)
        self.store = NativeChatStore(self.project_root)
        self.conversations = ConversationStore(self.project_root)
        self.attachments = AttachmentManager(self.project_root, self.conversations)
        self.context_builder = ChatContextBuilder(
            self.project_root,
            rag_runtime=rag_runtime,
            memory_explorer=memory_explorer,
            attachments=self.attachments,
        )
        from secondbrain.chat.evaluation import AnswerEvaluator
        self.answer_evaluator = AnswerEvaluator()
        self._provider_manager = provider_manager
        self.last_conversation_id: str | None = None

    def send(
        self,
        text: str,
        *,
        conversation_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        workspace: str = "chat",
        selected_sources: Iterable[str] = ("documents", "memory"),
        selected_documents: Iterable[str] = (),
        history: Iterable[dict[str, Any]] = (),
        limit: int = 5,
        goal_prompt: str = "",
    ) -> dict[str, Any]:
        prompt = (text or "").strip()
        if not prompt:
            return {"ok": False, "status": "empty_question", "error": "Keine Frage angegeben"}
        provider_name, model_name = self._provider_config(provider, model)
        conversation = self._prepare_conversation(
            prompt,
            conversation_id=conversation_id,
            workspace=workspace,
            provider=provider_name,
            model=model_name,
        )
        prior = [*self.conversations.messages(conversation["id"]), *[dict(item) for item in history]]
        context = self.context_builder.build(
            prompt,
            prior,
            selected_sources=selected_sources,
            selected_documents=selected_documents,
            limit=limit,
            conversation_id=str(conversation["id"]),
        )
        user_message = self.conversations.append_message(conversation["id"], "user", prompt)
        request = self._completion_request(
            prompt, prior, context, model_name, provider=provider_name,
            workspace=workspace, goal_prompt=goal_prompt, stream=False,
        )
        try:
            response = self._providers().complete(provider_name, request)
        except Exception as exc:
            return {
                "ok": False,
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {exc}",
                "conversation": self.conversations.get(conversation["id"]),
                "message": user_message,
                "citations": context["citations"],
            }
        evaluation = self.answer_evaluator.evaluate(
            prompt,
            response.content,
            evidence=[*context["hits"], *context["memories"]],
            citations=context["citations"],
        ).to_dict()
        assistant = self.conversations.append_message(
            conversation["id"],
            "assistant",
            response.content,
            metadata={"provider": response.provider, "model": response.model, "citations": context["citations"],
                      "usage": response.usage, "evaluation": evaluation},
        )
        return {
            "ok": True,
            "status": "answered",
            "conversation": self.conversations.get(conversation["id"]),
            "message": assistant,
            "answer": response.content,
            "citations": context["citations"],
            "memory_context": context["memories"],
            "evaluation": evaluation,
        }

    def stream_response(
        self,
        text: str,
        *,
        conversation_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        workspace: str = "chat",
        selected_sources: Iterable[str] = ("documents", "memory"),
        selected_documents: Iterable[str] = (),
        limit: int = 5,
        cancel_event: Event | None = None,
        goal_prompt: str = "",
    ) -> Iterator[StreamChunk]:
        prompt = (text or "").strip()
        if not prompt:
            raise ValueError("empty_question")
        provider_name, model_name = self._provider_config(provider, model)
        conversation = self._prepare_conversation(
            prompt,
            conversation_id=conversation_id,
            workspace=workspace,
            provider=provider_name,
            model=model_name,
        )
        prior = self.conversations.messages(conversation["id"])
        context = self.context_builder.build(
            prompt,
            prior,
            selected_sources=selected_sources,
            selected_documents=selected_documents,
            limit=limit,
            conversation_id=str(conversation["id"]),
        )
        self.conversations.append_message(conversation["id"], "user", prompt)
        request = self._completion_request(
            prompt, prior, context, model_name, provider=provider_name,
            workspace=workspace, goal_prompt=goal_prompt, stream=True,
        )
        parts: list[str] = []
        cancelled = False
        try:
            for provider_chunk in self._providers().stream(provider_name, request):
                token_chunks = self._token_chunks(provider_chunk)
                for chunk in token_chunks:
                    if cancel_event is not None and cancel_event.is_set():
                        cancelled = True
                        break
                    parts.append(chunk.delta)
                    yield chunk
                if cancelled:
                    break
        finally:
            cancelled = cancelled or bool(cancel_event and cancel_event.is_set())
            content = "".join(parts)
            if content:
                evaluation = self.answer_evaluator.evaluate(
                    prompt,
                    content,
                    evidence=[*context["hits"], *context["memories"]],
                    citations=context["citations"],
                ).to_dict()
                self.conversations.append_message(
                    conversation["id"],
                    "assistant",
                    content,
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "citations": context["citations"],
                        "cancelled": cancelled,
                        "evaluation": evaluation,
                    },
                )

    def retry(self, conversation_id: str, **options: Any) -> dict[str, Any]:
        messages = self.conversations.messages(conversation_id)
        prompt = next((str(row.get("content", "")) for row in reversed(messages) if row.get("role") == "user"), "")
        if not prompt:
            return {"ok": False, "status": "no_user_message"}
        return self.send(prompt, conversation_id=conversation_id, **options)

    def continue_response(self, conversation_id: str, **options: Any) -> dict[str, Any]:
        return self.send("Bitte setze die letzte Antwort fort.", conversation_id=conversation_id, **options)

    def _prepare_conversation(
        self,
        prompt: str,
        *,
        conversation_id: str | None,
        workspace: str,
        provider: str,
        model: str,
    ) -> dict[str, Any]:
        current = self.conversations.get(conversation_id) if conversation_id else None
        if current is None:
            created = self.conversations.create(prompt[:80], workspace=workspace, provider=provider, model=model)
            self.last_conversation_id = str(created["id"])
            return created
        if current.get("provider") != provider or current.get("model") != model:
            version = self.conversations.version(str(current["id"]), provider=provider, model=model)
            self.last_conversation_id = str(version["id"])
            return version
        self.last_conversation_id = str(current["id"])
        return current

    def _provider_config(self, provider: str | None, model: str | None) -> tuple[str, str]:
        provider_name = (provider or os.getenv("SECONDBRAIN_CHAT_PROVIDER") or "ollama").strip().lower()
        if provider_name == "claude":
            provider_name = "anthropic"
        model_name = (model or os.getenv("SECONDBRAIN_CHAT_MODEL") or self.DEFAULT_MODELS.get(provider_name) or "default").strip()
        return provider_name, model_name

    def _providers(self) -> Any:
        if self._provider_manager is None:
            from secondbrain.providers.routing.provider_factory import build_default_provider_manager
            self._provider_manager = build_default_provider_manager()
        return self._provider_manager

    @staticmethod
    def _token_chunks(chunk: StreamChunk) -> list[StreamChunk]:
        tokens = re.findall(r"\S+\s*|\s+", chunk.delta)
        if len(tokens) <= 1:
            return [chunk]
        return [
            StreamChunk(
                provider=chunk.provider,
                model=chunk.model,
                delta=token,
                done=chunk.done and index == len(tokens) - 1,
                raw=chunk.raw,
            )
            for index, token in enumerate(tokens)
        ]

    def _completion_request(
        self,
        prompt: str,
        prior: list[dict[str, Any]],
        context: dict[str, Any] | str,
        model: str,
        *,
        provider: str = "",
        workspace: str = "",
        goal_prompt: str = "",
        stream: bool,
    ) -> CompletionRequest:
        from secondbrain.chat.context import PromptAssembler

        assembler = PromptAssembler(project_root=self.project_root)
        if isinstance(context, dict) and isinstance(context.get("prompt_sections"), dict):
            workspace_text = f"Workspace: {workspace}" if workspace else ""
            return assembler.final_request(
                prompt,
                prior,
                context["prompt_sections"],
                model,
                provider=provider,
                workspace_prompt=workspace_text,
                goal_prompt=goal_prompt,
                stream=stream,
            )
        return assembler.completion_request(
            prompt, prior, str(context), model, provider=provider, stream=stream
        )

    def ask(self, text: str, *, limit: int = 5, **options: Any) -> dict[str, Any]:
        result = self.send(text, limit=limit, **options)
        return {
            **result,
            "question": (text or "").strip(),
            "history": self.store.status(limit=12),
        }

    def search(self, text: str, *, limit: int = 5) -> dict[str, Any]:
        query = (text or "").strip()
        if not query:
            return {"ok": False, "status": "empty_query", "error": "Keine Suche angegeben"}
        provider, model = self._provider_config(None, None)
        conversation = self._prepare_conversation(query, conversation_id=None, workspace="search", provider=provider, model=model)
        self.conversations.append_message(conversation["id"], "user", f"Suche: {query}")
        context = self.context_builder.build(query, [], selected_sources=("documents",), limit=limit)
        summary = "\n\n".join(str(hit.get("snippet") or hit.get("text") or "") for hit in context["hits"]) or "Keine Treffer."
        self.conversations.append_message(conversation["id"], "assistant", summary, metadata={"citations": context["citations"], "mode": "hybrid_search"})
        return {
            "ok": True,
            "status": "searched",
            "query": query,
            "summary": summary,
            "citations": context["citations"],
            "conversation": self.conversations.get(conversation["id"]),
            "history": self.store.status(limit=12),
        }

    def record_exchange(self, user_text: str, assistant_text: str, *, workspace: str = "compatibility") -> dict[str, Any]:
        provider, model = self._provider_config(None, None)
        conversation = self._prepare_conversation(user_text, conversation_id=None, workspace=workspace, provider=provider, model=model)
        user = self.conversations.append_message(conversation["id"], "user", user_text)
        assistant = self.conversations.append_message(conversation["id"], "assistant", assistant_text, metadata={"mode": "compatibility_adapter"})
        return {"ok": True, "conversation": self.conversations.get(conversation["id"]), "user": user, "assistant": assistant}


NativeChatService = ChatEngine


def native_chat_status(project_root: str | Path | None = None, limit: int = 20) -> dict[str, Any]:
    return NativeChatStore(project_root).status(limit=limit)


def native_chat_ask(project_root: str | Path | None, text: str, *, limit: int = 5) -> dict[str, Any]:
    return ChatEngine(project_root).ask(text, limit=limit)


def native_chat_search(project_root: str | Path | None, text: str, *, limit: int = 5) -> dict[str, Any]:
    return ChatEngine(project_root).search(text, limit=limit)


def conversation_cli_main(argv: list[str] | None = None) -> int:
    commands = {
        "ai-chat", "conversation-list", "conversation-open", "conversation-export",
        "conversation-delete", "conversation-pin", "conversation-search", "conversation-gui",
    }
    parser = argparse.ArgumentParser(prog="secondbrain conversation")
    parser.add_argument("cmd", choices=sorted(commands))
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parsed, _ = parser.parse_known_args(argv)
    store = ConversationStore(parsed.project_root)

    if parsed.cmd == "conversation-gui":
        from secondbrain.native.ai_workspace.gui import run_gui
        return run_gui(parsed.project_root, initial_module="chat")
    if parsed.cmd == "ai-chat":
        payload: Any = ChatEngine(parsed.project_root).send(
            " ".join(parsed.args), provider=parsed.provider, model=parsed.model,
        )
    elif parsed.cmd == "conversation-list":
        payload = {"ok": True, "conversations": store.list(), "count": len(store.list())}
    elif parsed.cmd == "conversation-search":
        rows = store.search(" ".join(parsed.args))
        payload = {"ok": True, "conversations": rows, "count": len(rows)}
    elif not parsed.args:
        payload = {"ok": False, "status": "missing_conversation_id"}
    elif parsed.cmd == "conversation-open":
        conversation = store.get(parsed.args[0])
        payload = {
            "ok": conversation is not None,
            "status": "opened" if conversation else "not_found",
            "conversation": conversation,
            "messages": store.messages(parsed.args[0]) if conversation else [],
            "attachments": AttachmentManager(parsed.project_root, store).list(parsed.args[0]) if conversation else [],
        }
    elif parsed.cmd == "conversation-export":
        payload = store.export(parsed.args[0], format=parsed.format)
    elif parsed.cmd == "conversation-delete":
        payload = store.delete(parsed.args[0])
    elif parsed.cmd == "conversation-pin":
        try:
            payload = {"ok": True, "status": "pinned", "conversation": store.update(parsed.args[0], pinned=True)}
        except KeyError:
            payload = {"ok": False, "status": "not_found", "conversation_id": parsed.args[0]}
    else:  # pragma: no cover - choices above make this unreachable
        payload = {"ok": False, "status": "unknown_command"}
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return 0 if payload.get("ok") else 1


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
