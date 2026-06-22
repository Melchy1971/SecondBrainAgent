"""P2 v21.1 - P1/P3 Integration Bridge."""

class IntegrationBridge:
    def build_context(self, rag_context: list[str], memory_context: list[str]) -> list[str]:
        return list(dict.fromkeys(rag_context + memory_context))
