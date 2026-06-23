from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Mapping, Protocol, Sequence


class HealthColor(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    UNKNOWN = "unknown"


class WidgetDataSource(Protocol):
    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        ...


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_count(items: Any) -> int:
    if items is None:
        return 0
    if isinstance(items, Sequence) and not isinstance(items, (str, bytes, bytearray)):
        return len(items)
    return int(items) if isinstance(items, int) else 0


@dataclass(slots=True)
class RecentImportsProvider:
    fetch_imports: Callable[[str], Sequence[Mapping[str, Any]]] | None = None
    limit: int = 5

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        rows = list(self.fetch_imports(workspace_id) if self.fetch_imports else [])
        rows = sorted(rows, key=lambda item: str(item.get("created_at", "")), reverse=True)[: self.limit]
        return {
            "workspace": workspace_id,
            "count": len(rows),
            "items": [dict(item) for item in rows],
            "updated_at": _utc_now_iso(),
        }


@dataclass(slots=True)
class RunningJobsProvider:
    fetch_jobs: Callable[[str], Sequence[Mapping[str, Any]]] | None = None

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        rows = [dict(item) for item in (self.fetch_jobs(workspace_id) if self.fetch_jobs else [])]
        running = [item for item in rows if str(item.get("state", "")).lower() in {"queued", "running"}]
        failed = [item for item in rows if str(item.get("state", "")).lower() == "failed"]
        return {
            "workspace": workspace_id,
            "running": len(running),
            "failed": len(failed),
            "total": len(rows),
            "items": running,
            "status": HealthColor.GREEN.value if not failed else HealthColor.YELLOW.value,
        }


@dataclass(slots=True)
class ConnectorHealthProvider:
    fetch_connectors: Callable[[str], Sequence[Mapping[str, Any]]] | None = None

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        connectors = [dict(item) for item in (self.fetch_connectors(workspace_id) if self.fetch_connectors else [])]
        red = sum(1 for item in connectors if str(item.get("status", "")).lower() == "red")
        yellow = sum(1 for item in connectors if str(item.get("status", "")).lower() == "yellow")
        green = sum(1 for item in connectors if str(item.get("status", "")).lower() == "green")
        status = HealthColor.RED if red else HealthColor.YELLOW if yellow else HealthColor.GREEN if connectors else HealthColor.UNKNOWN
        return {
            "workspace": workspace_id,
            "status": status.value,
            "green": green,
            "yellow": yellow,
            "red": red,
            "connectors": connectors,
        }


@dataclass(slots=True)
class RagStatusProvider:
    fetch_status: Callable[[str], Mapping[str, Any]] | None = None

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        status = dict(self.fetch_status(workspace_id) if self.fetch_status else {})
        indexed = _safe_count(status.get("indexed_documents", 0))
        pending = _safe_count(status.get("pending_documents", 0))
        errors = _safe_count(status.get("errors", 0))
        color = HealthColor.RED if errors else HealthColor.YELLOW if pending else HealthColor.GREEN
        return {
            "workspace": workspace_id,
            "status": status.get("status", color.value),
            "indexed_documents": indexed,
            "pending_documents": pending,
            "errors": errors,
            "embedding_provider": status.get("embedding_provider", "unknown"),
        }


@dataclass(slots=True)
class SystemHealthProvider:
    fetch_checks: Callable[[str], Mapping[str, str]] | None = None

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        checks = dict(self.fetch_checks(workspace_id) if self.fetch_checks else {})
        values = {key: str(value).lower() for key, value in checks.items()}
        red = sum(1 for value in values.values() if value == "red")
        yellow = sum(1 for value in values.values() if value == "yellow")
        status = HealthColor.RED if red else HealthColor.YELLOW if yellow else HealthColor.GREEN if values else HealthColor.UNKNOWN
        return {"workspace": workspace_id, "status": status.value, "checks": values, "red": red, "yellow": yellow}


@dataclass(slots=True)
class StorageUsageProvider:
    fetch_usage: Callable[[str], Mapping[str, Any]] | None = None
    warning_ratio: float = 0.80
    critical_ratio: float = 0.95

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        usage = dict(self.fetch_usage(workspace_id) if self.fetch_usage else {})
        used = int(usage.get("used_bytes", 0) or 0)
        total = int(usage.get("total_bytes", 0) or 0)
        ratio = (used / total) if total > 0 else 0.0
        status = HealthColor.RED if ratio >= self.critical_ratio else HealthColor.YELLOW if ratio >= self.warning_ratio else HealthColor.GREEN
        return {"workspace": workspace_id, "status": status.value, "used_bytes": used, "total_bytes": total, "usage_ratio": ratio}


@dataclass(slots=True)
class RecentErrorsProvider:
    fetch_errors: Callable[[str], Sequence[Mapping[str, Any]]] | None = None
    limit: int = 10

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        errors = [dict(item) for item in (self.fetch_errors(workspace_id) if self.fetch_errors else [])]
        errors = sorted(errors, key=lambda item: str(item.get("created_at", "")), reverse=True)[: self.limit]
        return {"workspace": workspace_id, "count": len(errors), "items": errors, "status": HealthColor.GREEN.value if not errors else HealthColor.YELLOW.value}


@dataclass(slots=True)
class WorkspaceSummaryProvider:
    fetch_summary: Callable[[str], Mapping[str, Any]] | None = None
    defaults: Mapping[str, Any] = field(default_factory=dict)

    def __call__(self, workspace_id: str) -> Mapping[str, Any]:
        summary = dict(self.defaults)
        if self.fetch_summary:
            summary.update(dict(self.fetch_summary(workspace_id)))
        summary.setdefault("documents", 0)
        summary.setdefault("connectors", 0)
        summary.setdefault("jobs", 0)
        summary["workspace"] = workspace_id
        return summary


def default_widget_providers(
    *,
    imports: Callable[[str], Sequence[Mapping[str, Any]]] | None = None,
    jobs: Callable[[str], Sequence[Mapping[str, Any]]] | None = None,
    connectors: Callable[[str], Sequence[Mapping[str, Any]]] | None = None,
    rag: Callable[[str], Mapping[str, Any]] | None = None,
    system: Callable[[str], Mapping[str, str]] | None = None,
    storage: Callable[[str], Mapping[str, Any]] | None = None,
    errors: Callable[[str], Sequence[Mapping[str, Any]]] | None = None,
    workspace: Callable[[str], Mapping[str, Any]] | None = None,
) -> dict[str, WidgetDataSource]:
    return {
        "recent_imports": RecentImportsProvider(imports),
        "running_jobs": RunningJobsProvider(jobs),
        "connector_health": ConnectorHealthProvider(connectors),
        "rag_status": RagStatusProvider(rag),
        "system_health": SystemHealthProvider(system),
        "storage_usage": StorageUsageProvider(storage),
        "recent_errors": RecentErrorsProvider(errors),
        "workspace_summary": WorkspaceSummaryProvider(workspace),
    }
