# v31.30 – Approval PostgreSQL Live Gate

## Ergebnis

`python launcher.py approval-postgres-live-gate` zertifiziert das bestehende
`PostgresReviewApprovalRepository` gegen eine reale, dedizierte Testdatenbank.
Das Gate liest ausschließlich `TEST_DATABASE_URL`; Produktionskonfiguration und
JSONL-Fallback werden nicht verwendet.

Der aktuelle Live-Status ist `BLOCKED`, weil in der Entwicklungsumgebung keine
`TEST_DATABASE_URL` konfiguriert ist. Offline-Vertragstests ersetzen diesen
Live-Nachweis nicht.

## Szenarien

- Approval erstellen, genehmigen, ablehnen und ablaufen lassen
- Persistenz nach neuer Repository-Instanz
- Workspace-Isolation
- Bindung von Actor, Action Type, Payload Hash, Connector, Empfänger, Anhängen,
  Event-/Ablaufzeit und Idempotency Key
- Erkennung einer veränderten gebundenen Payload
- zwei parallele Execution-Lease-Claims; exakt einer darf erfolgreich sein
- Completion, Audit und Replay-Sperre
- zwingendes PostgreSQL-Backend ohne Development-Fallback

Das Gate führt keine echten Mail-, Kalender-, Delete-, Forward- oder
Publish-Aktionen aus. Es zertifiziert die gemeinsame persistente
Exactly-once-/Recovery-Schicht; connector-spezifische Live-Writes bleiben dem
Connector-E2E-Gate vorbehalten.

## Isolation und Report

Jeder Lauf erzeugt ein zufälliges Schema `sb_approval_gate_*` und entfernt es in
einem `finally`-Pfad vollständig. Bestehende Tabellen werden nicht geleert.

Der redigierte Report liegt unter
`runtime/reports/approval_postgres_live_gate.json`. Er enthält weder DSN noch
Benutzer, Passwort, Host oder Nutzinhalte. `PASS` liefert Exitcode 0, `BLOCKED`
Exitcode 2.

```powershell
$env:TEST_DATABASE_URL = "<dedizierte PostgreSQL-Testdatenbank>"
python launcher.py approval-postgres-live-gate
```
