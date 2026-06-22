"""P3 v20.1 - Memory Gate."""

class P3MemoryGate:
    REQUIRED = [
        "semantic_memory",
        "episodic_memory",
        "memory_ranker",
        "context_builder",
        "memory_compression",
        "forgetting_policy",
    ]

    def evaluate(self, capabilities: dict[str, bool]) -> dict:
        checks = {c: capabilities.get(c, False) for c in self.REQUIRED}
        status = "PASS" if all(checks.values()) else "FAIL"
        return {"status": status, "checks": checks}
