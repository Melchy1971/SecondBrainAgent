"""v30.63 Background Agents - built-in agent-type handlers.

Each handler is ``handler(ctx) -> dict``. Returning normally = the check ran
(its findings are in the dict, including problems it noticed). Raising = the
check itself could not run, which the supervisor treats as a run failure and
feeds to the failure policy.

Handlers deliberately read only lightweight local state (job queue snapshot,
notification status, workflow store, provided config) so a monitor never drags
in a heavy DB/RAG import just to poll. Real monitors can be wired by overriding
the handler for an agent or by passing richer collaborators on the context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .models import AgentType


@dataclass
class AgentContext:
    project_root: Path
    agent: Any
    jobs: Any | None = None
    notifications: Any | None = None
    memory_sink: Callable[[dict], None] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def config(self) -> dict[str, Any]:
        return getattr(self.agent, "config", {}) or {}


def _maybe_force_error(ctx: AgentContext) -> None:
    if ctx.config.get("force_error"):
        raise RuntimeError(str(ctx.config.get("force_error_message", "forced_failure")))


def _job_snapshot(ctx: AgentContext) -> dict[str, Any]:
    if ctx.jobs is None:
        return {}
    try:
        return ctx.jobs.snapshot()
    except Exception:
        return {}


def import_monitor(ctx: AgentContext) -> dict[str, Any]:
    _maybe_force_error(ctx)
    snap = _job_snapshot(ctx)
    jobs = snap.get("jobs", [])
    imports = [j for j in jobs if j.get("kind") == "import"]
    blocked = [j for j in imports if j.get("status") in {"blocked", "failed", "dead_letter"}]
    return {
        "ok": True,
        "checked": "import_jobs",
        "import_jobs": len(imports),
        "blocked_or_failed": len(blocked),
        "healthy": len(blocked) == 0,
    }


def knowledge_quality_monitor(ctx: AgentContext) -> dict[str, Any]:
    _maybe_force_error(ctx)
    source = ctx.config.get("quality_report")
    findings = {"ok": True, "checked": "knowledge_quality", "healthy": True}
    if source:
        path = Path(source)
        if not path.is_absolute():
            path = ctx.project_root / source
        if path.exists():
            import json

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                score = data.get("knowledge_quality_score", data.get("score"))
                threshold = int(ctx.config.get("min_score", 60))
                findings.update({"score": score, "threshold": threshold,
                                 "healthy": score is None or score >= threshold})
            except Exception:
                findings.update({"note": "quality_report_unreadable", "healthy": True})
        else:
            findings.update({"note": "no_quality_data"})
    else:
        findings.update({"note": "no_quality_source_configured"})
    return findings


def memory_consolidation(ctx: AgentContext) -> dict[str, Any]:
    _maybe_force_error(ctx)
    fact = {
        "kind": "memory_consolidation",
        "agent_id": getattr(ctx.agent, "id", ""),
        "note": "consolidation_marker",
    }
    delivered = False
    if ctx.memory_sink is not None:
        ctx.memory_sink(fact)
        delivered = True
    return {"ok": True, "checked": "memory", "consolidated": True, "memory_delivered": delivered}


def rag_index_monitor(ctx: AgentContext) -> dict[str, Any]:
    _maybe_force_error(ctx)
    status_file = ctx.config.get("rag_status_file")
    result = {"ok": True, "checked": "rag_index", "healthy": True}
    if status_file:
        path = Path(status_file)
        if not path.is_absolute():
            path = ctx.project_root / status_file
        result["healthy"] = path.exists()
        result["note"] = "status_present" if path.exists() else "status_missing"
    else:
        result["note"] = "no_rag_status_configured"
    return result


def notification_agent(ctx: AgentContext) -> dict[str, Any]:
    _maybe_force_error(ctx)
    title = ctx.config.get("title", "Background-Agent Digest")
    message = ctx.config.get("message", "Periodische Zusammenfassung der Hintergrund-Agenten.")
    sent = False
    if ctx.notifications is not None:
        ctx.notifications.notify(title, message, level="info", category="agent",
                                 source="background_agent",
                                 metadata={"agent_id": getattr(ctx.agent, "id", "")})
        sent = True
    return {"ok": True, "checked": "notification", "notified": sent}


def system_health_agent(ctx: AgentContext) -> dict[str, Any]:
    _maybe_force_error(ctx)
    snap = _job_snapshot(ctx)
    queue_health = snap.get("health", "unknown")
    degraded = queue_health not in {"ok", "busy", "unknown"}
    if degraded and ctx.notifications is not None:
        ctx.notifications.notify("System Health degradiert",
                                 f"Job-Queue-Status: {queue_health}", level="warning",
                                 category="agent", source="background_agent")
    return {
        "ok": True,
        "checked": "system_health",
        "queue_health": queue_health,
        "queue_total": snap.get("total", 0),
        "healthy": not degraded,
    }


HANDLERS: dict[AgentType, Callable[[AgentContext], dict[str, Any]]] = {
    AgentType.IMPORT_MONITOR: import_monitor,
    AgentType.KNOWLEDGE_QUALITY_MONITOR: knowledge_quality_monitor,
    AgentType.MEMORY_CONSOLIDATION: memory_consolidation,
    AgentType.RAG_INDEX_MONITOR: rag_index_monitor,
    AgentType.NOTIFICATION_AGENT: notification_agent,
    AgentType.SYSTEM_HEALTH_AGENT: system_health_agent,
}


def get_handler(agent_type: AgentType) -> Callable[[AgentContext], dict[str, Any]]:
    handler = HANDLERS.get(agent_type)
    if handler is None:
        raise KeyError(f"no_handler_for_agent_type:{agent_type}")
    return handler
