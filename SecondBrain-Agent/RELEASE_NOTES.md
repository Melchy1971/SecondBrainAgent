# Release Notes v30.63 - Background Agents

## v30.63

- Neues Paket `secondbrain/agent/background_agents/`: registrierte, wiederkehrende Hintergrund-Agenten (Monitore + Wartung).
- Klassen: `BackgroundAgent`, `AgentSchedule`, `AgentRun`, `AgentHeartbeat`, `AgentSupervisor`, `AgentFailurePolicy` (plus Store, Handler, Service, CLI).
- Agent-Typen: Import Monitor, Knowledge Quality Monitor, Memory Consolidation, RAG Index Monitor, Notification Agent, System Health Agent.
- Funktionen: registrieren, starten, stoppen, pausieren, Status, Heartbeat, Fehlerbehandlung (Failure-Policy pause/stop/alert_only), Scheduling (`run_due`).
- Wiederverwendung ohne Neubau: jeder Run laeuft ueber die v30.62-Workflow-Engine und wird dadurch in der bestehenden Job Queue gespiegelt; Notification Center und Memory-Sink angebunden. Das bestehende `agent/background/` bleibt unangetastet.
- Persistenz unter `runtime/agent/background_agents/` (agents.json, runs.jsonl, heartbeats.json).
- Launcher-Kommandos `background-agent-list`, `-register`, `-start`, `-stop`, `-pause`, `-status`, `-run`, `-run-due`, `-runs`.
- Tests: `test_background_agents.py`, `test_agent_supervisor.py`, `test_agent_heartbeat.py` (27 passed). Keine Regression in v30.62/v30.61/Planner (74 passed).

# Release Notes v30.62 - Agent Workflow Engine

## v30.62

- Neue Engine `secondbrain/agent/workflow/` macht mehrstufige Agent-Plaene ausfuehrbar, checkpointbar und absturzsicher.
- Klassen: `Workflow`, `WorkflowStep` (re-export), `WorkflowState`, `WorkflowCheckpoint`, `StepRun`, `WorkflowExecutor`, `WorkflowRecovery`, `WorkflowAudit`, `WorkflowStore`, `WorkflowService`.
- Funktionen: Workflow starten, Schritt ausfuehren, Status speichern (atomarer Checkpoint), Fehler behandeln, Retry, Rollback vorbereiten, nach Approval fortsetzen, nach Absturz fortsetzen.
- Wiederverwendung ohne Neubau: Planner-Step-Schema, Tool Registry, v30.61 Approval Layer (`SafetyService`/`NativeApprovalQueue`, keine zweite Queue), Job Queue, Notification Center, Recovery-Klassifikation; Memory ueber optionalen Sink.
- Checkpoints unter `runtime/agent/workflows/<id>.json`, Audit-Trail `workflow_audit.jsonl`.
- Launcher-Kommandos `workflow-create`, `workflow-run`, `workflow-status`, `workflow-list`, `workflow-cancel`, `workflow-resume`, `workflow-audit`, `workflow-rollback`.
- Tests: `test_workflow_engine.py`, `test_workflow_checkpoint.py`, `test_workflow_recovery.py`, `test_workflow_approval.py` (21 passed). Keine Regression in `test_v303_agent_workflow_engine.py`, v30.61-Safety, Planner (55 passed).

# Release Notes v30.61 - Agent Approval & Safety Layer

## v30.61

- Zentrale Safety-Schicht `secondbrain/agent/safety/` für riskante Agent-Aktionen ergänzt.
- Risk Levels `read`, `low`, `medium`, `high`, `destructive`, `external` als Vertrag eingeführt (`RiskClassifier`).
- `SafetyPolicy` entscheidet je Aktion/Level: `allow` / `require_approval` / `block`; Blocklist, Allowlist und Level-Grenzen konfigurierbar.
- `ActionGuard` als zentraler Einstiegspunkt: klassifiziert, prüft Policy, stellt bei Bedarf einen Approval-Request.
- `SafetyService` bündelt den Lebenszyklus: request / approve / reject / expire (TTL) / audit / policy_check.
- Freigabepflichtig: Dateiänderungen, Löschaktionen, externe API-Aufrufe, E-Mail, Kalender, DB-Migration, Index-Reparatur, Bulk Import, Shell Commands.
- **Keine zweite Queue**: Wiederverwendung der bestehenden `NativeApprovalQueue` (`runtime/native/approval_queue.jsonl`) und des `NativeActionAuditLog`.
- `NativeApprovalQueue.create()` rückwärtskompatibel um optionale `risk_level` / `reason` erweitert.
- Launcher-Kommandos `approval-list`, `approval-show`, `approval-approve`, `approval-reject`, `approval-audit`, `approval-expire` ergänzt.
- Tests: `test_agent_safety.py`, `test_approval_policy.py`, `test_action_guard.py` (41 passed). Keine Regression in `test_v3028_native_action_audit_approval.py`, `test_agent_planner.py`.

## v30.60

- Bestehende Agent- und v121-Tool-Registries auf eine Implementierung konsolidiert.
- Einheitliche Modelle für Definition, Input-Schema, Resultat, Risiko, Capability und Health ergänzt.
- Bestandsmodule für Suche, Dokumente, Import, Memory, Agenten, Jobs, Notifications, Settings, Voice, Updates, GitHub und Filesystem registriert.
- Persistentes Enable/Disable und Audit verwenden weiterhin `runtime/tools_v121`.
- Approval-, Scope-, Input- und Output-Validierung zentralisiert.
- Filesystem-Tools auf den Projektordner begrenzt.
- Launcher-Kommandos `tool-list`, `tool-show`, `tool-health`, `tool-run`, `tool-disable`, `tool-enable` ergänzt.

# Release Notes v30.59 - Agent Planner

## v30.59

- Kanonische Modelle `AgentPlan`, `AgentStep` und `PlanStatus` ergänzt.
- Deterministische Zerlegung über bestehenden AgentCore und Command Center implementiert.
- Bestehende ChatService-, Memory-, Job-Queue- und Approval-Komponenten integriert.
- Planvalidierung, Risikobewertung und atomare Persistenz in `runtime/agent/plans.json` ergänzt.
- Erstellen, Anzeigen, Auflisten, Abbrechen und Fortsetzen über den Launcher verfügbar.
- Keine zweite Agent-, Queue- oder Approval-Architektur eingeführt.

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
Deskt