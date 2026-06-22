"""P5 v23.2 - RAG Citation Viewer."""

class CitationViewer:
    def render(self, citations: list[str]):
        return {
            "count": len(citations),
            "citations": citations,
        }
