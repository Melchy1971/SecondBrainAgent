"""v30.65 Agent Goal Tracking.

Lets Jarvis track goals, progress and open work: goals with milestones, metrics
and evidence, decomposed into plans via the Agent Planner, progress measured
against plans/workflows, and reports pushed to the Notification Center and
dashboard.

Public surface:
    Goal, GoalStatus            - goal + lifecycle state
    GoalMilestone, GoalMetric   - progress components
    GoalEvidence, GoalReview    - evidence + report record
    GoalStore                   - persistence
    GoalTracker                 - application service
"""

from __future__ import annotations

from .models import (
    Goal,
    GoalEvidence,
    GoalMetric,
    GoalMilestone,
    GoalReview,
    GoalStatus,
)
from .store import GoalStore
from .tracker import GoalProgress, GoalTracker

__all__ = [
    "Goal",
    "GoalStatus",
    "GoalMilestone",
    "GoalMetric",
    "GoalEvidence",
    "GoalReview",
    "GoalStore",
    "GoalTracker",
    "GoalProgress",
]
