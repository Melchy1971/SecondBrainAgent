"""Incremental adapters from existing import and Planner v2 services to jobs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
from uuid import uuid4

from secondbrain.jobs.models import Job, JobPriority, JobType


def submit_import_job(repository: Any, *, workspace_id: str, payload_reference: str,
                      idempotency_key: str, priority: str = JobPriority.NORMAL.value) -> Job:
    return repository.create_job(Job(
        job_id=str(uuid4()), type=JobType.IMPORT.value, workspace_id=workspace_id,
        payload_reference=payload_reference, idempotency_key=idempotency_key,
        priority=priority, idempotent=True,
    ))


def submit_planner_job(repository: Any, *, workspace_id: str, payload_reference: str,
                       idempotency_key: str, approval_required: bool = False) -> Job:
    return repository.create_job(Job(
        job_id=str(uuid4()), type=JobType.AGENT_PLAN.value, workspace_id=workspace_id,
        payload_reference=payload_reference, idempotency_key=idempotency_key,
        priority=JobPriority.HIGH.value, idempotent=False,
        approval_required=approval_required,
    ))


def register_import_handler(registry: Any, resolver: Callable[[str], tuple[Any, str, Mapping[str, Any]]]) -> None:
    """Resolver returns the existing StreamingImportService, file path and safe options."""
    def handle(job: Job, context: Any) -> None:
        service, path, options = resolver(job.payload_reference)

        def progress(update: Any) -> None:
            context.checkpoint(
                {"session_id": update.session_id, "position": update.position},
                progress=float(update.percent) / 100.0,
            )
            context.heartbeat()

        session = service.import_file(path, workspace_id=job.workspace_id,
                                      progress=progress, **dict(options))
        context.checkpoint({"session_id": session.session_id, "position": session.position},
                           progress=1.0)

    registry.register(JobType.IMPORT.value, handle)


def register_planner_handler(
    registry: Any,
    resolver: Callable[[str], tuple[Any, Any, Mapping[str, Callable[[dict[str, Any]], Any]], Any | None]],
) -> None:
    """Resolver returns the existing Planner, PlanGraph, tools and approval authority."""
    def handle(job: Job, context: Any) -> None:
        planner, plan, tools, approval_authority = resolver(job.payload_reference)
        if plan.workspace_id != job.workspace_id:
            raise PermissionError("workspace_mismatch")
        result = planner.execute_plan(plan, tools=tools, approval_authority=approval_authority)
        context.checkpoint({"plan_id": plan.plan_id, "completed_nodes": list(plan.checkpoint)},
                           progress=len(plan.checkpoint) / max(1, len(plan.nodes)))
        if result["status"] != "completed":
            raise RuntimeError(f"planner_not_completed:{result['status']}")

    registry.register(JobType.AGENT_PLAN.value, handle)
