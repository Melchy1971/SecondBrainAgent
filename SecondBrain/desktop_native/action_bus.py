from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from secondbrain.desktop_app import DesktopAppRuntime
from secondbrain.native.approval import NativeApprovalQueue
from secondbrain.native.chat import ChatEngine
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p1_vector_provider_guard import repair_vector_index

from .action_registry import ActionDefinition, ActionRegistry, build_core_registry
from .task_surface import TASK_FILTERS, TaskSurface
from .voice_de import parse_german_voice_command
from .voice_runtime import VoiceSession


class NativeActionBus:
    """Policy-aware adapter from all native inputs to existing application services."""

    def __init__(self, project_root: str | Path, *, workspace_id: str = "", actor: str = "local-user") -> None:
        self.project_root = Path(project_root).resolve()
        self.workspace_id = workspace_id
        self.actor = actor
        self.registry: ActionRegistry = build_core_registry(self._execute)
        self.voice = VoiceSession(self.registry, workspace_id=workspace_id, actor=actor)
        self.approvals = NativeApprovalQueue(self.project_root)

    def submit(self, utterance: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if self.voice.dialog and self.voice.dialog.missing_parameters:
            result = self.voice.provide_slots(parameters) if parameters else self.voice.continue_dialog(utterance)
        else:
            exact = self.registry.resolve_alias(utterance)
            result = self._submit_new(utterance, parameters, exact)
        if result.get("status") == "approval_required" and self.voice.dialog:
            dialog = self.voice.dialog
            approval = self.approvals.create(
                command=dialog.action_id,
                intent=dialog.action_id,
                text="",
                target=dialog.action_id.split(".", 1)[0],
                risk_level="external_write",
                reason="native_action_policy",
                category="native_action",
                payload={"binding": dialog.binding, "parameters": dialog.parameters},
                workspace_id=dialog.workspace_id,
                idempotency_key=dialog.binding,
                tool_idempotent=False,
            )
            result = {**result, "approval_id": approval["approval_id"]}
        return result

    def _submit_new(
        self,
        utterance: str,
        parameters: Mapping[str, Any] | None,
        exact: ActionDefinition | None,
    ) -> dict[str, Any]:
        if exact is not None:
            result = self.voice.dispatch(exact.id, parameters)
        else:
            command = parse_german_voice_command(utterance)
            mapped = self._map_legacy_command(command.intent, command.args)
            result = self.voice.dispatch(*mapped) if mapped else self.voice.understand(utterance, parameters)
        return result

    @staticmethod
    def _map_legacy_command(intent: str, args: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]] | None:
        if intent == "open_view":
            return f"navigation.{args.get('view', 'dashboard')}", {}
        if intent == "status":
            return "navigation.dashboard", {}
        if intent == "rag_search":
            return "search.query", {"query": args.get("query", "")}
        if intent in {"rag_answer", "chat"}:
            return "assistant.ask", {"text": args.get("query") or args.get("message", "")}
        if intent == "ingest_file":
            return "documents.import", {"path": args.get("path", "")}
        if intent == "vector_repair":
            return "index.repair", {}
        return None

    def confirm(self) -> dict[str, Any]:
        return self.voice.understand("ja")

    def approve(self, binding: str) -> dict[str, Any]:
        return self.voice.approve(binding)

    def _execute(self, payload: Mapping[str, Any]) -> Any:
        action_id = str(payload["action_id"])
        if action_id.startswith("navigation."):
            return {"next_view": payload["view"]}
        if action_id == "assistant.ask":
            return ChatEngine(self.project_root).ask(str(payload["text"]))
        if action_id == "search.query":
            return ChatEngine(self.project_root).search(str(payload["query"]))
        if action_id == "tasks.list":
            tasks = DesktopAppRuntime(self.project_root).tasks()
            return {"count": len(tasks), "items": tasks}
        if action_id.startswith("tasks.filter."):
            task_filter = action_id.rsplit(".", 1)[-1]
            if task_filter not in TASK_FILTERS:
                raise ValueError(f"unsupported task filter: {task_filter}")
            snapshot = TaskSurface(DesktopAppRuntime(self.project_root)).snapshot(task_filter)
            return {**snapshot, "next_view": "tasks"}
        if action_id == "tasks.create":
            title = str(payload["title"]).strip()
            if not title:
                raise ValueError("task title must not be empty")
            priority = str(payload.get("priority") or "medium").strip().casefold()
            if priority not in {"low", "medium", "high"}:
                raise ValueError("task priority must be low, medium, or high")
            return DesktopAppRuntime(self.project_root).add_task(title, priority=priority)
        if action_id == "tasks.complete":
            return DesktopAppRuntime(self.project_root).complete_task(payload["task"])
        if action_id == "tasks.rename":
            return DesktopAppRuntime(self.project_root).rename_task(payload["task"], payload["new_title"])
        if action_id == "tasks.archive":
            return DesktopAppRuntime(self.project_root).archive_task(payload["task"])
        if action_id == "tasks.restore":
            return DesktopAppRuntime(self.project_root).restore_task(payload["task"])
        runtime = P1RagRuntime(self.project_root)
        if action_id == "documents.import":
            return runtime.ingest_file(str(payload["path"]))
        if action_id == "index.repair":
            return repair_vector_index(runtime, write_report=True)
        raise RuntimeError(f"action has no bound application service: {action_id}")
