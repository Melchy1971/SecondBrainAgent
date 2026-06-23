# PATCH P1.2.2 - Connector Resilience

## Ziel
Connector-Sync gegen temporäre Fetch-Fehler, Item-Fehler und fortsetzbare Teilsynchronisation absichern.

## Geänderte Dateien

- `secondbrain/connectors/retry_policy.py`
- `secondbrain/connectors/dead_letter.py`
- `secondbrain/connectors/resilient_runner.py`
- `tests/test_p1_2_2_connector_resilience.py`

## Umsetzung

- Bounded Retry Policy mit deterministischem Backoff
- Retry nur für klassifizierte Fehler (`TimeoutError`, `ConnectionError` default)
- Dead-Letter-Queue für Fetch- und Item-Fehler
- Fatal Fetch Error: Cursor wird nicht committed
- Item Error: Fehler wird isoliert, Sync läuft weiter, Cursor wird committed
- Retry Trace für Diagnose und spätere Observability

## Validierung

- Neue Tests: `5 passed`
- Scope: P1.2.2 Connector Resilience

## Restrisiko

- Persistente Dead-Letter-Backends fehlen noch
- Replay-Mechanik ist noch nicht umgesetzt
- Backoff schläft im Test nicht real, produktiv über injizierbaren Sleeper steuerbar
