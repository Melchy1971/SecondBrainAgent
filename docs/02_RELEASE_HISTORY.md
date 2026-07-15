# Release-Historie

Diese Datei beschreibt nur die Hauptlinie. Einzelne, auditierbare Release-Notizen bleiben unter [`releases/`](releases/).

## v6 bis v16: Foundations

- Import, lokales RAG, Connector-, Agent-, Desktop-, Voice- und Mobile-Grundlagen aufgebaut.
- SQLite-Persistenz, Knowledge Graph, Long-Term Memory und Service-/Installer-Scaffolds ergaenzt.
- Viele dieser Versionsmodule bleiben aus Kompatibilitaetsgruenden im Code, sind aber nicht mehr die aktuelle Bedienoberflaeche.

## v17 bis v18: Runtime und Reproduzierbarkeit

- P0 Doctor, Readiness, Bootstrap, Production Gate und Artifact Audit eingefuehrt.
- Repo Doctor, Dependency Inventory, Packaging und Release Workflow gehaertet.
- P1 Parser/Ingest, Provider Health, Golden Retrieval und Production Gate aufgebaut.

## v19 bis v28: Stores und Produktbereiche

- PostgreSQL/pgvector Foundation, Store Interface und Store-backed Ingest eingefuehrt.
- Memory, Agent Runtime, Connector Runtime, GUI, Voice und Mobile iterativ erweitert.
- GA-Hardening und GA-Artefakte dokumentiert.

## v30.0 bis v30.18: Production- und Embedding-Schicht

- Provider Layer, PostgreSQL/pgvector Production und Connector-/Workflow-Fundament erweitert.
- Provider Health, Golden Quality, Dimensionsvertrag und Index-Identitaet gehaertet.
- Reparaturpfad fuer Provider-/Modell-/Dimensionsdrift eingefuehrt.

## v30.19 bis v30.24: GUI und Runtime Truth

- P1-Oberflaechen, einheitlicher GUI-Start und Application Bootstrap umgesetzt.
- Document und Memory Center an reale Runtime-Zustaende angebunden.

## v30.25: Native Desktop und deutsche Sprachsteuerung

- Native Desktop-App als Standardstart eingefuehrt.
- Deutsche Text-/Sprachkommandos und Bestaetigungsgrenzen integriert.
- Web-HUD als optionaler Kompatibilitaetsmodus beibehalten.

## v31.01 bis v31.04: Distribution und GA-Gates

- Signierten Auto-Updater mit Hashpruefung, Migration Safety und Rollback aufgebaut.
- Reproduzierbare Windows-Installer-/Portable-Artefakte und CI/CD-Releaseautomation ergaenzt.
- GA-Readiness-Gate als verbindliche Aggregation der vorhandenen kritischen Gates eingefuehrt.

## v31.05 bis v31.14: Persoenliche Arbeitsbereiche

- Task-/Projektverwaltung, Kalender-, Mail- und Briefing-Assistenten integriert.
- Knowledge Graph, Memory Consolidation, Planner v2 und recoverable Long-running Jobs ergaenzt.
- Proaktive Assistenz und ein gemeinsames persoenliches Dashboard bereitgestellt.

## Nacharbeiten v31.15 und v31.16

- v31.15: produktives PostgreSQL-Repository und validierende JSONL-Migration fuer Tasks/Projekte (`feature/v31.15-task-postgres`, noch nicht in `main`).
- v31.16: echte parallele Planner-Ausfuehrung mit Approval-Serialisierung, Ressourcen-Locks und konsistenten Recovery-Checkpoints (`feature/v31.16-planner-parallel-runtime`, noch nicht in `main`).

## v31.17: Persistente Long-Running-Job-Runtime

- Vorhandenes `SecondBrain/jobs`-Subsystem als einzige zentrale Runtime konsolidiert.
- PostgreSQL-Repository mit atomaren Claims, Leases, Checkpoints, Recovery, Idempotency und Workspace Isolation ergaenzt.
- Worker-/Handler-Registry, Job Monitor und content-freie Betriebsmetriken bereitgestellt.
- Import und Planner v2 als erste zwei Jobtypen migriert; weitere Typen bleiben bewusst schrittweise offen.
