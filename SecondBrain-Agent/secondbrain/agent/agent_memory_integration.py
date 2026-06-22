"""P2 v21.2 - Agent Memory Integration."""

class AgentMemoryIntegration:
    def build_context(self, semantic_memories, episodic_memories):
        return {
            "semantic_count": len(semantic_memories),
            "episodic_count": len(episodic_memories),
            "total": len(semantic_memories) + len(episodic_memories),
        }
