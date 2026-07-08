from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class AgentMetricsSnapshot:
    planned_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    approval_requests: int = 0
    tool_calls: int = 0
    blocked_tool_calls: int = 0
    average_execution_ms: float = 0.0

    @property
    def completion_rate(self) -> float:
        total = self.completed_tasks + self.failed_tasks
        return 1.0 if total == 0 else self.completed_tasks / total

    @property
    def blocked_tool_call_rate(self) -> float:
        return 0.0 if self.tool_calls == 0 else self.blocked_tool_calls / self.tool_calls

    def to_dict(self) -> dict[str, float | int]:
        data = asdict(self)
        data["completion_rate"] = self.completion_rate
        data["blocked_tool_call_rate"] = self.blocked_tool_call_rate
        return data


class AgentMetrics:
    """Creates RC1 metrics snapshots from execution counters."""

    def snapshot(
        self,
        *,
        planned_tasks: int = 0,
        completed_tasks: int = 0,
        failed_tasks: int = 0,
        approval_requests: int = 0,
        tool_calls: int = 0,
        blocked_tool_calls: int = 0,
        execution_durations_ms: Iterable[float] = (),
    ) -> AgentMetricsSnapshot:
        durations = list(execution_durations_ms)
        return AgentMetricsSnapshot(
            planned_tasks=max(0, planned_tasks),
            completed_tasks=max(0, completed_tasks),
            failed_tasks=max(0, failed_tasks),
            approval_requests=max(0, approval_requests),
            tool_calls=max(0, tool_calls),
            blocked_tool_calls=max(0, blocked_tool_calls),
            average_execution_ms=mean(durations) if durations else 0.0,
        )
