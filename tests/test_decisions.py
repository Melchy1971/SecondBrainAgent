from __future__ import annotations

from secondbrain.agent.reasoning import ReasoningSession
from secondbrain.agent.reasoning.models import (
    RISK_HIGH,
    RISK_LOW,
    SUPPORT,
    Evidence,
)


def _ev(text, conf, stance=SUPPORT, source="s", **md):
    return Evidence.create(text, source=source, confidence=conf, stance=stance, metadata=md)


def test_decision_picks_best_supported_option():
    s = ReasoningSession("Welche DB?")
    dec = s.decide("Welche DB?", ["Postgres", "SQLite"], evidence_by_option={
        "Postgres": [_ev("skaliert", 0.9), _ev("teamerfahrung", 0.8)],
        "SQLite": [_ev("einfach", 0.4)],
    })
    assert dec.chosen == "Postgres"


def test_decision_has_all_mandatory_attributes():
    s = ReasoningSession("Frage")
    dec = s.decide("Frage", ["A", "B"], evidence_by_option={
        "A": [_ev("pro A", 0.9, source="wiki")],
        "B": [_ev("pro B", 0.5, source="chat")],
    })
    d = dec.to_dict()
    for key in ("confidence", "evidence", "sources", "alternatives", "risk"):
        assert key in d
    assert d["confidence"]["level"] in {"low", "medium", "high"}
    assert d["sources"] == ["wiki"]
    assert d["alternatives"][0]["option"] == "B"


def test_strong_evidence_gives_low_risk():
    s = ReasoningSession("Frage")
    dec = s.decide("Frage", ["A", "B"], evidence_by_option={
        "A": [_ev("a1", 0.9), _ev("a2", 0.9), _ev("a3", 0.9)],
        "B": [_ev("b1", 0.2)],
    })
    assert dec.confidence.level == "high"
    assert dec.risk == RISK_LOW


def test_conflict_raises_risk_and_flags_uncertainty():
    s = ReasoningSession("Frage")
    dec = s.decide("Frage", ["A", "B"], evidence_by_option={
        "A": [_ev("Deadline August", 0.9, claim_key="deadline", claim_value="2026-08-01"),
              _ev("Deadline September", 0.9, claim_key="deadline", claim_value="2026-09-01")],
        "B": [_ev("pro B", 0.3)],
    })
    assert dec.conflicts                    # conflict detected
    assert "evidence_conflict" in dec.uncertainties
    assert dec.risk == RISK_HIGH            # bumped by conflict


def test_high_stakes_bumps_risk():
    s = ReasoningSession("Frage", high_stakes=True)
    dec = s.decide("Frage", ["A", "B"], evidence_by_option={
        "A": [_ev("a1", 0.9), _ev("a2", 0.9), _ev("a3", 0.9)],
        "B": [_ev("b1", 0.1)],
    })
    # would be low risk, but high_stakes lifts it
    assert dec.risk != RISK_LOW


def test_no_evidence_yields_uncertainty():
    s = ReasoningSession("Frage")
    dec = s.decide("Frage", ["A", "B"], evidence_by_option={"A": [], "B": []})
    assert "no_direct_evidence" in dec.uncertainties
    assert dec.confidence.level == "low"


def test_alternatives_sorted_descending():
    s = ReasoningSession("Frage")
    dec = s.decide("Frage", ["A", "B", "C"], evidence_by_option={
        "A": [_ev("a", 0.9), _ev("a2", 0.9)],
        "B": [_ev("b", 0.9)],
        "C": [_ev("c", 0.9, stance="refute")],
    })
    alts = dec.alternatives
    scores = [a["score"] for a in alts]
    assert scores == sorted(scores, reverse=True)


def test_decision_recorded_in_chain_and_session():
    s = ReasoningSession("Frage")
    dec = s.decide("Frage", ["A"], evidence_by_option={"A": [_ev("pro", 0.8)]})
    assert s.decisions[-1].id == dec.id
    assert any(step.kind == "decision" for step in s.chain.steps)
