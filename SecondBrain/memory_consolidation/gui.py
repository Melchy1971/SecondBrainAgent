"""Memory consolidation GUI view model and headless HTML renderer.

Review surfaces show consolidation candidates, conflicts, decaying memories and
provenance. Sensitive memory bodies are masked in previews; the reviewer sees
the type, source count and status but not the raw protected content.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any

from secondbrain.memory_consolidation.models import MemoryStatus
from secondbrain.memory_consolidation.service import MemoryConsolidator

__all__ = ["MemoryReviewViewModel", "render_memory_html"]

_MASK = "[geschützt]"


class MemoryReviewViewModel:
    def __init__(self, consolidator: MemoryConsolidator) -> None:
        self.mc = consolidator

    def build(self, *, workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        duplicates = self.mc.find_duplicates(workspace_id=workspace_id)
        conflicts = self.mc.detect_conflicts(workspace_id=workspace_id, now=now)
        expiring = []
        for m in self.mc.memories(workspace_id=workspace_id, status=MemoryStatus.ACTIVE.value):
            eff = self.mc.effective_confidence(m.memory_id, now=now)
            if eff < 0.3:
                expiring.append({"type": m.type, "preview": self._preview(m), "effective": eff})
        return {
            "review": [self._card(m) for m in self.mc.memories(workspace_id=workspace_id,
                                                               status=MemoryStatus.ACTIVE.value)],
            "duplicates": [g.to_dict() for g in duplicates],
            "conflicts": [c.to_dict() for c in conflicts],
            "expiring": expiring,
            "decisions": ["keep_both", "supersede", "merge", "reject", "defer"],
        }

    def _card(self, m: Any) -> dict[str, Any]:
        return {"type": m.type, "preview": self._preview(m), "confidence": m.confidence,
                "importance": m.importance, "source_count": len(m.source_ids),
                "user_confirmed": m.user_confirmed, "status": m.status}

    @staticmethod
    def _preview(m: Any) -> str:
        if m.sensitive:
            return _MASK
        return (m.content or "")[:100]


def render_memory_html(view: dict[str, Any]) -> str:
    def esc(v: Any) -> str:
        return html.escape(str(v))

    review = "".join(
        f"<tr><td>{esc(c['type'])}</td><td>{esc(c['preview'])}</td>"
        f"<td>{esc(round(c['confidence'], 2))}</td><td>{esc(c['source_count'])}</td>"
        f"<td>{'✓' if c['user_confirmed'] else ''}</td></tr>"
        for c in view["review"])
    dups = "".join(f"<li>{len(g['memory_ids'])} Memories · Ähnlichkeit {esc(round(g['similarity'], 2))}</li>"
                   for g in view["duplicates"])
    conf = "".join(f"<li>{esc(c['conflict_type'])}: {esc(c['detail'])} ({len(c['memory_ids'])})</li>"
                   for c in view["conflicts"])
    exp = "".join(f"<li>{esc(e['type'])}: {esc(e['preview'])} <small>eff {esc(round(e['effective'], 2))}</small></li>"
                  for e in view["expiring"])
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Memory Review</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f6f6f8}}
h1,h2{{color:#e20074}}
table{{border-collapse:collapse;width:100%;background:#fff}}
td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left}}
ul{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:10px 24px}}
</style></head><body>
<h1>Memory Review</h1>
<h2>Aktive Memories</h2>
<table><thead><tr><th>Typ</th><th>Inhalt</th><th>Confidence</th><th>Quellen</th><th>Bestätigt</th></tr></thead><tbody>{review}</tbody></table>
<h2>Dubletten</h2><ul>{dups}</ul>
<h2>Konflikte</h2><ul>{conf}</ul>
<h2>Ablaufende Memories</h2><ul>{exp}</ul>
</body></html>"""
