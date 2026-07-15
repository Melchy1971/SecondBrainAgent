# Task- und Projektarchitektur v31.15

## Bestand und Wiederverwendung

Die zentrale Domain liegt in `SecondBrain/tasks`. Sie ergaenzt Planner-, Workflow- und native Workspace-Flaechen, ohne deren Modelle zu duplizieren. Freigaben verwenden `secondbrain.native.approval.NativeApprovalQueue`. Connectoren und Agent-Tools greifen ausschliesslich ueber `TaskProjectService` zu; jeder Zugriff bleibt an den aktiven Workspace gebunden.

## Komponenten und Datenmodell

`models.py` definiert Project, Task, TaskDependency und TaskEvent. `service.py` enthaelt die gemeinsame Geschaeftslogik. `repository.py` trennt Persistenz und Migration von der Domain. `agent_tools.py` stellt kontrollierte Tools bereit, `gui.py` asynchrone Listen- und Detailansichten.

Statusuebergaenge und Abhaengigkeitszyklen werden vor dem Speichern validiert. Optimistische Versionen verhindern unbemerkte konkurrierende Ueberschreibungen. Jede Task-Mutation erzeugt ein Audit-Ereignis.

## Persistenz und Migration

- Entwicklung: atomare JSONL-Ablage unter `runtime/tasks`.
- Produktion: `PostgresTaskRepository` ueber den vorhandenen SQLAlchemy-/Database-Executor.
- Produktionsmodus ohne `DATABASE_URL` wird blockiert; ein stiller JSONL-Fallback ist nicht zulaessig.
- Datensaetze sind durch Collection, Record-ID und Workspace isoliert; JSON-Daten und Version werden transaktional geschrieben.
- `migrate_jsonl_to_repository` validiert zunaechst alle Quelldaten. Dry-Run und fehlerhafte Reports schreiben nichts; erfolgreiche Migrationen erhalten IDs, Versionen und Events.

Ein echter PostgreSQL-Integrationstest benoetigt eine isolierte `TEST_DATABASE_URL`. Die automatisierten Repository-Tests verwenden zusaetzlich den vorhandenen SQL-Testexecutor und ersetzen keine Live-Abnahme.

## Berechtigungen und GUI

Lesen, lokale Erstellung und nicht-destruktive Aenderungen sind im aktiven Workspace erlaubt. Loeschen, externe Connector-Aenderungen, Kalendererstellung und Nachrichtenversand benoetigen Approval. Archivieren bleibt der Standard. Die Ansichten Aufgaben, Projekte, Heute, Ueberfaellig und Blockiert verwenden denselben Service und laden nach fehlgeschlagenen Schreibvorgaengen den persistierten Stand neu.
