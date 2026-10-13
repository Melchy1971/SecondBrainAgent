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

## Anforderungen an das Approval-PostgreSQL-Gate

Einzeln ausführbar mit `python launcher.py approval-postgres-live-gate`
(Report: `runtime/reports/approval_postgres_live_gate.json`). Gleiche
`TEST_DATABASE_URL` wie das PostgreSQL-Gate; `sslmode=verify-full` ist auch hier
Pflicht (`tls_verify_full`).

Nachgewiesen wird gegen die produktive Klasse `PostgresReviewApprovalRepository`:

- **Freigaben:** approve, reject, expire sowie deferred → approved.
- **Konkurrierende Entscheidungen:** 4 Reviewer entscheiden gleichzeitig
  (approve gegen reject, je eigene Verbindung): genau eine Entscheidung gewinnt,
  nur sie steht im Audit. Zwei Reviewer mit gleicher erwarteter Version: genau
  einer setzt sich durch. Eine doppelte Entscheidung wird nicht doppelt erfasst.
- **Persistente Zustandsübergänge:** Jede Prüfung liest über eine neue
  Verbindung (Neustart-Nachweis). Versionen steigen streng monoton, das Audit
  zeigt approved → executing → completed in dieser Reihenfolge. Unzulässige
  Übergänge (rejected/expired/completed → approved, approved → rejected) werden
  abgewiesen und ändern weder Status noch Version; workspace-fremde Entscheidungen
  greifen nicht.
- **Ausführung und Recovery:** genau einer von 4 parallelen Executoren erhält die
  Lease, Replay ist gesperrt; nach Verlust der Lease (recovery_required) übernimmt
  ein neuer Executor, der abgelöste kann nicht mehr abschließen.
- **Manipulation:** Eine direkt in der Datenbank veränderte Payload ist über den
  Binding-Hash erkennbar.

Zuletzt live bestanden am 2026-10-12: `PASS`, 27/27 Checks, 20 von 20
Wiederholungen. Der Gewinner der konkurrierenden Entscheidung wechselte zufällig
(11× rejected, 9× approved), es gewann aber stets genau einer. Gegenprobe
`sslmode=require` blockiert. Lokale Testinstanz, nicht die Zielinstanz.

## Disaster-Recovery-Gate (pg_dump / pg_restore)

Einzeln ausführbar mit `python launcher.py disaster-recovery-gate`
(Report: `runtime/reports/disaster_recovery_gate.json`). PASS gibt es nur, wenn
der echte Datenbankpfad gelaufen ist; ohne Werkzeuge oder `TEST_DATABASE_URL`
höchstens `CONDITIONAL_PASS`.

Voraussetzungen:

- PostgreSQL-Clientwerkzeuge im `PATH`: `pg_dump`, `pg_restore`, `psql`,
  `createdb`, `dropdb` (gleiche Hauptversion wie der Server).
- `TEST_DATABASE_URL` mit `sslmode=verify-full`; die TLS-Parameter werden an die
  Werkzeuge weitergereicht (`PGSSLMODE`, `PGSSLROOTCERT`). Andere sslmodes
  blockieren über `pg_tls_verify_full`.
- Rolle mit `CREATEDB` für die temporären Restore-Ziele (kein Superuser nötig).
- **Restore-Template**, sobald nicht vertrauenswürdige Extensions wie pgvector
  genutzt werden: Eine Rolle ohne Superuser-Recht kann `vector` in einer leeren
  Datenbank nicht anlegen; der Restore scheitert dann mit
  `permission denied to create extension`. Ein Administrator legt einmalig an:

  ```sql
  CREATE DATABASE sb_dr_template;
  ALTER DATABASE sb_dr_template WITH IS_TEMPLATE true;
  \connect sb_dr_template
  CREATE EXTENSION vector;
  ```

  und setzt `DR_RESTORE_TEMPLATE=sb_dr_template`. Das Template enthält nur
  Extensions, keine Tabellen. Die entsprechenden `EXTENSION`- und
  `COMMENT ON EXTENSION`-Einträge des Dumps werden beim Restore übersprungen.

Ablauf: Das Gate legt eigene Testdaten an (25 Approvals mit Payload-Hash,
lückenloses Audit mit 50 Einträgen, 30 Vektoren in der Projektdimension 3072 mit
dem produktiven `halfvec`-HNSW-Index aus `secondbrain.storage.vector_index`), erstellt einen
echten Dump im Custom-Format und spielt ihn in eine nachweislich leere Datenbank
zurück. Verglichen werden Tabellenmenge, Zeilenzahlen und Prüfsummen; der Recall
zählt nur, wenn der Ausführungsplan den wiederhergestellten HNSW-Index nutzt. Für den
Fehlerfall wird ein Dump im Verzeichnisformat so beschädigt, dass der Restore
erst beim letzten Datenblock scheitert; `--single-transaction` muss dann alles
zurückrollen. Testdaten, temporäre Datenbanken und Arbeitsdateien werden immer
entfernt.

Zuletzt live bestanden am 2026-10-13: `PASS`, 26/26 Checks, 5 von 5 Läufen,
PostgreSQL 18.4 und Clientwerkzeuge 18.4 unter Linux (Container), `verify-full`,
Rolle `NOSUPERUSER NOBYPASSRLS CREATEDB`. Der Fehlerfall scheiterte jeweils erst,
nachdem 3 Tabellen angelegt und 2 befüllt waren, und hinterließ nichts.
Gegenproben: ohne `--single-transaction` blieben 3 Tabellen mit 25/50 Zeilen
zurück (die Rollback-Prüfung erkennt das); `sslmode=require` und ein Restore ohne
Template blockieren. Unter Windows ist der Datenbankteil nicht live belegt,
weil dort die Clientwerkzeuge fehlten.

## Commit-gebundene Nachweise und jarvis-1.0-gate

`python launcher.py jarvis-1.0-gate` führt keine Gates aus. Es prüft die unter
`runtime/reports/` gespeicherten Berichte von zwölf Gates und blockiert jeden
Bericht, der nicht für den aktuellen Commit, die geforderte Umgebung und
unverändert erzeugt wurde.

Jeder Produzent versiegelt seinen Bericht über `secondbrain.release.evidence.seal`:

| Feld | Bedeutung |
|---|---|
| `schema` | Berichtsschema des Gates |
| `commit_sha` | `git rev-parse HEAD` beim Lauf |
| `worktree_clean` | keine uncommitteten Änderungen an versionierten Dateien; sonst blockiert der Aggregator (`dirty_worktree`) |
| `environment` | `production` und `clean-windows` nur explizit über `SECONDBRAIN_EVIDENCE_ENVIRONMENT`; in GitHub Actions `ci`; sonst `local` |
| `generated_at` / `expires_at` | UTC, 24 Stunden gültig |
| `evidence_sha256` | SHA-256 über alle übrigen Felder |

Produzenten:

| Nachweis | Kommando | geforderte Umgebung |
|---|---|---|
| PostgreSQL | `postgres-live-gate` | production |
| Approval | `approval-postgres-live-gate` | production |
| Provider | `provider-live-gate` | production |
| Connector-E2E | `connector-e2e-gate` (Release-Umfang über `REQUIRED_E2E_CONNECTORS`) | production |
| Runtime-Architektur | `runtime-architecture-gate` | production |
| Native Voice App | `native-voice-app-gate` | production |
| Disaster Recovery | `disaster-recovery-gate` | production |
| OS-Keyring | `os-keyring-gate` | production |
| Windows-Installer | `windows-installer-gate` | clean-windows |
| Testsuite | `evidence-full-pytest` | ci |
| Versionssync | `evidence-version-sync` | ci |
| CI des Commits | `evidence-ci-commit` (GitHub-Check-Runs genau dieses Commits) | ci (fest, die Fakten stammen aus der CI) |

Ablauf: alles committen, Nachweise in der jeweiligen Umgebung erzeugen, dann
`jarvis-1.0-gate` ausführen. Jeder neue Commit macht alle Nachweise ungültig.
Lokal erzeugte Nachweise tragen `environment=local` und können das Gate daher
nicht bestehen; das ist beabsichtigt.

Das Runtime-Architektur-Gate prüft: `gui/launch` startet die kanonische
Job-Runtime; eine Job-Runtime in Produktion ohne Datenbank ist für jede
verwendete Schreibweise der Produktionsvariable `blocked`; kein zweiter
Job-Scheduler wird außerhalb seines Definitionsmoduls instanziiert. Native Voice
ordnet seine Checks den Komponenten `desktop` und `voice` zu;
Querschnittsprüfungen zählen für beide.

## Bekannte Grenzen

- Unter Docker Desktop für Windows ist `localhost` im DSN sehr langsam (libpq
  versucht zuerst IPv6; im Test 185 s statt 4 s). Dort `127.0.0.1` verwenden; das
  Serverzertifikat braucht dann einen IP-SAN, damit `verify-full` besteht.
- Ein Server ohne TLS blockiert den `postgres`- und `approval`-Bereich über den
  `transport_encryption`-Check des PostgreSQL-Gates.
