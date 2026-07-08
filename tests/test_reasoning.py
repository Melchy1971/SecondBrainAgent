from __future__ import annotations

from secondbrain.agent.reasoning import EvidenceCollector, ReasoningHistory, ReasoningSession
from secondbrain.agent.reasoning.models import (
    HYP_REFUTED,
    HYP_SUPPORTED,
    HYP_UNCERTAIN,
    REFUTE,
    SUPPORT,
    Evidence,
)

from tests._mem_helpers import make_record, make_store


def test_chain_of_thought_is_internal():
    s = ReasoningSession("Wie skaliere ich den Import?")
    s.think("interner Gedanke A")
    s.think("interner Gedanke B")
    assert len(s.chain.steps) == 2
    assert s.chain.public_steps() == []          # CoT stays internal


def test_tree_of_thoughts_best_branch():
    s = ReasoningSession("Architektur wählen")
    root = s.think("Wurzel", internal=False)
    s.branch("Option A", parent_id=root.id, score=0.3)
    best = s.branch("Option B", parent_id=root.id, score=0.8)
    s.branch("Option C", parent_id=root.id, score=0.5)
    assert s.best_branch(root.id).id == best.id


def test_hypothesis_supported():
    s = ReasoningSession("Ist der Watcher stabil?")
    h = s.hypothesize("Der Watcher ist stabil")
    e1 = s.add_evidence(Evidence.create("Läuft seit 30 Tagen", source="log", confidence=0.9))
    e2 = s.add_evidence(Evidence.create("Keine Fehler gemeldet", source="mon", confidence=0.8))
    s.link_evidence(h.id, e1.id, SUPPORT)
    s.link_evidence(h.id, e2.id, SUPPORT)
    tested = s.test_hypothesis(h.id)
    assert tested.status == HYP_SUPPORTED
    assert tested.support_score == 1.0


def test_hypothesis_refuted():
    s = ReasoningSession("Frage")
    h = s.hypothesize("These")
    e = s.add_evidence(Evidence.create("Gegenbeweis", source="x", confidence=0.9))
    s.link_evidence(h.id, e.id, REFUTE)
    assert s.test_hypothesis(h.id).status == HYP_REFUTED


def test_hypothesis_uncertain_without_evidence():
    s = ReasoningSession("Frage")
    h = s.hypothesize("Unbelegte These")
    assert s.test_hypothesis(h.id).status == HYP_UNCERTAIN


def test_collect_evidence_from_memory_into_session():
    store = make_store([make_record("SAP Migration Fakt", source="wiki-1")])
    s = ReasoningSession("SAP?", collector=EvidenceCollector(memory_store=store))
    collected = s.collect_evidence("SAP Migration")
    assert collected
    assert len(s.evidence) == len(collected)


def test_snapshot_and_history_persist(tmp_path):
    s = ReasoningSession("Problem", project_root=tmp_path)
    s.think("Gedanke")
    s.decide("Welche Option?", ["A", "B"], evidence_by_option={
        "A": [Evidence.create("pro A", source="s", confidence=0.9, stance=SUPPORT, target="A")],
        "B": [],
    })
    snap = s.save()
    assert snap["decisions"]
    stored = ReasoningHistory(tmp_path).get(s.id)
    assert stored is not None
    assert stored["problem"] == "Problem"


def test_snapshot_separates_public_and_internal_steps():
    s = ReasoningSession("P")
    s.think("intern")
    s.think("öffentlich", internal=False)
    snap = s.snapshot()
    assert len(snap["steps"]) == 2
    assert len(snap["public_steps"]) == 1
