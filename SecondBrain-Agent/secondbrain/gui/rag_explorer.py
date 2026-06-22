"""P5 v23.0 - RAG Explorer."""

class RagExplorer:
    def render(self, results: list[dict]):
        return {
            "result_count": len(results),
            "results": results,
        }
