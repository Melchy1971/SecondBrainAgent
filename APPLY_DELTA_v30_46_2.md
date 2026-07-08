# APPLY DELTA v30.46.2 - Eine Context Pipeline

## Inhalt

- Neues Paket `secondbrain/chat/context/` mit der einen Context Pipeline:

```text
Prompt -> Conversation Memory -> Working Memory -> Semantic Memory
       -> Document Retrieval -> Hybrid Search -> Context Builder -> LLM
```

- Komponenten (komponieren ausschliesslich Bestandsmodule):
  - `ContextBuilder`         Orchestrierung, Vertrag kompatibel zum bisherigen ChatContextBuilder
  - `PromptAssembler`        Sektionen -> CompletionRequest (ersetzt ChatEngine._completion_request-Logik)
  - `MemorySelector`         Conversation/Working/Semantic via MemoryExplorer, MemoryRanker, SemanticMemorySearch
  - `RetrievalCoordinator`   P1-RAG hybrid_search + Anhaenge + Agent-/Workspace-Provider (injizierbar)
  - `ContextLimiter`         Sektionsweises Kuerzen (ersetzt ContextWindowManager-Logik)
  - `TokenBudgetManager`     Budgetierung des Kontextfensters (Zeichenheuristik, Anteile pro Sektion)
- Kontextquellen: Conversation, Memory, RAG, Dokumente, Anhaenge, Agenten, Workspace.
  Agent/Workspace sind injizierbare Provider (Callable[[str, int], list[str]]); ohne Provider leer.
- `ChatContextBuilder` (native/chat.py) ist jetzt eine Kompatibilitaets-Fassade
  ueber `ContextBuilder`; keine zweite Retrieval- oder Memory-Engine.
- P3-Stubs `memory/context_builder.py`, `context_assembly_pipeline.py`,
  `context_window_manager.py` sind Shims mit unveraendertem Kontrakt.
- `build()` liefert zusaetzlich einen Budget-Report (`result["budget"]`).

## Neue Tests

```text
tests/test_context_builder.py   + 4 Pipeline-Tests (Stufen, Reihenfolge, Budget, Quellen-Gating)
tests/test_prompt_builder.py    PromptAssembler (Reihenfolge, History-Limit, Budget, Temperature)
tests/test_memory_selector.py   Conversation/Working/Semantic-Auswahl
tests/test_token_budget.py      Schaetzung, Shares, Allokation, Report
```

## Akzeptanz

```bash
python -m compileall .
pytest -q
python launcher.py repo-doctor --execute-runtime-checks
```
