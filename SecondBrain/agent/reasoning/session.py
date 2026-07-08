"""v30.68 Reasoning Engine - ReasoningChain and ReasoningSession.

Deterministic, auditable structured problem solving:

* Chain of Thought (internal) - linear internal thoughts (not surfaced as answer).
* Tree of Thoughts           - branch steps scored, best branch selected.
* Hypothesis Testing         - hypotheses scored by supporting vs refuting evidence.
* Evidence Ranking           - via EvidenceCollector (reuses memory injection).
* Alternatives / Uncertainties / Conflicts - attached to every Decision.

Every Decision carries Confidence, Evidence, Sources, Alternatives and Risk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence import EvidenceCollector
from .models import (
    HYP_REFUTED,
    HYP_SUPPORTED,
    HYP_UNCERTAIN,
    REFUTE,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    STEP_BRANCH,
    STEP_DECISION,
    STEP_EVIDENCE,
    STEP_HYPOTHESIS,
    STEP_THOUGHT,
    SUPPORT,
    Confidence,
    Decision,
    DecisionScore,
    Evidence,
    Hypothesis,
    ReasoningStep,
    clamp,
    confidence_level,
    new_id,
    utc_now,
)


class ReasoningChain:
    """Ordered steps forming a chain (linear) or a tree (via parent_id)."""

    def __init__(self) -> None:
        self.steps: list[ReasoningStep] = []

    def add(self, step: ReasoningStep) -> ReasoningStep:
        self.steps.append(step)
        return step

    def children(self, parent_id: str) -> list[ReasoningStep]:
        return [s for s in self.steps if s.parent_id == parent_id]

    def roots(self) -> list[ReasoningStep]:
        return [s for s in self.steps if not s.parent_id]

    def best_branch(self, parent_id: str) -> ReasoningStep | None:
        children = [s for s in self.children(parent_id) if s.kind == STEP_BRANCH]
        if not children:
            return None
        return max(children, key=lambda s: s.score)

    def public_steps(self) -> list[ReasoningStep]:
        return [s for s in self.steps if not s.internal]

    def to_list(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.steps]


class ReasoningSession:
    def __init__(self, problem: str, *, project_root: str | Path | None = None,
                 collector: EvidenceCollector | None = None, high_stakes: bool = False):
        self.id = new_id("reason")
        self.problem = problem
        self.project_root = Path(project_root).resolve() if project_root else None
        self.collector = collector or EvidenceCollector(project_root)
        self.high_stakes = high_stakes
        self.chain = ReasoningChain()
        self.evidence: dict[str, Evidence] = {}
        self.hypotheses: dict[str, Hypothesis] = {}
        self.decisions: list[Decision] = []
        self.created_at = utc_now()

    # -- chain / tree of thoughts -----------------------------------------
    def think(self, content: str, *, parent_id: str = "", internal: bool = True) -> ReasoningStep:
        return self.chain.add(ReasoningStep.create(STEP_THOUGHT, content, parent_id=parent_id,
                                                   internal=internal))

    def branch(self, content: str, *, parent_id: str = "", score: float = 0.0) -> ReasoningStep:
        return self.chain.add(ReasoningStep.create(STEP_BRANCH, content, parent_id=parent_id,
                                                   score=clamp(score)))

    def best_branch(self, parent_id: str) -> ReasoningStep | None:
        return self.chain.best_branch(parent_id)

    # -- evidence ----------------------------------------------------------
    def add_evidence(self, evidence: Evidence) -> Evidence:
        self.evidence[evidence.id] = evidence
        self.chain.add(ReasoningStep.create(STEP_EVIDENCE, evidence.text[:120], ref_id=evidence.id,
                                            score=evidence.confidence))
        return evidence

    def collect_evidence(self, query: str, *, limit: int = 10, privacy_mode: bool = False) -> list[Evidence]:
        collected = self.collector.collect(query, limit=limit, privacy_mode=privacy_mode)
        for ev in collected:
            self.add_evidence(ev)
        return collected

    def evidence_for(self, target: str) -> list[Evidence]:
        return [e for e in self.evidence.values() if e.target == target]

    def conflicts(self) -> list[dict[str, Any]]:
        return EvidenceCollector.detect_conflicts(list(self.evidence.values()))

    # -- hypotheses --------------------------------------------------------
    def hypothesize(self, statement: str) -> Hypothesis:
        hyp = Hypothesis.create(statement)
        self.hypotheses[hyp.id] = hyp
        self.chain.add(ReasoningStep.create(STEP_HYPOTHESIS, statement, ref_id=hyp.id))
        return hyp

    def link_evidence(self, hypothesis_id: str, evidence_id: str, stance: str) -> None:
        hyp = self.hypotheses[hypothesis_id]
        ev = self.evidence[evidence_id]
        ev.stance = stance
        if evidence_id not in hyp.evidence_ids:
            hyp.evidence_ids.append(evidence_id)

    def test_hypothesis(self, hypothesis_id: str) -> Hypothesis:
        hyp = self.hypotheses[hypothesis_id]
        support = sum(self.evidence[e].confidence for e in hyp.evidence_ids
                      if self.evidence[e].stance == SUPPORT)
        refute = sum(self.evidence[e].confidence for e in hyp.evidence_ids
                     if self.evidence[e].stance == REFUTE)
        total = support + refute
        hyp.support_score = (support / total) if total else 0.0
        volume = min(1.0, len(hyp.evidence_ids) / 3.0)
        hyp.confidence = round(clamp(hyp.support_score * (0.5 + 0.5 * volume)), 4)
        if total == 0:
            hyp.status = HYP_UNCERTAIN
        elif hyp.support_score >= 0.6:
            hyp.status = HYP_SUPPORTED
        elif hyp.support_score <= 0.4:
            hyp.status = HYP_REFUTED
        else:
            hyp.status = HYP_UNCERTAIN
        return hyp

    # -- decision ----------------------------------------------------------
    def score_option(self, option: str, evidence: list[Evidence] | None = None) -> DecisionScore:
        items = evidence if evidence is not None else self.evidence_for(option)
        support = sum(e.confidence for e in items if e.stance == SUPPORT)
        refute = sum(e.confidence for e in items if e.stance == REFUTE)
        total = support + refute
        ratio = (support / total) if total else 0.0
        volume = min(1.0, len([e for e in items if e.stance in (SUPPORT, REFUTE)]) / 3.0)
        # Blend ratio with evidence volume so stronger/greater support outranks a
        # single weak data point that happens to be unopposed.
        score = clamp(ratio * (0.5 + 0.5 * volume))
        return DecisionScore(option=option, score=score, confidence=score, support=support,
                             refute=refute, evidence_ids=[e.id for e in items])

    def decide(self, question: str, options: list[str], *,
               evidence_by_option: dict[str, list[Evidence]] | None = None) -> Decision:
        if not options:
            raise ValueError("no_options")
        scores = [self.score_option(opt, (evidence_by_option or {}).get(opt))
                  for opt in options]
        scores.sort(key=lambda s: (s.score, s.confidence), reverse=True)
        best = scores[0]
        runner_up = scores[1] if len(scores) > 1 else None

        chosen_evidence = [self.evidence.get(eid) or _find(evidence_by_option, best.option, eid)
                           for eid in best.evidence_ids]
        chosen_evidence = [e for e in chosen_evidence if e is not None]
        support_evidence = [e for e in chosen_evidence if e.stance == SUPPORT]
        conflicts = EvidenceCollector.detect_conflicts(
            [e for lst in (evidence_by_option or {}).values() for e in lst] or list(self.evidence.values()))

        # confidence factors
        margin = best.score - (runner_up.score if runner_up else 0.0)
        factors = {
            "support": best.score,
            "volume": min(1.0, len(support_evidence) / 3.0),
            "margin": min(1.0, max(0.0, margin) / 0.5),
            "agreement": 1.0 - min(1.0, len(conflicts) * 0.34),
        }
        conf_score = clamp(0.4 * factors["support"] + 0.2 * factors["volume"]
                           + 0.2 * factors["margin"] + 0.2 * factors["agreement"])
        confidence = Confidence(score=conf_score, factors=factors)

        # risk: derived from confidence, bumped by conflicts / stakes
        risk = {"high": RISK_LOW, "medium": RISK_MEDIUM, "low": RISK_HIGH}[confidence.level]
        if (conflicts or self.high_stakes) and risk != RISK_HIGH:
            risk = RISK_HIGH if risk == RISK_MEDIUM else RISK_MEDIUM

        uncertainties = self._uncertainties(best, factors, conflicts)
        sources = []
        for e in support_evidence:
            if e.source and e.source not in sources:
                sources.append(e.source)

        decision = Decision(
            id=new_id("dec"), question=question, chosen=best.option, confidence=confidence,
            evidence=[e.to_dict() for e in chosen_evidence],
            sources=sources,
            alternatives=[s.to_dict() for s in scores[1:]],
            risk=risk, uncertainties=uncertainties, conflicts=conflicts,
            rationale=(f"'{best.option}' gewählt (Score {round(best.score, 2)}, "
                       f"Confidence {confidence.level}); {len(scores) - 1} Alternative(n), "
                       f"{len(conflicts)} Konflikt(e)."),
        )
        self.decisions.append(decision)
        self.chain.add(ReasoningStep.create(STEP_DECISION, decision.chosen, ref_id=decision.id,
                                            score=conf_score))
        return decision

    def _uncertainties(self, best: DecisionScore, factors: dict[str, float],
                       conflicts: list) -> list[str]:
        out: list[str] = []
        if factors["volume"] < 0.34:
            out.append("low_evidence_volume")
        if factors["margin"] < 0.2:
            out.append("close_margin")
        if best.score < 0.5:
            out.append("weak_support")
        if conflicts:
            out.append("evidence_conflict")
        if best.support == 0 and best.refute == 0:
            out.append("no_direct_evidence")
        return out

    # -- persistence -------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "problem": self.problem,
            "created_at": self.created_at,
            "steps": self.chain.to_list(),
            "public_steps": [s.to_dict() for s in self.chain.public_steps()],
            "evidence": [e.to_dict() for e in self.evidence.values()],
            "hypotheses": [h.to_dict() for h in self.hypotheses.values()],
            "decisions": [d.to_dict() for d in self.decisions],
        }

    def save(self) -> dict[str, Any]:
        if self.project_root is None:
            raise RuntimeError("project_root_required_to_save")
        from .history import ReasoningHistory
        snap = self.snapshot()
        ReasoningHistory(self.project_root).save(snap)
        return snap


def _find(evidence_by_option, option, eid):
    for e in (evidence_by_option or {}).get(option, []):
        if e.id == eid:
            return e
    return None
