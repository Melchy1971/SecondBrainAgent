from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .flow_models import FlowResult


def flow_result_to_report(result: FlowResult) -> dict[str, Any]:
    return {
        "flow_id": result.flow_id,
        "status": result.status.value,
        "passed": result.passed,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
        "steps": [
            {
                **asdict(step),
                "status": step.status.value,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "finished_at": step.finished_at.isoformat() if step.finished_at else None,
            }
            for step in result.steps
        ],
        "context_keys": sorted(result.context.keys()),
        "failed_steps": [step.step_id for step in result.failed_steps],
    }
