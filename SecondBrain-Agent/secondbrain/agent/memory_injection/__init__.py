"""v30.64 Agent Memory Injection.

Lets agents use memory in a targeted, bounded and auditable way on top of the
existing ``secondbrain.agent.memory`` store - no second memory engine.

Public surface:
    MemoryInjector          - orchestration (preview / inject)
    MemoryQuery             - what to retrieve and under which constraints
    MemoryContext           - the assembled result handed to the agent
    MemoryEvidence          - one injected memory (source, confidence, recency)
    MemoryRanking           - relevance + recency + confidence scoring
    MemoryBudget            - token accounting / hard ceiling
    MemoryConflictDetector  - contradiction detection
    MemoryInjectionAudit    - audit trail
"""

from __future__ import annotations

from .audit import MemoryInjectionAudit
from .budget import MemoryBudget, estimate_tokens
from .conflicts import MemoryConflictDetector
from .injector import MemoryInjector
from .models import (
    MemoryConflict,
    MemoryContext,
    MemoryEvidence,
    MemoryExclusion,
    MemoryQuery,
)
from .ranking import MemoryRanking, RankedMemory

__all__ = [
    "MemoryInjector",
    "MemoryQuery",
    "MemoryContext",
    "MemoryEvidence",
    "MemoryExclusion",
    "MemoryConflict",
    "MemoryRanking",
    "RankedMemory",
    "MemoryBudget",
    "estimate_tokens",
    "MemoryConflictDetector",
    "MemoryInjectionAudit",
]
