# Release Notes v30.46.2 - Eine Context Pipeline

## Neu

- `secondbrain/chat/context/`: ContextBuilder, PromptAssembler, MemorySelector,
  RetrievalCoordinator, ContextLimiter, TokenBudgetManager.
- Feste Pipeline-Reihenfolge: Conversation -> Working -> Semantic ->
  Document Retrieval -> Hybrid Search -> Context -> LLM.
- Token-Budgetierung pro Kontextsektion inklusive Budget-Report im
  build()-Ergebnis.
- Kontextquellen: Conversation, Memory, RAG, Dokumente, Anhaenge,
  Agenten (Provider-Hook), Workspace (Provider-Hook).

## Kompatibilitaet

- `ChatContextBuilder` (native/chat.py) bleibt als Fassade erhalten;
  build()/citations()-Vertrag unveraendert.
- `ContextWindowManager.trim`, `ContextAssemblyPipeline.assemble` und
  `memory.context_builder.ContextBuilder.build` behalten ihre Kontrakte
  als Shims.
- Keine zweite Retrieval- oder Memory-Engine: hybrid_search (P1-RAG)
  und MemoryExplorer/MemoryRanker bleiben die einzigen Engines.
