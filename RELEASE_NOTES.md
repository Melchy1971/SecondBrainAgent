# Release Notes v30.77 - UI Path Override and Import Consolidation

## v30.77

- UI-konfigurierte Pfade aus `data/desktop_app/settings.json` ueberschreiben jetzt `config/settings.yaml` fuer Vault- und Inbox-Aufloesung.
- Zentrale Pfadlogik ueber `secondbrain/path.py` konsolidiert; Kompatibilitaets-Bruecken `from_settings_mapping()` und `from_settings_service()` halten die bisherigen Verbraucher stabil.
- Viele direkte `settings["vault_path"]`-/`settings["incoming_path"]`-Verbraucher auf die zentrale Aufloesung migriert.
- Kompatibilitaets-Wrapper fuer `secondbrain.goal_engine` und `secondbrain.recommendations` stellen die alten Importpfade weiter bereit.
- V9/V97-Module wurden auf die kanonischen Implementierungen umgebogen, um Doppelimplementierungen zu vermeiden.
- Dokumentation aktualisiert: README um Pfad-Override-Hinweise ergaenzt.

# Release Notes v30.76 - Plugin Runtime

## v30.76

- Deklarativer Plugin Loader und versioniertes Plugin Manifest.
- Explizites Host-Trust vor jeder Python-Aktivierung.
- Plugin API mit vorhandener ToolRegistry statt zweiter Registry.
- Deklarierte/gewaehrte Plugin Permissions und pfadgesicherte Sandbox-API.
- Schema-validierte Plugin Settings; Secret-Werte nur als Referenzen.
- Aktivierungs-Rollback und Deaktivierung entfernen registrierte Plugin-Tools.
- Offline Marketplace-Katalogvorbereitung mit Publisher-/Lizenz-/Checksum-Pruefung.

# Release Notes v30.75 - Answer Evaluation

## v30.75

- Automatische Answer Evaluation nach synchronen und gestreamten Provider-Antworten.
- Hallucination Detection ueber Claim-/Evidenzabdeckung und nicht belegte Zahlen.
- Source Verification ueber starke Chunk-/Dokument-IDs.
- Confidence wiederverwendet das bestehende Reasoning-Modell.
- Answer Rating und Evidence Rating mit transparenten Teilmetriken.
- Self Critique und Improvement Suggestions ohne internes Chain-of-Thought.
- Direkte Ablage in bestehenden Assistant-Message-Metadaten; keine neue Datenhaltung.

# Release Notes v30.74 - Layered Prompt Pipeline

## v30.74

- Typisierte System-, Workspace-, Memory-, Goal-, Document-, User- und Provider-Prompt-Layer.
- `FinalPromptBuilder` ist die zentrale Assembly hinter dem vorhandenen `PromptAssembler`.
- Kanonischer ChatEngine-Pfad nutzt die Layer direkt aus den bestehenden Context-Sektionen.
- Prompt Audit speichert Hashes, Groessen und Layer-Metadaten ohne Inhalte.
- Prompt History speichert lokale Inhalte mit bestehender Secret-Redaction.
- Provider-Fallback fuer fehlende System-Prompt-Unterstuetzung.

# Release Notes v30.73 - Context Optimization

## v30.73

- Gemeinsames Context Ranking fuer bestehende Memory- und RAG-Ergebnisse.
- Memory Ranking ueber die bestehende `MemoryRanking`-Implementierung.
- Source Ranking mit explizitem Trust-/Confidence-Vorrang und sicheren Defaults.
- Exakte und nahe Duplicate Removal vor der Token-Budgetierung.
- Conflict Resolution ueber den bestehenden `MemoryConflictDetector`; die staerker bewertete Aussage bleibt erhalten.
- Prompt Compression und explizite Prompt Expansion im bestehenden `PromptAssembler`.
- Keine neue Datenhaltung und keine zweite Context-Pipeline.

# Release Notes v30.72 - Semantic Graph Explorer

## v30.72

- Entity-, Relationship-, Project-, People-, Timeline- und Evidence-Graph im vorhandenen `SemanticExplorerService`.
- Timeline aus vorhandenen Dokument- und Memory-Zeitstempeln; Evidence aus RAG-Chunks und Memory-Eintraegen.
- Gewichtete Graph Search mit Knoten-, Beziehungs- und Quellfiltern.
- Graph Explorer bleibt direkt in der bestehenden AI-Workspace-GUI integriert.
- Ausschliesslich read-only Projektion ueber RAG und Memory; keine neue Datenhaltung.

# Release Notes v30.71 - Scheduler (Recurring Jobs / Cron / Dependencies / Maintenance)

## v30.71

- Neues Paket `secondbrain/agent/scheduler/`: wiederkehrende und geplante Jobs mit Cron, Abhaengigkeiten und Wartung.
- Cron (5 Felder: `*`, `*/n`, `a-b`, `a,b`) + Intervall-Schedule; `matches`, `due` (1-Tag-Fenster), `next_after`.
- Dependency Scheduler: abhaengige Jobs laufen erst nach erfolgreichem Vorlauf (sonst skipped), topologische Reihenfolge.
- Eingebaute Wartung: health_check (*/15), auto_index (stuendlich), knowledge_refresh (3am, abhaengig von auto_index), memory_consolidation (4am, Memory-Sink).
- Wiederverwendung: jede Ausloesung wird ueber `JobQueueService.add_job` in die bestehende Job Queue gespiegelt - keine zweite Queue. Health-Check liest `snapshot()`.
- Klassen: `JobScheduler`, `RecurringJob`, `JobRun`, `CronSchedule`, `IntervalSchedule`, `SchedulerStore`.
- Persistenz `runtime/agent/scheduler/` (recurring_jobs.json, runs.jsonl).
- Tests: `test_cron.py`, `test_scheduler.py`, `test_dependencies.py`, `test_maintenance.py` (25 passed). Keine Regression in v30.61-v30.70.

# Release Notes v30.70 - ToolChain

## v30.70

- Neues Paket `secondbrain/agent/toolchain/`: zusammengesetzte Tool-Workflows mit Kontrollfluss und Resilienz.
- Kontrollfluss: Conditional Steps, Loops (while/foreach mit max_iterations), Parallel Steps.
- Resilienz: Retry (max_attempts), Fallback (Alternativ-Step), Rollback (Kompensation in umgekehrter Reihenfolge), Error Handling.
- Visual Workflow: Mermaid (`flowchart TD`) + ASCII-Baum ueber `chain.visualize()`.
- Wiederverwendung: Tools laufen ueber die bestehende `ToolRegistry.run` - kein zweiter Tool-Executor.
- Klassen: `ToolChain`, `ToolChainExecutor`, `VisualWorkflow`, `ToolStep`, `ConditionalStep`, `LoopStep`, `ParallelStep`, `ChainContext`, `ChainRun`, `StepResult`, `RetryPolicy`.
- Tests: `test_toolchain.py`, `test_toolchain_control_flow.py`, `test_toolchain_recovery.py` (20 passed). Keine Regression in v30.61-v30.69.

# Release Notes v30.69 - Multi-Agent Coordination

## v30.69

- Neues Paket `secondbrain/agent/coordination/`: bestehende Agenten als Spezialisten hinter einem Coordinator - keine zweite Agent Engine.
- Spezialisten (Adapter ueber Bestands-Subsystemen): Planner (AgentPlanService), Executor (WorkflowExecutor), Critic (ReasoningSession), Reviewer, Memory + Search (Memory-Store/MemoryInjector), Import (JobQueueService).
- Communication Bus (Pub/Sub + Log), Task Delegation nach Capability, Shared Context / Shared Memory / Shared Goals (GoalTracker).
- `solve`-Pipeline: Planen -> Kritik -> Review -> Ausfuehren (nur bei approved und Severity != high).
- Persistenz `runtime/agent/coordination/bus.jsonl`.
- Tests: `test_communication.py`, `test_agents.py`, `test_coordinator.py` (22 passed). Keine Regression in v30.61-v30.68.

# Release Notes v30.68 - Reasoning Engine

## v30.68

- Neues Paket `secondbrain/agent/reasoning/`: strukturiertes Problemloesen (nicht nur Tool-Aufrufe), deterministisch und auditierbar.
- Klassen: `ReasoningSession`, `ReasoningChain`, `ReasoningStep`, `EvidenceCollector`, `Evidence`, `Hypothesis`, `Decision`, `DecisionScore`, `Confidence`, `ReasoningHistory`.
- Verfahren: Chain of Thought (intern), Tree of Thoughts, Hypothesentest, Evidenz-Ranking, Alternativen, Unsicherheiten, Konflikterkennung.
- Wiederverwendung ohne Parallelarchitektur: Evidenz ueber v30.64 `MemoryInjector` (Quelle/Confidence/Aktualitaet, Secret-/Privacy-Filter) + injizierbare RAG-Suche; Konflikte ueber v30.64 `MemoryConflictDetector`.
- Jede Entscheidung traegt Confidence, Evidence, Sources, Alternatives, Risk (+ uncertainties, conflicts).
- Persistenz `runtime/agent/reasoning/history.jsonl`.
- Tests: `test_reasoning.py`, `test_evidence.py`, `test_decisions.py` (22 passed). Keine Regression in v30.61-v30.67.

# Release Notes v30.67 - Phase 3 Stabilisierung

## v30.67

- Nicht-destruktive Stabilisierung: kein Bestands-Quellcode geloescht (alle Dubletten sind noch in Benutzung; Deprecation-Plan im Bericht).
- Runtime-/Testartefakte aus Git entfernt: 2455 faelschlich getrackte Dateien in neun `.pytest_tmp_v3045_*`-Ordnern untracked (`git rm -r --cached`), `.gitignore` um `.pytest_tmp*/` erweitert.
- Launcher-Kommandos geprueft: alle v30.61-v30.66-Dispatch-Ziele importieren und antworten.
- Dubletten-Inventur (4 Approval-Pfade, 2 Tool-Registries, alte Workflow-/Background-Pfade) mit risikobewertetem Deprecation-Plan.
- Validierung: compileall ok; Agent-Framework-Testset 170 passed; RepoDoctor ok=true (48/2/0); Launcher- und GUI-Smoke ok.
- Berichte: Phase 3 Completion Report, Known Limitations, Remaining Risks, Phase 4 Readiness (docs/releases/v30_67_phase3_stabilization.md).

# Release Notes v30.66 - Native Agent Control GUI

## v30.66

- Alle Agent-Funktionen (v30.59-v30.65) in die bestehende native Desktop-Anwendung integriert - eine Agent-Control-Oberflaeche im AI Workspace, keine zweite GUI.
- Neues Modul `secondbrain/native/agent_control/` (Aggregations-Service, GUI-Panel, CLI); im AI Workspace als Modul `agent_control` registriert.
- GUI-Bereiche: Agenten, Plaene, Workflows, Background Agents, Approvals, Goals, Audit, Logs - jeder aus dem jeweiligen Bestands-Subsystem.
- Funktionen: Plan erstellen/pruefen/starten, Approval bestaetigen/ablehnen, Workflow ueberwachen, Goal Tracking anzeigen, Background Agents verwalten.
- Jeder Bereich degradiert defensiv; GUI-Logik UI-frei ueber `view_model()`/`build_tabs()` getestet (Tkinter lazy).
- Launcher-Kommandos `agent-control-center`, `-gui`, `-status`, `agent-control-area`, `agent-control-plan-*`, `agent-control-approve/reject`, `agent-control-workflow`, `agent-control-goal-report`, `agent-control-bg`.
- Tests: `test_agent_control_gui.py`, `test_agent_workspace_integration.py` (14 passed). Keine Regression in v30.61-v30.65 (71 passed).

# Release Notes v30.65 - Agent Goal Tracking

## v30.65

- Neues Paket `secondbrain/agent/goals/`: Jarvis verfolgt Ziele, Fortschritt und offene Aufgaben.
- Klassen: `Goal`, `GoalMilestone`, `GoalMetric`, `GoalStatus`, `GoalEvidence`, `GoalReview`, `GoalStore`, `GoalTracker`.
- Funktionen: Ziel erstellen, in Plaene zerlegen, Fortschritt messen, offene Risiken anzeigen, pausieren, abschliessen, Zielbericht erzeugen.
- Integration ohne Neubau: Agent Planner (Zerlegung, Plaene bleiben in `runtime/agent/plans.json`), Workflow Engine (Status), Memory-Sink, Notification Center, Dashboard-Snapshot.
- Fortschritt = deterministische Mischung aus Meilenstein-, Metrik- und Plan-Fortschritt.
- Persistenz unter `runtime/agent/goals/` (goals.json, reviews.jsonl).
- Launcher-Kommandos `goal-create`, `goal-list`, `goal-show`, `goal-update`, `goal-report`, `goal-close`.
- Tests: `test_goal_tracking.py`, `test_goal_metrics.py`, `test_goal_reporting.py` (28 passed). Keine Regression in v30.61-v30.64 (70 passed).

# Release Notes v30.64 - Agent Memory Injection

## v30.64

- Neues Paket `secondbrain/agent/memory_injection/`: Agenten nutzen Memory gezielt, begrenzt und nachvollziehbar.
- Keine zweite Memory Engine - liest die bestehende `secondbrain.agent.memory` (`InMemoryMemoryStore`, `MemoryRecord`).
- Klassen: `MemoryInjector`, `MemoryQuery`, `MemoryContext`, `MemoryEvidence`, `MemoryRanking`, `MemoryBudget`, `MemoryConflictDetector` (plus Filter, Audit, Service, CLI).
- Agenten erhalten: relevante Erinnerungen, Quellen, Confidence, Aktualitaet, Konflikte, Ausschluesse im Privacy Mode.
- Regeln: Secrets niemals injizieren, Privacy Mode erzwingen, Tokenbudget beachten, Quellenpflicht.
- Pipeline in Sicherheitsreihenfolge: Secrets -> Privacy -> Quellenpflicht -> Ranking -> Budget/Limit -> Konflikte.
- Audit-Trail unter `runtime/agent/memory_injection/audit.jsonl` (nur `inject` schreibt).
- Launcher-Kommandos `agent-memory-preview`, `agent-memory-inject`, `agent-memory-audit`.
- Tests: `test_memory_injection.py`, `test_memory_budget.py`, `test_memory_privacy.py`, `test_memory_conflicts.py` (25 passed). Keine Regression in v30.61-v30.63 (72 passed).

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
- Document Explorer und Connectoren auf den zentralen ImportService umgestellt.

# Release Notes v30.53 - Unified Enterprise Importer

## v30.53

- Kanonisches Conversation-Modell für sämtliche Chat-Exporte.
- Acht Provider-Adapter auf `StreamingImportService` vereinheitlicht.
- Perplexity-Importpfad entfernt.
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
