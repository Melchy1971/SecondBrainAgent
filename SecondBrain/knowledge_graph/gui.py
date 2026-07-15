"""Knowledge graph GUI view model and headless HTML renderer.

Overview surfaces (explorer nodes, edges, timeline) show ``canonical_name``
only - no technical identifiers. The entity detail view deliberately keeps the
id, source ids and evidence so a user can trace and open the underlying record.
"""

from __future__ import annotations

import html
from typing import Any

from secondbrain.knowledge_graph.service import KnowledgeGraph

__all__ = ["GraphViewModel", "render_graph_html"]


class GraphViewModel:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def explorer(self, *, workspace_id: str) -> dict[str, Any]:
        ents = self.graph.entities(workspace_id=workspace_id)
        ids = {e.id for e in ents}
        nodes = [{"label": e.canonical_name, "type": e.type} for e in ents]  # no ids in overview
        edges = []
        for e in ents:
            for r in self.graph.relations_of(e.id):
                if r["other_id"] in ids:
                    edges.append({"from": e.canonical_name, "to": r["other"], "type": r["relationship"]})
        return {
            "nodes": nodes,
            "edges": edges,
            "conflicts": len(self.graph.conflicts(workspace_id=workspace_id)),
            "merge_proposals": [p.to_dict() for p in self.graph.detect_duplicates(workspace_id=workspace_id)],
        }

    def entity_detail(self, entity_id: str) -> dict[str, Any]:
        ent = self.graph.get(entity_id)
        if ent is None:
            return {}
        return {
            "id": ent.id,  # detail view keeps technical id for drill-down
            "canonical_name": ent.canonical_name,
            "type": ent.type,
            "aliases": ent.aliases,
            "confidence": ent.confidence,
            "source_ids": ent.source_ids,
            "evidence": ent.evidence,
            "attributes": {k: [v.to_dict() for v in vals] for k, vals in ent.attributes.items()},
            "relationships": self.graph.relations_of(entity_id),
            "timeline": self._timeline(ent),
        }

    @staticmethod
    def _timeline(ent: Any) -> list[dict[str, str]]:
        events = [{"at": ent.created_at, "event": "created"}]
        if ent.updated_at and ent.updated_at != ent.created_at:
            events.append({"at": ent.updated_at, "event": "updated"})
        if ent.superseded_by:
            events.append({"at": ent.valid_to, "event": "superseded"})
        return sorted(events, key=lambda e: e["at"])


def render_graph_html(explorer: dict[str, Any]) -> str:
    def esc(v: Any) -> str:
        return html.escape(str(v))

    nodes = "".join(f"<li>{esc(n['label'])} <span class='t'>{esc(n['type'])}</span></li>" for n in explorer["nodes"])
    edges = "".join(f"<li>{esc(e['from'])} —{esc(e['type'])}→ {esc(e['to'])}</li>" for e in explorer["edges"])
    props = "".join(
        f"<li>{esc(p['entity_a'][:8])}… ↔ {esc(p['entity_b'][:8])}… "
        f"<b>{esc(round(p['score'], 2))}</b> {'auto' if p['auto_mergeable'] else 'manuell'}</li>"
        for p in explorer["merge_proposals"]
    )
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Knowledge Graph</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f6f6f8}}
h1,h2{{color:#e20074}}
ul{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:10px 24px}}
.t{{font-size:11px;color:#777}}
</style></head><body>
<h1>Knowledge Graph</h1>
<p>Konflikte: {esc(explorer['conflicts'])} · Merge-Vorschläge: {len(explorer['merge_proposals'])}</p>
<h2>Entitäten</h2><ul>{nodes}</ul>
<h2>Beziehungen</h2><ul>{edges}</ul>
<h2>Merge-Vorschläge</h2><ul>{props}</ul>
</body></html>"""
