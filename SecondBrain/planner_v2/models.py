"""Data model for the graph-based planner (v2).

A plan is a directed acyclic graph of :class:`PlanNode` objects. Each node
declares the tool it needs, its dependencies, preconditions, risk, whether it
requires approval, and cost/duration estimates plus retry and rollback
policies. The model carries no execution logic - it is the contract the planner
validates, simulates and executes against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "RiskLevel", "NodeStatus", "PlanStatus", "RetryPolicy", "RollbackPolicy",
    "Budget", "PlanEdge", "PlanNode", "PlanGraph",
]


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NodeStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    INVALID = "invalid"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass
class RetryPolicy:
    max_attempts: int = 1
    backoff_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"max_attempts": self.max_attempts, "backoff_seconds": self.backoff_seconds}


@dataclass
class RollbackPolicy:
    supported: bool = False
    tool: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"supported": self.supported, "tool": self.tool}


@dataclass
class Budget:
    max_cost: float = float("inf")
    max_duration: float = float("inf")

    def to_dict(self) -> dict[str, Any]:
        return {"max_cost": self.max_cost, "max_duration": self.max_duration}


@dataclass
class PlanNode:
    node_id: str
    objective: str
    tool: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    expected_output: str = ""
    risk: str = RiskLevel.LOW.value
    approval_required: bool = False
    estimated_cost: float = 0.0
    estimated_duration: float = 0.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    rollback_policy: RollbackPolicy = field(default_factory=RollbackPolicy)
    alt_tools: list[str] = field(default_factory=list)
    idempotent: bool = True
    status: str = NodeStatus.PENDING.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id, "objective": self.objective, "tool": self.tool,
            "input": dict(self.input), "dependencies": list(self.dependencies),
            "preconditions": list(self.preconditions), "expected_output": self.expected_output,
            "risk": self.risk, "approval_required": self.approval_required,
            "estimated_cost": self.estimated_cost, "estimated_duration": self.estimated_duration,
            "retry_policy": self.retry_policy.to_dict(), "rollback_policy": self.rollback_policy.to_dict(),
            "alt_tools": list(self.alt_tools), "status": self.status,
            "idempotent": self.idempotent,
        }


@dataclass
class PlanEdge:
    source_node_id: str
    target_node_id: str
    condition: str = "success"
    dependency_type: str = "finish_to_start"


@dataclass
class PlanGraph:
    plan_id: str
    goal: str
    workspace_id: str
    nodes: list[PlanNode] = field(default_factory=list)
    edges: list[PlanEdge] = field(default_factory=list)
    intent: str = ""
    status: str = PlanStatus.DRAFT.value
    budget: Budget = field(default_factory=Budget)
    created_at: str = ""
    updated_at: str = ""
    checkpoint: list[str] = field(default_factory=list)   # completed node ids
    audit: list[dict[str, Any]] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    version: int = 1

    @property
    def dependencies(self) -> dict[str, list[str]]:
        return {n.node_id: list(n.dependencies) for n in self.nodes}

    def node(self, node_id: str) -> PlanNode | None:
        return next((n for n in self.nodes if n.node_id == node_id), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id, "goal": self.goal, "workspace_id": self.workspace_id,
            "nodes": [n.to_dict() for n in self.nodes], "status": self.status,
            "budget": self.budget.to_dict(), "created_at": self.created_at, "updated_at": self.updated_at,
            "checkpoint": list(self.checkpoint), "audit": [dict(a) for a in self.audit],
            "intent": self.intent, "edges": [vars(edge) for edge in self.edges],
            "constraints": dict(self.constraints), "version": self.version,
        }
