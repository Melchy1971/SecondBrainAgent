# v30.86 – Review-/Approval-Governance Release Gate

## Ergebnis

Das Kommando `python launcher.py review-approval-release-gate` zertifiziert den
Review- und Approval-Layer nur dann mit `PASS`, wenn alle kritischen Prüfungen
erfolgreich sind und ein erreichbares PostgreSQL-Backend konfiguriert ist.
JSONL bleibt als Development-Backend verfügbar, ist für eine produktive
Zertifizierung jedoch ein harter Blocker.

Der maschinenlesbare Report wird atomisch nach
`runtime/reports/review_approval_release_gate.json` geschrieben.

## Architektur

Das Release-Gate führt isolierte Laufzeitprüfungen für acht Gruppen aus:

1. Datenmodell: ReviewItem, ApprovalItem, Übergänge, Versionierung und
   Workspace-Isolation.
2. Agent: Pause, Approve, Resume, Reject, Defer, Idempotenz und persistierte
   Pläne.
3. Security: Mandatory Approval, Privacy Mode, Redaction und Schutz gegen den
   `confirmed=True`-Bypass.
4. Import: fehlgeschlagene, sensible und unsichere Klassifikationen sowie deren
   Entscheidungslebenszyklus.
5. Memory: sensible und unsichere Kandidaten, Privacy Mode, Secrets und
   Exactly-once-Speicherung.
6. Connector: Bindung an Scope-Diff, Payload-Hash, Workspace, Ablaufzeit und
   einmaligen Verbrauch.
7. Operations: Audit, Notifications, Metriken, Concurrency, Crash Recovery und
   Repository Health.
8. GUI: Inbox, Badge, Entscheidungen, kontrollierte Fehlerzustände und
   redaktierte Darstellung.

Das bestehende E2E-Gate bleibt die Grundlage für den Agent-/Approval-Datenfluss.
Das v30.86-Gate ergänzt produktive Backend- und Domänenprüfungen. Ausnahmen in
einzelnen Checks werden kontrolliert in einen Check-Status übersetzt; technische
Fehlermeldungen oder Verbindungsdaten werden nicht in den Report übernommen.

## Zustands- und Bewertungsmodell

- `PASS`: alle kritischen Checks sind erfolgreich; PostgreSQL ist erreichbar.
- `CONDITIONAL_PASS`: ausschließlich nichtkritische GUI- oder
  Reporting-Warnungen.
- `BLOCKED`: mindestens eine Sicherheits-, Persistenz- oder
  Ausführungsgarantie ist verletzt.

Insbesondere führen Approval-Bypass, doppelte Ausführung, fehlender Audit,
Secret- oder Privacy-Leak, Workspace-Verwechslung, Queue-Verlust, fehlende
Crash-Recovery, produktives JSONL oder ein nicht erreichbares PostgreSQL zu
`BLOCKED` und `release_recommendation=DO_NOT_RELEASE`.

## Sicherheitsregeln

- Delete, Send, External Write, Credential Change und Scope Change benötigen
  eine persistente Freigabe.
- Ein boolesches `confirmed=True` ist keine Freigabe.
- Connector-Freigaben sind an Scope-Diff, Payload-Hash, Workspace und
  Ablaufzeit gebunden und nur einmal konsumierbar.
- Secrets dürfen weder Queue, Audit, Report noch GUI-Detailansicht erreichen.
- Memory Writes werden durch Privacy- und Classification-Policies kontrolliert.
- Statusentscheidungen und Execution-Leases bleiben versions- und
  konfliktgeschützt.

## Backend-Betrieb

Produktiv erforderlich:

```text
REVIEW_APPROVAL_BACKEND=postgres
DATABASE_URL=postgresql://...
```

Es gibt keinen stillen Fallback auf JSONL. Ein nicht erreichbares PostgreSQL
erzeugt einen kontrollierten `BLOCKED`-Report und Exit-Code `2`.

## Bekannte Grenzen

- Der echte PostgreSQL-Healthcheck benötigt eine erreichbare produktionsnahe
  Datenbank und installierte SQLAlchemy-/PostgreSQL-Treiber.
- Headless Tests prüfen das GUI-ViewModel; ein realer Desktop-Rendercheck bleibt
  abhängig von einer verfügbaren Windows-Display-Session.
- Provider- und Connector-Liveprüfungen außerhalb des Governance-Layers bleiben
  separate Release-Gates.

## Rollback

1. Commit `test(release): certify review and approval governance layer`
   zurücknehmen.
2. Das vorherige Gate-Kommando bleibt unter demselben Launcher-Pfad erreichbar.
3. Bereits persistierte Review-, Approval- und Audit-Daten werden nicht gelöscht.
4. PostgreSQL darf nicht automatisch auf JSONL zurückfallen; für einen expliziten
   Development-Rollback muss `REVIEW_APPROVAL_BACKEND=jsonl` gesetzt werden.

## Verifikation

Vorgesehene Befehle:

```text
python launcher.py review-approval-release-gate
pytest -q tests/test_review_approval_release_gate.py
pytest -q tests/test_review_approval_e2e.py
pytest -q tests/test_review_approval_security.py
pytest -q tests/test_review_approval_concurrency.py
pytest -q
```

Lokale Resultate unter Windows/Python 3.13:

- `python launcher.py review-approval-release-gate`: `BLOCKED`, 55/58 Checks
  erfolgreich. Die drei Blocker sind erwartungsgemäß `production_backend`,
  `postgresql_health` und `repository_health`, weil lokal JSONL konfiguriert und
  kein erreichbares PostgreSQL vorhanden ist.
- `pytest -q tests/test_review_approval_release_gate.py`: 9 passed.
- `pytest -q tests/test_review_approval_e2e.py`: 3 passed.
- `pytest -q tests/test_review_approval_security.py`: 4 passed.
- `pytest -q tests/test_review_approval_concurrency.py`: 15 passed.
- `pytest -q`: nach 300 Sekunden bei 77 Prozent abgebrochen. Der Lauf enthält
  bekannte, außerhalb dieser fünf Dateien liegende Provider-, Memory- und
  reihenfolgeabhängige RAG-/Legacy-Fehler. Die Review-/Approval-Suites sind
  davon nicht betroffen.

Lokale Release-Empfehlung: `DO_NOT_RELEASE`, bis der Gate-Lauf mit einem
erreichbaren PostgreSQL-Backend `PASS` meldet und die externen Fehler der
Gesamtsuite getrennt bereinigt oder als akzeptierte Plattformblocker
dokumentiert sind.
