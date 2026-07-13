"""P3 v20.4 / v30.46.2 - Kompatibilitaets-Shim.

Die Kontextmontage lebt in secondbrain.chat.context (PromptAssembler/
ContextLimiter). Der bisherige Kontrakt (assemble(memories, max_items))
bleibt.
"""


class ContextAssemblyPipeline:
    def assemble(self, memories: list[str], max_items: int = 10) -> str:
        cleaned = [m.strip() for m in memories if m and m.strip()]
        return "\n".join(cleaned[:max_items])
