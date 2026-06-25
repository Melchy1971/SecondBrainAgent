![Jarvis](../jarvis.jpg)

# SecondBrain-Agent v18.x

Lokaler Jarvis-/SecondBrain-Agent mit modularer Runtime, Desktop/HUD, Mobile Companion, Voice, Knowledge Graph, P0/P1-Gates und Release-Hygiene-Werkzeugen.

## Projektwurzel

Alle Befehle laufen aus dem Projektordner:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Wenn Befehle aus `H:\SecondBrainAgent` gestartet werden, findet Python `launcher.py`, `pytest.ini`, `pyproject.toml` und `requirements.txt` nicht zuverlässig.

## Installation

Empfohlen für Entwicklung und lokale Ausführung:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Minimaler Legacy-Pfad:

```powershell
python -m pip install -r requirements-dev.txt
```

Optionale Feature-Sets:

```powershell
pip install -e ".[pdf]"
pip install -e ".[connectors]"
pip install -e ".[openai]"
pip install -e ".[all]"
```

## Schnellstart

```powershell
python launcher.py repo-doctor
python launcher.py dependency-inventory
python launcher.py health
python launcher.py command-index
```

Nach editable install zusätzlich:

```powershell
secondbrain health
secondbrain command-index
```

## Primäre lokale Oberfläche

### Jarvis HUD

```powershell
python scripts\start_hud.py
```

Browser:

```text
http://127.0.0.1:8851
```

Alternativ:

```powershell
.\Jarvis.bat
```

Stoppen:

```powershell
.\Jarvis-stop.bat
```

### Einfaches lokales Dashboard

```powershell
python scripts\web_dashboard.py
```

Browser:

```text
http://localhost:8765
```

## Release-Gate-Reihenfolge

Vor Featureentwicklung oder Merge:

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

Logische Reihenfolge:

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

## Release-Dokumentation

Source of Truth für Paketstände und Sprint-Ergebnisse:

```text
docs/releases/
```

Git-History bleibt die technische Änderungsquelle. Root-Artefakte mit Präfix `PATCH_`, `CHANGELOG_` oder `VALIDATION_` sind nicht mehr zulässig.

## Hygiene-Gates

### Repo Doctor

Prüft Repository-Struktur, Packaging, pytest-Konfiguration, Requirements-Policy, README-Basis, Release-Dokumentation, CI-Smoke, verbotene Runtime-/Cache-Artefakte und optionale Launcher-Smokes.

```powershell
python launcher.py repo-doctor
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py repo-doctor --write-report
```

Report:

```text
release/repo_doctor_latest.json
```

Doku:

```text
docs/REPO_DOCTOR_v18_7.md
```

### Dependency Inventory

Erzeugt ein statisches Import-Inventar und trennt Standardbibliothek, interne Module, externe Pakete und optionale Provider.

```powershell
python launcher.py dependency-inventory
python launcher.py dependency-inventory --write-report
```

Report:

```text
release/dependency_inventory_latest.json
```

Doku:

```text
docs/DEPENDENCY_INVENTORY_v18_8.md
```

## Core-Kommandos

```powershell
python launcher.py health
python launcher.py status
python launcher.py module-status
python launcher.py module-health
python launcher.py command-index
python launcher.py core-status
```
