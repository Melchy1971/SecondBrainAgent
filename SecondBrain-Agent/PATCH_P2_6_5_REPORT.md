# PATCH P2.6.5 — Settings RC1 Gate

## Ziel
Settings-Center als RC1-validierbaren Desktop-Baustein abschließen.

## Enthalten
- `secondbrain/desktop/settings/release/settings_rc1_gate.py`
- `secondbrain/desktop/settings/release/settings_validation.py`
- `secondbrain/desktop/settings/release/settings_metrics.py`
- `secondbrain/desktop/settings/release/settings_health_report.py`
- `secondbrain/desktop/settings/release/settings_checklist.py`
- Release-Exports in `__init__.py`
- Tests unter `tests/desktop/settings/release/`

## Prüfungen
- Foundation vorhanden
- Provider Profiles vorhanden
- Security/Governance vorhanden
- Privacy Mode prüfbar
- Secret Handling prüfbar
- Backup/Recovery vorhanden
- Migration/Integrity/Rollback vorhanden
- Blockerklassifikation für rohe Secrets

## Validierung
`10 passed in 0.20s`

## Ergebnis
Settings-Center RC1 Gate ist als deterministische Validierungsschicht vorhanden.
