# Persistente Long-Running-Job-Runtime v31.17

## Bestand

Die verbindliche Basis ist `SecondBrain/jobs`: `models.py` definiert Jobs und Leases, `service.py` stellt den persistenten Manager bereit und `gui.py` den bestehenden Job Monitor. Dieses Subsystem wird erweitert; es entsteht keine zweite Queue.

Daneben existieren spezialisierte Laufzeiten: Streaming-/Upload-Queues fuer Importe, Connector-Scheduler und Sync-Runner, `AgentPlanStore` und Planner-v2-Checkpoints, Memory Consolidation, Reindex-Scheduler, Backup-/Restore-Manager, Background-Agent-/Desktop-Worker sowie mehrere Event-Busse und Monitoring-Projektionen. Diese bleiben waehrend der schrittweisen Migration als Adapter oder fachliche Handler erhalten.

## Zielarchitektur

```text
Import / Connector / Planner / Memory / Backup / Reindex
                         |
                 Handler-Adapter
                         |
              zentrale Job Runtime
        Registry | Worker | Retry | Approval
                         |
         PostgreSQL JobRepository
             Jobs | Leases | Audit
                         |
             Job Monitor / Metrics
```

Payloads werden nie in der Queue gespeichert, sondern nur ueber `payload_reference` adressiert. Jeder Repository-Zugriff ist an `workspace_id` gebunden. JSONL bleibt ein expliziter Development-Fallback; Produktion blockiert ohne PostgreSQL-Konfiguration.

## Statusmodell

Der Lebenszyklus verwendet `queued`, `claimed`, `running`, `paused`, `waiting_for_approval`, `retrying`, `completed`, `failed`, `cancelled` und `recovery_required`. Terminale Jobs werden nicht erneut ausgefuehrt. `claimed` trennt das atomare Repository-Claim vom Start des Handlers.

Prioritaeten sind `low`, `normal`, `high` und `critical`; innerhalb derselben Prioritaet gilt FIFO. Unterstuetzte Typen sind Import, Connector Sync, Embedding, Reindex, Graph Extraction, Memory Consolidation, Agent Plan, Backup, Restore und Diagnostics.

## Lease- und Recovery-Modell

PostgreSQL claimt mit `SELECT ... FOR UPDATE SKIP LOCKED` in einer Transaktion. Eine separate Lease bindet Job, Worker, Akquisitionszeit, Heartbeat und Ablaufzeit. Heartbeats verlaengern nur die eigene aktive Lease. Abgelaufene idempotente Jobs werden mit erhaltenem Checkpoint erneut eingereiht; nicht-idempotente oder hinsichtlich externer Wirkung unklare Jobs wechseln zu `recovery_required`.

Optimistische Versionierung schuetzt alle Mutationen. Eindeutige Idempotency Keys verhindern doppelte Jobs und doppelte Abschluesse. Graceful Shutdown gibt idempotente Jobs kontrolliert frei und erhaelt Approval- sowie Checkpoint-Zustand.

## Retry- und Approval-Regeln

Retries sind begrenzt, verwenden Backoff und gelten nur fuer als idempotent deklarierte Handler. Send, Delete, Forward, Publish und Connector Writes sind approvalpflichtig und werden niemals automatisch wiederholt. Approval ist an Workspace, Job, Aktion und Payload-Referenz beziehungsweise deren Hash gebunden. Eine veraenderte Bindung invalidiert die Freigabe.

Fehlerzusammenfassungen enthalten nur kontrollierte Fehlercodes und redigierte technische Angaben. Payloads, Secrets und Nutzinhalte gelangen weder in Logs noch in Metriken oder Hauptansichten.

## Migrationspfad

1. Vorhandenes Modell und API kompatibel erweitern; JSONL-Tests bleiben fuer Entwicklung bestehen.
2. PostgreSQL-Repository und Worker Registry hinter gemeinsamen Protokollen einfuehren.
3. Pro Phase hoechstens zwei Jobtypen ueber Adapter migrieren: zuerst Import und Planner, danach Connector/Memory, danach Backup/Reindex.
4. Job Monitor und Monitoring auf die zentrale read-only Projektion umstellen.
5. Legacy-Queues erst entfernen, wenn Restart-, Lease-, Approval- und Datenintegritaetstests fuer den jeweiligen Typ gruen sind.
