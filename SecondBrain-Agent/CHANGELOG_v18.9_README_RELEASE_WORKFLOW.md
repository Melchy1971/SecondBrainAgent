# CHANGELOG v18.9 README & Release Workflow

## Pakettyp

P0/P1 Release Guidance / Documentation Hygiene

## Branch

`dev/v18-6-repo-doctor`

## Geändert

### README

- `README.md` von historischer v8.0-Einstiegsdoku auf aktuellen v18.x Betriebsstand gehoben.
- Schnellstart aktualisiert.
- Hygiene-Gates prominent dokumentiert.
- P0/P1-Gate-Kette verbindlich aufgenommen.
- Core-, P0-, P1-, Desktop-, Voice-, Graph- und Mobile-Kommandos konsolidiert.
- Source-of-Truth-Tabelle ergänzt.
- aktuelle technische Risiken ergänzt.

### Repo-Hygiene

- `.gitignore` ergänzt für:
  - Python-Caches
  - virtuelle Umgebungen
  - Build-Artefakte
  - lokale Runtime-Artefakte
  - Logs
  - PID-Dateien
  - lokale `release/*_latest.json` Reports

### Dokumentation

- `docs/RELEASE_WORKFLOW_v18_9.md`
  - Gate-Kette
  - Report-Artefakte
  - Merge-Regeln
  - nicht zu committende Artefakte
  - bekannte aktuelle Repo-Hygiene-Lücke
  - Entwicklungsregel für neue Pakete

## Technischer Befund

Der Branch war gegen `main` nicht mehr linear. Die Abweichung in `main` betrifft nach Vergleich Laufzeit-/Cache-Artefakte:

```text
SecondBrain-Agent/logs/jarvis_gui.log
SecondBrain-Agent/runtime/jarvis_hud.pid
SecondBrain-Agent/secondbrain/__pycache__/__init__.cpython-313.pyc
SecondBrain-Agent/secondbrain/__pycache__/jarvis_hud_server.cpython-313.pyc
SecondBrain-Agent/tests/__pycache__/conftest.cpython-313-pytest-8.4.2.pyc
```

Diese Dateien sind kein fachlicher Konflikt, aber ein Repo-Hygiene-Problem.

## Validierung lokal

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python launcher.py repo-doctor
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q tests/test_repo_doctor_v18_7.py
pytest -q tests/test_dependency_inventory_v18_8.py
```

## Folgearbeit v18.10

- Runtime-/Cache-Artefakte aus `main` entfernen
- Branch auf aktuellen `main` bringen
- optional CI Workflow für Hygiene-Gates ergänzen
- danach fachliche P1/P03-Featureentwicklung fortsetzen
