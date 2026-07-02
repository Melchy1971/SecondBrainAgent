# Release Notes v30.46.1 - Unified Chat Engine

## Ergebnis

Der bestehende native Chat ist der Mittelpunkt des AI Workspace. Conversations,
Memory, Dokument-Retrieval, Hybrid Search, Provider, Streaming und Citations
laufen durch einen gemeinsamen Service- und State-Pfad.

v30.46.1 entfernt die verbliebenen parallelen Ausführungspfade: `ask`, `search`,
Desktop-App, Actions und Legacy-HUD delegieren jetzt an dieselbe `ChatEngine`.

## Neu

- `ApplicationState` enthält Workspace, Provider, Modell, Conversation, ausgewählte
  Dokumente, Runtime Health, Notifications, Memory, Jobs, Agents und Voice State.
- Conversation Store unter `runtime/chat/<uuid>/` mit Pin/Favorite/Archive,
  Suche, Export, Provider-Versionen und deduplizierten Attachment-Manifests.
- Nicht-blockierendes Streaming mit Start, Cancel, Retry und Continue.
- Markdown-Renderer für Tabellen, Codeblöcke, Listen, Checklisten, Blockquotes,
  Links und Inline Code; Syntax-Tags sind vorbereitet.
- Linker Document-Context-Bereich, zentraler Chat und rechtes Citation Panel sind
  in die bestehende AI-Workspace-Shell eingebettet.
- OpenAI, Ollama, Gemini und Claude nutzen ausschließlich die vorhandenen Provider.
- Legacy-Chat-Store und bestehende Launcher-Kommandos bleiben kompatibel.

## Start

```powershell
python launcher.py
python launcher.py desktop
python launcher.py conversation-gui
python launcher.py conversation-list
```

## Validierung

```powershell
python -m compileall .
pytest -q
```

## Risiko

- Provider-Aufrufe benötigen die jeweilige lokale Konfiguration beziehungsweise Credentials.
- Provider ohne nativen Streaming-Transport werden in der Chat-Pipeline tokenweise an die GUI weitergereicht.
