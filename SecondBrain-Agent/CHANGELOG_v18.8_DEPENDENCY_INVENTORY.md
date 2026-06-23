# CHANGELOG v18.8 Dependency Inventory

## Pakettyp

P0 Release Hygiene / Dependency Transparency

## Branch

`dev/v18-6-repo-doctor`

## Geändert

### Code

- `secondbrain/release/dependency_inventory.py`
  - AST-basierter Importscanner
  - Standardbibliothek-only
  - Klassifizierung:
    - `standard_library`
    - `internal`
    - `external`
    - `optional_provider`
    - `unknown`
  - Requirements-Vorschlagslisten:
    - `requirements_suggestion`
    - `optional_requirements_suggestion`
  - JSON-Report:
    - `release/dependency_inventory_latest.json`

- `launcher.py`
  - neuer Befehl `dependency-inventory`
  - Optionen:
    - `--project-root`
    - `--write-report`

- `secondbrain/module_registry.py`
  - `dependency-inventory` im Core-Command-Index registriert
  - `dependency-` als Core-Präfix ergänzt

### Tests

- `tests/test_dependency_inventory_v18_8.py`
  - Standardbibliothekserkennung
  - interne Module
  - externe Module
  - optionale Provider
  - Alias-Mapping
  - Report-Datei-Erzeugung
  - Command-Index-Registrierung

### Dokumentation

- `docs/DEPENDENCY_INVENTORY_v18_8.md`
  - Zweck
  - Befehle
  - Klassifizierung
  - Exit Codes
  - Requirements-Ableitung
  - Grenzen

## Validierung lokal

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python -m pip install -r requirements-dev.txt
pytest -q tests/test_dependency_inventory_v18_8.py
python launcher.py dependency-inventory
python launcher.py dependency-inventory --write-report
```

## Gate-Reihenfolge ab v18.8

```text
repo-doctor
  ↓
dependency-inventory
  ↓
p0-gate
  ↓
p1-gate
  ↓
feature-specific tests
  ↓
release report
```

## Release-Risiko weiter offen

`requirements-runtime.txt` ist weiterhin nicht automatisch befüllt.

Grund: Das Inventar erzeugt Vorschläge. Die finale Requirements-Liste muss nach Sichtung der Importklassen kuratiert werden, damit optionale Provider nicht als Pflichtabhängigkeit installiert werden.

## Folgearbeit v18.9

- README auf aktuellen v18.x Stand heben
- Gate-Befehle prominent dokumentieren
- optional CI Workflow für Hygiene-Gates ergänzen
- Dependency-Inventar gegen echte Repo-Ausgabe kuratieren
