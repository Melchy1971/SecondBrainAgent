"""Briefing GUI view model and headless HTML renderer.

The view model groups sections into the six GUI tabs (Heute, Diese Woche,
Risiken, Vorbereitung, Entscheidungen, Systemstatus). Only visible (non-hidden)
items are exposed and every rendered string is secret-redacted. No technical
identifier is shown in overview text; ``source_reference`` is kept solely to let
the GUI open the underlying record on drill-down.
"""

from __future__ import annotations

import html
from typing import Any

from secondbrain.briefing.models import Briefing, SectionStatus
from secondbrain.briefing.service import redact_briefing_text

__all__ = ["BriefingViewModel", "render_briefing_html"]

_TABS: dict[str, tuple[str, ...]] = {
    "Heute": ("today_events", "meeting_prep", "open_tasks", "overdue_tasks",
              "important_mail", "follow_ups", "reminders", "next_actions", "relevant_documents"),
    "Diese Woche": ("top_goals", "deadlines", "project_progress", "completed_tasks",
                    "deferred_tasks", "week_review"),
    "Risiken": ("blocked_projects", "risks", "conflicts", "connector_errors"),
    "Vorbereitung": ("meeting_prep",),
    "Entscheidungen": ("open_approvals", "open_decisions"),
    "Systemstatus": ("connector_errors",),
}


class BriefingViewModel:
    def build(self, briefing: Briefing) -> dict[str, Any]:
        by_id = {s.section_id: s for s in briefing.sections}
        tabs: dict[str, list[dict[str, Any]]] = {}
        for tab, ids in _TABS.items():
            blocks = []
            for sid in ids:
                section = by_id.get(sid)
                if section is None:
                    continue
                blocks.append({
                    "title": section.title,
                    "priority": section.priority,
                    "status": section.status,
                    "confidence": section.confidence,
                    "items": [self._item(i) for i in section.visible_items],
                })
            tabs[tab] = blocks
        return {
            "kind": briefing.kind,
            "generated_at": briefing.generated_at,
            "tabs": tabs,
            "critical_count": sum(1 for s in briefing.sections if s.priority == "critical" and s.visible_items),
        }

    @staticmethod
    def _item(item: Any) -> dict[str, Any]:
        return {
            "text": redact_briefing_text(item.text),
            "uncertain": item.uncertain,
            "due": item.due,
            "has_preparation": bool(item.preparation),
            "source": item.source,
            # source_reference retained for drill-down, not for display text
            "source_reference": item.source_reference,
        }


def render_briefing_html(view: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value))

    sections_html = []
    for tab, blocks in view["tabs"].items():
        parts = [f"<section><h2>{esc(tab)}</h2>"]
        if not blocks:
            parts.append("<p class='empty'>keine Daten</p>")
        for block in blocks:
            badge = "" if block["status"] == SectionStatus.OK.value else f"<span class='status {esc(block['status'])}'>{esc(block['status'])}</span>"
            parts.append(f"<div class='block p-{esc(block['priority'])}'><h3>{esc(block['title'])} {badge}</h3>")
            if not block["items"]:
                parts.append("<p class='empty'>–</p>")
            else:
                parts.append("<ul>")
                for it in block["items"]:
                    unc = " <em>(unsicher)</em>" if it["uncertain"] else ""
                    due = f" <small>fällig {esc(it['due'])}</small>" if it["due"] else ""
                    prep = " 📎" if it["has_preparation"] else ""
                    parts.append(f"<li>{esc(it['text'])}{due}{prep}{unc}</li>")
                parts.append("</ul>")
            parts.append("</div>")
        parts.append("</section>")
        sections_html.append("".join(parts))

    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Tagesbriefing</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f5f5f7}}
h1{{color:#e20074}}
section{{margin-bottom:24px}}
h2{{border-bottom:2px solid #e20074;padding-bottom:4px}}
.block{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:10px 12px;margin:8px 0}}
.block.p-critical{{border-left:5px solid #c0142c}}
.block.p-high{{border-left:5px solid #e20074}}
.status{{font-size:11px;padding:2px 6px;border-radius:10px;background:#eee;color:#555}}
.status.connector_error{{background:#fde2e2;color:#c0142c}}
.status.uncertain{{background:#fff4d6;color:#8a6d00}}
.empty{{color:#999;font-style:italic}}
small{{color:#666}}
</style></head><body>
<h1>Briefing – {esc(view['kind'])} <small>{esc(view['generated_at'])}</small></h1>
{"".join(sections_html)}
</body></html>"""
