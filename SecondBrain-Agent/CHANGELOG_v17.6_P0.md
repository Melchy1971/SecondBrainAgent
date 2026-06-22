# CHANGELOG v17.6 P0

## Ziel
P0-Launcher-Vertrag absichern, damit neue Feature-Branches die zentrale Command-Oberfläche nicht erneut überschreiben.

## Änderungen
- Neuer Befehl: `p0-contract`
- Neuer Report: `runtime/reports/p0_contract_latest.json`
- `p0-gate` prüft jetzt zusätzlich den Launcher-Vertrag
- `p0-smoke` prüft jetzt zusätzlich den Launcher-Vertrag
- `ModuleRegistry` enthält `p0-contract` als Core-Command
- Tests für Contract, Gate-Integration und Command-Index ergänzt

## Wirkung
- Verhindert Regression: Mobile-/Feature-Launcher darf zentrale Core-/Desktop-/P0-Befehle nicht ersetzen
- Macht Command-Oberfläche maschinenlesbar prüfbar
- Erhöht CI-Nutzbarkeit der P0-Gates
