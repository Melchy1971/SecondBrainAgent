"""Sprint 49 acceptance tests - memory consolidation, decay, conflicts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.memory_consolidation.models import Decision, MemoryStatus, MemoryType, ConflictType
from secondbrain.memory_consolidation.service import MemoryConsolidator, IMPORTANT_THRESHOLD
from secondbrain.memory_consolidation.gui import MemoryReviewViewModel, render_memory_html

WS = "ws-1"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _mc():
    return MemoryConsolidator()


# 1: duplicates grouped
def test_duplicates_grouped():
    mc = _mc()
    mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Markus mag Kaffee am Morgen", now=T0)
    mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Markus mag morgens Kaffee", now=T0)
    groups = mc.find_duplicates(workspace_id=WS)
    assert groups and len(groups[0].memory_ids) == 2


# 2: user correction wins
def test_user_correction_wins():
    mc = _mc()
    old = mc.add_memory(workspace_id=WS, type=MemoryType.PREFERENCE.value, content="Markus nutzt Windows", now=T0)
    corr = mc.apply_correction(workspace_id=WS, type=MemoryType.PREFERENCE.value,
                               content="Markus nutzt Linux", supersedes=[old.memory_id], now=T0)
    assert mc.get(old.memory_id).status == MemoryStatus.SUPERSEDED.value
    assert mc.get(old.memory_id).superseded_by == corr.memory_id
    assert corr.confidence == 1.0 and corr.user_confirmed


# 3: conflicts not silently overwritten
def test_conflict_not_silent():
    mc = _mc()
    a = mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Projekt X ist aktiv", now=T0)
    b = mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Projekt X ist abgeschlossen", now=T0)
    conflicts = mc.detect_conflicts(workspace_id=WS, now=T0)
    contradictory = [c for c in conflicts if c.conflict_type == ConflictType.CONTRADICTORY.value]
    assert contradictory
    # both still active until an explicit decision
    assert mc.get(a.memory_id).status == MemoryStatus.ACTIVE.value
    assert mc.get(b.memory_id).status == MemoryStatus.ACTIVE.value
    mc.resolve(contradictory[0], decision=Decision.SUPERSEDE.value, keep=b.memory_id)
    assert mc.get(a.memory_id).status == MemoryStatus.SUPERSEDED.value
    assert mc.get(a.memory_id).superseded_by == b.memory_id  # retained


# 4: expired episodic memory is marked
def test_episodic_expired_marked():
    mc = _mc()
    m = mc.add_memory(workspace_id=WS, type=MemoryType.EPISODIC.value, content="Kurzer Vermerk",
                      importance=0.2, now=T0)
    later = T0 + timedelta(days=120)  # well past 14d half-life
    res = mc.apply_decay(workspace_id=WS, now=later)
    assert res["expired"] == 1
    assert mc.get(m.memory_id).status == MemoryStatus.EXPIRED.value  # marked, not deleted
    assert mc.get(m.memory_id) is not None


# 4b: important memory never auto-expired
def test_important_not_expired():
    mc = _mc()
    m = mc.add_memory(workspace_id=WS, type=MemoryType.EPISODIC.value, content="Wichtig",
                      importance=0.95, now=T0)
    mc.apply_decay(workspace_id=WS, now=T0 + timedelta(days=365))
    assert mc.get(m.memory_id).status == MemoryStatus.ACTIVE.value


# 4c: user confirmation resets age
def test_confirm_resets_age():
    mc = _mc()
    m = mc.add_memory(workspace_id=WS, type=MemoryType.EPISODIC.value, content="Notiz", importance=0.2, now=T0)
    old_eff = mc.effective_confidence(m.memory_id, now=T0 + timedelta(days=28))
    mc.confirm(m.memory_id, now=T0 + timedelta(days=28))
    new_eff = mc.effective_confidence(m.memory_id, now=T0 + timedelta(days=28))
    assert new_eff > old_eff


# 5: sensitive memories protected (not grouped/consolidated away)
def test_sensitive_protected():
    mc = _mc()
    s1 = mc.add_memory(workspace_id=WS, type=MemoryType.CONTACT.value,
                       content="Gehalt von Anna ist vertraulich", sensitive=True, now=T0)
    s2 = mc.add_memory(workspace_id=WS, type=MemoryType.CONTACT.value,
                       content="Gehalt von Anna ist vertraulich", sensitive=True, now=T0)
    assert mc.find_duplicates(workspace_id=WS) == []  # sensitive never grouped
    mc.apply_decay(workspace_id=WS, now=T0 + timedelta(days=999))
    assert mc.get(s1.memory_id).status == MemoryStatus.ACTIVE.value


# 6: privacy mode blocks writes
def test_privacy_mode_blocks():
    mc = MemoryConsolidator(privacy_mode=True)
    with pytest.raises(PermissionError):
        mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="x")
    with pytest.raises(PermissionError):
        mc.apply_correction(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="y", supersedes=[])


# 7: consolidation is idempotent
def test_consolidation_idempotent():
    mc = _mc()
    mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Team nutzt Jira taeglich", now=T0)
    mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Team nutzt Jira jeden Tag", now=T0)
    r1 = mc.consolidate(workspace_id=WS, now=T0)
    active1 = mc.export(workspace_id=WS)
    r2 = mc.consolidate(workspace_id=WS, now=T0)
    active2 = mc.export(workspace_id=WS)
    assert r2["merged"] == 0
    assert active1 == active2


# 8: evidence preserved after consolidation
def test_evidence_preserved():
    mc = _mc()
    a = mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Kunde bevorzugt Rechnung per Mail",
                      source_ids=["doc-1"], evidence=[{"source_id": "doc-1"}], now=T0)
    b = mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="Kunde will Rechnung per Mail",
                      source_ids=["doc-2"], evidence=[{"source_id": "doc-2"}], now=T0)
    mc.consolidate(workspace_id=WS, now=T0)
    winner = next(m for m in mc.memories(workspace_id=WS, status=MemoryStatus.ACTIVE.value))
    assert {"doc-1", "doc-2"} <= set(winner.source_ids)
    assert len(winner.evidence) == 2


# 9: delete requires approval
def test_delete_requires_approval():
    mc = _mc()
    m = mc.add_memory(workspace_id=WS, type=MemoryType.TASK.value, content="temp", now=T0)
    prep = mc.prepare_delete(m.memory_id, workspace_id=WS)
    assert prep["status"] == "approval_required"
    assert mc.get(m.memory_id) is not None
    assert mc.commit_delete(prep, approved=False)["status"] == "blocked"
    assert mc.commit_delete(prep, approved=True)["status"] == "committed"
    assert mc.get(m.memory_id) is None
    assert mc.commit_delete(prep, approved=True)["status"] == "duplicate"


# 10: export contains full provenance
def test_export_full_provenance():
    mc = _mc()
    mc.add_memory(workspace_id=WS, type=MemoryType.PROJECT.value, content="SecondBrain Ziel Q3",
                  source_ids=["s-1"], evidence=[{"source_id": "s-1", "snippet": "Ziel Q3"}], now=T0)
    export = mc.export(workspace_id=WS)
    assert export and "provenance" in export[0]
    prov = export[0]["provenance"]
    assert prov["source_ids"] == ["s-1"] and prov["evidence"]


# 10b: no_memory absolute - never stored active nor exported
def test_no_memory_absolute():
    mc = _mc()
    m = mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="nicht merken",
                      no_memory=True, now=T0)
    assert m.status == MemoryStatus.BLOCKED.value
    assert mc.export(workspace_id=WS, include_blocked=True) == []


# secret content auto-blocked
def test_secret_blocked():
    mc = _mc()
    m = mc.add_memory(workspace_id=WS, type=MemoryType.SYSTEM.value,
                      content="token=sk-abcdef1234567890", now=T0)
    assert m.status == MemoryStatus.BLOCKED.value


# workspace isolation
def test_workspace_isolation():
    mc = _mc()
    mc.add_memory(workspace_id=WS, type=MemoryType.SEMANTIC.value, content="A", now=T0)
    mc.add_memory(workspace_id="ws-2", type=MemoryType.SEMANTIC.value, content="A", now=T0)
    assert len(mc.memories(workspace_id=WS)) == 1
    assert mc.find_duplicates(workspace_id=WS) == []


# gui render + sensitive masked
def test_gui_render_masks_sensitive():
    mc = _mc()
    mc.add_memory(workspace_id=WS, type=MemoryType.CONTACT.value, content="Geheim: Gehalt 99999",
                  sensitive=True, now=T0)
    view = MemoryReviewViewModel(mc).build(workspace_id=WS, now=T0)
    html_out = render_memory_html(view)
    assert "99999" not in html_out
    assert "geschützt" in html_out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
