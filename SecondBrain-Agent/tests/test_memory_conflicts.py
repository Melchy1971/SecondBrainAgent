from __future__ import annotations

from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery
from secondbrain.agent.memory_injection.conflicts import MemoryConflictDetector

from tests._mem_helpers import make_record, make_store


def test_claim_value_mismatch_is_a_conflict():
    a = make_record("Deadline ist der 1. August", source="a",
                    metadata={"claim_key": "deadline", "claim_value": "2026-08-01"})
    b = make_record("Deadline ist der 15. August", source="b",
                    metadata={"claim_key": "deadline", "claim_value": "2026-08-15"})
    conflicts = MemoryConflictDetector().detect([a, b])
    assert len(conflicts) == 1
    assert conflicts[0].reason == "claim_value_mismatch"
    assert set(conflicts[0].memory_ids) == {a.memory_id, b.memory_id}


def test_same_claim_value_is_no_conflict():
    a = make_record("Deadline August", source="a",
                    metadata={"claim_key": "deadline", "claim_value": "2026-08-01"})
    b = make_record("Deadline ebenfalls August", source="b",
                    metadata={"claim_key": "deadline", "claim_value": "2026-08-01"})
    assert MemoryConflictDetector().detect([a, b]) == []


def test_negation_heuristic_detects_contradiction():
    a = make_record("Der Server ist online und erreichbar", source="a")
    b = make_record("Der Server ist nicht online und erreichbar", source="b")
    conflicts = MemoryConflictDetector().detect([a, b])
    assert any(c.reason == "negation" for c in conflicts)


def test_unrelated_memories_do_not_conflict():
    a = make_record("Kaffee schmeckt gut", source="a")
    b = make_record("Das Auto ist rot", source="b")
    assert MemoryConflictDetector().detect([a, b]) == []


def test_conflicts_surface_in_injected_context(tmp_path):
    store = make_store([
        make_record("Budget ist genehmigt", source="a",
                    metadata={"claim_key": "budget", "claim_value": "approved"}),
        make_record("Budget ist abgelehnt", source="b",
                    metadata={"claim_key": "budget", "claim_value": "rejected"}),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="Budget"))
    assert len(ctx.evidences) == 2               # both are still injected...
    assert len(ctx.conflicts) == 1               # ...but the conflict is flagged
    assert ctx.to_dict()["counts"]["conflicts"] == 1
