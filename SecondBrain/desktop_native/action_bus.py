from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

from secondbrain.calendar_assistant.models import parse_dt
from secondbrain.calendar_assistant.service import CalendarService
from secondbrain.desktop_app import DesktopAppRuntime
from secondbrain.mail_assistant.service import MailAssistant
from secondbrain.native.approval import NativeApprovalQueue
from secondbrain.native.chat import ChatEngine
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p1_vector_provider_guard import repair_vector_index

from .action_registry import ActionDefinition, ActionRegistry, build_core_registry
from .task_surface import TASK_FILTERS, TaskSurface
from .voice_de import parse_german_voice_command
from .voice_runtime import DialogContext, VoiceSession


class NativeActionBus:
    """Policy-aware adapter from all native inputs to existing application services."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        workspace_id: str = "",
        actor: str = "local-user",
        calendar_service: CalendarService | None = None,
        mail_assistant: MailAssistant | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.workspace_id = workspace_id
        self.actor = actor
        self.calendar_service = calendar_service or CalendarService()
        self.mail_assistant = mail_assistant or MailAssistant()
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
            result = self._prepare_external_approval(result, dialog)
        return result

    def _prepare_external_approval(
        self,
        result: dict[str, Any],
        dialog: DialogContext,
    ) -> dict[str, Any]:
        parameters = dict(dialog.parameters)
        if dialog.action_id == "calendar.create":
            raw_start = str(parameters["when"])
            start = parse_dt(raw_start)
            resolved = start is not None and start.tzinfo is not None
            execution_payload = {
                "event_id": "",
                "title": str(parameters["title"]),
                "start": start.isoformat() if resolved else raw_start,
                "end": (start + timedelta(hours=1)).isoformat() if resolved else raw_start,
            }
            prepared = self.calendar_service.prepare_change(
                "create_event",
                execution_payload,
                workspace_id=dialog.workspace_id,
                actor=dialog.actor,
                approval_queue=self.approvals,
            )
        elif dialog.action_id == "mail.send":
            execution_payload = {
                "recipients": [str(parameters["recipient"])],
                "subject": "",
                "body": str(parameters["body"]),
            }
            prepared = self.mail_assistant.prepare_change(
                "send_new_message",
                execution_payload,
                workspace_id=dialog.workspace_id,
                approval_queue=self.approvals,
            )
        else:
            approval = self.approvals.create(
                command=dialog.action_id,
                intent=dialog.action_id,
                text="",
                target=dialog.action_id.split(".", 1)[0],
                risk_level="external_write",
                reason="native_action_policy",
                category="native_action",
                payload={"binding": dialog.binding, "parameters": parameters},
                workspace_id=dialog.workspace_id,
                idempotency_key=dialog.binding,
                tool_idempotent=False,
            )
            return {**result, "approval_id": approval["approval_id"]}
        approval_id = str(prepared.get("approval_id") or "")
        if not approval_id:
            return {"status": "error", "error": "approval_creation_failed"}
        row = self.approvals.get(approval_id)
        bound_payload = dict(row.get("payload") or {}) if row else {}
        bound_payload.update({
            "binding": dialog.binding,
            "native_action_id": dialog.action_id,
            "execution_payload": execution_payload,
        })
        self.approvals.update_metadata(
            approval_id,
            {"payload": bound_payload, "tool_idempotent": False},
        )
        return {**result, "approval_id": approval_id}

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

    def decide_approval(self, approval_id: str, *, approved: bool, note: str = "") -> dict[str, Any]:
        row = self.approvals.get(str(approval_id).strip())
        if row is None:
            raise LookupError("approval not found")
        if str(row.get("workspace_id") or "") != self.workspace_id:
            raise PermissionError("approval workspace mismatch")
        if row.get("status") != "pending":
            raise ValueError(f"approval is not pending: {row.get('status')}")
        if not approved:
            rejected = self.approvals.reject(
                row["approval_id"],
                actor=self.actor,
                note=note,
            )
            return {"status": "rejected", "approval_id": row["approval_id"], "version": rejected["version"]}

        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        action_id = str(payload.get("native_action_id") or "")
        execution_payload = payload.get("execution_payload")
        if not isinstance(execution_payload, dict):
            raise ValueError("approval execution payload is unavailable")
        service = self._external_service(action_id)
        prepared = {**payload, "approval_id": row["approval_id"]}
        expected_action = {
            "calendar.create": "create_event",
            "mail.send": "send_new_message",
        }.get(action_id)
        if prepared.get("action") != expected_action:
            raise ValueError("approval action binding changed")
        if service._payload_hash(execution_payload) != prepared.get("payload_hash"):
            raise ValueError("approval payload changed")
        if action_id == "calendar.create":
            start = parse_dt(execution_payload.get("start"))
            end = parse_dt(execution_payload.get("end"))
            if start is None or end is None or start.tzinfo is None or end.tzinfo is None or end <= start:
                raise ValueError("calendar time is unresolved")
        connector = service.connector
        method = getattr(connector, str(prepared.get("action") or ""), None) if connector is not None else None
        if not callable(method):
            raise RuntimeError("external connector is not configured")

        self.approvals.approve(row["approval_id"], actor=self.actor, note=note)
        execution = service.commit_change(
            prepared,
            execution_payload,
            approval_queue=self.approvals,
            workspace_id=self.workspace_id,
        )
        active = self.approvals.get(row["approval_id"])
        lease_acquired = execution.get("status") in {
            "committed", "connector_offline", "recovery_required", "error",
        }
        if lease_acquired and active and active.get("status") == "executing" and active.get("execution_token"):
            completed = execution.get("status") == "committed"
            self.approvals.complete_execution(
                row["approval_id"],
                execution_token=str(active["execution_token"]),
                result_status="completed" if completed else "failed",
                result=execution,
            )
        if execution.get("status") != "committed":
            if execution.get("status") == "expired":
                current = self.approvals.get(row["approval_id"])
                if current and current.get("status") == "approved":
                    self.approvals.transition(row["approval_id"], "expired", actor=self.actor, note="approval expired")
            raise RuntimeError(
                f"external action failed: {execution.get('status')}:{execution.get('reason', '')}"
            )
        return {"status": "completed", "approval_id": row["approval_id"], "execution": execution}

    def _external_service(self, action_id: str) -> CalendarService | MailAssistant:
        if action_id == "calendar.create":
            return self.calendar_service
        if action_id == "mail.send":
            return self.mail_assistant
        raise ValueError(f"unsupported external approval action: {action_id}")

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
        if action_id == "approvals.approve":
            return self.decide_approval(str(payload["approval"]), approved=True)
        if action_id == "approvals.reject":
            return self.decide_approval(str(payload["approval"]), approved=False)
        if action_id in {"calendar.create", "mail.send"}:
            return {"status": "blocked", "reason": "persistent_approval_required"}
        runtime = P1RagRuntime(self.project_root)
        if action_id == "documents.import":
            return runtime.ingest_file(str(payload["path"]))
        if action_id == "index.repair":
            return repair_vector_index(runtime, write_report=True)
        raise RuntimeError(f"action has no bound application service: {action_id}")
