from __future__ import annotations

import pytest

from secondbrain.agent.memory import MemoryError
from secondbrain.agent.reasoning import EvidenceCollector, Evidence
from secondbrain.agent.reasoning.models import SUPPORT

from tests._mem_helpers import make_record, make_store


def test_manual_evidence_and_ranking():
    c = EvidenceCollector()
    c.add_fact("schwach", source="a", confidence=0.3)
    c.add_fact("stark", source="b", confidence=0.9)
    ranked = c.collect("egal")
    assert [e.text for e in ranked] == ["stark", "schwach"]


def test_collect_from_memory_reuses_injection():
    store = make_store([
        make_record("SAP Migration hat hohe Prioritaet", source="wiki-1"),
        make_record("Unrelated", source="chat-9"),
    ])
    c = EvidenceCollector(memory_store=store)
    ev = c.collect_from_memory("SAP Migration")
    assert ev
    assert all(e.ref.startswith("memory:") for e in ev)
    assert any("wiki-1" == e.source for e in ev)


def test_memory_secret_is_not_collected():
    store = make_store([make_record("Harmlos", source="a")])
    with pytest.raises(MemoryError, match="memory_write_blocked:secret"):
        store.add(make_record("key sk-abcdefghijklmnop1234", source="leak"))

    c = EvidenceCollector(memory_store=store)
    texts = [e.text for e in c.collect_from_memory("key")]
    assert all("sk-" not in t for t in texts)


def test_collect_from_rag_with_injected_search():
    def fake_rag(query, limit):
        return [{"text": "RAG Treffer", "source": "doc-3", "score": 0.7, "id": "r1"}]

    c = EvidenceCollector(rag_search=fake_rag)
    ev = c.collect_from_rag("frage")
    assert len(ev) == 1
    assert ev[0].ref == "rag:r1"
    assert ev[0].source == "doc-3"


def test_conflict_detection_reused_on_evidence():
    a = Evidence.create("Deadline 1. August", source="a",
                        metadata={"claim_key": "deadline", "claim_value": "2026-08-01"})
    b = Evidence.create("Deadline 15. August", source="b",
                        metadata={"claim_key": "deadline", "claim_value": "2026-08-15"})
    conflicts = EvidenceCollector.detect_conflicts([a, b])
    assert len(conflicts) == 1
    assert conflicts[0]["reason"] == "claim_value_mismatch"


def test_collect_merges_memory_and_manual():
    store = make_store([make_record("Memory Fakt", source="m")])
    c = EvidenceCollector(memory_store=store)
    c.add_fact("Manueller Fakt", source="u", confidence=0.95)
    allev = c.collect("Fakt")
    sources = {e.source for e in allev}
    assert "m" in sources and "u" in sources
    # ranked by confidence desc (memory relevance can legitimately top a manual fact)
    confs = [e.confidence for e in allev]
    assert confs == sorted(confs, reverse=True)
