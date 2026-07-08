<<<<<<< HEAD
# README_PATCH - v30.76 Plugin Runtime

Lokale Plugins werden deklarativ ueber `plugins/<plugin>/plugin.json` entdeckt. Discovery ist schreibfrei und fuehrt keinen Code aus. Eine Aktivierung erfordert explizites Host-Trust sowie deklarierte und gewaehte Permissions.

Die Plugin API verwendet die bestehende ToolRegistry, validierte Plugin Settings und pfadgesicherte Workspace-Zugriffe. Marketplace-Vorbereitung erzeugt ausschliesslich Offline-Metadaten; Installation und Downloads sind nicht aktiviert.

---

# README_PATCH - v30.75 Answer Evaluation

Der kanonische ChatEngine-Pfad bewertet Provider-Antworten jetzt gegen die bereits abgerufene RAG-/Memory-Evidenz. Die Auswertung umfasst Hallucination Detection, Source Verification, Answer/Evidence Rating, Confidence, Self Critique und konkrete Improvement Suggestions.

Die Bewertung ist deterministisch und liefert keine versteckten Gedankengänge. Ergebnisse werden in den bestehenden Assistant-Message-Metadaten abgelegt; keine neue Datenhaltung oder zweite Chat-/RAG-Pipeline.

---

# README_PATCH - v30.74 Layered Prompt Pipeline

Der bestehende `PromptAssembler` verwendet jetzt einen zentralen `FinalPromptBuilder` fuer System-, Workspace-, Memory-, Goal-, Document-, Provider- und User-Prompts. Provider ohne native System-Prompt-Unterstuetzung erhalten die System-Layer kontrolliert im User-Request.

Projektgebundene Chat-Requests schreiben ein inhaltsfreies Audit sowie eine lokale, Secret-redigierte Prompt History. Direkte Utility-Aufrufe bleiben ohne `project_root` schreibfrei.

---

# README_PATCH - v30.73 Context Optimization

Die bestehende Chat-Context-Pipeline bewertet Memory- und RAG-Kandidaten jetzt gemeinsam nach Relevanz, bestehendem Memory-Score und Quellenvertrauen. Vor der vorhandenen Token-Budgetierung werden exakte/nahe Duplikate sowie unterlegene, widerspruechliche Memory-Aussagen entfernt.

`PromptCompressor` normalisiert Whitespace, entfernt identische Saetze und kann ein hartes Token-Budget anwenden. `PromptExpander` ergaenzt nur explizit uebergebene Kontextbegriffe und Constraints; bestehende Prompts bleiben standardmaessig unveraendert.

Keine neue Datenhaltung, Retrieval-Engine oder Context-Pipeline.

---

# README_PATCH - v30.72 Semantic Graph Explorer

Der vorhandene Semantic Explorer projiziert RAG-Dokumente, RAG-Chunks und Memory-Eintraege in sechs Graph-Sichten: Entity, Relationship, Project, People, Timeline und Evidence. Graph Search bewertet exakte Treffer, Praefixe, Labels, Metadaten, Quellen und Beziehungsevidenz.

Die Projektion ist read-only (`storage=None`). Sie legt keine Tabellen, Indizes oder Graphdateien an und bleibt direkt im AI Workspace eingebettet.

## Pruefen

```powershell
python -m compileall .
pytest -q
```

---

# README_PATCH - v30.71 Scheduler (Recurring Jobs / Cron / Maintenance)

Wiederkehrende und geplante Jobs mit Cron, Abhaengigkeiten und eingebauter Wartung. Jede Ausloesung wird in die bestehende Job Queue gespiegelt - keine zweite Queue.

## Enthaltene Dateien (neu)

- `secondbrain/agent/scheduler/` (cron, models, store, scheduler, maintenance, __init__)
- `tests/test_cron.py`, `tests/test_scheduler.py`, `tests/test_dependencies.py`, `tests/test_maintenance.py`
- `docs/releases/v30_71_scheduler.md`

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## Nutzung

```python
from secondbrain.agent.scheduler import JobScheduler
sch = JobScheduler(project_root, memory_sink=my_sink)
sch.register_maintenance()
sch.add("report", "0 8 * * 1-5", kind="system")
sch.add("sync", {"interval_seconds": 900})
runs = sch.run_due()   # von aussen getaktet; enqueued in die Job Queue
```

## Pruefen

```
python -m compileall .
pytest tests/test_cron.py tests/test_scheduler.py tests/test_dependencies.py tests/test_maintenance.py -q
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH - v30.70 ToolChain

Zusammengesetzte Tool-Workflows: Conditional Steps, Loops, Parallel Steps, Retry, Fallback, Rollback, Error Handling, Visual Workflow. Tools laufen ueber die bestehende ToolRegistry - kein zweiter Executor.

## Enthaltene Dateien (neu)

- `secondbrain/agent/toolchain/` (models, executor, visual, chain, __init__)
- `tests/_toolchain_fakes.py`, `tests/test_toolchain.py`, `tests/test_toolchain_control_flow.py`, `tests/test_toolchain_recovery.py`
- `docs/releases/v30_70_toolchain.md`

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## Nutzung

```python
from secondbrain.agent.toolchain import ToolChain, ToolChainExecutor, ToolStep
ch = ToolChain("demo").tool("fetch", output_var="doc", max_attempts=3,
                            fallback=ToolStep.create("fetch_cache"))
ch.foreach("chunks", body=[ToolStep.create("embed", inputs={"c":"$item"})])
run = ToolChainExecutor(project_root).run(ch, {"chunks":[1,2,3]})
print(ch.visualize().mermaid())
```

## Pruefen

```
python -m compileall .
pytest tests/test_toolchain.py tests/test_toolchain_control_flow.py tests/test_toolchain_recovery.py -q
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH - v30.69 Multi-Agent Coordination

Bestehende Agenten als Spezialisten hinter einem Coordinator - keine zweite Agent Engine. Communication Bus, Task Delegation nach Capability, Shared Context/Memory/Goals.

## Enthaltene Dateien (neu)

- `secondbrain/agent/coordination/` (models, bus, shared, agents, coordinator, __init__)
- `tests/_coord_fakes.py`, `tests/test_communication.py`, `tests/test_agents.py`, `tests/test_coordinator.py`
- `docs/releases/v30_69_multi_agent_coordination.md`

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## Nutzung

```python
from secondbrain.agent.coordination import Coordinator
c = Coordinator(project_root)
out = c.solve("Importiere und indexiere die Prozessdokumente")
# Planner -> Critic -> Reviewer -> Executor (WorkflowExecutor)
```

## Pruefen

```
python -m compileall .
pytest tests/test_communication.py tests/test_agents.py tests/test_coordinator.py -q
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH - v30.68 Reasoning Engine

Jarvis loest Probleme strukturiert - Chain of Thought (intern), Tree of Thoughts, Hypothesentest, Evidenz-Ranking, Alternativen, Unsicherheiten, Konflikterkennung. Keine zweite Engine: Evidenz und Konflikte kommen aus der v30.64 Memory-Injektion.

## Enthaltene Dateien (neu)

- `secondbrain/agent/reasoning/` (models, evidence, session, history, __init__)
- `tests/test_reasoning.py`, `tests/test_evidence.py`, `tests/test_decisions.py`
- `docs/releases/v30_68_reasoning_engine.md`

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## Nutzung

```python
from secondbrain.agent.reasoning import ReasoningSession
from secondbrain.agent.reasoning.models import Evidence, SUPPORT

s = ReasoningSession("Welche DB?")
dec = s.decide("DB-Wahl", ["Postgres","SQLite"], evidence_by_option={
  "Postgres":[Evidence.create("skaliert",source="wiki",confidence=0.9,stance=SUPPORT)],
  "SQLite":[Evidence.create("einfach",source="blog",confidence=0.4,stance=SUPPORT)],
})
# dec.chosen / dec.confidence / dec.evidence / dec.sources / dec.alternatives / dec.risk
```

## Pruefen

```
python -m compileall .
pytest tests/test_reasoning.py tests/test_evidence.py tests/test_decisions.py -q
```

Zielinterpreter: Python 3.11+.

---

=======
>>>>>>> 5e262f05d5b ( Changes to be committed:)
# README_PATCH - v30.67 Phase 3 Stabilisierung

Stabilisierung des Agent Frameworks und Abbau technischer Schulden - bewusst nicht-destruktiv.

## Was dieser Patch tut

- Entfernt 2455 faelschlich getrackte Pytest-Artefakte aus Git (untracked, Dateien bleiben) und ignoriert `.pytest_tmp*/` kuenftig.
- Prueft alle Launcher-Kommandos (v30.61-v30.66) auf saubere Imports.
- Liefert eine Dubletten-Inventur + Deprecation-Plan statt riskanter Sofort-Loeschung (alle Dubletten sind noch in Benutzung).
- Berichte: Phase 3 Completion, Known Limitations, Remaining Risks, Phase 4 Readiness.

## Was dieser Patch NICHT tut

- Keine Loeschung genutzter Klassen (ApprovalSystem, ApprovalStore, tool_registry_v121, agent/background, alter workflow_executor) - Migration erst nach gruenem `pytest` auf Python 3.13.

## Validierung

```
python -m compileall .
pytest -q
python launcher.py repo-doctor --project-root .
```

Ergebnis in dieser Umgebung (3.10 + Shim): Agent-Framework-Set 170 passed, RepoDoctor ok=true.

Details: `docs/releases/v30_67_phase3_stabilization.md`.

---

# README_PATCH - v30.66 Native Agent Control GUI

Alle Agent-Funktionen in der bestehenden nativen Desktop-Anwendung - eine Agent-Control-Oberflaeche im AI Workspace. Keine zweite GUI, keine zweite Engine: alle Bereiche komponieren die Bestands-Subsysteme.

## Enthaltene Dateien (neu)

- `secondbrain/native/agent_control/` (service, gui, cli, __init__)
- `tests/test_agent_control_gui.py`, `tests/test_agent_workspace_integration.py`
- `docs/releases/v30_66_native_agent_control_gui.md`

Geaendert: `secondbrain/native/ai_workspace/service.py` (Modul `agent_control` registriert), `launcher.py` (Dispatch `agent-control-center*`).

## Bereiche

Agenten, Plaene, Workflows, Background Agents, Approvals, Goals, Audit, Logs.

## Pruefen

```
python -m compileall .
pytest tests/test_agent_control_gui.py tests/test_agent_workspace_integration.py -q
python launcher.py agent-control-center
python launcher.py ai-workspace-navigation
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH - v30.65 Agent Goal Tracking

Jarvis verfolgt Ziele, Fortschritt und offene Aufgaben - integriert in Agent Planner, Workflow Engine, Memory, Notification Center und Dashboard, ohne zweite Plan- oder Ziel-Ausfuehrung.

## Enthaltene Dateien (neu)

- `secondbrain/agent/goals/` (models, store, tracker, service, cli, __init__)
- `tests/_goal_fakes.py`, `tests/test_goal_tracking.py`, `tests/test_goal_metrics.py`, `tests/test_goal_reporting.py`
- `docs/releases/v30_65_goal_tracking.md`

Geaendert: `launcher.py` (Dispatch `goal-*`).

## Nutzung

```python
from secondbrain.agent.goals import GoalTracker

tracker = GoalTracker.for_project(project_root)
goal = tracker.create_goal("SAP Migration Q3", metrics=[{"name":"tasks","target":10,"current":4}],
                           milestones=[{"title":"Analyse"}])
tracker.decompose(goal.id)               # Ziel -> Plan (Agent Planner)
tracker.measure_progress(goal.id)        # Meilenstein + Metrik + Plan
tracker.report(goal.id)                  # Bericht + Risiken + Notification
```

## Pruefen

```
python -m compileall .
pytest tests/test_goal_tracking.py tests/test_goal_metrics.py tests/test_goal_reporting.py -q
python launcher.py goal-list
```

Zielinterpreter: Python 3.11+.

---

# README_PATCH - v30.64 Agent Memory Injection

Agenten nutzen Memory gezielt, begrenzt und nachvollziehbar - auf Basis der bestehenden `secondbrain.agent.memory`, ohne zweite Memory Engine. Harte Regeln: keine Secrets, Privacy Mode, Tokenbudget, Quellenpflicht.

## Enthaltene Dateien (neu)

- `secondbrain/agent/memory_injection/` (models, budget, filters, ranking, conflicts, injector, audit, service, cli, __init__)
- `tests/_mem_helpers.py`, `tests/test_memory_injection.py`, `tests/test_memory_budget.py`, `tests/test_memory_privacy.py`, `tests/test_memory_conflicts.py`
- `docs/releases/v30_64_memory_injection.md`

Geaendert: `launcher.py` (Dispatch `agent-memory-*`).

## Nutzung

```python
from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery
from secondbrain.agent.memory import InMemoryMemoryStore  # bestehender Store

injector = MemoryInjector.for_project(project_root, store)  # store: bestehender, befuellter Memory-Store
ctx = injector.inject(MemoryQuery(text="SAP Migration", privacy_mode=True, token_budget=500),
                      actor="agent", agent_id="agent-7")
# ctx.evidences -> mit Quelle/Confidence/Aktualitaet; ctx.conflicts; ctx.exclusions; ctx.sources
```

## Pruefen

```
python -m compileall .
pytest tests/test_memory_injection.py tests/test_memory_budget.py tests/test_memory_privacy.py tests/test_memory_conflicts.py -q
python launcher.py agent-memory-preview --query "SAP" --memories mem.json --privacy
```

Zielinterpreter: Python 3.11+.

---

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
  denselben Service (Details siehe Release Notes).

## v30.50

- Der Semantic Explorer projiziert vorhandene RAG- und Memory-Daten read-only
  als Knowledge-, Dokument-, Workspace- und Memory-Graph.
- Personen, Projekte, Tags, Beziehungen und Quellen werden aus vorhandenen
  Metadaten abgeleitet; Suche, Filter und Nachbarschaftsnavigation sind integriert.
- Es gibt keinen eigenen Index und keine zweite Datenhaltung
  (Details siehe Release Notes).

## v30.49

- Aufgaben, Erinnerungen, Kalender, Agent Jobs, Genehmigungen und Historie
  sind direkt in den AI Workspace integriert.
- Prioritaeten und Abhaengigkeiten erweitern den bestehenden Agent-Task-Pfad;
  Queue und Approval-Komponenten werden wiederverwendet.
- Das native Dashboard enthaelt eine read-only Aufgabenkarte.
- Es wurde keine zweite Taskverwaltung eingefuehrt
  (Details siehe Release Notes).

## v30.48

- Projekte, Workspaces, Favoriten, Tags, Archiv und Papierkorb sind direkt in
  die bestehende AI-Workspace-Shell eingebettet.
- Suche, Filter, JSON-Import/-Export sowie Benutzer, Rollen und Rechte nutzen
  die vorhandenen ProjectCenter-, WorkspaceManager- und RBAC-Datenpfade.
- Es wurde keine zweite Projektverwaltung und keine zweite Desktop-Shell
  eingefuehrt (Details siehe Release Notes).

## v30.46.3

- Die bestehende Desktop-Shell ist der AI Workspace: Navigation links,
  Conversation/Streaming/Markdown Mitte, Quellen/Memory/Dokumente/Runtime
  rechts, Prompt/Anhaenge/Sprache/Provider unten.
- Panel-Logik UI-frei in `ai_workspace/panels.py`; keine zweite Navigation,
  keine zweite Toolbar (Details siehe Release Notes).

## v30.46.2

- `secondbrain/chat/context/` ist die eine Context Pipeline:
  Prompt -> Conversation -> Working -> Semantic -> Document Retrieval ->
  Hybrid Search -> Context Builder -> LLM.
- ContextBuilder, PromptAssembler, MemorySelector, RetrievalCoordinator,
  ContextLimiter und TokenBudgetManager komponieren Bestandsmodule;
  keine zweite Retrieval- oder Memory-Engine.
- `ChatContextBuilder` und die P3-Kontextstubs bleiben als
  Kompatibilitaets-Fassaden erhalten (Details siehe Release Notes).

## v30.46.1

- `ChatEngine` ist die einzige ausführende Chat-Engine im Projekt.
- Native Desktop, AI Workspace, Actions, Desktop-App und Web-HUD verwenden
  dieselbe Provider-, Context-, Retrieval- und Conversation-Pipeline.
- `NativeChatService` bleibt ausschließlich als kompatibler Alias erhalten.
- Chat-JSONL wird nur noch gelesen; neue Nachrichten landen aus
