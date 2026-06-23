# CHANGELOG v18.7 Repo Doctor

## Pakettyp

P0 Release Hygiene / Repository Gate

## Branch

`dev/v18-6-repo-doctor`

## Geändert

### Code

- `secondbrain/release/repo_doctor.py`
  - statischer Repository-Doctor
  - prüft Pflichtdateien
  - prüft pytest-Konfiguration
  - prüft README-Basiszustand
  - erkennt schwaches Dependency Management als Release-Risiko
  - kann optionale Launcher-Smokes ausführen
  - kann JSON-Report schreiben

- `launcher.py`
  - neuer Befehl `repo-doctor`
  - Optionen:
    - `--project-root`
    - `--execute-runtime-checks`
    - `--timeout`
    - `--write-report`

- `secondbrain/module_registry.py`
  - `repo-doctor` im Core-Command-Index registriert
  - `repo-` als Core-Präfix ergänzt

### Tests

- `tests/test_repo_doctor_v18_7.py`
  - minimal gültiges Projekt
  - blockierender Fehler bei fehlendem `launcher.py`
  - Report-Datei-Erzeugung
  - Command-Index-Registrierung

### Build/Dependencies

- `requirements-dev.txt`
  - Dev/Test-Installationspfad

- `requirements-runtime.txt`
  - explizite Runtime-Abgrenzung
  - aktuell keine neuen externen Runtime-Abhängigkeiten für v18.7

### Dokumentation

- `docs/REPO_DOCTOR_v18_7.md`
  - Zweck
  - Befehle
  - Prüfmatrix
  - Exit Codes
  - Gate-Reihenfolge

## Validierung lokal

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python -m pip install -r requirements-dev.txt
pytest -q tests/test_repo_doctor_v18_7.py
python launcher.py repo-doctor
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py repo-doctor --write-report
```

## Erwartetes Ergebnis

`repo-doctor` liefert Exit Code `0`, solange keine blockierenden Strukturfehler bestehen.

Warnung bleibt erwartbar:

```text
requirements.txt:runtime-dependencies
```

Grund: `requirements.txt` enthält aktuell nur `pytest>=8.0.0`.

## Folgearbeit v18.8

- echtes Dependency-Inventar erstellen
- Runtime-Abhängigkeiten aus Importgraph ableiten
- optional CI Workflow ergänzen
- README auf aktuellen Stand v18.x heben
- P0/P1-Gate-Kette dokumentieren
