"""Proactive suggestions GUI view model and headless HTML renderer.

Each card includes a "Warum sehe ich das?" explanation built from the
suggestion's evidence and confidence, plus accept/dismiss/snooze/disable-rule
controls. Notification-style text is secret-free.
"""

from __future__ import annotations

import html
from typing import Any

from secondbrain.proactive.service import ProactiveEngine

__all__ = ["ProactiveViewModel", "render_suggestions_html"]


class ProactiveViewModel:
    def __init__(self, engine: ProactiveEngine) -> None:
        self.engine = engine

    def build(self, *, workspace_id: str) -> dict[str, Any]:
        cards = []
        for s in sorted(self.engine.active(workspace_id=workspace_id),
                        key=lambda x: -x.confidence):
            cards.append({
                "suggestion_id": s.suggestion_id,
                "category": s.category,
                "title": s.title,
                "priority": s.priority,
                "confidence": s.confidence,
                "why": self._why(s),
                "evidence": s.evidence,
                "proposed_action": s.proposed_action,
                "actions": ["accept", "dismiss", "snooze", "disable_rule", "open_source", "show_plan"],
            })
        return {"suggestions": cards,
                "disabled_rules": sorted(self.engine.disabled_rules),
                "feedback_count": len(self.engine.feedback_log())}

    @staticmethod
    def _why(s: Any) -> str:
        n = len(s.evidence)
        return f"{s.category}: {n} Beleg(e), Confidence {round(s.confidence, 2)}"


def render_suggestions_html(view: dict[str, Any]) -> str:
    def esc(v: Any) -> str:
        return html.escape(str(v))

    cards = []
    for c in view["suggestions"]:
        ev = "".join(f"<li>{esc(e)}</li>" for e in c["evidence"])
        cards.append(
            f"<div class='card p-{esc(c['priority'])}'>"
            f"<h3>{esc(c['title'])} <span class='pri'>{esc(c['priority'])}</span></h3>"
            f"<details><summary>Warum sehe ich das?</summary><p>{esc(c['why'])}</p><ul>{ev}</ul></details>"
            f"<div class='act'>Akzeptieren · Ablehnen · Snooze · Regel deaktivieren</div></div>")
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Vorschläge</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f6f6f8}}
h1{{color:#e20074}}
.card{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:10px 14px;margin:8px 0}}
.card.p-critical{{border-left:5px solid #c0142c}}
.card.p-high{{border-left:5px solid #e20074}}
.card.p-low{{border-left:5px solid #bbb}}
.pri{{font-size:11px;color:#666}}
.act{{margin-top:6px;font-size:13px;color:#555}}
</style></head><body>
<h1>Proaktive Vorschläge</h1>
<p>Deaktivierte Regeln: {esc(', '.join(view['disabled_rules']) or 'keine')} · Feedback-Einträge: {esc(view['feedback_count'])}</p>
{"".join(cards) or "<p>Keine Vorschläge.</p>"}
</body></html>"""
