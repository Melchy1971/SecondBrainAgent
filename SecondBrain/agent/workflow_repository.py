"""v30.3 - workflow repository.

Repository uses plain SQL and JSON payloads.
"""

from __future__ import annotations

import json
from secondbrain.agent.workflow_models import WorkflowPlan, WorkflowStep


class WorkflowRepository:
    def __init__(self, database):
        self.database = database

    def save_plan(self, plan: WorkflowPlan) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("""
                INSERT INTO workflows (id, objective, status)
                VALUES (:id, :objective, 'PENDING')
                ON CONFLICT (id) DO UPDATE SET objective = EXCLUDED.objective
                """),
                {"id": plan.id, "objective": plan.objective},
            )
            for step in plan.steps:
                session.execute(
                    text("""
                    INSERT INTO workflow_steps (
                        id, workflow_id, name, tool_name, input, dependencies,
                        timeout_seconds, max_retries, requires_approval
                    )
                    VALUES (
                        :id, :workflow_id, :name, :tool_name, CAST(:input AS jsonb),
                        CAST(:dependencies AS jsonb), :timeout_seconds, :max_retries, :requires_approval
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        tool_name = EXCLUDED.tool_name,
                        input = EXCLUDED.input,
                        dependencies = EXCLUDED.dependencies,
                        timeout_seconds = EXCLUDED.timeout_seconds,
                        max_retries = EXCLUDED.max_retries,
                        requires_approval = EXCLUDED.requires_approval
                    """),
                    {
                        "id": step.id,
                        "workflow_id": plan.id,
                        "name": step.name,
                        "tool_name": step.tool_name,
                        "input": json.dumps(step.input),
                        "dependencies": json.dumps(step.dependencies),
                        "timeout_seconds": step.timeout_seconds,
                        "max_retries": step.max_retries,
                        "requires_approval": step.requires_approval,
                    },
                )

    def update_workflow_status(self, workflow_id: str, status: str) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("UPDATE workflows SET status = :status, updated_at = now() WHERE id = :id"),
                {"id": workflow_id, "status": status},
            )

    def update_step_status(self, step_id: str, status: str, output: dict | None = None, attempt: int | None = None) -> None:
        from sqlalchemy import text
        params = {"id": step_id, "status": status, "output": json.dumps(output or {})}
        attempt_sql = ""
        if attempt is not None:
            attempt_sql = ", attempt = :attempt"
            params["attempt"] = attempt
        with self.database.session() as session:
            session.execute(
                text(f"""
                UPDATE workflow_steps
                SET status = :status, output = CAST(:output AS jsonb), updated_at = now()
                {attempt_sql}
                WHERE id = :id
                """),
                params,
            )

    def record_event(self, event_id: str, workflow_id: str, event_type: str, payload: dict, step_id: str | None = None) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("""
                INSERT INTO workflow_events (id, workflow_id, step_id, event_type, payload)
                VALUES (:id, :workflow_id, :step_id, :event_type, CAST(:payload AS jsonb))
                """),
                {
                    "id": event_id,
                    "workflow_id": workflow_id,
                    "step_id": step_id,
                    "event_type": event_type,
                    "payload": json.dumps(payload),
                },
            )
