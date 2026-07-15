"""Sprint 48 acceptance tests - evidence-based knowledge graph."""

from __future__ import annotations

import pytest

from secondbrain.knowledge_graph.models import EntityType, RelationType
from secondbrain.knowledge_graph.service import KnowledgeGraph, AUTO_MERGE_THRESHOLD
from secondbrain.knowledge_graph.gui import GraphViewModel, render_graph_html

WS = "ws-1"


def _g():
    return KnowledgeGraph()


class ApprovalQueue:
    def __init__(self): self.started = set()
    def create(self, **_kwargs): return {"approval_id": "approval-1"}
    def begin_execution(self, approval_id, **_kwargs):
        if approval_id in self.started: raise RuntimeError("already_executed")
        self.started.add(approval_id)


# 1: document produces entity candidates
def test_document_creates_candidates():
    g = _g()
    doc = {"id": "doc-1", "text": "Markus arbeitet mit Anna an SecondBrain.",
           "people": ["Markus", "Anna"], "projects": ["SecondBrain"]}
    cands = g.extract_candidates(doc, workspace_id=WS)
    assert len(cands) == 3
    assert all("doc-1" in c.source_ids for c in cands)
    assert all(c.evidence for c in cands)


# 2: relationships carry evidence
def test_relationship_requires_evidence():
    g = _g()
    a = g.add_entity(workspace_id=WS, canonical_name="Markus", type=EntityType.PERSON.value)
    b = g.add_entity(workspace_id=WS, canonical_name="Telekom", type=EntityType.ORGANIZATION.value)
    rel = g.add_relationship(workspace_id=WS, source_entity=a.id, target_entity=b.id,
                             type=RelationType.WORKS_FOR.value,
                             evidence=[{"source_id": "doc-1", "snippet": "Markus @ Telekom"}])
    assert rel.evidence
    with pytest.raises(ValueError):
        g.add_relationship(workspace_id=WS, source_entity=a.id, target_entity=b.id,
                           type=RelationType.RELATED_TO.value)  # no evidence, no source


# 3: duplicates detected
def test_duplicates_detected():
    g = _g()
    g.add_entity(workspace_id=WS, canonical_name="Markus Dickscheit", type=EntityType.PERSON.value)
    g.add_entity(workspace_id=WS, canonical_name="Markus Dickscheit", type=EntityType.PERSON.value)
    props = g.detect_duplicates(workspace_id=WS)
    assert props and props[0].score >= AUTO_MERGE_THRESHOLD


# 4: uncertain duplicates not auto-merged
def test_uncertain_not_auto_merged():
    g = _g()
    g.add_entity(workspace_id=WS, canonical_name="Markus D.", type=EntityType.PERSON.value)
    g.add_entity(workspace_id=WS, canonical_name="Markus Berger", type=EntityType.PERSON.value)
    props = g.detect_duplicates(workspace_id=WS, threshold=0.4)
    weak = [p for p in props if not p.auto_mergeable]
    assert weak  # at least one weak pair
    merged = g.resolve_duplicates(workspace_id=WS, auto_only=True)
    assert merged == []  # nothing merged automatically
    assert len(g.entities(workspace_id=WS)) == 2


# 4b: strong match auto-merges when requested
def test_strong_auto_merge():
    g = _g()
    g.add_entity(workspace_id=WS, canonical_name="ACME GmbH", type=EntityType.ORGANIZATION.value)
    g.add_entity(workspace_id=WS, canonical_name="ACME GmbH", type=EntityType.ORGANIZATION.value)
    merged = g.resolve_duplicates(workspace_id=WS, auto_only=True)
    assert len(merged) == 1
    assert len(g.entities(workspace_id=WS)) == 1


def test_person_is_not_auto_merged_by_name_only():
    g = _g()
    g.add_entity(workspace_id=WS, canonical_name="Anna Meyer", type=EntityType.PERSON.value)
    g.add_entity(workspace_id=WS, canonical_name="Anna Meyer", type=EntityType.PERSON.value)
    assert g.resolve_duplicates(workspace_id=WS, auto_only=True) == []


# 5: conflicts traceable, not silently overwritten
def test_conflict_traceable():
    g = _g()
    e = g.add_entity(workspace_id=WS, canonical_name="Projekt X", type=EntityType.PROJECT.value)
    assert g.set_attribute(e.id, "status", "aktiv", source_id="doc-1") is None
    conflict = g.set_attribute(e.id, "status", "abgeschlossen", source_id="doc-2")
    assert conflict is not None
    assert {v.value for v in conflict.values} == {"aktiv", "abgeschlossen"}
    # both retained with their source
    vals = g.get(e.id).attributes["status"]
    assert len(vals) == 2 and {v.source_id for v in vals} == {"doc-1", "doc-2"}
    # resolve by supersede keeps both, marks one
    g.resolve_conflict(conflict, resolution="supersede", keep_value="abgeschlossen")
    superseded = [v for v in g.get(e.id).attributes["status"] if v.superseded_by]
    assert superseded and superseded[0].value == "aktiv"


# 6: workspace isolation
def test_workspace_isolation():
    g = _g()
    g.add_entity(workspace_id=WS, canonical_name="A", type=EntityType.PERSON.value)
    g.add_entity(workspace_id="ws-2", canonical_name="B", type=EntityType.PERSON.value)
    assert [e.canonical_name for e in g.entities(workspace_id=WS)] == ["A"]
    assert g.detect_duplicates(workspace_id=WS) == []


# 7: graph query returns sources
def test_query_returns_sources():
    g = _g()
    a = g.add_entity(workspace_id=WS, canonical_name="Markus", type=EntityType.PERSON.value, source_ids=["s-a"])
    b = g.add_entity(workspace_id=WS, canonical_name="SecondBrain", type=EntityType.PROJECT.value, source_ids=["s-b"])
    g.add_relationship(workspace_id=WS, source_entity=a.id, target_entity=b.id,
                       type=RelationType.RESPONSIBLE_FOR.value, origin_source_ids=["doc-9"],
                       evidence=[{"source_id": "doc-9"}])
    rels = g.relations_of(a.id)
    assert rels[0]["sources"] == ["doc-9"]
    ctx = g.context(a.id)
    assert ctx["related"]["project"][0]["sources"] == ["s-b"]


# 8: technical ids only in detail view, not overview
def test_ids_only_in_detail():
    g = _g()
    e = g.add_entity(workspace_id=WS, canonical_name="Markus", type=EntityType.PERSON.value)
    vm = GraphViewModel(g)
    explorer = vm.explorer(workspace_id=WS)
    assert all("id" not in n for n in explorer["nodes"])  # overview: no ids
    detail = vm.entity_detail(e.id)
    assert detail["id"] == e.id  # detail: id present


# 9: deletion is approval-gated
def test_delete_requires_approval():
    g = _g()
    e = g.add_entity(workspace_id=WS, canonical_name="Temp", type=EntityType.TOPIC.value)
    queue = ApprovalQueue()
    prep = g.prepare_delete(e.id, workspace_id=WS, approval_queue=queue)
    assert prep["status"] == "approval_required"
    assert g.get(e.id) is not None  # not deleted yet
    assert g.commit_delete(prep, approval_queue=None, workspace_id=WS)["status"] == "blocked"
    assert g.get(e.id) is not None
    r1 = g.commit_delete(prep, approval_queue=queue, workspace_id=WS)
    assert r1["status"] == "committed"
    assert g.get(e.id).status == "archived"  # evidence is retained
    r2 = g.commit_delete(prep, approval_queue=queue, workspace_id=WS)
    assert r2["status"] == "duplicate"  # exactly once


# 9b: tampered delete payload rejected
def test_delete_tamper_rejected():
    g = _g()
    e = g.add_entity(workspace_id=WS, canonical_name="Temp", type=EntityType.TOPIC.value)
    queue = ApprovalQueue()
    prep = dict(g.prepare_delete(e.id, workspace_id=WS, approval_queue=queue))
    prep["entity_id"] = "other"
    assert g.commit_delete(prep, approval_queue=queue, workspace_id=WS)["status"] == "invalid"


# 10: graph-RAG can use entities as context
def test_rag_context():
    g = _g()
    a = g.add_entity(workspace_id=WS, canonical_name="Markus", type=EntityType.PERSON.value,
                     aliases=["M. Dickscheit"], source_ids=["s-1"],
                     evidence=[{"source_id": "s-1", "snippet": "Markus ist PO"}])
    b = g.add_entity(workspace_id=WS, canonical_name="Telekom", type=EntityType.ORGANIZATION.value)
    g.add_relationship(workspace_id=WS, source_entity=a.id, target_entity=b.id,
                       type=RelationType.WORKS_FOR.value, evidence=[{"source_id": "s-1"}])
    ctx = g.context_for_rag(a.id)
    assert ctx["canonical_name"] == "Markus"
    assert ctx["sources"] == ["s-1"]
    assert ctx["evidence"] and ctx["relations"]


# path between
def test_path_between():
    g = _g()
    a = g.add_entity(workspace_id=WS, canonical_name="A", type=EntityType.PERSON.value)
    b = g.add_entity(workspace_id=WS, canonical_name="B", type=EntityType.PROJECT.value)
    c = g.add_entity(workspace_id=WS, canonical_name="C", type=EntityType.ORGANIZATION.value)
    g.add_relationship(workspace_id=WS, source_entity=a.id, target_entity=b.id,
                       type=RelationType.RELATED_TO.value, evidence=[{"source_id": "x"}])
    g.add_relationship(workspace_id=WS, source_entity=b.id, target_entity=c.id,
                       type=RelationType.BELONGS_TO.value, evidence=[{"source_id": "y"}])
    path = g.path_between(a.id, c.id)
    assert path == [a.id, b.id, c.id]


# merge retains superseded
def test_merge_retains_superseded():
    g = _g()
    a = g.add_entity(workspace_id=WS, canonical_name="ACME", type=EntityType.ORGANIZATION.value, source_ids=["s1"])
    b = g.add_entity(workspace_id=WS, canonical_name="ACME Inc", type=EntityType.ORGANIZATION.value, source_ids=["s2"])
    g.merge(a.id, b.id)
    assert g.get(b.id).superseded_by == a.id  # not deleted
    assert "s2" in g.get(a.id).source_ids
    restored = g.undo_merge(a.id, b.id)
    assert restored.superseded_by == "" and len(g.entities(workspace_id=WS)) == 2


# gui render
def test_gui_render():
    g = _g()
    a = g.add_entity(workspace_id=WS, canonical_name="Markus", type=EntityType.PERSON.value)
    b = g.add_entity(workspace_id=WS, canonical_name="SecondBrain", type=EntityType.PROJECT.value)
    g.add_relationship(workspace_id=WS, source_entity=a.id, target_entity=b.id,
                       type=RelationType.RESPONSIBLE_FOR.value, evidence=[{"source_id": "d"}])
    html_out = render_graph_html(GraphViewModel(g).explorer(workspace_id=WS))
    assert "Markus" in html_out and "Beziehungen" in html_out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
