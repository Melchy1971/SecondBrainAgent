# v31.25 – CI Release Smoke Gate

## Ziel

Der Release-Pfad wird auf jedem Pull Request und jedem Push nach `main` reproduzierbar geprüft. Der Workflow verhindert insbesondere Paketlayout-Regressionen, fehlende Jarvis-Module und nicht ausführbare Release-Gates.

## Prüfungen

- Editable Installation über `pip install -e ".[dev]"`
- Import des öffentlichen `secondbrain`-Pakets
- Import des Knowledge-Graph-Moduls
- Version-Synchronisation ohne unbeabsichtigte Dokuänderung
- Repo Doctor mit Runtime-Smokes
- Dependency Inventory
- Release- und Connector-Tests
- Integrationstests ohne Live-Zugangsdaten
- persistenter Knowledge Graph
- Personal-Jarvis-End-to-End-Gate
- Release-Candidate-Gate

## Laufzeitumgebung

Die Prüfungen laufen unter Python 3.12 und Python 3.13 auf Ubuntu. Fehlgeschlagene Läufe laden vorhandene Diagnose- und Releaseberichte als Artefakte hoch.

## Sicherheit

Der Workflow verwendet nur Leserechte auf Repository-Inhalte. Live-Provider und produktive Zugangsdaten werden nicht benötigt. Gleichzeitige veraltete Läufe desselben Branches werden abgebrochen.

## Lokale Vorprüfung

```bash
pip install -e ".[dev]"
pytest -q tests/test_ci_workflow_contract.py
python launcher.py repo-doctor --execute-runtime-checks
python scripts/personal_jarvis_gate.py --project-root .
```
