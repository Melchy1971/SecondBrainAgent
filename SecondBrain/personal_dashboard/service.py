"""Personal dashboard service.

Assembles independent cards from already-fetched context. Each card is built in
isolation: a failing source yields an ``error`` card, never an exception that
blanks the dashboard. Slow sources are deferred to an async status instead of
blocking the initial render, keeping load time bounded. Visible labels carry no
technical id and no sensitive preview; drill-down uses an opaque reference.
Risky quick actions are never executed - they return an approval-gated intent.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from secondbrain.personal_dashboard.models import (
    CardArea, CardItem, CardStatus, DashboardCard, DashboardConfig, DEFAULT_CARD_ORDER,
)

__all__ = ["Dashboard", "redact_dashboard_text"]

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*", re.IGNORECASE),
    re.compile(r"(?i)[\w.\-]*(?:api[\s_-]?key|apikey|token|secret|password|passwd|credential(?:s)?)\s*[:=]\s*[^\s,;\"']+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
_RISKY_ACTIONS = {"send_reply", "send_message", "delete", "archive", "forward", "run_restore"}


def redact_dashboard_text(text: str) -> str:
    out = text or ""
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


class Dashboard:
    # card_id -> (title, area, builder_method_name, slow)
    _CARDS: dict[str, tuple[str, str, str, bool]] = {
        "next_up": ("Als Nächstes", CardArea.HEUTE.value, "_card_next_up", False),
        "open_approvals": ("Offene Approvals", CardArea.ENTSCHEIDUNGEN.value, "_card_approvals", False),
        "tasks": ("Aufgaben", CardArea.ARBEIT.value, "_card_tasks", False),
        "calendar": ("Kalender", CardArea.HEUTE.value, "_card_calendar", False),
        "important_mail": ("Wichtige E-Mails", CardArea.KOMMUNIKATION.value, "_card_mail", False),
        "projects": ("Projekte", CardArea.ARBEIT.value, "_card_projects", False),
        "suggestions": ("Vorschläge", CardArea.ENTSCHEIDUNGEN.value, "_card_suggestions", False),
        "documents": ("Dokumente", CardArea.WISSEN.value, "_card_documents", True),
        "knowledge": ("Wissen", CardArea.WISSEN.value, "_card_knowledge", False),
        "system": ("Systemstatus", CardArea.SYSTEM.value, "_card_system", False),
        "recent_activity": ("Letzte Aktivitäten", CardArea.HEUTE.value, "_card_recent", False),
    }

    def __init__(self, *, slow_cards: Sequence[str] | None = None) -> None:
        # cache of the last build per workspace (local cache / fast refresh)
        self._cache: dict[str, list[DashboardCard]] = {}
        self._slow_override = set(slow_cards) if slow_cards is not None else None

    def default_config(self, *, workspace_id: str) -> DashboardConfig:
        order = list(DEFAULT_CARD_ORDER)
        return DashboardConfig(enabled=order, order=order, timeframe="today", workspace_id=workspace_id)

    # -- build ------------------------------------------------------------

    def build(self, *, config: DashboardConfig, context: Mapping[str, Any],
              now: datetime | None = None, defer_slow: bool = True) -> list[DashboardCard]:
        moment = now or _now()
        cards: list[DashboardCard] = []
        order = config.order or list(self._CARDS)
        for card_id in order:
            if config.enabled and card_id not in config.enabled:
                continue
            spec = self._CARDS.get(card_id)
            if spec is None:
                continue
            title, area, builder, slow = spec
            is_slow = slow if self._slow_override is None else (card_id in self._slow_override)
            card = DashboardCard(card_id=card_id, title=title, area=area)
            if is_slow and defer_slow:
                card.status = CardStatus.LOADING.value  # async, does not block render
                cards.append(card)
                continue
            self._safe_build(card, builder, config, context, moment)
            cards.append(card)
        self._cache[config.workspace_id] = cards
        return cards

    def resolve_async(self, *, card_id: str, config: DashboardConfig, context: Mapping[str, Any],
                      now: datetime | None = None) -> DashboardCard:
        spec = self._CARDS[card_id]
        card = DashboardCard(card_id=card_id, title=spec[0], area=spec[1])
        self._safe_build(card, spec[2], config, context, now or _now())
        return card

    def refresh(self, *, config: DashboardConfig, context: Mapping[str, Any],
                now: datetime | None = None) -> list[DashboardCard]:
        self._cache.pop(config.workspace_id, None)
        return self.build(config=config, context=context, now=now)

    def cached(self, *, workspace_id: str) -> list[DashboardCard] | None:
        return self._cache.get(workspace_id)

    def _safe_build(self, card: DashboardCard, builder: str, config: DashboardConfig,
                    context: Mapping[str, Any], moment: datetime) -> None:
        try:
            items = getattr(self, builder)(config, context, moment)
        except Exception as exc:  # noqa: BLE001 - fault isolation is the whole point
            card.status = CardStatus.ERROR.value
            card.error = f"{type(exc).__name__}: {exc}"
            return
        card.items = items
        card.status = CardStatus.OK.value if items else CardStatus.EMPTY.value

    # -- source access (raises on connector error -> isolated per card) --

    def _source(self, context: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
        raw = context.get(key, [])
        if isinstance(raw, Mapping) and raw.get("error"):
            raise RuntimeError(f"connector_error:{raw['error']}")
        if isinstance(raw, Mapping):
            return list(raw.get("items", []))
        return list(raw)

    def _ws(self, items: Sequence[Mapping[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
        return [dict(i) for i in items if i.get("workspace_id") in (None, "", workspace_id)]

    @staticmethod
    def _item(label: str, reference: str = "", detail: str = "", badge: str = "",
              approval_required: bool = False) -> CardItem:
        return CardItem(label=redact_dashboard_text(label), reference=reference,
                        detail=redact_dashboard_text(detail), badge=badge, approval_required=approval_required)

    # -- card builders ----------------------------------------------------

    def _card_tasks(self, config, context, moment):
        tasks = self._ws(self._source(context, "tasks"), config.workspace_id)
        return [self._item(t.get("title", ""), reference=t.get("id", ""),
                           badge="überfällig" if self._overdue(t, moment) else "")
                for t in self._rank_tasks(tasks, moment)]

    def _card_calendar(self, config, context, moment):
        events = self._ws(self._source(context, "events"), config.workspace_id)
        events.sort(key=lambda e: str(e.get("start", "")))
        return [self._item(e.get("title", ""), reference=e.get("id", ""), detail=str(e.get("start", "")))
                for e in events]

    def _card_mail(self, config, context, moment):
        mail = self._ws(self._source(context, "mail"), config.workspace_id)
        return [self._item(m.get("subject", ""), reference=m.get("id", ""),
                           badge="Follow-up" if m.get("awaiting_reply") else "")
                for m in mail if m.get("important") or m.get("awaiting_reply")]

    def _card_projects(self, config, context, moment):
        projects = self._ws(self._source(context, "projects"), config.workspace_id)
        return [self._item(p.get("name", ""), reference=p.get("id", ""),
                           badge="blockiert" if p.get("blocked") else "")
                for p in projects]

    def _card_approvals(self, config, context, moment):
        approvals = self._ws(self._source(context, "approvals"), config.workspace_id)
        approvals.sort(key=lambda a: 0 if a.get("critical") else 1)
        return [self._item(a.get("title", "Freigabe"), reference=a.get("id", ""),
                           badge="kritisch" if a.get("critical") else "", approval_required=True)
                for a in approvals]

    def _card_suggestions(self, config, context, moment):
        sugs = self._ws(self._source(context, "suggestions"), config.workspace_id)
        return [self._item(s.get("title", ""), reference=s.get("id", ""), detail=str(s.get("priority", "")))
                for s in sugs]

    def _card_documents(self, config, context, moment):
        docs = self._ws(self._source(context, "documents"), config.workspace_id)
        return [self._item(d.get("name", ""), reference=d.get("id", "")) for d in docs]

    def _card_knowledge(self, config, context, moment):
        conflicts = self._ws(self._source(context, "knowledge_conflicts"), config.workspace_id)
        return [self._item(f"Konflikt: {c.get('subject','')}", reference=c.get("id", ""), badge="Konflikt")
                for c in conflicts]

    def _card_system(self, config, context, moment):
        system = context.get("system", {}) or {}
        items = []
        for name, ok in system.items():
            items.append(self._item(name, detail="ok" if ok else "Fehler",
                                     badge="" if ok else "Fehler"))
        return items

    def _card_recent(self, config, context, moment):
        recent = self._ws(self._source(context, "recent"), config.workspace_id)
        return [self._item(r.get("text", ""), reference=r.get("id", "")) for r in recent]

    def _card_next_up(self, config, context, moment):
        # aggregate the single most important thing: critical approval > overdue
        # task > next task > next event
        approvals = self._ws(self._source(context, "approvals"), config.workspace_id)
        crit = [a for a in approvals if a.get("critical")]
        if crit:
            return [self._item(crit[0].get("title", "Kritische Freigabe"),
                               reference=crit[0].get("id", ""), badge="kritisch", approval_required=True)]
        tasks = self._rank_tasks(self._ws(self._source(context, "tasks"), config.workspace_id), moment)
        if tasks:
            t = tasks[0]
            return [self._item(t.get("title", ""), reference=t.get("id", ""),
                               badge="überfällig" if self._overdue(t, moment) else "nächste Aufgabe")]
        events = sorted(self._ws(self._source(context, "events"), config.workspace_id),
                        key=lambda e: str(e.get("start", "")))
        if events:
            return [self._item(events[0].get("title", ""), reference=events[0].get("id", ""),
                               detail=str(events[0].get("start", "")))]
        return []

    # -- interactions -----------------------------------------------------

    def quick_action(self, *, action: str, reference: str, workspace_id: str) -> dict[str, Any]:
        risky = action in _RISKY_ACTIONS
        return {
            "action": action, "reference": reference, "workspace_id": workspace_id,
            "executed": False,  # dashboard never executes; hands off to the owning service
            "approval_required": risky,
            "route": "approval_inbox" if risky else "detail_view",
        }

    def drill_down(self, *, card_id: str, reference: str) -> dict[str, Any]:
        area = self._CARDS.get(card_id, ("", "", "", False))[1]
        view_map = {
            "tasks": "task_detail", "next_up": "task_detail", "calendar": "calendar_detail",
            "important_mail": "mail_thread", "projects": "project_detail",
            "open_approvals": "approval_detail", "suggestions": "suggestion_detail",
            "documents": "document_view", "knowledge": "graph_explorer",
            "system": "system_status", "recent_activity": "activity_detail",
        }
        return {"view": view_map.get(card_id, "detail"), "reference": reference, "area": area}

    def global_search(self, *, query: str, context: Mapping[str, Any], workspace_id: str) -> list[dict[str, Any]]:
        q = query.strip().lower()
        hits: list[dict[str, Any]] = []
        if not q:
            return hits
        for key, label_field, card in (("tasks", "title", "tasks"), ("events", "title", "calendar"),
                                       ("mail", "subject", "important_mail"),
                                       ("projects", "name", "projects"), ("documents", "name", "documents")):
            try:
                items = self._ws(self._source(context, key), workspace_id)
            except RuntimeError:
                continue
            for it in items:
                label = str(it.get(label_field, ""))
                if q in label.lower():
                    hits.append({"label": redact_dashboard_text(label), "card": card,
                                 "reference": it.get("id", "")})
        return hits

    @staticmethod
    def command_palette() -> list[dict[str, str]]:
        return [
            {"command": "refresh", "label": "Aktualisieren"},
            {"command": "switch_workspace", "label": "Workspace wechseln"},
            {"command": "configure_cards", "label": "Karten konfigurieren"},
            {"command": "search", "label": "Globale Suche"},
            {"command": "timeframe", "label": "Zeitraum wählen"},
        ]

    # -- ranking helpers --------------------------------------------------

    def _rank_tasks(self, tasks: Sequence[Mapping[str, Any]], moment: datetime) -> list[dict[str, Any]]:
        def score(t: Mapping[str, Any]) -> tuple[int, str]:
            overdue = 0 if self._overdue(t, moment) else 1
            return (overdue, str(t.get("due", "~")))
        return sorted([dict(t) for t in tasks], key=score)

    @staticmethod
    def _overdue(task: Mapping[str, Any], moment: datetime) -> bool:
        due = _parse(task.get("due"))
        return due is not None and due < moment and not task.get("done")
