"""Sprint 53 acceptance tests - unified personal dashboard."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from secondbrain.personal_dashboard.models import CardStatus, DashboardConfig, DEFAULT_CARD_ORDER
from secondbrain.personal_dashboard.service import Dashboard
from secondbrain.personal_dashboard.gui import DashboardViewModel, render_dashboard_html

WS = "ws-1"
NOW = datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc)


def _cfg(**over):
    order = list(DEFAULT_CARD_ORDER)
    d = dict(enabled=order, order=order, timeframe="today", workspace_id=WS)
    d.update(over)
    return DashboardConfig(**d)


def _ctx(**over):
    ctx = {"tasks": [], "events": [], "mail": [], "projects": [], "approvals": [],
           "suggestions": [], "documents": [], "knowledge_conflicts": [], "recent": [], "system": {}}
    ctx.update(over)
    return ctx


def _card(cards, cid):
    return next(c for c in cards if c.card_id == cid)


# 1: dashboard starts on empty data
def test_starts_empty():
    d = Dashboard()
    cards = d.build(config=_cfg(), context=_ctx(), now=NOW)
    assert cards  # all configured cards present
    assert all(c.status in (CardStatus.EMPTY.value, CardStatus.OK.value, CardStatus.LOADING.value) for c in cards)


# 2: broken connector does not block other cards
def test_broken_connector_isolated():
    d = Dashboard(slow_cards=[])  # nothing deferred so all build synchronously
    ctx = _ctx(mail={"error": "offline"},
               tasks=[{"id": "t-1", "title": "Konzept", "due": "2026-07-10"}])
    cards = d.build(config=_cfg(), context=ctx, now=NOW)
    mail = _card(cards, "important_mail")
    tasks = _card(cards, "tasks")
    assert mail.status == CardStatus.ERROR.value and mail.error
    assert tasks.status == CardStatus.OK.value and tasks.items  # unaffected


# 3: critical approval visible (and next_up surfaces it)
def test_critical_approval_visible():
    d = Dashboard()
    ctx = _ctx(approvals=[{"id": "a-1", "title": "Send an Kunde", "critical": True}])
    cards = d.build(config=_cfg(), context=ctx, now=NOW)
    nxt = _card(cards, "next_up")
    assert nxt.items and nxt.items[0].badge == "kritisch"
    appr = _card(cards, "open_approvals")
    assert appr.items[0].approval_required is True


# 4: next task correctly prioritized (overdue first)
def test_next_task_prioritized():
    d = Dashboard()
    ctx = _ctx(tasks=[
        {"id": "t-future", "title": "Später", "due": "2026-07-20"},
        {"id": "t-over", "title": "Überfällig", "due": "2026-07-01"}])
    cards = d.build(config=_cfg(), context=ctx, now=NOW)
    nxt = _card(cards, "next_up")
    assert nxt.items[0].reference == "t-over"
    assert nxt.items[0].badge == "überfällig"


# 5: calendar and mail aggregated
def test_calendar_and_mail_aggregated():
    d = Dashboard()
    ctx = _ctx(events=[{"id": "e-1", "title": "Standup", "start": "2026-07-14T09:00"}],
               mail=[{"id": "m-1", "subject": "Wichtig", "important": True}])
    cards = d.build(config=_cfg(), context=ctx, now=NOW)
    assert _card(cards, "calendar").items[0].reference == "e-1"
    assert _card(cards, "important_mail").items[0].reference == "m-1"


# 6: cards are configurable (enable subset + reorder)
def test_cards_configurable():
    d = Dashboard()
    cfg = _cfg(enabled=["tasks", "calendar"], order=["calendar", "tasks"])
    cards = d.build(config=cfg, context=_ctx(), now=NOW)
    assert [c.card_id for c in cards] == ["calendar", "tasks"]


# 7: workspace switch works
def test_workspace_switch():
    d = Dashboard()
    ctx = _ctx(tasks=[{"id": "a", "title": "Mein", "workspace_id": WS},
                      {"id": "b", "title": "Fremd", "workspace_id": "ws-2"}])
    mine = d.build(config=_cfg(workspace_id=WS), context=ctx, now=NOW)
    assert [i.reference for i in _card(mine, "tasks").items] == ["a"]
    other = d.build(config=_cfg(workspace_id="ws-2"), context=ctx, now=NOW)
    assert [i.reference for i in _card(other, "tasks").items] == ["b"]


# 8: no secrets in visible labels
def test_no_secrets():
    d = Dashboard(slow_cards=[])
    ctx = _ctx(mail=[{"id": "m-1", "subject": "Zugang api_key=sk-abcdef012345ABCDEF", "important": True}])
    cards = d.build(config=_cfg(), context=ctx, now=NOW)
    html_out = render_dashboard_html(DashboardViewModel().build(cards))
    assert "sk-abcdef" not in html_out


# 9: load time bounded - slow source deferred, does not block
def test_slow_source_deferred():
    d = Dashboard()  # documents is slow by default
    def boom(_):
        raise AssertionError("slow source must not run synchronously")
    class Ctx(dict):
        def get(self, k, default=None):
            if k == "documents":
                boom(k)
            return super().get(k, default)
    ctx = Ctx(_ctx())
    cards = d.build(config=_cfg(), context=ctx, now=NOW)  # must not raise
    docs = _card(cards, "documents")
    assert docs.status == CardStatus.LOADING.value
    # resolved on demand (async)
    resolved = d.resolve_async(card_id="documents", config=_cfg(),
                               context=_ctx(documents=[{"id": "d-1", "name": "Angebot.pdf"}]), now=NOW)
    assert resolved.status == CardStatus.OK.value and resolved.items[0].reference == "d-1"


# 10: drill-down opens the correct detail view
def test_drilldown_routes():
    d = Dashboard()
    assert d.drill_down(card_id="important_mail", reference="m-1")["view"] == "mail_thread"
    assert d.drill_down(card_id="tasks", reference="t-1")["view"] == "task_detail"
    assert d.drill_down(card_id="knowledge", reference="k-1")["view"] == "graph_explorer"


# risky quick action requires approval, never executed
def test_quick_action_approval():
    d = Dashboard()
    class Queue:
        def create(self, **_kwargs): return {"approval_id": "approval-1"}
    res = d.quick_action(action="send_reply", reference="m-1", workspace_id=WS, approval_queue=Queue())
    assert res["executed"] is False and res["approval_required"] is True
    assert res["route"] == "approval_inbox"
    assert res["approval_id"] == "approval-1"
    safe = d.quick_action(action="open", reference="t-1", workspace_id=WS)
    assert safe["approval_required"] is False


# no technical ids in visible labels
def test_no_ids_in_labels():
    d = Dashboard()
    ctx = _ctx(tasks=[{"id": "TASK-INTERNAL-9999", "title": "Konzept schreiben"}])
    cards = d.build(config=_cfg(), context=ctx, now=NOW)
    item = _card(cards, "tasks").items[0]
    assert "TASK-INTERNAL-9999" not in item.label  # id only in reference
    assert item.reference == "TASK-INTERNAL-9999"


# refresh recomputes; cache present
def test_refresh_and_cache():
    d = Dashboard()
    d.build(config=_cfg(), context=_ctx(), now=NOW)
    assert all(card.cached for card in d.cached(workspace_id=WS))
    refreshed = d.refresh(config=_cfg(), context=_ctx(tasks=[{"id": "t", "title": "Neu"}]), now=NOW)
    assert _card(refreshed, "tasks").items


def test_critical_cards_cannot_be_hidden_and_snapshot_contract():
    dashboard = Dashboard(slow_cards=[])
    config = _cfg(enabled=["tasks"], order=["tasks"])
    context = _ctx(approvals=[{"id": "a", "title": "Kritisch", "critical": True}], system={"vault": False})
    snapshot = dashboard.snapshot(config=config, context=context, now=NOW)
    ids = {card.card_id for card in snapshot.cards}
    assert {"open_approvals", "system", "tasks"} <= ids
    assert snapshot.to_dict()["source_status"]["system"] == CardStatus.OK.value


# global search + command palette
def test_search_and_palette():
    d = Dashboard()
    ctx = _ctx(tasks=[{"id": "t-1", "title": "Konzept SecondBrain"}],
               documents=[{"id": "d-1", "name": "SecondBrain Spec"}])
    hits = d.global_search(query="secondbrain", context=ctx, workspace_id=WS)
    assert {h["card"] for h in hits} >= {"tasks", "documents"}
    assert any(c["command"] == "refresh" for c in d.command_palette())


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
