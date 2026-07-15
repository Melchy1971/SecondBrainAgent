"""Sprint 47 acceptance tests - consolidated daily and weekly briefing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from secondbrain.briefing.models import Briefing, BriefingKind, Priority, SectionStatus
from secondbrain.briefing.service import BriefingBuilder
from secondbrain.briefing.gui import BriefingViewModel, render_briefing_html

WS = "ws-1"
NOW = datetime(2026, 7, 14, 6, 0, tzinfo=timezone.utc)
SECRET = "api_key=sk-abcdef012345ABCDEF6789 password=Hunter2Hunter2"


def full_sources():
    return {
        "calendar": {"items": [
            {"text": "Standup 09:00", "source_reference": "ev-1", "bucket": "today",
             "preparation": ["doc-agenda"], "kind": "event"},
            {"text": "Review 11:00", "source_reference": "ev-2", "bucket": "prep",
             "preparation": ["doc-spec"]},
        ]},
        "tasks": {"items": [
            {"text": "Konzept schreiben", "source_reference": "task-1", "bucket": "open"},
            {"text": "Bug fixen", "source_reference": "task-2", "bucket": "overdue", "due": "2026-07-10"},
        ]},
        "projects": {"items": [
            {"text": "SecondBrain blockiert", "source_reference": "prj-1", "bucket": "blocked"},
        ]},
        "mail": {"items": [
            {"text": "Chef: Freigabe nötig", "source_reference": "mail-1", "bucket": "important"},
            {"text": "Warte auf Antwort", "source_reference": "mail-2", "bucket": "followup"},
        ]},
        "approvals": {"items": [
            {"text": "Send an Kunde", "source_reference": "apr-1", "critical": True, "kind": "critical"},
        ]},
        "documents": {"items": [{"text": "Neues Angebot.pdf", "source_reference": "doc-1"}]},
        "reminders": {"items": [{"text": "Wasser trinken", "source_reference": "rem-1"}]},
        "next_actions": {"items": [{"text": "Konzept an Chef", "source_reference": "na-1"}]},
        "system": {"items": []},
    }


def _daily(sources=None, hidden=None, now=NOW):
    b = BriefingBuilder(hidden_references=hidden or [])
    return b, b.build_daily(workspace_id=WS, sources=sources if sources is not None else full_sources(), now=now)


# 1: aggregates all available sources
def test_aggregates_all_sources():
    _, br = _daily()
    ids = {s.section_id for s in br.sections}
    assert {"today_events", "open_tasks", "overdue_tasks", "blocked_projects",
            "important_mail", "follow_ups", "open_approvals", "relevant_documents",
            "reminders", "next_actions"} <= ids
    assert br.kind == BriefingKind.DAILY.value


# 2: missing connector shown as status
def test_missing_connector_status():
    src = full_sources()
    del src["mail"]  # connector missing entirely
    _, br = _daily(src)
    mail_sections = [s for s in br.sections if s.source == "mail"]
    assert mail_sections
    assert all(s.status == SectionStatus.CONNECTOR_ERROR.value for s in mail_sections)


# 2b: connector error object also -> status
def test_connector_error_object():
    src = full_sources()
    src["calendar"] = {"error": "offline"}
    _, br = _daily(src)
    cal = [s for s in br.sections if s.source == "calendar"]
    assert cal and all(s.status == SectionStatus.CONNECTOR_ERROR.value for s in cal)


# 3: critical approval appears on top
def test_critical_approval_on_top():
    _, br = _daily()
    assert br.sections[0].section_id == "open_approvals"
    assert br.sections[0].priority == Priority.CRITICAL.value


# 4: events contain preparation material
def test_events_have_preparation():
    _, br = _daily()
    ev = next(s for s in br.sections if s.section_id == "today_events")
    assert ev.items[0].preparation == ["doc-agenda"]


# 5: tasks carry source reference
def test_tasks_have_source_reference():
    _, br = _daily()
    ot = next(s for s in br.sections if s.section_id == "open_tasks")
    assert ot.items[0].source_reference == "task-1"
    assert ot.items[0].uncertain is False


# 5b: item without reference is marked uncertain
def test_missing_reference_uncertain():
    src = {"tasks": {"items": [{"text": "Ohne Quelle", "bucket": "open"}]}}
    _, br = _daily(src)
    ot = next(s for s in br.sections if s.section_id == "open_tasks")
    assert ot.items[0].uncertain is True


# 6: no duplicates
def test_no_duplicates():
    src = {"tasks": {"items": [
        {"text": "Doppelt", "source_reference": "t-1", "bucket": "open"},
        {"text": "Doppelt", "source_reference": "t-1", "bucket": "open"},
    ]}}
    _, br = _daily(src)
    ot = next(s for s in br.sections if s.section_id == "open_tasks")
    assert len(ot.items) == 1


# 7: no secrets anywhere
def test_no_secrets():
    src = {"mail": {"items": [{"text": f"Zugang {SECRET}", "source_reference": "m-1", "bucket": "important"}]}}
    b, br = _daily(src)
    blob = b.to_json(br) + b.to_markdown(br) + " ".join(b.notification_preview(br))
    blob += render_briefing_html(BriefingViewModel().build(br))
    assert "sk-abcdef" not in blob and "Hunter2" not in blob


# 8: empty sources don't break briefing
def test_empty_sources_ok():
    b = BriefingBuilder()
    br = b.build_daily(workspace_id=WS, sources={}, now=NOW)
    assert br.sections  # every declared section present
    assert all(s.status == SectionStatus.CONNECTOR_ERROR.value for s in br.sections)
    # explicit empty list -> empty status, not crash
    _, br2 = _daily({"tasks": {"items": []}})
    ot = next(s for s in br2.sections if s.section_id == "open_tasks")
    assert ot.status == SectionStatus.EMPTY.value


# 9: reproducible
def test_reproducible():
    b1 = BriefingBuilder(); r1 = b1.build_daily(workspace_id=WS, sources=full_sources(), now=NOW)
    b2 = BriefingBuilder(); r2 = b2.build_daily(workspace_id=WS, sources=full_sources(), now=NOW)
    assert BriefingBuilder.to_json(r1) == BriefingBuilder.to_json(r2)


# 10: user can hide entries
def test_hide_entries():
    b, br = _daily()
    n = b.hide_in(br, "task-1")
    assert n == 1
    ot = next(s for s in br.sections if s.section_id == "open_tasks")
    assert all(i.hidden for i in ot.items if i.source_reference == "task-1")
    assert "task-1" not in {i.source_reference for i in ot.visible_items}
    # hidden pre-configured builder excludes at build time
    b2, br2 = _daily(hidden=["task-2"])
    ov = next(s for s in br2.sections if s.section_id == "overdue_tasks")
    assert all(i.hidden for i in ov.items)


# workspace isolation
def test_workspace_isolation():
    src = {"tasks": {"items": [
        {"text": "Mein", "source_reference": "a", "bucket": "open", "workspace_id": WS},
        {"text": "Fremd", "source_reference": "b", "bucket": "open", "workspace_id": "ws-2"},
    ]}}
    _, br = _daily(src)
    ot = next(s for s in br.sections if s.section_id == "open_tasks")
    assert [i.source_reference for i in ot.items] == ["a"]


# weekly briefing builds
def test_weekly_briefing():
    b = BriefingBuilder()
    src = {"goals": {"items": [{"text": "Ziel A", "source_reference": "g-1"}]},
           "risks": {"items": [{"text": "Risiko X", "source_reference": "r-1"}]}}
    br = b.build_weekly(workspace_id=WS, sources=src, now=NOW)
    assert br.kind == BriefingKind.WEEKLY.value
    ids = {s.section_id for s in br.sections}
    assert {"top_goals", "risks", "deadlines", "week_review"} <= ids


# gui tabs + render
def test_gui_view_and_render():
    _, br = _daily()
    view = BriefingViewModel().build(br)
    assert set(view["tabs"]) == {"Heute", "Diese Woche", "Risiken", "Vorbereitung", "Entscheidungen", "Systemstatus"}
    assert view["critical_count"] >= 1
    html_out = render_briefing_html(view)
    assert "Entscheidungen" in html_out and "Systemstatus" in html_out


# no external action surface on briefing object
def test_no_external_action_methods():
    b, br = _daily()
    for attr in ("send", "execute", "commit", "forward", "delete"):
        assert not hasattr(b, attr)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
