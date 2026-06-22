"""P3 v20.4 - Context Assembly Pipeline."""

class ContextAssemblyPipeline:
    def assemble(self, memories: list[str], max_items: int = 10) -> str:
        cleaned = [m.strip() for m in memories if m and m.strip()]
        return "\n".join(cleaned[:max_items])
