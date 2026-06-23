# PATCH P1.2.3 - Connector Health Observability

## Ziel
Connector-Syncs nicht nur robust ausführen, sondern ihren Zustand releasefähig messbar machen.

## Änderungen

### Neu
- `secondbrain/connectors/health.py`
  - `HealthStatus`
  - `ConnectorHealthPolicy`
  - `ConnectorHealthSnapshot`
  - `ConnectorHealthEvaluator`
  - `ConnectorHealthReporter`
  - `InMemoryHealthSink`

### Tests
- `tests/test_p1_2_3_connector_health.py`

## Abgedeckte Fälle
- Erfolgreicher Sync wird `healthy`
- Partial Sync mit Dead Letter wird `degraded`
- Fataler Fetch-Fehler wird `failed`
- Dead-Letter-Schwelle degradiert auch ohne aktuellen Sync-Run
- Reporter schreibt Health-Snapshots in Sink

## Validierung

```text
454 passed in 13.79s
```

## Einordnung
P1.2 Connector-Schicht hat jetzt:
- inkrementellen Cursor-Sync
- Retry-Policy
- Dead-Letter-Queue
- Health/Observability-Snapshot

Nächster sinnvoller Schritt:
- P1.2.4 Connector Replay / Dead-Letter-Reprocessing
