"""v30.68 Reasoning Engine - domain models.

Structured problem solving, not just tool calls. Every decision carries the five
mandated attributes: Confidence, Evidence, Sources, Alternatives, Risk.

``Evidence`` is intentionally duck-compatible with the v30.64
``MemoryConflictDetector`` (exposes ``memory_id``, ``text``, ``metadata``) so
conflict detection is reused rather than reimplemented.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


# -- Confidence -------------------------------------------------------------
LOW = "low"
MEDIUM = "medium"
HIGH = "high"


def confidence_level(score: float) -> str:
    if score < 0.4:
        return LOW
    if score < 0.7:
        return MEDIUM
    return HIGH


@dataclass(frozen=True)
class Confidence:
    score: float
    factors: dict[str, float] = field(default_factory=dict)

    @property
    def level(self) -> str:
        return confidence_level(self.score)

    def to_dict(self) -> dict[str, Any]:
        return {"score": round(self.score, 4), "level": self.level,
                "factors": {k: round(v, 4) for k, v in self.factors.items()}}


# -- Evidence ---------------------------------------------------------------
SUPPORT = "support"
REFUTE = "refute"
NEUTRAL = "neutral"


@dataclass
class Evidence:
    id: str
    text: str
    source: str
    confidence: float = 0.5
    stance: str = NEUTRAL          # support | refute | neutral
    target: str = ""               # option/hypothesis this evidence bears on
    recency_days: int = 0
    ref: str = ""                  # e.g. memory:<id> / rag:<id> / manual
    metadata: dict[str, Any] = field(default_factory=dict)

    # -- compatibility with MemoryConflictDetector ----------------------
    @property
    def memory_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("metadata", None)
        d["metadata"] = self.metadata
        return d

    @classmethod
    def create(cls, text: str, *, source: str, confidence: float = 0.5, stance: str = NEUTRAL,
               target: str = "", recency_days: int = 0, ref: str = "manual",
               metadata: dict | None = None) -> "Evidence":
        return cls(id=new_id("ev"), text=text, source=source, confidence=clamp(confidence),
                   stance=stance, target=target, recency_days=recency_days, ref=ref,
                   metadata=metadata or {})


# -- Hypothesis -------------------------------------------------------------
HYP_PROPOSED = "proposed"
HYP_SUPPORTED = "supported"
HYP_REFUTED = "refuted"
HYP_UNCERTAIN = "uncertain"


@dataclass
class Hypothesis:
    id: str
    statement: str
    evidence_ids: list[str] = field(default_factory=list)
    support_score: float = 0.0
    confidence: float = 0.0
    status: str = HYP_PROPOSED

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "statement": self.statement, "evidence_ids": list(self.evidence_ids),
                "support_score": round(self.support_score, 4), "confidence": round(self.confidence, 4),
                "status": self.status}

    @classmethod
    def create(cls, statement: str) -> "Hypothesis":
        return cls(id=new_id("hyp"), statement=statement)


# -- Reasoning step (Chain / Tree of Thoughts) -----------------------------
STEP_THOUGHT = "thought"       # chain-of-thought (internal)
STEP_HYPOTHESIS = "hypothesis"
STEP_EVIDENCE = "evidence"
STEP_BRANCH = "branch"         # tree-of-thoughts branch
STEP_DECISION = "decision"


@dataclass
class ReasoningStep:
    id: str
    kind: str
    content: str
    parent_id: str = ""            # for tree-of-thoughts
    internal: bool = False         # chain-of-thought stays internal
    score: float = 0.0
    ref_id: str = ""               # linked hypothesis/decision/evidence id
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(cls, kind: str, content: str, *, parent_id: str = "", internal: bool = False,
               score: float = 0.0, ref_id: str = "") -> "ReasoningStep":
        return cls(id=new_id("step"), kind=kind, content=content, parent_id=parent_id,
                   internal=internal, score=score, ref_id=ref_id)


# -- Decision ---------------------------------------------------------------
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"


@dataclass
class DecisionScore:
    option: str
    score: float
    confidence: float
    support: float
    refute: float
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"option": self.option, "score": round(self.score, 4),
                "confidence": round(self.confidence, 4), "support": round(self.support, 4),
                "refute": round(self.refute, 4), "evidence_ids": list(self.evidence_ids)}


@dataclass
class Decision:
    id: str
    question: str
    chosen: str
    confidence: Confidence
    evidence: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    risk: str = RISK_MEDIUM
    uncertainties: list[str] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    rationale: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "chosen": self.chosen,
            "confidence": self.confidence.to_dict(),
            "evidence": self.evidence,
            "sources": self.sources,
            "alternatives": self.alternatives,
            "risk": self.risk,
            "uncertainties": self.uncertainties,
            "conflicts": self.conflicts,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }
