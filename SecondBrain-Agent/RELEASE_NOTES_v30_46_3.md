# Release Notes v30.46.3 - AI Workspace

## Neu

- Vier-Zonen-Layout in der bestehenden Desktop-Shell: Navigation links,
  Conversation/Streaming/Markdown in der Mitte, Quellen/Memory/Dokumente/
  Runtime rechts, Prompt/Anhaenge/Sprache/Provider unten.
- UI-freie Panel-Modelle (`ai_workspace/panels.py`) fuer headless-Tests.
- Bottom-Bar bedient den Chat ueber die gemeinsame Chat-API (ChatService);
  Enter startet, Cancel/Retry wie gehabt, Anhangszaehler integriert.

## Kompatibilitaet

- `AIWorkspaceApp`, `AIChatWorkspaceFrame`, `run_gui` behalten Namen und
  Einstiege; Modul-Navigation und Toolbar unveraendert (keine Duplikate).
