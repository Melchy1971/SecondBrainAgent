"""v30.46.1 - CitationRenderer: einheitliche Zitat-Aufbereitung.

Konsolidiert die bisher verstreute Zitatlogik (ChatContextBuilder.citations,
gui.citation_viewer.CitationViewer-Stub, Treeview-Mapping im AI Workspace)
in eine Komponente fuer GUI, HUD und CLI.
"""
from __future__ import annotations

from typing import Any, Iterable

Citation = dict[str, Any]


class CitationRenderer:
    COLUMNS = ("chunk", "score", "workspace", "source", "provider")

    def normalize(self, hits: Iterable[dict[str, Any]], *, workspace: str = "chat") -> list[Citation]:
        """Rohe Retrieval-Hits -> Zitatstruktur (Schema von ChatContextBuilder)."""
        citations: list[Citation] = []
        for hit in hits or []:
            citations.append(
                {
                    "document": hit.get("title") or hit.get("document_id"),
                    "document_id": hit.get("document_id"),
                    "chunk": hit.get("chunk_id"),
                    "score": hit.get("hybrid_score", hit.get("score", 0.0)),
                    "workspace": workspace,
                    "source": hit.get("source"),
                    "provider": hit.get("provider") or "hybrid",
                    "preview": str(hit.get("text") or hit.get("snippet") or hit.get("preview") or "")[:240],
                }
            )
        return citations

    def rows(self, citations: Iterable[Citation]) -> list[dict[str, Any]]:
        """Zeilen fuer Tabellen-Frontends (z. B. ttk.Treeview)."""
        rows: list[dict[str, Any]] = []
        for index, item in enumerate(citations or []):
            rows.append(
                {
                    "iid": f"citation-{index}",
                    "document": item.get("document"),
                    "values": tuple(item.get(column) for column in self.COLUMNS),
                    "tag": str(item.get("document_id") or item.get("source") or ""),
                }
            )
        return rows

    def render_text(self, citations: Iterable[Citation]) -> str:
        """Kompakte Textdarstellung fuer CLI/HUD-Fallbacks."""
        lines = []
        for item in citations or []:
            score = item.get("score")
            score_text = f" ({score:.2f})" if isinstance(score, (int, float)) else ""
            lines.append(f"- {item.get('document')}{score_text} [{item.get('source') or item.get('provider') or '-'}]")
        return "\n".join(lines)

    def render(self, citations: list[Any]) -> dict[str, Any]:
        """Kompatibel zum bisherigen CitationViewer-Kontrakt."""
        items = list(citations or [])
        return {"count": len(items), "citations": items}

    def sources(self, citations: Iterable[Citation]) -> list[dict[str, Any]]:
        """HUD-Assistant-Kontrakt: note/score/chunk_id/preview."""
        return [
            {
                "note": str(item.get("document") or ""),
                "score": item.get("score", 0),
                "chunk_id": item.get("chunk") or 0,
                "preview": str(item.get("preview") or "")[:240],
            }
            for item in citations or []
        ]
