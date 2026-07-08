"""v30.68 Reasoning Engine.

Lets Jarvis solve problems in a structured, auditable way - not just call tools.
Chain of Thought (internal), Tree of Thoughts, hypothesis testing, evidence
ranking, alternatives, uncertainties and conflict detection. Evidence is gathered
through the existing memory injection (v30.64) and optional RAG; nothing here is
a parallel architecture.

Public surface:
    ReasoningSession, ReasoningChain, ReasoningStep
    EvidenceCollector, Evidence
    Hypothesis
    Decision, DecisionScore, Confidence
    ReasoningHistory
"""

from __future__ import annotations

from .evidence import EvidenceCollector
from .history import ReasoningHistory
from .models import (
    Confidence,
    Decision,
    DecisionScore,
    Evidence,
    Hypothesis,
    ReasoningStep,
)
from .session import ReasoningChain, ReasoningSession

__all__ = [
    "ReasoningSession",
    "ReasoningChain",
    "ReasoningStep",
    "EvidenceCollector",
    "Evidence",
    "Hypothesis",
    "Decision",
    "DecisionScore",
    "Confidence",
    "ReasoningHistory",
]
