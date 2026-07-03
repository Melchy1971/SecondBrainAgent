# Historischer Patch-Hinweis

Dieses Dokument ist nur noch ein Archivhinweis fuer alte v9-Patchpakete.

Aktuelle Installation und Startbefehle stehen hier:

- `README.md`
- `INSTALLATION_BEGINNER.md`
- `docs/README.md`
- `docs/04_STARTBEFEHLE.md`

Aktueller Stand: v30.48 AI Workspace.

## v30.48

- Projekte, Workspaces, Favoriten, Tags, Archiv und Papierkorb sind direkt in
  die bestehende AI-Workspace-Shell eingebettet.
- Suche, Filter, JSON-Import/-Export sowie Benutzer, Rollen und Rechte nutzen
  die vorhandenen ProjectCenter-, WorkspaceManager- und RBAC-Datenpfade.
- Es wurde keine zweite Projektverwaltung und keine zweite Desktop-Shell
  eingefuehrt (Details: APPLY_DELTA_v30_48.md).

## v30.46.3

- Die bestehende Desktop-Shell ist der AI Workspace: Navigation links,
  Conversation/Streaming/Markdown Mitte, Quellen/Memory/Dokumente/Runtime
  rechts, Prompt/Anhaenge/Sprache/Provider unten.
- Panel-Logik UI-frei in `ai_workspace/panels.py`; keine zweite Navigation,
  keine zweite Toolbar (Details: APPLY_DELTA_v30_46_3.md).

## v30.46.2

- `secondbrain/chat/context/` ist die eine Context Pipeline:
  Prompt -> Conversation -> Working -> Semantic -> Document Retrieval ->
  Hybrid Search -> Context Builder -> LLM.
- ContextBuilder, PromptAssembler, MemorySelector, RetrievalCoordinator,
  ContextLimiter und TokenBudgetManager komponieren Bestandsmodule;
  keine zweite Retrieval- oder Memory-Engine.
- `ChatContextBuilder` und die P3-Kontextstubs bleiben als
  Kompatibilitaets-Fassaden erhalten (Details: APPLY_DELTA_v30_46_2.md).

## v30.46.1

- `ChatEngine` ist die einzige ausführende Chat-Engine im Projekt.
- Native Desktop, AI Workspace, Actions, Desktop-App und Legacy-HUD verwenden
  dieselbe Provider-, Context-, Retrieval- und Conversation-Pipeline.
- `NativeChatService` bleibt ausschließlich als kompatibler Alias erhalten.
- Legacy-Chat-JSONL wird nur noch gelesen; neue Nachrichten landen ausschließlich
  im zentralen Conversation Store unter `runtime/chat/`.
- Chat View, Streaming, Mobile-Darstellung und Voice Conversation bleiben
  Oberflächen-/Transportadapter und implementieren keine eigene Chatlogik.
- `secondbrain.chat.ChatService` ist die gemeinsame API aller Oberflaechen:
  `ask() / stream() / retry() / cancel() / export() / import_()`.
- StreamingManager, MarkdownRenderer, CitationRenderer, ConversationState und
  ConversationImporter/-Exporter leben unter `secondbrain/chat/`; alte
  Importadressen bleiben als Aliase erhalten (Details: APPLY_DELTA_v30_46_1.md).

## v30.46

- Der bestehende `NativeChatService` ist der zentrale Chat-Einstieg im AI Workspace.
- Conversations werden unter `runtime/chat/<uuid>/` mit Metadaten, JSONL-Nachrichten,
  Attachment-Manifests und Exporten gespeichert.
- Memory, ausgewählte Dokumentquellen, Hybrid Search, bestehende LLM-Provider,
  Streaming und Citations sind in einer Pipeline verbunden.
- Die bestehende Desktop-Shell enthält den Chat als eingebettete Drei-Spalten-Ansicht;
  es wird kein zweites Fenster und kein paralleler Chat-Stack erzeugt.
- Neue Conversation-Kommandos sind über `launcher.py` verfügbar.

## v30.45

- `python launcher.py` und `python launcher.py desktop` starten dieselbe native Desktop-Shell.
- Gemeinsamer `ApplicationState`, zentrale Navigation, Toolbar und Statusleiste.
- Dashboard, Workspace, Chat, Document Explorer, Memory Explorer, Agent Control,
  Voice Control, Command Center, Job Queue, Notification Center, Settings Center,
  Theme Center und Update Center sind ueber die Shell erreichbar.
- Bestehende Modulstarts und Diagnosekommandos bleiben erhalten.


## v30.25

Native Desktop ist jetzt der Primaerstart. Web-HUD bleibt nur noch Legacy-Kompatibilitaet. Deutsche Sprachsteuerung ist in `secondbrain.desktop_native.voice_de` verdrahtet.
