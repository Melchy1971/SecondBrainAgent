"""P3 v20.0 - Unified Memory Registry."""

from secondbrain.memory.semantic_memory import SemanticMemoryStore
from secondbrain.memory.episodic_memory import EpisodicMemoryStore


class MemoryRegistry:
    def __init__(self):
        self.semantic = SemanticMemoryStore()
        self.episodic = EpisodicMemoryStore()
