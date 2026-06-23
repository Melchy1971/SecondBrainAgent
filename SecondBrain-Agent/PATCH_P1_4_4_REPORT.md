# PATCH P1.4.4 — Installation & Upgrade Pipeline

## Inhalt

- `secondbrain/deployment/upgrade.py`
  - Preflight-Checks für Projektroot, Pflichtpfade und Metadata-Ziel
  - Backup-Plan mit SHA-256-Prüfsummen
  - Migrationsplan mit reversiblen/nicht reversiblen Schritten
  - Rollback-Plan auf Basis vorhandener Backup-Items
  - Upgrade-Plan als JSON-Manifest
  - Validierung gegen gleiche Version, fehlende Schritte und Preflight-Fehler

- `tests/test_p1_4_4_upgrade_pipeline.py`
  - Preflight PASS/FAIL
  - Backup-Metadaten
  - Migration-Step-Vertrag
  - Rollback-Metadaten
  - JSON-Export

## Ergebnis

P1.4.4 macht Upgrades planbar und prüfbar, ohne direkt Dateisystem-Mutationen am Produktivcode auszuführen.

## Validierung

`7 passed in 0.29s`
