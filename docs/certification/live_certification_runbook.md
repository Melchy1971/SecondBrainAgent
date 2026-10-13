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

## Anforderungen an das PostgreSQL-Gate

Einzeln ausführbar mit `python launcher.py postgres-live-gate`
(Report: `runtime/reports/postgres_live_gate.json`).

- **TLS mit Zertifikats- und Hostnamenprüfung:** `TEST_DATABASE_URL` muss
  `sslmode=verify-full` verwenden, bei eigener CA zusätzlich
  `sslrootcert=<pfad/ca.crt>`. `require` oder `verify-ca` blockieren über
  `tls_verify_full`, denn ohne Hostnamenprüfung ist ein Man-in-the-Middle möglich.
  Massgeblich ist der effektive sslmode der Verbindung (auch über `PGSSLMODE`).
- **Rolle ohne RLS-Umgehung:** kein Superuser, kein `BYPASSRLS`
  (`role_cannot_bypass_rls`). Benötigt werden nur `CONNECT` und `CREATE` auf der
  Testdatenbank; das Gate legt eigene Schemata an und entfernt sie wieder.
- **pgvector** muss in der Testdatenbank installiert sein (`CREATE EXTENSION vector`
  durch einen Administrator).

Geprüft werden unter anderem: RLS-Workspace-Isolation, Repository-Verträge,
Zeilensperren (ein konkurrierender Schreiber wird blockiert, die Sperre nach
Rollback freigegeben), echte parallele Schreiber (4 Threads mit eigener
Verbindung: keine verlorenen Updates, genau ein Gewinner bei gleichem
Idempotency Key, disjunkte und vollständige Vergabe per `SKIP LOCKED`) sowie
Rollback, Savepoint und Transaktionsabbruch nach Fehlern.

Zuletzt live bestanden am 2026-10-12: `PASS`, 45/45 Checks, gegen PostgreSQL 18.4
und pgvector 0.8.6 mit TLS 1.3, `verify-full`, `hostssl`-only und einer Rolle mit
`NOSUPERUSER NOBYPASSRLS`. Gegenproben (`sslmode=require`, fremde CA,
`BYPASSRLS`-Rolle) blockieren wie vorgesehen. Lokale Testinstanz, nicht die
Zielinstanz.

## Bekannte Grenzen

- Unter Docker Desktop für Windows ist `localhost` im DSN sehr langsam (libpq
  versucht zuerst IPv6; im Test 185 s statt 4 s). Dort `127.0.0.1` verwenden; das
  Serverzertifikat braucht dann einen IP-SAN, damit `verify-full` besteht.
- Ein Server ohne TLS blockiert den `postgres`- und `approval`-Bereich über den
  `transport_encryption`-Check des PostgreSQL-Gates.
