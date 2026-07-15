"""Sprint 52 acceptance tests - evidence-based proactive suggestions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.proactive.models import Priority, SuggestionCategory, SuggestionStatus
from secondbrain.proactive.service import ProactiveEngine, redact_suggestion_text
from secondbrain.proactive.gui import ProactiveViewModel, render_suggestions_html

WS = "ws-1"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _eng():
    return ProactiveEngine()


def _ctx(**over):
    ctx = {"tasks": [], "events": [], "mail": [], "projects": [], "contracts": [],
           "connectors": [], "approvals": [], "knowledge_conflicts": [], "recurring": [], "backup": {}}
    ctx.update(over)
    return ctx


# 1: deadline risk detected
def test_deadline_risk_detected():
    e = _eng()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-01-02", "started": False}])
    sugs = e.generate(workspace_id=WS, context=ctx, now=T0)
    assert any(s.category == SuggestionCategory.DEADLINE_RISK.value for s in sugs)


# 2: evidence visible
def test_evidence_visible():
    e = _eng()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-01-02", "started": False}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    assert s.evidence and s.evidence[0]["source_id"] == "t-1"


# 3: dismiss prevents repeat within cooldown
def test_dismiss_cooldown():
    e = _eng()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-01-02", "started": False}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    e.dismiss(s.suggestion_id, now=T0, cooldown_days=7)
    again = e.generate(workspace_id=WS, context=ctx, now=T0 + timedelta(days=2))
    assert all(x.category != SuggestionCategory.DEADLINE_RISK.value for x in again)  # suppressed
    later = e.generate(workspace_id=WS, context=ctx, now=T0 + timedelta(days=8))
    assert any(x.category == SuggestionCategory.DEADLINE_RISK.value for x in later)  # cooldown over


# 4: snooze works
def test_snooze():
    e = _eng()
    ctx = _ctx(projects=[{"id": "p-1", "name": "X", "blocked_days": 10}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    e.snooze(s.suggestion_id, until=T0 + timedelta(days=5))
    hidden = e.generate(workspace_id=WS, context=ctx, now=T0 + timedelta(days=1))
    assert hidden == []
    shown = e.generate(workspace_id=WS, context=ctx, now=T0 + timedelta(days=6))
    assert shown


# 5: accepted only creates a task/plan, no direct external action
def test_accept_no_direct_external():
    e = _eng()
    ctx = _ctx(mail=[{"id": "m-1", "subject": "Frage", "awaiting_reply": True}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    intent = e.accept(s.suggestion_id)
    assert intent["executed"] is False
    assert intent["created"] in ("task", "plan", "review", "job", "automation")
    # this one has an external effect -> must be approval-gated, not executed
    assert intent["external_action"] is True
    assert intent["approval_required"] is True


# 6: low confidence never shown as critical
def test_low_confidence_not_critical():
    e = _eng()
    ctx = _ctx(recurring=[{"id": "r-1", "name": "manuell", "occurrences": 5}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    assert s.confidence < 0.6
    assert s.priority in (Priority.LOW.value, Priority.MEDIUM.value)
    assert s.priority != Priority.CRITICAL.value


# 7: no duplicates
def test_no_duplicates():
    e = _eng()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-01-02", "started": False}])
    e.generate(workspace_id=WS, context=ctx, now=T0)
    second = e.generate(workspace_id=WS, context=ctx, now=T0)  # same context again
    assert second == []  # already suggested, deduped


# 8: no secrets in suggestion or notification
def test_no_secrets():
    e = _eng()
    ctx = _ctx(mail=[{"id": "m-1", "subject": "Zugang api_key=sk-abcdef012345ABCDEF", "awaiting_reply": True}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    assert "sk-abcdef" not in s.title
    assert "sk-abcdef" not in e.notification_preview(s)


# 9: user can disable a rule
def test_disable_rule():
    e = _eng()
    e.disable_rule(SuggestionCategory.DEADLINE_RISK.value)
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-01-02", "started": False}])
    sugs = e.generate(workspace_id=WS, context=ctx, now=T0)
    assert all(s.category != SuggestionCategory.DEADLINE_RISK.value for s in sugs)


# 10: feedback stored auditably
def test_feedback_audited():
    e = _eng()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-01-02", "started": False}])
    s = e.generate(workspace_id=WS, context=ctx, now=T0)[0]
    e.accept(s.suggestion_id)
    e2 = e.generate(workspace_id=WS, context=_ctx(projects=[{"id": "p-1", "name": "X", "blocked_days": 9}]), now=T0)[0]
    e.dismiss(e2.suggestion_id, now=T0)
    log = e.feedback_log()
    assert {r.action for r in log} >= {"accepted", "dismissed"}
    assert all(r.suggestion_id and r.category for r in log)


# dismiss dampens future priority for that category
def test_dismiss_dampens_priority():
    e = _eng()
    conn = [{"name": "Jira", "error_count": 5}]
    for i in range(2):
        s = e.generate(workspace_id=WS, context=_ctx(connectors=conn), now=T0 + timedelta(days=10 * i))[0]
        assert s.priority == Priority.CRITICAL.value
        e.dismiss(s.suggestion_id, now=T0 + timedelta(days=10 * i), cooldown_days=1)
    s3 = e.generate(workspace_id=WS, context=_ctx(connectors=conn), now=T0 + timedelta(days=30))[0]
    assert s3.priority == Priority.HIGH.value  # damped from critical after repeated dismiss


# workspace isolation
def test_workspace_isolation():
    e = _eng()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "A", "due": "2026-01-02", "started": False}])
    e.generate(workspace_id=WS, context=ctx, now=T0)
    other = e.generate(workspace_id="ws-2", context=ctx, now=T0)
    assert other  # different workspace -> not deduped against ws-1


# gui render with why + no secrets
def test_gui_render():
    e = _eng()
    ctx = _ctx(contracts=[{"id": "c-1", "name": "Wartung", "expires": "2026-01-20"}])
    e.generate(workspace_id=WS, context=ctx, now=T0)
    view = ProactiveViewModel(e).build(workspace_id=WS)
    assert view["suggestions"] and view["suggestions"][0]["why"]
    html_out = render_suggestions_html(view)
    assert "Warum sehe ich das?" in html_out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
