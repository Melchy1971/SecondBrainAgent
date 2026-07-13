"""Discovery of existing SecondBrain capabilities for the unified registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from secondbrain.agent.tool_registry import (
    ToolCapability,
    ToolDefinition,
    ToolInputSchema,
    ToolRegistry,
    ToolRiskLevel,
)


class ToolDiscovery:
    def __init__(self, project_root: str | Path = ".", registry: ToolRegistry | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.registry = registry or ToolRegistry(self.project_root / "runtime")

    def discover(self) -> list[ToolDefinition]:
        for definition in self._definitions():
            self.registry.upsert(definition)
        return self.registry.list(enabled_only=False)

    def _definitions(self) -> list[ToolDefinition]:
        return [
            self._tool("search.query", "Hybrid search over existing RAG data", "search", ToolCapability.SEARCH,
                       self._search, {"query": "string", "limit": "integer"}, required=("query",)),
            self._tool("documents.search", "Search existing documents", "document", ToolCapability.DOCUMENT,
                       self._documents_search, {"query": "string", "limit": "integer"}, required=("query",)),
            self._tool("import.file", "Import a file through the enterprise import engine", "connector", ToolCapability.CONNECTOR,
                       self._import_file, {"path": "string", "source": "string"}, required=("path",), risk=ToolRiskLevel.HIGH),
            self._tool("memory.search", "Search existing memory", "memory", ToolCapability.MEMORY_CORE,
                       self._memory_search, {"query": "string", "limit": "integer"}, required=("query",)),
            self._tool("memory.add", "Add an entry to existing memory", "memory", ToolCapability.MEMORY_CORE,
                       self._memory_add, {"content": "string", "kind": "string"}, required=("content",), risk=ToolRiskLevel.HIGH),
            self._tool("agents.status", "Read existing agent status", "workflow", ToolCapability.WORKFLOW_CORE, self._agents_status),
            self._tool("agents.plan.create", "Create a plan with the existing Agent Planner", "workflow", ToolCapability.WORKFLOW_CORE,
                       self._agent_plan, {"goal": "string", "workspace_id": "string"}, required=("goal",), risk=ToolRiskLevel.HIGH),
            self._tool("jobs.list", "List jobs from the native job queue", "workflow", ToolCapability.WORKFLOW_CORE,
                       self._jobs_list, {"status": "string", "kind": "string"}),
            self._tool("jobs.cancel", "Cancel a job in the native job queue", "workflow", ToolCapability.WORKFLOW_CORE,
                       self._job_cancel, {"job_id": "string"}, required=("job_id",), risk=ToolRiskLevel.HIGH),
            self._tool("notifications.list", "List native notifications", "system", ToolCapability.SYSTEM_CORE,
                       self._notifications_list, {"limit": "integer", "unread_only": "boolean"}),
            self._tool("notifications.send", "Create a native notification", "system", ToolCapability.SYSTEM_CORE,
                       self._notification_send, {"title": "string", "message": "string", "level": "string", "category": "string"},
                       required=("title", "message"), risk=ToolRiskLevel.HIGH),
            self._tool("settings.show", "Show existing embedding and store settings", "system", ToolCapability.SYSTEM_CORE,
                       self._settings_show),
            self._tool("voice.status", "Read native voice status", "system", ToolCapability.SYSTEM_CORE, self._voice_status),
            self._tool("voice.parse", "Parse a German voice command", "system", ToolCapability.SYSTEM_CORE,
                       self._voice_parse, {"text": "string"}, required=("text",)),
            self._tool("updates.check", "Check the existing local update manifest", "system", ToolCapability.SYSTEM_CORE,
                       self._updates_check, {"current_version": "string"}),
            self._tool("github.status", "Check availability of the existing GitHub connector", "connector", ToolCapability.CONNECTOR,
                       self._github_status),
            self._tool("filesystem.list", "List files below the project root", "file", ToolCapability.FILE,
                       self._filesystem_list, {"path": "string", "limit": "integer"}),
            self._tool("filesystem.read", "Read a UTF-8 text file below the project root", "file", ToolCapability.FILE,
                       self._filesystem_read, {"path": "string", "max_chars": "integer"}, required=("path",)),
        ]

    @staticmethod
    def _tool(
        name: str,
        description: str,
        category: str,
        capability: ToolCapability,
        handler: Callable[[Mapping[str, Any]], Any],
        properties: Mapping[str, str] | None = None,
        *,
        required: tuple[str, ...] = (),
        risk: ToolRiskLevel = ToolRiskLevel.LOW,
    ) -> ToolDefinition:
        schema = ToolInputSchema(
            properties={key: {"type": value} for key, value in dict(properties or {}).items()},
            required=required,
            additional_properties=False,
        )
        return ToolDefinition(
            name,
            description,
            category=category,
            input_schema=schema,
            output_schema={"type": "object"},
            risk_level=risk,
            requires_approval=risk in {ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL},
            handler=handler,
            capabilities=(capability,),
        )

    def _search(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.p1_rag_runtime import P1RagRuntime
        return P1RagRuntime(self.project_root).hybrid_search(str(payload["query"]), int(payload.get("limit", 5)))

    def _documents_search(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.document_explorer import DocumentExplorer
        return DocumentExplorer(self.project_root).search(str(payload["query"]), limit=int(payload.get("limit", 25)))

    def _import_file(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.importing import StreamingImportService
        session = StreamingImportService(self.project_root).import_file(
            str(payload["path"]), source=str(payload.get("source") or "tool_registry")
        )
        return {"ok": session.status == "completed", **session.to_dict()}

    def _memory_search(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.memory_explorer import MemoryExplorer
        return MemoryExplorer(self.project_root).search(str(payload["query"]), limit=int(payload.get("limit", 25)))

    def _memory_add(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.memory_explorer import MemoryExplorer
        return MemoryExplorer(self.project_root).add(str(payload["content"]), kind=str(payload.get("kind") or "semantic"), source="tool_registry")

    def _agents_status(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.agent_control_center import AgentControlCenter
        return AgentControlCenter(self.project_root).status()

    def _agent_plan(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.agent.planner import AgentPlanService
        return AgentPlanService(self.project_root).create(
            str(payload["goal"]), workspace_id=payload.get("workspace_id")
        ).to_dict()

    def _jobs_list(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.job_queue_center.service import JobQueueService
        service = JobQueueService(self.project_root)
        rows = service.list_jobs(status=payload.get("status"), kind=payload.get("kind"))
        return {"ok": True, "count": len(rows), "jobs": [item.to_dict() for item in rows]}

    def _job_cancel(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.job_queue_center.service import JobQueueService
        return {"ok": True, "job": JobQueueService(self.project_root).cancel(str(payload["job_id"])).to_dict()}

    def _notifications_list(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.notification_center.service import NotificationCenterService
        return NotificationCenterService(self.project_root).list_items(
            limit=int(payload.get("limit", 50)), unread_only=bool(payload.get("unread_only", False))
        )

    def _notification_send(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.notification_center.service import NotificationCenterService
        return NotificationCenterService(self.project_root).notify(
            str(payload["title"]), str(payload["message"]),
            level=str(payload.get("level") or "info"), category=str(payload.get("category") or "system"),
            source="tool_registry",
        )

    def _settings_show(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.gui.settings_center import SettingsCenter
        return {"ok": True, **SettingsCenter().render_embedding_settings()}

    def _voice_status(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.voice_control_center import voice_center_status
        return voice_center_status()

    def _voice_parse(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.native.voice_control_center import run_voice_command
        return {"ok": True, **run_voice_command(str(payload["text"]), record=False)}

    def _updates_check(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        from secondbrain.installer_update import InstallerUpdateRuntime
        return {"ok": True, **InstallerUpdateRuntime(self.project_root).update_check(str(payload.get("current_version") or "unknown"))}

    def _github_status(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        module = self.project_root / "secondbrain" / "connectors" / "github_sync.py"
        return {"ok": module.exists(), "connector": "github", "module": str(module), "mode": "existing_connector"}

    def _filesystem_list(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self._safe_path(str(payload.get("path") or "."))
        if not path.is_dir():
            raise ValueError(f"filesystem_not_directory:{path}")
        limit = max(0, min(1000, int(payload.get("limit", 100))))
        items = []
        for item in sorted(path.iterdir(), key=lambda entry: entry.name.lower())[:limit]:
            items.append({"name": item.name, "path": str(item), "type": "directory" if item.is_dir() else "file", "size": item.stat().st_size if item.is_file() else None})
        return {"ok": True, "path": str(path), "count": len(items), "items": items}

    def _filesystem_read(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self._safe_path(str(payload["path"]))
        if not path.is_file():
            raise ValueError(f"filesystem_not_file:{path}")
        max_chars = max(1, min(1_000_000, int(payload.get("max_chars", 100_000))))
        content = path.read_text(encoding="utf-8", errors="replace")[:max_chars]
        return {"ok": True, "path": str(path), "content": content, "truncated": path.stat().st_size > len(content.encode("utf-8"))}

    def _safe_path(self, value: str) -> Path:
        candidate = (self.project_root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
        if not candidate.is_relative_to(self.project_root):
            raise PermissionError("filesystem_path_outside_project")
        return candidate
