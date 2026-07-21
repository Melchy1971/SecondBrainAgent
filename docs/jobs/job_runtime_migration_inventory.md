# Job-Runtime — Migrationsinventar

Erhebungsdatum: 2026-07-21
Basis: `feature/v31.89-declare-desktop-runtime-dependency` (`61f12d5`), inhaltsgleich mit `main` plus Stufe 0
Methode: AST-Scan über 1509 Python-Dateien in `SecondBrain/`, `scripts/`, `launcher.py`, `secondbrain.py`. Tests, Archive und `OUTPUTS/` ausgenommen. Ergebnis: 67 Kandidaten mit eigener Nebenläufigkeit oder eigenem Prozess-Handling.

Scanwerkzeug: `OUTPUTS/v31.90-job-runtime-inventory/_scan_job_runtime.py` (read-only, wiederholbar).

---

## Kernbefund — die Aufgabenstellung stimmt nicht

Prompt 70 geht davon aus, dass eine zentrale Job-Runtime existiert und einzelne Langläufer noch daran vorbeilaufen. Das trifft nicht zu.

Es existieren **vier voneinander unabhängige Job-Subsysteme** mit je eigenem Modell, eigener Queue, eigener Historie und eigener Retry-Logik:

| # | Subsystem | Einstieg | Modell | Persistenz |
|---|---|---|---|---|
| 1 | `SecondBrain/jobs/` | `JobManager` | `Job`, `JobType`, `JobStatus`, `Lease` | `JobStore` → **JSONL** |
| 2 | `SecondBrain/desktop/jobs/` | `JobManager` (Namensdublette) | `DesktopJob`, `JobState` | `JobHistory` in-memory |
| 3 | `SecondBrain/agent/background/` | `AgentJobManager` | `AgentJob`, `AgentJobStatus` | `AgentJobHistory` in-memory |
| 4 | `SecondBrain/importing/pipeline.py` | `WorkerPool` | `QueueJob`, `JobKind` | `QueueManager` dateibasiert |

Zwei davon exportieren eine Klasse namens `JobManager`. Ein Import `from ... import JobManager` sagt ohne Pfadkontext nicht, welches System gemeint ist.

### Der produktionsreife Pfad ist implementiert, aber nicht verdrahtet

`SecondBrain/jobs/` enthält eine vollständige, produktionstaugliche Runtime:

| Baustein | Pfad | Inhalt |
|---|---|---|
| `PostgresJobRepository` | `jobs/repository.py:44` | `FOR UPDATE SKIP LOCKED` (Z. 91), Leases, Checkpoints, optimistische Versionierung, Workspace-Bindung in jeder Signatur |
| `create_job_repository` | `jobs/repository.py:264` | Backend-Factory mit Guard `jsonl_not_allowed_in_production` (Z. 272) |
| `JobHandlerRegistry`, `JobWorker`, `JobContext` | `jobs/worker.py` | Handler-Registrierung, Heartbeat, Checkpoint, Cancel |
| `submit_import_job`, `register_import_handler`, `submit_planner_job`, `register_planner_handler` | `jobs/integrations.py` | Adapter für Import und Planner v2 |

**Diese Bausteine werden von keinem produktiven Einstiegspunkt instanziiert.** Verifiziert per `git grep`:

- `create_job_repository` — Treffer nur in `jobs/repository.py` und `tests/test_job_repository.py`
- `PostgresJobRepository` — Treffer nur in der eigenen Datei, vier Testdateien und `docs/jobs/long_running_jobs_architecture.md`
- `jobs.integrations` — Treffer nur in Testdateien
- kein `from ... jobs.repository import` irgendwo unter `SecondBrain/`

Es handelt sich also **nicht um toten Code**, sondern um eine getestete, aber unverdrahtete Runtime. Der Unterschied ist erheblich: der Migrationsaufwand liegt in der Verdrahtung, nicht in der Implementierung.

Zusätzlich: die vier Testdateien treiben `PostgresJobRepository` über einen `SqliteExecutor`, nicht über PostgreSQL. Das Verhalten des Produktionsbackends ist damit auch testseitig unbelegt.

Produktiv verdrahtet ist stattdessen `JobStore` aus `service.py`, laut eigenem Docstring „JSONL-backed job repository". Das widerspricht Projektregel 13.

### Drift in der bestehenden Architekturdokumentation

`docs/jobs/long_running_jobs_architecture.md` behauptet für v31.17:

> „Import Pipeline und Planner v2 sind als erste zwei fachliche Handler an die zentrale Runtime angebunden."

Auf Adapterebene stimmt das — `jobs/integrations.py` existiert. Zur Laufzeit ruft diese Adapter niemand außer den Tests auf. Die Aussage ist damit dieselbe Art von Dokumentationsdrift, die Prompt 67 im Masterplan bereinigt hat, nur eine Ebene tiefer.

---

## Zielbild: der bestehende Vertrag von `SecondBrain/jobs/`

Subsystem 1 ist das mit Abstand vollständigste und damit das Migrationsziel. Es erfüllt den in Prompt 70 Phase 3 geforderten Vertrag bereits weitgehend.

`JobManager` (`SecondBrain/jobs/service.py`):

```
enqueue    approve    claim      heartbeat   checkpoint
complete   fail       pause      resume      cancel
recover_stale         graceful_shutdown
metrics    queue_snapshot
```

`Job` (`SecondBrain/jobs/models.py`) persistiert: `workspace_id`, `status`, `payload_reference`, `progress`, `checkpoint`, `retry`, `error_code`, `error_summary`, `version`, `created_at`, `updated_at`, `completed_at`.

Bemerkenswert und korrekt: `payload_reference` ist ausdrücklich als „pointer only - never the payload" kommentiert. Phase 4 („keine sensiblen Nutzinhalte im Job-Record") ist im Modell bereits umgesetzt.

`JobStatus` deckt alle geforderten Zustände ab, einschließlich `WAITING_FOR_APPROVAL` und `RECOVERY_REQUIRED`.

`JobType` kennt bereits: `import`, `connector_sync`, `embedding`, `reindex`, `graph_extraction`, `memory_consolidation`, `agent_plan`, `backup`, `restore`, `diagnostics`.

`JobHandlerRegistry` und `JobWorker` in `jobs/worker.py` ergänzen Handler-Registrierung, `JobContext.heartbeat`, `JobContext.checkpoint` und `JobContext.cancelled`.

**Fehlende Vertragsbestandteile gegenüber Prompt 70 Phase 3:** `validate`, `prepare`, `cleanup`. Die Registry nimmt beliebige Callables entgegen und erzwingt diese drei Schritte nicht.

**Fehlende Klassifizierung gegenüber Phase 5:** Kein Feld für `idempotent` / `conditionally_idempotent` / `non_idempotent`. Ohne dieses Feld kann die Runtime nicht entscheiden, ob ein Job automatisch wiederholt werden darf — die zentrale Sicherheitsanforderung aus Projektregel 15.

---

## Kandidaten

Bewertung der Spalten:

- **Dauer**: `kurz` < 5 s, `mittel` 5–60 s, `lang` > 60 s oder unbegrenzt
- **Idempotenz**: nach Phase-5-Schema
- **Risiko**: Auswirkung eines Doppellaufs oder Abbruchs

### A — Konkurrierende Job-Subsysteme (Migration zwingend)

| Pfad | Jobtyp | Aktuelle Runtime | Dauer | Idempotenz | Risiko | Migration | Zielhandler |
|---|---|---|---|---|---|---|---|
| `SecondBrain/desktop/jobs/job_manager.py` | Desktop-Jobs | eigener `JobManager` + `BackgroundExecutor` | mittel | unbekannt | hoch — Namensdublette zu Subsystem 1 | ja | `jobs.JobManager` |
| `SecondBrain/desktop/jobs/background_executor.py` | Ausführung | `ThreadPoolExecutor(max_workers=2)` | — | — | mittel — kein Lease, kein Recovery | ja | `jobs.worker` |
| `SecondBrain/agent/background/agent_job_manager.py` | Agentenläufe | `AgentJobManager` + `AgentRetryPolicy` | lang | conditionally_idempotent | hoch — eigene Retry-Policy neben Runtime-Retry | ja | `JobType.AGENT_PLAN` |
| `SecondBrain/importing/pipeline.py` | Import | `WorkerPool` mit eigenen Threads, `QueueManager`, `DeadLetterQueue`, `RetryManager` | lang | conditionally_idempotent | hoch — vollständige Parallelinfrastruktur | ja | `JobType.IMPORT` |

### B — Langläufer mit eigenen Threads (Migration erforderlich)

| Pfad | Jobtyp | Aktuelle Runtime | Dauer | Idempotenz | Risiko | Migration | Zielhandler |
|---|---|---|---|---|---|---|---|
| `SecondBrain/document_center/core.py` | Dokumentverarbeitung / OCR | `threading.Thread` | lang | idempotent | mittel | ja | neuer `JobType.OCR` |
| `SecondBrain/native/streaming_import_panel.py` | Import-UI | `threading.Thread` | lang | conditionally_idempotent | mittel — UI-Thread ohne Job-Tracking | ja | `JobType.IMPORT` |
| `SecondBrain/service_runtime/runtime.py` | Dienstlauf | `threading.Thread` | lang | unbekannt | mittel | prüfen | — |
| `SecondBrain/connector_runtime/center.py` | Connector Sync | `threading.Thread` | lang | conditionally_idempotent | **hoch** — externe Writes | ja | `JobType.CONNECTOR_SYNC` |
| `SecondBrain/jarvis_hud_server.py` | HUD-Server | `threading.Thread`, 1862 LOC | dauerhaft | non_idempotent | niedrig — Serverprozess, kein Job | nein | — |
| `SecondBrain/desktop_native/app.py` | Desktop-Shell | `threading.Thread` + `Queue`, 1092 LOC | dauerhaft | — | niedrig — GUI-Eventloop | nein | — |
| `SecondBrain/desktop_native/wake_word.py` | Wake Word | `threading.Thread` | dauerhaft | — | niedrig — Audio-Listener | nein | — |
| `SecondBrain/voice/assistant.py` | Voice | `threading.Thread` | dauerhaft | — | niedrig — Audio-Listener | nein | — |
| `SecondBrain/chat/streaming.py` | Chat-Streaming | `threading.Thread` | mittel | — | niedrig — Antwortstrom | nein | — |
| `SecondBrain/gui/secret_manager_panel.py` | Vault-UI | `threading.Thread` | kurz | idempotent | niedrig | nein | — |
| `SecondBrain/agent/tool_registry.py` | Tool-Discovery | `threading.Thread` + Retry-Loop | mittel | idempotent | niedrig | nein | — |

### C — Eigene Pools (Bewertung erforderlich)

| Pfad | Jobtyp | Aktuelle Runtime | Dauer | Idempotenz | Risiko | Migration | Zielhandler |
|---|---|---|---|---|---|---|---|
| `SecondBrain/planner_v2/service.py` | Planner | `ThreadPoolExecutor`, Ressourcen-Locks | lang | conditionally_idempotent | mittel — Approval-Knoten bleiben korrekt seriell | prüfen | `JobType.AGENT_PLAN` |
| `SecondBrain/monitoring/operations_monitor.py` | Monitoring | `ThreadPoolExecutor` | mittel | idempotent | niedrig | nein | — |
| `SecondBrain/personal_dashboard/runtime.py` | Dashboard-Reads | `ThreadPoolExecutor` | kurz | idempotent | niedrig — parallele Reads mit Timeout | nein | — |
| `SecondBrain/agent/review_approval_gate.py` | Gate | `ThreadPoolExecutor` | mittel | idempotent | niedrig | nein | — |
| `SecondBrain/agent/review_approval_release_gate.py` | Gate, 1150 LOC | `ThreadPoolExecutor` | lang | idempotent | niedrig | nein | — |
| `SecondBrain/release/approval_postgres_live_gate.py` | Live-Gate | `ThreadPoolExecutor` | lang | idempotent | niedrig | nein | — |
| `SecondBrain/agent/parallel_executor.py` | Ausführung, 9 LOC | `ThreadPoolExecutor` | — | — | niedrig — Hilfsmodul | prüfen | — |

Gates laufen bewusst synchron und liefern einen Report. Sie gehören nicht in die Job-Runtime.

### D — Retry-Logik außerhalb der Runtime

| Pfad | Zweck | Bewertung |
|---|---|---|
| `SecondBrain/storage/db_retry.py` | Datenbank-Retry | behalten — Transportebene, nicht Jobebene |
| `SecondBrain/connector_runtime/resilience.py` | Connector-Retry | **prüfen** — darf nie Mail Send, Forward, Delete, Calendar Write oder Publish wiederholen |
| `SecondBrain/utils.py` | generisch | prüfen |
| `SecondBrain/agent/toolchain/executor.py` | Tool-Retry | behalten — Toolchain-Ebene |
| `SecondBrain/operations_v119.py` | Operations, 912 LOC | prüfen |
| `SecondBrain/desktop_native/lifecycle.py` | Single-Instance-Retry | behalten |
| `SecondBrain/native/approval.py` | Approval, 1451 LOC | **prüfen** — Retry im Approval-Pfad ist sicherheitsrelevant |

`connector_runtime/resilience.py` und `native/approval.py` sind die einzigen Retry-Stellen mit Bezug zu externen Schreibaktionen. Beide müssen gegen Projektregel 15 geprüft werden, bevor irgendetwas migriert wird.

---

## Großimport — Phase 6 ist besser erfüllt als angenommen

`SecondBrain/importing/streaming.py` (531 LOC) erfüllt die Anforderungen aus Prompt 70 Phase 6 bereits weitgehend:

| Anforderung | Stand |
|---|---|
| Streaming Parsing | erfüllt — `ijson`, einzige Nutzung im Projekt |
| ZIP | erfüllt — `zipfile.ZipFile` |
| Chunk Processing | erfüllt — `chunks`, `batch_size`, `DEFAULT_BATCH_SIZE` |
| Checkpoints | erfüllt — `CheckpointManager` |
| Resume | erfüllt — `bytes_processed`, `position`, `file_mtime_ns` |
| Fortschrittsanzeige | erfüllt — `ImportProgress.percent` |
| Abbruch | erfüllt — `control_state` |
| Kein Vollladen in den RAM | erfüllt — kein `json.load` auf die Exportdatei |
| Deduplizierung | teilweise — `skipped_documents` vorhanden, Strategie nicht belegt |
| Beschädigte Einzeldatei | unbelegt |

**Ausnahme:** `CheckpointManager` schreibt laut Docstring „in the existing RAG SQLite database". Für den Produktionsbetrieb ist das nach Projektregel 13 unzulässig. Das ist der eigentliche Migrationsbedarf beim Großimport — nicht das Streaming.

---

## Empfohlene Reihenfolge — abweichend von Prompt 70

Die in Prompt 70 vorgegebene Priorisierung (Reindex, Embedding Rebuild, Graph Extraction, …) setzt eine funktionierende Runtime voraus. Die ist nicht produktiv verdrahtet. Migrationen in diesen Zustand hinein erzeugen Arbeit, die später erneut anzufassen ist.

**Phase 1 — Vorhandene Runtime verdrahten, bevor irgendetwas migriert wird**

1. `create_job_repository` an den produktiven Einstiegspunkt hängen. Factory, Guard und Repository existieren und sind getestet — es fehlt ausschließlich der Aufruf. Ohne diesen Schritt ist jede Migration eine Migration nach JSONL.
2. `jobs/integrations.py` zur Laufzeit registrieren, nicht nur im Test.
3. `JobStore` auf Development und Tests beschränken. Der Guard existiert bereits in `create_job_repository`, greift aber nur, wenn die Factory auch aufgerufen wird.
4. `docs/jobs/long_running_jobs_architecture.md` korrigieren: Adapter vorhanden ist nicht dasselbe wie angebunden.

**Phase 2 — Vertrag vervollständigen**

5. `JobHandlerRegistry` um `validate`, `prepare`, `cleanup` erweitern.
6. Idempotenzklasse als Pflichtfeld am Job. Ohne dieses Feld darf die Runtime nicht automatisch wiederholen.

**Phase 3 — Sicherheitsrelevante Retry-Pfade prüfen**

7. `connector_runtime/resilience.py` und `native/approval.py` gegen Projektregel 15 prüfen.

**Phase 4 — Subsysteme zusammenführen, maximal zwei je Paket**

8. `SecondBrain/desktop/jobs/` → Subsystem 1
9. `SecondBrain/agent/background/` → `JobType.AGENT_PLAN`
10. `SecondBrain/importing/pipeline.py` → `JobType.IMPORT`
11. `connector_runtime/center.py` → `JobType.CONNECTOR_SYNC`
12. `document_center/core.py` → neuer `JobType.OCR`

**Phase 5 — Großimport-Checkpoints von SQLite auf PostgreSQL**

13. `CheckpointManager` in `importing/streaming.py`

---

## Nicht migrieren

Dauerhafte Listener und Serverprozesse sind keine Jobs. Sie in die Job-Runtime zu zwingen würde das Modell verfälschen:

`jarvis_hud_server.py`, `desktop_native/app.py`, `desktop_native/wake_word.py`, `voice/assistant.py`, `chat/streaming.py`

Gates laufen synchron und liefern Reports. Auch sie bleiben außerhalb.

---

## Abhängigkeit zu anderen Stufen

Phase 1 dieser Reihenfolge setzt ein funktionierendes PostgreSQL-Live-Gate voraus (Roadmap-Stufe 1, Prompt 68). Ohne `TEST_DATABASE_URL` lässt sich die Verdrahtung von `PostgresJobRepository` schreiben, aber nicht nachweisen.

Solange Prompt 68 zurückgestellt ist, ist Phase 1 implementierbar und nicht abnehmbar.
