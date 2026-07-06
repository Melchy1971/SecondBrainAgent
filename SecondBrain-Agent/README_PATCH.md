# Historischer Patch-Hinweis

Dieses Dokument ist nur noch ein Archivhinweis fuer alte v9-Patchpakete.

Aktuelle Installation und Startbefehle stehen hier:

- `README.md`
- `INSTALLATION_BEGINNER.md`
- `docs/README.md`
- `docs/04_STARTBEFEHLE.md`

Aktueller Stand: v30.57 Import Quality Scoring.

## v30.57

Alle importierten Dokumente werden automatisch auf Duplikate, Near-Duplikate, Sprache, PII, Secrets, Klassifikation sowie Chunk-, Embedding-, OCR- und Parserqualität geprüft. Confidence, Source Trust und Knowledge Quality ergeben einen Score von 0 bis 100. Das bestehende Import Center enthält Quality Dashboard, Import Warnings und Duplicate Viewer.

## v30.56

Die Enterprise Import Engine arbeitet inkrementell: stabile IDs, Content-Hashes und Change Detection unterscheiden neue, geänderte, unveränderte und duplizierte Dokumente. Nur neue oder geänderte Inhalte laufen durch Chunk-, Embedding-, Memory-, Graph- und Search-Stages. Versionen bleiben in der bestehenden RAG-Datenbank erhalten. PostgreSQL/pgvector verwendet COPY-Staging mit Upsert.

## v30.55

Der vorhandene AI Workspace enthält ein vollständiges Import Center mit ETA, Pipeline-Zählern, Worker-/CPU-/RAM-Anzeige, Session-Steuerung, Logs und Fehleransicht. CLI-Zugriff: `python launcher.py import-center`, `import-status`, `import-history`.

## v30.54

PST, EML, PDF, DOCX, XLSX, CSV, TXT, Markdown sowie Obsidian-, Notion-, Paperless- und OneNote-Exporte verwenden die vorhandene Parser-Orchestrierung und denselben Enterprise ImportService. Dokument, Metadaten, Anhänge, OCR-Status, Version und Workspace werden im bestehenden RAG-Dokumentmodell gespeichert.

## v30.53

ChatGPT, Claude, Gemini, Perplexity, LibreChat, AnythingLLM, OpenWebUI und OpenAI Export werden in der bestehenden Enterprise Import Engine auf Conversation, Message, Attachment, Source und Metadata normalisiert. Provider-Adapter besitzen keine eigenen Importpfade.

## v30.52

Der Enterprise-Streaming-Import übergibt jeden Batch an die vorhandene native Job Queue. CPU-abhängige Worker verarbeiten Chunk-, Embedding-, Memory-, Graph- und Search-Stages unabhängig vom Import. Retry, Backoff und Dead Letters bleiben Zustände derselben Queue.

## v30.51

- Zentrale resumierbare Streaming-Import-Engine für ChatGPT, Claude, Gemini,
  JSON, JSONL und Markdown.
- `ijson`, konfigurierbare 500er-Batches und transaktionale Checkpoints im
  bestehenden P1-RAG-Store ermöglichen sehr große Dateien ohne Voll-Read.
- Das bestehende Import Center, die Provider-Adapter, Queue und RAG-CLI nutzen
  denselben Service (Details: APPLY_DELTA_v30_51.md).

## v30.50

- Der Semantic Explorer projiziert vorhandene RAG- und Memory-Daten read-only
  als Knowledge-, Dokument-, Workspace- und Memory-Graph.
- Personen, Projekte, Tags, Beziehungen und Quellen werden aus vorhandenen
  Metadaten abgeleitet; Suche, Filter und Nachbarschaftsnavigation sind integriert.
- Es gibt keinen eigenen Index und keine zweite Datenhaltung
  (Details: APPLY_DELTA_v30_50.md).

## v30.49

- Aufgaben, Erinnerungen, Kalender, Agent Jobs, Genehmigungen und Historie
  sind direkt in den AI Workspace integriert.
- Prioritaeten und Abhaengigkeiten erweitern den bestehenden Agent-Task-Pfad;
  Queue und Approval-Komponenten werden wiederverwendet.
- Das native Dashboard enthaelt eine read-only Aufgabenkarte.
- Es wurde keine zweite Taskverwaltung eingefuehrt
  (Details: APPLY_DELTA_v30_49.md).

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
