"""Canonical agent planning for executable, approval-aware plans."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from secondbrain.agent.agent_core import AgentCore
from secondbrain.agent.task_graph import TaskGraph, TaskNode
from secondbrain.agent.tool_registry import ToolDefinition
from secondbrain.chat.service import ChatService
from secondbrain.native.approval import NativeApprovalQueue
from secondbrain.native.command_center import CommandCenter
from secondbrain.native.job_queue_center.service import JobQueueService
from secondbrain.native.memory_explorer import MemoryExplorer


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PlanStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


RISK_LEVELS = ("low", "medium", "high", "critical")


@dataclass(slots=True)
class AgentStep:
    id: str
    title: str
    intent: str
    tool: str
    inputs: dict[str, Any]
    expected_output: str
    risk_level: str = "low"
    requires_approval: bool = False
    status: PlanStatus = PlanStatus.PENDING
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentStep":
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            intent=str(payload["intent"]),
            tool=str(payload["tool"]),
            inputs=dict(payload.get("inputs") or {}),
            expected_output=str(payload["expected_output"]),
            risk_level=str(payload.get("risk_level") or "low"),
            requires_approval=bool(payload.get("requires_approval", False)),
            status=PlanStatus(payload.get("status", PlanStatus.PENDING.value)),
            evidence=[dict(item) for item in payload.get("evidence") or []],
        )


@dataclass(slots=True)
class AgentPlan:
    id: str
    goal: str
    steps: list[AgentStep]
    status: PlanStatus = PlanStatus.DRAFT
    workspace_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "workspace_id": self.workspace_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentPlan":
        return cls(
            id=str(payload["id"]),
            goal=str(payload["goal"]),
            steps=[AgentStep.from_dict(item) for item in payload.get("steps") or []],
            status=PlanStatus(payload.get("status", PlanStatus.DRAFT.value)),
            workspace_id=payload.get("workspace_id"),
            created_at=str(payload.get("created_at") or _utc_now()),
            updated_at=str(payload.get("updated_at") or _utc_now()),
            metadata=dict(payload.get("metadata") or {}),
        )


class PlanRiskAnalyzer:
    """Classify steps with the existing command metadata plus explicit action markers."""

    CRITICAL_MARKERS = {"delete", "remove", "loesche", "lösche", "shell", "execute", "system change"}
    HIGH_MARKERS = {"write", "update", "repair", "import", "export", "send", "create", "ändern", "aendern"}
    MEDIUM_MARKERS = {"external", "download", "upload", "sync", "publish"}

    def analyze(self, step: AgentStep, *, command_risk: str | None = None, command_requires_approval: bool = False) -> AgentStep:
        # Natural-language questions must not become risky merely because they
        # mention a destructive operation. Risk follows the selected capability.
        capability = " ".join((step.intent, step.tool)).lower()
        if step.tool in {"chat.ask", "memory.search"}:
            level = "low"
        elif any(marker in capability for marker in self.CRITICAL_MARKERS):
            level = "critical"
        elif command_risk in {"write", "execute", "system"} or any(marker in capability for marker in self.HIGH_MARKERS):
            level = "high"
        elif command_risk not in {None, "read"} or any(marker in capability for marker in self.MEDIUM_MARKERS):
            level = "medium"
        else:
            level = "low"
        step.risk_level = level
        step.requires_approval = bool(command_requires_approval or level in {"high", "critical"})
        return step

    def analyze_plan(self, plan: AgentPlan) -> AgentPlan:
        for step in plan.steps:
            self.analyze(step)
        plan.metadata["maximum_risk"] = max(
            (step.risk_level for step in plan.steps),
            key=RISK_LEVELS.index,
            default="low",
        )
        plan.touch()
        return plan


class PlanValidator:
    def validate(self, plan: AgentPlan) -> list[str]:
        errors: list[str] = []
        if not plan.id.strip():
            errors.append("plan_id_required")
        if not plan.goal.strip():
            errors.append("plan_goal_required")
        if not plan.steps:
            errors.append("plan_steps_required")
        ids: set[str] = set()
        for index, step in enumerate(plan.steps):
            prefix = f"step[{index}]"
            if not step.id.strip():
                errors.append(f"{prefix}.id_required")
            elif step.id in ids:
                errors.append(f"{prefix}.duplicate_id:{step.id}")
            ids.add(step.id)
            if not step.title.strip():
                errors.append(f"{prefix}.title_required")
            if not step.intent.strip():
                errors.append(f"{prefix}.intent_required")
            if not step.tool.strip():
                errors.append(f"{prefix}.tool_required")
            if not isinstance(step.inputs, dict):
                errors.append(f"{prefix}.inputs_must_be_object")
            if not step.expected_output.strip():
                errors.append(f"{prefix}.expected_output_required")
            if step.risk_level not in RISK_LEVELS:
                errors.append(f"{prefix}.invalid_risk_level:{step.risk_level}")
            if step.risk_level in {"high", "critical"} and not step.requires_approval:
                errors.append(f"{prefix}.approval_required_for_risk")
            if not isinstance(step.evidence, list):
                errors.append(f"{prefix}.evidence_must_be_list")
        return errors

    def require_valid(self, plan: AgentPlan) -> AgentPlan:
        errors = self.validate(plan)
        if errors:
            raise ValueError("invalid_agent_plan:" + ",".join(errors))
        return plan


class PlanPersistence:
    """Atomic collection persistence in the existing runtime/agent plan file."""

    _locks: dict[Path, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, project_root: str | Path = ".", path: str | Path | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.path = Path(path).resolve() if path else self.project_root / "runtime" / "agent" / "plans.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._locks_guard:
            self._lock = self._locks.setdefault(self.path, threading.RLock())

    def save(self, plan: AgentPlan) -> AgentPlan:
        with self._lock:
            plans = self._read()
            plan.touch()
            plans[plan.id] = plan.to_dict()
            self._write(plans)
        return plan

    def load(self, plan_id: str) -> AgentPlan:
        with self._lock:
            payload = self._read().get(plan_id)
        if payload is None:
            raise KeyError(f"agent_plan_not_found:{plan_id}")
        return AgentPlan.from_dict(payload)

    def list(self) -> list[AgentPlan]:
        with self._lock:
            plans = [AgentPlan.from_dict(item) for item in self._read().values()]
        return sorted(plans, key=lambda plan: plan.updated_at, reverse=True)

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        raw = self.path.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid_plan_store:{self.path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"invalid_plan_store:{self.path}")
        # Compatibility with the former single-plan PlanRepository payload.
        if "id" in payload and "goal" in payload:
            payload = {str(payload["id"]): payload}
        return {str(key): dict(value) for key, value in payload.items() if isinstance(value, dict)}

    def _write(self, plans: dict[str, dict[str, Any]]) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(plans, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)


class PlanBuilder:
    """Decompose goals using existing AgentCore routes and Command Center tools."""

    _SPLIT = re.compile(r"(?:\r?\n|;|\s+(?:then|danach|anschließend|anschliessend)\s+)", re.IGNORECASE)

    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        agent_core: AgentCore | None = None,
        chat_service: ChatService | None = None,
        command_center: CommandCenter | None = None,
        memory: MemoryExplorer | None = None,
        risk_analyzer: PlanRiskAnalyzer | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.agent_core = agent_core or AgentCore()
        self.chat_service = chat_service or ChatService(self.project_root)
        self.command_center = command_center or CommandCenter(self.project_root)
        self.memory = memory or MemoryExplorer(self.project_root)
        self.risk_analyzer = risk_analyzer or PlanRiskAnalyzer()
        self._register_existing_tools()

    def build(self, goal: str, *, workspace_id: str | None = None) -> AgentPlan:
        normalized = (goal or "").strip()
        if not normalized:
            raise ValueError("plan_goal_required")
        clauses = [self._clean_clause(item) for item in self._SPLIT.split(normalized)]
        clauses = [item for item in clauses if item]
        memory_evidence = self._memory_evidence(normalized, workspace_id)
        steps = [self._build_step(clause, memory_evidence if index == 0 else []) for index, clause in enumerate(clauses)]
        plan = AgentPlan(
            id=f"plan_{uuid4().hex[:12]}",
            goal=normalized,
            steps=steps,
            workspace_id=workspace_id,
            metadata={"planner": "agent_core_command_center", "step_count": len(steps)},
        )
        plan.metadata["maximum_risk"] = max(
            (step.risk_level for step in steps), key=RISK_LEVELS.index, default="low"
        )
        return plan

    @staticmethod
    def _clean_clause(value: str) -> str:
        return re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", value).strip()

    def _build_step(self, title: str, memory_evidence: list[dict[str, Any]]) -> AgentStep:
        command = self.command_center.resolve(title)
        route = self.agent_core.router.route(title)
        if command is not None:
            intent = f"command.{command.category.lower()}"
            tool = "command.center"
            inputs = {"command": command.id}
            expected = f"Strukturiertes Ergebnis für {command.id}"
            evidence = [{"type": "command", "source": "command_center", "id": command.id}]
            step = AgentStep(f"step_{uuid4().hex[:12]}", title, intent, tool, inputs, expected, evidence=evidence + memory_evidence)
            return self.risk_analyzer.analyze(
                step,
                command_risk=command.risk,
                command_requires_approval=command.requires_confirmation,
            )
        if route.tool_name:
            inputs = dict(route.parameters)
            inputs.setdefault("text", title)
            step = AgentStep(
                f"step_{uuid4().hex[:12]}", title, route.intent, route.tool_name, inputs,
                f"Ergebnis des Tools {route.tool_name}",
                evidence=[{"type": "route", "source": "agent_core", "confidence": route.confidence}] + memory_evidence,
            )
            return self.risk_analyzer.analyze(step)
        step = AgentStep(
            f"step_{uuid4().hex[:12]}", title, route.intent or "chat", "chat.ask", {"text": title},
            "Begründete Chat-Antwort mit vorhandenen RAG-/Memory-Quellen",
            evidence=[{"type": "route", "source": "agent_core", "confidence": route.confidence}] + memory_evidence,
        )
        return self.risk_analyzer.analyze(step)

    def _register_existing_tools(self) -> None:
        registrations = (
            ToolDefinition("chat.ask", "Answer through the existing ChatService", lambda payload: self.chat_service.ask(str(payload.get("text") or ""))),
            ToolDefinition("command.center", "Run an existing Command Center command", lambda payload: self.command_center.run(str(payload.get("command") or ""), confirmed=bool(payload.get("confirmed", False)))),
            ToolDefinition("memory.search", "Search existing memory", lambda payload: self.memory.search(str(payload.get("query") or ""))),
        )
        for definition in registrations:
            if not self.agent_core.registry.has(definition.name):
                self.agent_core.registry.register(definition)

    def _memory_evidence(self, goal: str, workspace_id: str | None) -> list[dict[str, Any]]:
        result = self.memory.search(goal, limit=5)
        evidence = []
        for item in result.get("memories", []):
            metadata = item.get("metadata") or {}
            item_workspace = metadata.get("workspace_id") or metadata.get("workspace")
            if workspace_id and item_workspace and str(item_workspace) != workspace_id:
                continue
            evidence.append({
                "type": "memory",
                "source": str(item.get("source") or "memory"),
                "id": str(item.get("memory_id") or ""),
                "summary": str(item.get("content") or "")[:240],
            })
        return evidence


class AgentPlanService:
    """Application service joining planner, persistence, queue and approvals."""

    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        builder: PlanBuilder | None = None,
        validator: PlanValidator | None = None,
        persistence: PlanPersistence | None = None,
        queue: JobQueueService | None = None,
        approvals: NativeApprovalQueue | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.builder = builder or PlanBuilder(self.project_root)
        self.validator = validator or PlanValidator()
        self.persistence = persistence or PlanPersistence(self.project_root)
        self.queue = queue or JobQueueService(self.project_root)
        self.approvals = approvals or NativeApprovalQueue(self.project_root)

    def create(self, goal: str, *, workspace_id: str | None = None) -> AgentPlan:
        plan = self.builder.build(goal, workspace_id=workspace_id)
        self.validator.require_valid(plan)
        plan.status = PlanStatus.VALIDATED
        return self.persistence.save(plan)

    def load(self, plan_id: str) -> AgentPlan:
        return self.persistence.load(plan_id)

    def list(self) -> list[AgentPlan]:
        return self.persistence.list()

    def cancel(self, plan_id: str) -> AgentPlan:
        plan = self.load(plan_id)
        if plan.status == PlanStatus.COMPLETED:
            raise ValueError("completed_plan_cannot_be_cancelled")
        for step in plan.steps:
            if step.status == PlanStatus.COMPLETED:
                continue
            job_id = self._evidence_value(step.evidence, "queue", "job_id")
            if job_id:
                job = self.queue.get_job(job_id)
                if job and job.status not in {"success", "failed", "dead_letter", "cancelled"}:
                    self.queue.cancel(job_id)
            step.status = PlanStatus.CANCELLED
        plan.status = PlanStatus.CANCELLED
        return self.persistence.save(plan)

    def resume(self, plan_id: str) -> AgentPlan:
        plan = self.load(plan_id)
        if plan.status == PlanStatus.COMPLETED:
            raise ValueError("completed_plan_cannot_be_resumed")
        waiting = False
        queued = False
        running = False
        for step in plan.steps:
            if step.status == PlanStatus.COMPLETED:
                continue
            if step.status in {PlanStatus.CANCELLED, PlanStatus.FAILED, PlanStatus.PAUSED}:
                step.status = PlanStatus.PENDING
            approved = not step.requires_approval
            approval_id = self._evidence_value(step.evidence, "approval", "approval_id")
            approval = self.approvals.get(approval_id) if approval_id else None
            if step.requires_approval:
                if approval is None:
                    approval = self.approvals.create(
                        command=step.tool,
                        intent=step.intent,
                        text=step.title,
                        target=f"{plan.id}:{step.id}",
                    )
                    step.evidence.append({"type": "approval", "approval_id": approval["approval_id"]})
                approved = approval.get("status") == "approved"
                if approval.get("status") == "rejected":
                    step.status = PlanStatus.FAILED
                    plan.status = PlanStatus.FAILED
                    continue
            job_id = self._evidence_value(step.evidence, "queue", "job_id")
            job = self.queue.get_job(job_id) if job_id else None
            if job and job.status == "success":
                step.status = PlanStatus.COMPLETED
                continue
            if job is None or job.status in {"failed", "dead_letter", "cancelled"}:
                job = self.queue.add_job(
                    "agent",
                    step.title,
                    approval_required=step.requires_approval and not approved,
                    payload={
                        "plan_id": plan.id,
                        "step_id": step.id,
                        "tool": step.tool,
                        "inputs": step.inputs,
                        "workspace_id": plan.workspace_id,
                    },
                )
                step.evidence.append({"type": "queue", "job_id": job.id})
            elif approved and job.status == "blocked":
                job = self.queue.approve(job.id)
            if approved:
                if job.status == "running":
                    step.status = PlanStatus.RUNNING
                    running = True
                else:
                    step.status = PlanStatus.QUEUED
                    queued = True
            else:
                step.status = PlanStatus.WAITING_APPROVAL
                waiting = True
        if plan.status != PlanStatus.FAILED:
            plan.status = (
                PlanStatus.WAITING_APPROVAL if waiting else
                PlanStatus.RUNNING if running else
                PlanStatus.QUEUED if queued else
                PlanStatus.COMPLETED
            )
        return self.persistence.save(plan)

    @staticmethod
    def _evidence_value(evidence: Iterable[dict[str, Any]], kind: str, key: str) -> str | None:
        return next((str(item[key]) for item in reversed(list(evidence)) if item.get("type") == kind and item.get(key)), None)


class Planner:
    """Compatibility facade for the original v21 TaskGraph API."""

    def create_plan(self, objective: str) -> TaskGraph:
        graph = TaskGraph()
        graph.add(TaskNode("objective", objective))
        return graph
