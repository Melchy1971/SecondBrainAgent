"""P5 v23.0 - Memory Explorer."""

class MemoryExplorer:
    def render(self, memories: list[dict]):
        return {
            "memory_count": len(memories),
            "memories": memories,
        }
