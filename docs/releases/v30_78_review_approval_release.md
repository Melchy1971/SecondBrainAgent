# v30.78 – Review & Approval Governance Release

Abschluss der Review- und Approval-Entwicklung (Prompts 8–16). Dieser Release
bündelt die Governance-Schicht rund um die zentrale `NativeApprovalQueue` und
zertifiziert sie über ein belastbares Release-Gate.

## Umfang

- **Review Queue / Approval Inbox** – vereinheitlichte Inbox über native
  Review- und Approval-Queues (`UnifiedReviewInbox`), Entscheidungslogik
  Approve/Reject/Defer mit Audit.
- **Agent Resume** – pausieren, freigeben, fortsetzen; idempotente
  Wiederaufnahme nach Freigabe.
- **Import Review** – `failed_import`, `sensitive_document`,
  `low_confidence_classification`; Retry ohne Dubletten.
- **Connector Approval** – `connector_permission_change` als eigene Kategorie
  mit hoher bzw. kritischer Eskalation.
- **Memory Governance** – sensible Memory-Writes gehen in Review, Privacy Mode
  und Secrets werden blockiert, Kandidaten tragen Evidence
  (`GovernedMemoryService`, `MemoryExtractor`, Klassifikationspolicy).
- **Notifications & Eskalation** – Notification-Typen und Prioritäten,
  Zeitregeln, Deduplizierung, Acknowledgement, Snooze, Desktop-Badge, keine
  Secrets in Benachrichtigungen (`review_notifications`).
- **Metrics** – Volumen-, Zeit- und Qualitätsmetriken, Segmentierung, Trends;
  keine technischen IDs, keine Payloads, keine Secrets im Export
  (`review_approval_metrics`).
- **Concurrency & Crash Recovery** – optimistische Versionierung,
  Compare-and-set, plattformkompatibles File-Lock, Execution-Token und Lease,
  Backup vor Mutation, Wiederherstellung aus Backup, Zustände
  `executing`/`completed`/`recovery_required`.
- **Persistence** – Repository-Abstraktion mit JSONL-Fallback und
  PostgreSQL-Backend (`REVIEW_APPROVAL_BACKEND=jsonl|postgres`), Migration mit
  ID- und Audit-Erhalt, kein stiller Fallback bei konfiguriertem PostgreSQL.

## Release-Gate

```
python launcher.py review-approval-release-gate
```

Erzeugt `runtime/reports/review_approval_release_gate.json` mit `schema`,
`version`, `timestamp`, `overall_status`, `checks`, `blockers`, `warnings`,
`metrics`, `test_commands`, `backend_status` und `security_summary`.

Bewertung:

- **PASS** – alle kritischen Prüfungen erfolgreich, keine doppelte Ausführung,
  keine Freigabeumgehung, kein Secret-Leak, persistente Wiederaufnahme
  funktioniert.
- **CONDITIONAL_PASS** – nur nichtkritische GUI- oder Reporting-Warnungen.
- **BLOCKED** – riskante Aktion ohne Approval, fehlender Audit-Trail, verlorene
  Entscheidung, doppelte Ausführung, falsche Workspace-Nutzung, Privacy-Bypass,
  Secret-Leak oder beschädigte Queue ohne Recovery.

## Verifikation

```
python launcher.py review-approval-release-gate
pytest -q tests/test_review_approval_release_gate.py
pytest -q tests/test_review_approval_e2e.py
pytest -q tests/test_review_approval_security.py
pytest -q tests/test_review_approval_concurrency.py
pytest -q
```
