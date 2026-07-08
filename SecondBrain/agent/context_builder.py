"""P2 v21.1 - Agent Context Builder."""

class AgentContextBuilder:
    def build(self, objective: str, memories: list[str], documents: list[str]) -> dict:
        return {
            "objective": objective,
            "memory_count": len(memories),
            "document_count": len(documents),
            "context": memories + documents,
        }
