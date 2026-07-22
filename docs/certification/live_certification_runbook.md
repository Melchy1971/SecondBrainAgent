# Runbook: Live-Zertifizierung

Stand: 2026-07-21
Kommando: `python launcher.py live-certification [--scope <bereich>]`
Orchestrator: `SecondBrain/release/live_certification.py`
Report: `runtime/reports/live_certification_summary.json`

## Zweck

Ein Runner, der die vorhandenen Live-Gates ausführt und ihren Status gemeinsam
auswertet. Er schreibt keine Gates neu — er ruft sie auf und aggregiert.

## Bereiche

| Scope | Gate | Konfiguration | Pflicht machbar |
|---|---|---|---|
| `postgres` | PostgreSQL-/pgvector-Live-Gate | `TEST_DATABASE_URL` | ja |
| `approval` | Approval-PostgreSQL-Gate | `TEST_DATABASE_URL` | ja |
| `provider` | Provider-Live-Gate | `LIVE_PROVIDERS` | ja |
| `gmail` | Connector-E2E-Gate | `GMAIL_TEST_ACCOUNT` | ja |
| `outlook` | Connector-E2E-Gate | `OUTLOOK_TEST_ACCOUNT` | ja |
| `google-calendar` | Connector-E2E-Gate | `GOOGLE_CALENDAR_TEST_ACCOUNT` | ja |
| `microsoft-calendar` | Connector-E2E-Gate | `MICROSOFT_CALENDAR_TEST_ACCOUNT` | ja |
| `all` | alle oben | — | — |

## Statusregeln

Der Gesamtstatus folgt festen Regeln, damit ein Teilerfolg nicht als
Vollzertifizierung erscheint:

- **BLOCKED** — mindestens ein Bereich ist blockiert, oder ein als Pflicht
  markierter Bereich ist nicht konfiguriert.
- **CONDITIONAL_PASS** — kein Blocker, aber mindestens ein Bereich ist nur
  bedingt bestanden oder wurde übersprungen.
- **PASS** — jeder ausgeführte Bereich besteht und kein Bereich wurde
  übersprungen.

Ein nicht konfigurierter **optionaler** Bereich ist `SKIPPED` und kein Blocker.
Das ist die Kernanforderung: die Zertifizierung soll nicht daran scheitern, dass
ein optionaler Connector kein Testkonto hat.

## Pflichtbereiche festlegen

```
LIVE_CERTIFICATION_REQUIRED="postgres,approval"
```

Ein Pflichtbereich ohne Konfiguration führt zu `BLOCKED` statt `SKIPPED`.

## Ablauf

1. Konfiguration setzen — siehe `config/live-certification.example.toml`. Keine
   Secrets in Dateien; alles über Umgebungsvariablen.
2. Einzelbereich zuerst, um Konfiguration zu prüfen:
   ```
   python launcher.py live-certification --scope postgres
   ```
3. Volllauf:
   ```
   python launcher.py live-certification --scope all
   ```
4. Report unter `runtime/reports/live_certification_summary.json` auswerten.

## Exit-Codes

- `0` — `PASS` oder `CONDITIONAL_PASS`
- `2` — `BLOCKED`

## Sicherheit

- Der Orchestrator fügt dem Report keine Umgebungswerte hinzu. Redaktion ist
  Sache der einzelnen Gates.
- Externe Schreibaktionen (Mail Send/Forward/Delete, Calendar Write, Publish)
  laufen ausschließlich über das Approval-System und werden bei unklarem
  Ergebnis nicht automatisch wiederholt — erzwungen durch die Gates, nicht durch
  den Orchestrator.
- Die produktive `DATABASE_URL` wird nie gelesen; die Datenbankbereiche nutzen
  ausschließlich `TEST_DATABASE_URL`.

## Bekannte Grenzen

- Das PostgreSQL-Gate erreicht höchstens `CONDITIONAL_PASS`, solange dessen
  Phase 3 (Repository-Verträge) nicht implementiert ist. Der Gesamtlauf erbt das.
- Ein Server ohne TLS blockiert den `postgres`- und `approval`-Bereich über den
  `transport_encryption`-Check des PostgreSQL-Gates.
