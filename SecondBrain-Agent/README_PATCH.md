# README_PATCH - v30.63 Background Agents

Jarvis fuehrt wiederkehrende und langfristige Aufgaben eigenstaendig im Hintergrund aus: registrierte Agenten mit Schedule, Heartbeat, Supervisor und Failure-Policy. Jeder Run laeuft ueber die v30.62-Workflow-Engine und wird in der bestehenden Job Queue gespiegelt - kein zweiter Ausfuehrungs- oder Queue-Mechanismus.

## Enthaltene Dateien (neu)

- `secondbrain/agent/background_agents/` (models, store, handlers, supervisor, service, cli, __init__)
- `tests/_bg_fakes.py`, `tests/test_background_agents.py`, `tests/test_agent_supervisor.py`, `tests/test_agent_heartbeat.py`
- `docs/releases/v30_63_background_agents.md`

Geaendert: `launcher.py` (Dispatch `background-agent-*`).

## Nutzung

```python
from secondbrain.agent.background_agents import AgentSupervisor, AgentSchedule

sup = AgentSupervisor.for_project(project_root)
agent = sup.register("Import Waechter", "import_monitor", schedule=AgentSchedule(interval_seconds=3600))
sup.start(agent.id)
sup.run_agent(agent.id)      # laeuft als Workflow, spiegelt in die Job Queue
sup.run_due()                # von aussen getaktet (Scheduler / scheduled task)
```

## Pruefen

```
python -m compileall .
pytest tests/test_background_agents.py tests/test_agent_supervisor.py tests/test_agent_heartbeat.py -q
python launcher.py background-agent-list
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH - v30.62 Agent Workflow Engine

Macht mehrstufige Agent-Plaene ausfuehrbar: klassifiziert, freigabefaehig, nach jedem Schritt gesichert und damit nach Approval und nach Absturz fortsetzbar. Reine Wiederverwendung der Bestands-Subsysteme, kein zweiter Store, keine zweite Approval Queue.

## Enthaltene Dateien (neu)

- `secondbrain/agent/workflow/` (models, store, audit, recovery, executor, service, cli, __init__)
- `tests/_workflow_fakes.py`, `tests/test_workflow_engine.py`, `tests/test_workflow_checkpoint.py`, `tests/test_workflow_recovery.py`, `tests/test_workflow_approval.py`
- `docs/releases/v30_62_workflow_engine.md`

Geaendert: `launcher.py` (Dispatch `workflow-*`).

## Nutzung

```python
from secondbrain.agent.workflow import WorkflowExecutor
from secondbrain.agent.workflow_models import WorkflowStep

ex = WorkflowExecutor.for_project(project_root)
cp = ex.create("Ziel", [
    WorkflowStep(id="a", name="Vorbereiten", tool_name="t.a"),
    WorkflowStep(id="b", name="Loeschen", tool_name="file.delete", dependencies=["a"], requires_approval=True),
])
ex.run(cp.workflow_id)          # haelt bei Freigabe-Schritt (WAITING_APPROVAL)
# nach Freigabe in der native Queue:
ex.resume(cp.workflow_id)       # laeuft weiter
# nach Absturz:
ex.resume_after_crash(cp.workflow_id)
```

## Pruefen

```
python -m compileall .
pytest tests/test_workflow_engine.py tests/test_workflow_checkpoint.py tests/test_workflow_recovery.py tests/test_workflow_approval.py -q
python launcher.py workflow-list
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH – v30.61 Agent Approval & Safety Layer

Zentrale Freigabe- und Sicherheitslogik für riskante Agent-Aktionen. Aktionen werden nach Risk Level klassifiziert und – wenn die Policy es verlangt – über die **bestehende** native Approval Queue freigegeben. Keine zweite Queue, kein zweiter Audit-Trail.

## Enthaltene Dateien

Neu:

- `secondbrain/agent/safety/__init__.py`
- `secondbrain/agent/safety/risk.py` – `RiskClassifier`
- `secondbrain/agent/safety/policy.py` – `SafetyPolicy`, `PolicyVerdict`
- `secondbrain/agent/safety/models.py` – `ApprovalDecision`, `GuardDecision`, Re-Export `ApprovalRequest`
- `secondbrain/agent/safety/audit.py` – `ApprovalAudit`
- `secondbrain/agent/safety/guard.py` – `ActionGuard`, `SafetyService`
- `secondbrain/agent/safety/cli.py` – Launcher-Kommandos
- `tests/test_agent_safety.py`, `tests/test_approval_policy.py`, `tests/test_action_guard.py`
- `docs/releases/v30_61_agent_safety.md`

Geändert (rückwärtskompatibel):

- `secondbrain/native/approval.py` – `NativeApprovalQueue.create()` um optionale `risk_level` / `reason` erweitert
- `launcher.py` – Dispatch für `approval-*` Kommandos

## Nutzung

```python
from secondbrain.agent.safety import ActionGuard, SafetyService

guard = ActionGuard(project_root)
decision = guard.guard(actor="agent", action="file.delete",
                       text="Notiz löschen", target="plan:42:step:3")
# decision.allowed / decision.outcome in {"allow","require_approval","block"}
# decision.approval_id -> Freigabe:
SafetyService(project_root).approve(decision.approval_id, decided_by="markus")
```

## Prüfen

```
python -m compileall .
pytest tests/test_agent_safety.py tests/test_approval_policy.py tests/test_action_guard.py -q
python launcher.py approval-list
```

Zielinterpreter: Python 3.11+ (Repo verwendet `enum.StrEnum`).

---

# Historischer Patch-Hinweis

Dieses Dokument ist nur noch ein Archivhinweis fuer alte v9-Patchpakete.

Aktuelle Installation und Startbefehle stehen hier:

- `README.md`
- `INSTALLATION_BEGINNER.md`
- `docs/README.md`
- `docs/04_STARTBEFEHLE.md`

Aktueller Stand: v30.60 Unified Tool Registry.

## v30.60

Jarvis nutzt eine einzige Tool Registry für Suche, Dokumente, Import, Memory, Agenten, Jobs, Notifications, Settings, Voice, Updates, GitHub und Filesystem. Der gemeinsame Vertrag validiert Ein- und Ausgaben, Risiko, Approval und Enable-Status. Die bisherigen v121- und Agent-Tool-Importpfade sind Kompatibilitätsimporte derselben Registry. Launcher: `tool-list`, `tool-show`, `tool-health`, `tool-run`, `tool-disable`, `tool-enable`.

## v30.59

Der bestehende AgentCore zerlegt Benutzerziele in persistente, validierte und risikobewertete Agent-Pläne. Jeder Schritt enthält Tool, Inputs, erwartete Ausgabe, Risiko, Approval-Status und Evidence. Plan-Aktivierung nutzt ausschließlich die vorhandene Native Job Queue und Approval Queue. Launcher: `agent-plan-create`, `agent-plan-show`, `agent-plan-list`, `agent-plan-cancel`, `agent-plan-resume`.

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
- Legacy-Chat-JSONL wird nur noch gelesen; neue Nachrichten landen aus