# APPLY DELTA v30.77 — Refactoring / reversible Quarantäne

## Zusammenfassung
Umbau ohne Löschungen. Verwaiste Module werden reversibel nach `archive/v30_77_quarantine/`
verschoben und erst nach grünem Abnahmelauf (compileall + pytest + GUI-/Launcher-Smoke) endgültig
akzeptiert. Versionierte `_vNN`-Ketten bleiben unangetastet (live referenziert).

## Was analysiert wurde
- 1659 Python-Dateien, 1095 `secondbrain`-Module (statische AST-Analyse).
- 127 statische Orphans → nach Cross-Check 100 belastbare Quarantäne-Kandidaten, 25 zurückgestellt.
- 6 versionierte Modulfamilien als LIVE-Ketten identifiziert (nicht löschbar).

## Anwenden (Windows)
```
powershell -ExecutionPolicy Bypass -File OUTPUTS/v30_77_refactoring/apply_v30_77.ps1
```
Self-gating: roter Schritt → automatischer Rollback, Repo bleibt unverändert.

## Nicht enthalten (bewusst)
- Kein Löschen von `_vNN`-Ständen (eigenes Konsolidierungs-Release v30.78+).
- Kein Zusammenführen doppelter Klassen (Vorschlag in Report 01, separat umzusetzen).

## Dateien
- `DELTA_MANIFEST_v30_77.json` — Manifest (Schema wie bestehende Deltas).
- `apply_v30_77.ps1` — Abnahme-gesteuertes Apply/Rollback.
- `quarantine_candidates.csv` — 100 Kandidaten + 25 KEEP mit Begründung.
- `01..05_*_REPORT.md` — Architecture / Performance / Security / Technical Debt / Release Readiness.
