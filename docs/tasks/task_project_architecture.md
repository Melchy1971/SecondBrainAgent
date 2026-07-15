# Task- und Projektarchitektur v31.05

## Bestand und Wiederverwendung

Die zentrale Domain liegt in `SecondBrain/tasks`. Sie ergänzt bestehende Planner-, Workflow- und native Workspace-Flächen, ohne deren Modelle zu duplizieren. Für Freigaben wird `secondbrain.native.approval.NativeApprovalQueue` wiederverwendet. Workspace-Grenzen werden bei jedem Lese- und Schreibzugriff geprüft; Connectoren und Agent-Tools greifen ausschließlich über `TaskProjectService` zu.

## Komponenten und Datenmodell

`models.py` definiert Project, Task, TaskDependency und TaskEvent samt Status-, Prioritäts- und Abhängigkeitstypen. `service.py` ist die gemeinsame Geschäftslogik für Nutzer, Agenten, Dokumentextraktion und Connectoren. `agent_tools.py` stellt die kontrollierten Tools bereit. `gui.py` liefert asynchrone, ID-freie Listen- und Detailansichten.

Statusübergänge werden explizit validiert. Abhängigkeiten werden vor dem Speichern auf Zyklen geprüft. Projektfortschritt ergibt sich aus erledigten Aufgaben. Versionen werden optimistisch geprüft, damit konkurrierende Änderungen nicht unbemerkt überschrieben werden. Jede Task-Mutation erzeugt ein Audit-Ereignis.

## Persistenz, Migration und Berechtigungen

Die JSONL-Ablage unter `runtime/tasks` bleibt ausschließlich lokaler Entwicklungsfallback und schreibt atomar über temporäre Dateien. `PostgresTaskRepository` verwendet in Produktion die bestehende Datenbank-/Executor-Runtime, parametrisierte SQL-Abfragen, Workspace-Schlüssel, Row Locks und optimistische Versionen. `create_task_repository` blockiert JSONL sowie eine fehlende PostgreSQL-URL im Produktionsprofil; ein stiller Fallback ist ausgeschlossen.

`migrate_jsonl_to_repository` validiert zunächst alle Collections als Dry-Run, meldet ungültige Zeilen und doppelte IDs ohne Inhalte auszugeben und schreibt erst, wenn die vollständige Prüfung `ready` ergibt. IDs, Workspace-Zuordnungen, Versionen und Audit-Ereignisse bleiben erhalten. Dadurch kann ein Fehler in einer späteren Collection keinen Teilimport verursachen.

Lesen, lokale Erstellung und nicht-destruktive Änderungen sind innerhalb des aktiven Workspace erlaubt. Löschen, externe Connector-Änderungen, Kalendererstellung und Nachrichtenversand benötigen eine Approval. Archivieren ist der Standard statt Löschen. Logs und GUI-Hauptflächen enthalten keine technischen IDs oder vertraulichen Inhalte.

## GUI-Integration

Die Module Aufgaben, Projekte, Heute, Überfällig und Blockiert verwenden denselben Service. Listen, Kanban, Projektübersicht, Quellenbezug und Detailansicht werden daraus abgeleitet. Fehler bleiben auf das jeweilige Modul begrenzt; nach fehlgeschlagenen Schreibvorgängen wird der persistierte Stand neu geladen.
