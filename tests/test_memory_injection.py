from __future__ import annotations

from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery
from secondbrain.agent.memory_injection.audit import MemoryInjectionAudit

from tests._mem_helpers import make_record, make_store


def test_preview_returns_ranked_evidence_with_sources_and_confidence(tmp_path):
    store = make_store([
        make_record("Markus arbeitet an der SAP Migration", source="wiki-1"),
        make_record("Das Wetter war gestern schoen", source="chat-9"),
        make_record("Die SAP Migration hat hohe Prioritaet", source="wiki-2"),
    ])
    injector = MemoryInjector(store)
    ctx = injector.preview(MemoryQuery(text="SAP Migration"))

    assert len(ctx.evidences) == 2               # the unrelated weather note is dropped
    assert all(e.source for e in ctx.evidences)  # Quellenpflicht
    assert all(0.0 <= e.confidence <= 1.0 for e in ctx.evidences)
    assert ctx.evidences[0].relevance >= ctx.evidences[1].relevance
    assert "chat-9" not in ctx.sources


def test_irrelevant_memory_excluded_when_query_present(tmp_path):
    store = make_store([
        make_record("Projekt Phoenix startet im August", source="a"),
        make_record("Voellig anderes Thema ohne Bezug", source="b"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="Phoenix"))
    reasons = {x.reason for x in ctx.exclusions}
    assert "low_relevance" in reasons
    assert [e.text for e in ctx.evidences] == ["Projekt Phoenix startet im August"]


def test_no_query_returns_all_non_excluded(tmp_path):
    store = make_store([
        make_record("Fakt eins", source="a"),
        make_record("Fakt zwei", source="b"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text=""))
    assert len(ctx.evidences) == 2


def test_require_source_strict_excludes_unsourced(tmp_path):
    store = make_store([
        make_record("Mit Quelle", source="doc-1"),
        make_record("Ohne Quelle", source=None),  # no explicit source metadata
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", require_source=True))
    texts = [e.text for e in ctx.evidences]
    assert "Mit Quelle" in texts
    assert "Ohne Quelle" not in texts
    assert any(x.reason == "no_source" for x in ctx.exclusions)


def test_workspace_filter(tmp_path):
    store = make_store([
        make_record("Workspace A Notiz", source="a", scope="workspace", workspace_id="ws-a"),
        make_record("Workspace B Notiz", source="b", scope="workspace", workspace_id="ws-b"),
        make_record("Globale Notiz", source="g"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="Notiz", workspace_id="ws-a"))
    texts = {e.text for e in ctx.evidences}
    assert "Workspace A Notiz" in texts
    assert "Workspace B Notiz" not in texts


def test_inject_writes_audit_trail(tmp_path):
    store = make_store([make_record("SAP Fakt", source="wiki-1")])
    injector = MemoryInjector.for_project(tmp_path, store)
    injector.inject(MemoryQuery(text="SAP"), actor="agent", agent_id="agent-1")

    events = MemoryInjectionAudit(tmp_path).events("agent-1")
    assert len(events) == 1
    assert events[0]["injected_memory_ids"]
    assert events[0]["sources"] == ["wiki-1"]
    assert events[0]["actor"] == "agent"


def test_preview_does_not_write_audit(tmp_path):
    store = make_store([make_record("SAP Fakt", source="wiki-1")])
    injector = MemoryInjector.for_project(tmp_path, store)
    injector.preview(MemoryQuery(text="SAP"))
    assert MemoryInjectionAudit(tmp_path).events() == []
