from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .task_planner import TaskPlan, TaskStep, TaskStepState
from .tool_registry import ToolRegistry


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentPlanStore:
    """Atomic JSON persistence for resumable agent plans."""

    def __init__(self, project_root: str | Path, *, registry: ToolRegistry | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.root = self.project_root / "runtime" / "agent" / "plans"
        self.registry = registry
        self._runtime_payloads: dict[str, dict[str, dict[str, Any]]] = {}

    def save(self, plan: TaskPlan) -> TaskPlan:
        return self._write(plan)

    def load(self, plan_id: str) -> TaskPlan:
        record = self._read_record(plan_id)
        runtime_payloads = self._runtime_payloads.get(plan_id, {})
        steps = []
        for row in record.get("steps", []):
            step_id = str(row["step_id"])
            payload = runtime_payloads.get(step_id, row.get("payload") or {})
            steps.append(
                TaskStep(
                    step_id=step_id,
                    name=str(row.get("name") or ""),
                    tool_name=str(row["tool_name"]) if row.get("tool_name") else None,
                    payload=dict(payload),
                    state=TaskStepState(str(row.get("state") or TaskStepState.PENDING.value)),
                    result=row.get("result"),
                    error=str(row["error"]) if row.get("error") is not None else None,
                )
            )
        metadata = dict(record.get("metadata") or {})
        metadata["status"] = str(record.get("status") or metadata.get("status") or "pending")
        metadata["approval_ids"] = list(record.get("approval_ids") or metadata.get("approval_ids") or [])
        return TaskPlan(
            plan_id=str(record["plan_id"]),
            intent=str(record.get("intent") or ""),
            metadata=metadata,
            steps=steps,
        )

    def update(self, plan: TaskPlan) -> TaskPlan:
        return self._write(plan)

    def list_waiting(self) -> list[TaskPlan]:
        if not self.root.exists():
            return []
        waiting = []
        for path in sorted(self.root.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, TypeError):
                continue
            if isinstance(record, dict) and record.get("status") == "waiting_for_approval":
                waiting.append(self.load(str(record.get("plan_id") or path.stem)))
        return waiting

    def mark_completed(self, plan_id: str) -> TaskPlan:
        plan = self.load(plan_id)
        plan.metadata["status"] = "completed"
        return self.update(plan)

    def claim_step(self, plan_id: str, step_id: str) -> bool:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._claim_path(plan_id, step_id)
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(_utc_now())
        except FileExistsError:
            return False
        return True

    def release_step(self, plan_id: str, step_id: str) -> None:
        self._claim_path(plan_id, step_id).unlink(missing_ok=True)

    def _write(self, plan: TaskPlan) -> TaskPlan:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path(plan.plan_id)
        created_at = _utc_now()
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
                created_at = str(existing.get("created_at") or created_at)
            except (OSError, json.JSONDecodeError, TypeError, AttributeError):
                pass

        runtime_payloads = self._runtime_payloads.setdefault(plan.plan_id, {})
        step_rows = []
        approval_ids = set(str(item) for item in plan.metadata.get("approval_ids", []) if item)
        for step in plan.steps:
            runtime_payloads[step.step_id] = dict(step.payload)
            if isinstance(step.result, Mapping) and step.result.get("approval_id"):
                approval_ids.add(str(step.result["approval_id"]))
            step_rows.append(
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "tool_name": step.tool_name,
                    "payload": self._sanitize_payload(step),
                    "state": step.state.value,
                    "result": self._json_safe(step.result),
                    "error": step.error,
                }
            )

        status = self._plan_status(plan)
        plan.metadata["status"] = status
        plan.metadata["approval_ids"] = sorted(approval_ids)
        record = {
            "plan_id": plan.plan_id,
            "intent": plan.intent,
            "metadata": self._json_safe(plan.metadata),
            "status": status,
            "steps": step_rows,
            "approval_ids": sorted(approval_ids),
            "created_at": created_at,
            "updated_at": _utc_now(),
        }
        temporary = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return plan

    def _read_record(self, plan_id: str) -> dict[str, Any]:
        path = self._path(plan_id)
        if not path.exists():
            raise KeyError(f"agent_plan_not_found:{plan_id}")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"agent_plan_corrupt:{plan_id}") from exc
        if not isinstance(record, dict) or record.get("plan_id") != plan_id:
            raise RuntimeError(f"agent_plan_invalid:{plan_id}")
        return record

    def _path(self, plan_id: str) -> Path:
        self._validate_id(plan_id, "plan")
        return self.root / f"{plan_id}.json"

    def _claim_path(self, plan_id: str, step_id: str) -> Path:
        self._validate_id(plan_id, "plan")
        self._validate_id(step_id, "step")
        return self.root / f"{plan_id}.{step_id}.claim"

    @staticmethod
    def _validate_id(value: str, kind: str) -> None:
        if not value or Path(value).name != value or any(char in value for char in ("/", "\\")):
            raise ValueError(f"invalid_{kind}_id:{value}")

    def _sanitize_payload(self, step: TaskStep) -> dict[str, Any]:
        payload = dict(step.payload)
        if self.registry is not None and step.tool_name:
            try:
                payload = self.registry.get(step.tool_name).input_schema.sanitize(payload)
            except Exception:  # noqa: BLE001 - persistence must still redact common secret fields
                pass
        return self._redact_common(payload)

    @classmethod
    def _redact_common(cls, value: Any, *, key: str = "") -> Any:
        sensitive_tokens = ("password", "secret", "token", "api_key", "authorization", "cookie")
        if key and any(token in key.lower() for token in sensitive_tokens):
            return "***"
        if isinstance(value, Mapping):
            return {str(item_key): cls._redact_common(item, key=str(item_key)) for item_key, item in value.items()}
        if isinstance(value, list):
            return [cls._redact_common(item) for item in value]
        if isinstance(value, tuple):
            return [cls._redact_common(item) for item in value]
        return cls._json_safe(value)

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Mapping):
            return {str(key): AgentPlanStore._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [AgentPlanStore._json_safe(item) for item in value]
        return repr(value)

    @staticmethod
    def _plan_status(plan: TaskPlan) -> str:
        explicit = str(plan.metadata.get("status") or "")
        states = {step.state for step in plan.steps}
        if TaskStepState.REJECTED in states or explicit == "rejected":
            return "rejected"
        if TaskStepState.FAILED in states or explicit == "failed":
            return "failed"
        if states and states <= {TaskStepState.COMPLETED, TaskStepState.SKIPPED}:
            return "completed"
        if states & {TaskStepState.WAITING_FOR_APPROVAL, TaskStepState.APPROVED, TaskStepState.DEFERRED}:
            return "waiting_for_approval"
        return explicit or "pending"
