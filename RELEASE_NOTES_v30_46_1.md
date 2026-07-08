# Release Notes v30.46.1 - AI Chat Foundation

## Neu

- `secondbrain.chat.ChatService`: eine API fuer alle Chat-Oberflaechen
  (ask, stream, retry, cancel, export, import_).
- `ConversationImporter`: Re-Import exportierter Konversationen (json/md).
- `StreamingManager`, `MarkdownRenderer`, `CitationRenderer` und
  `ConversationState` als eigenstaendige Bausteine unter `secondbrain/chat/`.
- HUD `/api/assistant` und AI Workspace nutzen dieselbe Fassade; die
  kanonische `ChatEngine` (secondbrain.native.chat) bleibt der einzige
  ausfuehrende Pfad.
- Volle pytest-Suite ueber das HUD ausfuehrbar (`run_pytest_q.py`).

## Kompatibilitaet

- `NativeChatService`, `gui.chat_stream.ChatStream`,
  `gui.citation_viewer.CitationViewer` und
  `secondbrain.markdown.MarkdownRenderer` bleiben als Aliase/Re-Exporte
  erhalten; keine Importadresse bricht.

## Kommandos

- `python launcher.py ai-chat "Frage"` (unveraendert, jetzt Fassaden-Pfad)
- `GET /api/run?script=run_pytest_q.py` (HUD)
