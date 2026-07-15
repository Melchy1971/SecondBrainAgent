# Jarvis v31.04 GA Readiness

Overall status: **BLOCKED**

## Components

| Component | Status |
|---|---|
| build | BLOCKED |
| security | BLOCKED |
| data | BLOCKED |
| rag | BLOCKED |
| operations | BLOCKED |
| gui | BLOCKED |
| performance | BLOCKED |
| privacy | BLOCKED |

## Blockers

- `repo_doctor`: existing Repo Doctor
- `review_approval_gate`: existing Review/Approval release gate
- `backup_restore`: existing Backup/Restore gate
- `rag_production`: provider, golden dataset, MRR, nDCG, citations and index
- `postgres_pgvector`: PostgreSQL/pgvector production readiness
- `packaging`: Windows packaging artifacts
- `installer_smoke`: fresh install, first start, repair, uninstall and portable
- `signed_update_rollback`: signed update and rollback smoke
- `performance_small`: small load, regression, deadlock, OOM and GUI freeze
- `full_test_suite`: complete pytest suite evidence
- `gui_centers`: existing evidence: runtime/reports/gui_smoke.json
- `privacy_governance`: existing evidence: runtime/reports/privacy_gate.json
- `operations_recovery`: existing evidence: runtime/reports/operations_smoke.json
- `data_integrity_migrations`: existing evidence: runtime/reports/data_integrity.json

## Warnings

- `system_rc_gate`: existing system RC gate

## Release recommendation

Keine GA-Freigabe; kritische Evidenz fehlt oder ist rot
