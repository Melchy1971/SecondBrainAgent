# Release Notes v30.57 - Import Quality Scoring

## v30.57

- Automatische Qualitätsbewertung in die bestehende Importpipeline integriert.
- Duplicate- und Near-Duplicate-Erkennung ohne neue Datenhaltung ergänzt.
- Language-, PII- und Secret-Detection sowie Dokumentklassifikation ergänzt.
- Chunk-, Embedding-, OCR- und Parserqualität werden einzeln ausgewiesen.
- Confidence Score, Source Trust und Knowledge Quality Score 0–100 ergänzt.
- Native Quality Dashboard, Import Warnings und Duplicate Viewer ergänzt.

# Release Notes v30.56 - Delta Import

## v30.56

- Delta- und Incremental-Import mit stabilen Dokumentidentitäten implementiert.
- Hashing, Change Detection und globale Inhalts-Deduplizierung ergänzt.
- Bestehende Dokumente werden aktualisiert und in `document_versions` historisiert.
- Auto Resume für unterbrochene Sessions und Auto Retry für transiente Import-/Pipeline-Fehler ergänzt.
- PostgreSQL COPY-Staging für Dokumente, Chunks und pgvector-Embeddings implementiert.
- Nur neue/geänderte Inhalte erzeugen Pipeline-Jobs für Chunks, Embeddings, Memory, Graph und Search.

# Release Notes v30.55 - Native Import Center

## v30.55

- Import Center direkt in die bestehende Native Desktop GUI integriert.
- ETA, Fortschritt, Chats, Dokumente, Chunks, Embeddings und Worker sichtbar.
- CPU-/RAM-Metriken ohne verpflichtende neue Abhängigkeit ergänzt.
- Pause, Continue, Retry und Stop an bestehende Session-/Queue-Zustände angebunden.
- Launcher-Kommandos `import-center`, `import-status`, `import-history` ergänzt.

# Release Notes v30.54 - Unified Document Import

## v30.54

- Bestehende Parser-Orchestrierung direkt an die Enterprise Import Engine angebunden.
- PST-Parser im vorhandenen Registry-Pattern mit optionalem `pypff` ergänzt.
- Dokumentmetadaten um Anhänge, OCR-Status, Version und Workspace erweitert.
- Workspace-Import für Obsidian, Notion, Paperless und OneNote ergänzt.
- Document Explorer und Legacy-Connectoren auf den zentralen ImportService umgestellt.

# Release Notes v30.53 - Unified Enterprise Importer

## v30.53

- Kanonisches Conversation-Modell für sämtliche Chat-Exporte.
- Acht Provider-Adapter auf `StreamingImportService` vereinheitlicht.
- Legacy-Perplexity-Importpfad entfernt.
- TXT- und HTML-Streaming als zusätzliche Enterprise-Eingaben ergänzt.
- Provider- und Integrationsfixtures für alle unterstützten Formate ergänzt.

# Release Notes v30.52 - Parallel Import Runtime

## v30.52

- Bestehende Runtime-Queue um atomisches Claiming und Pipeline-Jobtypen erweitert.
- `WorkerPool`, `QueueManager`, `RetryManager`, `DeadLetterQueue`, `Backoff` und `ImportScheduler` ergänzt.
- Worker-Anzahl CPU-abhängig und mit `SECONDBRAIN_IMPORT_WORKERS` konfigurierbar.
- Import-Batches werden dedupliziert an Chunk, Embedding, Memory, Graph und Search weitergereicht.
- Embeddings blockieren den Streaming-Import nicht.

# Release Notes v30.51 - Enterprise Streaming Import Engine

## v30.51

- Bounded-memory Streaming für ChatGPT, Claude, Gemini, JSON, JSONL und Markdown.
- Resume über persistente `import_sessions`-Checkpoints.
- Dokument-/Chunk-Batches mit Standardgröße 500 und ohne Einzelinserts.
- Direkte Integration in bestehenden P1-RAG-Store, Job Queue und AI Import Center.
- Bestehende Provider-Importer delegieren an den zentralen Importservice.

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
