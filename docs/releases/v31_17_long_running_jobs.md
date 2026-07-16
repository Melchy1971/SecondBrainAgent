# Jarvis v31.17 Long-Running Jobs

## Ergebnis

Die vorhandene Job-Runtime wurde zur PostgreSQL-first Basis fuer neustartfeste Langlaeufer erweitert. Es wurde keine zweite Queue aufgebaut. JSONL bleibt ausschließlich Development-Fallback; Produktion benoetigt eine konfigurierte PostgreSQL-Verbindung.

## Sicherheits- und Recovery-Eigenschaften

- Atomisches Claiming mit `FOR UPDATE SKIP LOCKED` auf PostgreSQL.
- Workspacegebundene Lese-, Claim- und Mutationsoperationen.
- Versionierte Jobs und Leases sowie eindeutige Idempotency Keys.
- Checkpoint-Erhalt nach Neustart und Lease-Ablauf.
- Nicht-idempotente Jobs wechseln bei unklarem Zustand zu `recovery_required`.
- Keine Payload-Inhalte in Job Monitor, Metriken oder Fehlerzusammenfassungen.
- Approval-Zustand wird persistent erhalten; externe Schreibhandler duerfen ihn nicht umgehen.

## Migrierte Jobtypen

Import und Planner v2 laufen ueber registrierte Adapter durch die zentrale Runtime. Connector Sync, Memory Consolidation, Backup und Reindex bleiben fuer weitere, jeweils auf zwei Typen begrenzte Migrationsphasen offen.

## Verifikation

Die vorgeschriebenen Repository-, Worker-, Recovery-, Import- und Planner-Tests sowie zusaetzliche Monitor-/Metriktests sind gruen. Der SQL-Vertrag wurde ueber den vorhandenen SQLite-Testexecutor geprueft. Ein echter PostgreSQL-Integrationstest bleibt umgebungsabhaengig und erfordert eine isolierte `TEST_DATABASE_URL`.
