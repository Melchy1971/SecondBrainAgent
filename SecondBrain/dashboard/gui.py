"""Personal dashboard GUI view model and headless HTML renderer.

Renders cards grouped by area. Every card shows its own status badge so a broken
or still-loading source is visible without hiding the rest. Labels are already
redacted by the service; the renderer only escapes for HTML safety.
"""

from __future__ import annotations

import html
from typing import Any, Sequence

from secondbrain.dashboard.models import CardStatus, DashboardCard

__all__ = ["DashboardViewModel", "render_dashboard_html"]


class DashboardViewModel:
    def build(self, cards: Sequence[DashboardCard]) -> dict[str, Any]:
        areas: dict[str, list[dict[str, Any]]] = {}
        for card in cards:
            areas.setdefault(card.area, []).append({
                "title": card.title,
                "status": card.status,
                "error": card.error,
                "items": [i.to_dict() for i in card.items],
                "card_id": card.card_id,
            })
        critical = any(
            i.get("badge") == "kritisch"
            for c in cards for i in [it.to_dict() for it in c.items])
        return {"areas": areas, "critical_present": critical,
                "card_count": len(cards),
                "error_cards": [c.card_id for c in cards if c.status == CardStatus.ERROR.value]}


def render_dashboard_html(view: dict[str, Any]) -> str:
    def esc(v: Any) -> str:
        return html.escape(str(v))

    sections = []
    for area, cards in view["areas"].items():
        blocks = []
        for c in cards:
            badge = "" if c["status"] == "ok" else f"<span class='st st-{esc(c['status'])}'>{esc(c['status'])}</span>"
            if c["status"] == "error":
                body = f"<p class='err'>Quelle nicht verfügbar</p>"
            elif c["status"] == "loading":
                body = "<p class='load'>lädt …</p>"
            elif not c["items"]:
                body = "<p class='empty'>keine Einträge</p>"
            else:
                lis = "".join(
                    f"<li>{esc(i['label'])}"
                    f"{' <b>' + esc(i['badge']) + '</b>' if i['badge'] else ''}"
                    f"{' 🔒' if i['approval_required'] else ''}</li>"
                    for i in c["items"])
                body = f"<ul>{lis}</ul>"
            blocks.append(f"<div class='card'><h3>{esc(c['title'])} {badge}</h3>{body}</div>")
        sections.append(f"<section><h2>{esc(area)}</h2>{''.join(blocks)}</section>")
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Dashboard</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f5f5f7}}
h1{{color:#e20074}}
section{{margin-bottom:20px}}
h2{{border-bottom:2px solid #e20074;padding-bottom:3px;text-transform:capitalize}}
.card{{display:inline-block;vertical-align:top;width:300px;background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:8px 12px;margin:6px}}
.st{{font-size:11px;padding:1px 6px;border-radius:10px}}
.st-error{{background:#fde2e2;color:#c0142c}}
.st-loading{{background:#eef;color:#3a4b8a}}
.st-empty{{background:#eee;color:#777}}
.err{{color:#c0142c}}.load{{color:#3a4b8a}}.empty{{color:#999;font-style:italic}}
</style></head><body>
<h1>Persönliches Dashboard</h1>
<p>Karten: {esc(view['card_count'])} · Fehlerkarten: {esc(len(view['error_cards']))} · kritisch: {esc(view['critical_present'])}</p>
{''.join(sections)}
</body></html>"""
