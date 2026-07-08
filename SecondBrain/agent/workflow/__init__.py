"""v30.62 Agent Workflow Engine.

Makes multi-step agent plans executable, checkpointed and crash-recoverable,
reusing the Agent Planner step schema, Tool Registry, the v30.61 Approval Layer,
the native Job Queue, the Notification Center and an optional Memory sink.

Public surface:
    Workflow, WorkflowStep      - plan + step definition
    WorkflowState               - lifecycle state
    WorkflowCheckpoint, StepRun - persisted run snapshot
    WorkflowExecutor            - the engine
    WorkflowRecovery            - error -> strategy
    WorkflowAudit               - lifecycle event trail
    WorkflowService             - CLI/application facade
"""

from __future__ import annotations

from .audit import WorkflowAudit
from .executor import WorkflowExecutor
from .models import (
    StepRun,
    Workflow,
    WorkflowCheckpoint,
    WorkflowState,
    WorkflowStatus,
    WorkflowStep,
)
from .recovery import RecoveryVerdict, WorkflowRecovery
from .service import WorkflowService
from .store import WorkflowStore

__all__ = [
    "Workflow",
    "WorkflowStep",
    "WorkflowState",
    "WorkflowStatus",
    "WorkflowCheckpoint",
    "StepRun",
    "WorkflowExecutor",
    "WorkflowRecovery",
    "RecoveryVerdict",
    "WorkflowAudit",
    "WorkflowStore",
    "WorkflowService",
]
