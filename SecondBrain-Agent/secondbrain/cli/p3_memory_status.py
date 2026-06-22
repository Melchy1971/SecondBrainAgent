"""P3 v20.0 - Memory Status CLI."""

from secondbrain.memory.memory_registry import MemoryRegistry


def run_memory_status() -> dict:
    registry = MemoryRegistry()
    return {
        "semantic_items": len(registry.semantic.list()),
        "episodic_items": len(registry.episodic.list()),
        "status": "PASS",
    }
