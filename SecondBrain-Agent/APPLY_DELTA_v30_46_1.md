# APPLY DELTA v30.46.1 - AI Chat Foundation (Fassade + Konsolidierung)

Ergaenzt die Unified Chat Engine (siehe APPLY_DELTA_v30_46.md) um die
gemeinsame Chat-API und raeumt die letzten Duplikate aus.

## Inhalt

- Neues Paket `secondbrain/chat/` mit einer API fuer alle Oberflaechen:
  `ChatService.ask() / stream() / retry() / cancel() / export() / import_()`.
  Hinweis: `import` ist Python-Schluesselwort, daher `import_` mit Alias
  `import_conversation`.
- `StreamingManager` (vormals `gui.chat_stream.ChatStream`) nach
  `secondbrain.chat.streaming` verschoben; alte Importadresse bleibt Alias.
- `MarkdownRenderer` (vormals in `secondbrain.markdown`) nach
  `secondbrain.chat.markdown_renderer` verschoben; Re-Export bleibt.
- `CitationRenderer` konsolidiert Zitatlogik (Normalisierung, Treeview-Zeilen,
  Text- und HUD-Quellenformat); `gui.citation_viewer.CitationViewer` ist Alias.
- `ConversationState` als konversationsbezogener Zustand (Fassade/HUD/CLI).
- NEU: `ConversationImporter` liest eigene Exporte (json/md) zurueck in den
  Conversation Store; `ConversationExporter` delegiert an den Store.
- AI Workspace (Tk) und HUD `/api/assistant` laufen ueber `ChatService`;
  keine direkten Engine-/Stream-Instanzen mehr in den Oberflaechen.
- HUD-Allowlist ergaenzt um `run_pytest_q.py` (volle pytest-Suite via
  `GET /api/run?script=run_pytest_q.py`).

## Bewusst unveraendert

- `/api/coding/generate` nutzt weiterhin `_llm_chat` (eigener Feature-Pfad,
  kein Chat); Kandidat fuer eine spaetere Provider-Konsolidierung.
- `ChatEngine.ask()/search()` (Launcher-RAG-Bridge) bleibt als LLM-freier
  Fallback erhalten und ist ueber `ChatService.ask_rag()` erreichbar.

## Neue Tests

```text
tests/test_streaming_manager.py        StreamingManager + Alias-Vertrag
tests/test_chat_service.py             + 7 Fassaden-Tests (ask/stream/retry/
                                         cancel/export/import_/state)
tests/test_conversation_store.py       + 3 Importer-Tests (json/md/Fehlerfaelle)
tests/test_markdown_renderer.py        + Kanonischer-Pfad-Test
```

## Akzeptanz

```bash
python -m compileall .
pytest -q
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py native-desktop-health
```
