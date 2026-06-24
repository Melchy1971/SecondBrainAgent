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

## Hygiene-Gates

### Repo Doctor

Prüft Repository-Struktur, Packaging, pytest-Konfiguration, Requirements-Policy, README-Basis, verbotene Runtime-/Cache-Artefakte und optionale Launcher-Smokes.

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

## P0 Runtime Gate

```powershell
python launcher.py p0-doctor
python launcher.py p0-gate
python launcher.py p0-smoke
python launcher.py p0-contract
python launcher.py p0-readiness
python launcher.py p0-production
python launcher.py p0-audit
```

`p0-gate` ist das strikte maschinenlesbare P0-Gate. Exit-Code `0` bedeutet PASS. Exit-Code `1` bedeutet BLOCKED.

## P1 RAG Runtime

```powershell
python launcher.py p1-rag-status
python launcher.py p1-rag-ingest-text "Beispielinhalt" --source manual --title "Test"
python launcher.py p1-rag-ingest-file .\README.md --source manual --title "README"
python launcher.py p1-rag-search "Suchbegriff"
python launcher.py p1-rag-vector-search "Suchbegriff"
python launcher.py p1-rag-hybrid-search "Suchbegriff"
python launcher.py p1-rag-answer "Frage"
python launcher.py p1-rag-sources
python launcher.py p1-rag-validate
python launcher.py p1-rag-quality "Qualitätsfrage"
python launcher.py p1-rag-reindex
python launcher.py p1-embedding-status
python launcher.py p1-retrieval-benchmark
python launcher.py p1-retrieval-metrics
python launcher.py p1-production
python launcher.py p1-gate
```

## Desktop OS

```powershell
python launcher.py desktop-status
python launcher.py desktop-open
python launcher.py desktop-dashboard
python launcher.py desktop-activity
python launcher.py desktop-widgets
python launcher.py desktop-commands
python launcher.py desktop-notifications
python launcher.py desktop-session
python launcher.py desktop-notify "Test" --body "Nachricht" --level info
```

## Voice Runtime

```powershell
python launcher.py voice-status2
python launcher.py voice-session2
python launcher.py voice-sessions2
python launcher.py voice-wake "Jarvis status"
python launcher.py voice-parse2 "Jarvis notiz Neuer Gedanke"
python launcher.py voice-handle2 "Jarvis status"
python launcher.py voice-speak2 "Hallo"
python launcher.py voice-events
python launcher.py voice-memory
```

## Knowledge Graph

```powershell
python launcher.py graph-status
python launcher.py graph-ingest-text "Jarvis nutzt lokale Quellen"
python launcher.py graph-search Jarvis
python launcher.py graph-neighbors Jarvis
python launcher.py graph-timeline
python launcher.py graph-contradictions
python launcher.py graph-export
```

## Mobile Companion

```powershell
python launcher.py mobile16-migrate
python launcher.py mobile16-status
python launcher.py mobile16-manifest
python launcher.py mobile16-pair-request "iPhone Markus" ios
python launcher.py mobile16-pairing-requests
python launcher.py mobile16-devices
python launcher.py mobile16-widgets
python launcher.py mobile16-sync
python launcher.py mobile16-sync-runs
python launcher.py mobile16-sessions
```

## Tests

Gezielte Hygiene-Tests:

```powershell
pytest -q tests/test_repo_doctor_v18_7.py
pytest -q tests/test_dependency_inventory_v18_8.py
```

Gesamttestlauf:

```powershell
pytest -q
```

## Requirements und Packaging

| Datei | Zweck |
|---|---|
| `pyproject.toml` | Package-Metadaten, Entry Point, Extras, pytest-Konfiguration |
| `requirements.txt` | Legacy-Minimalpfad; Core bleibt aktuell Standardbibliothek-only |
| `requirements-dev.txt` | Legacy-Dev/Test-Installationspfad |
| `requirements-runtime.txt` | kuratierte Runtime-Policy; optionale Dependencies liegen in Extras |

`dependency-inventory` erzeugt Vorschläge, aber befüllt Requirements nicht automatisch. Provider-Abhängigkeiten dürfen nicht ungeprüft Pflichtabhängigkeiten werden.

## Source of Truth

| Bereich | Quelle |
|---|---|
| Launcher-Befehle | `python launcher.py command-index` |
| Modulzuordnung | `secondbrain/module_registry.py` |
| Repository-Hygiene | `python launcher.py repo-doctor` |
| Dependency-Inventar | `python launcher.py dependency-inventory` |
| Packaging | `pyproject.toml` |
| P0 Releasefähigkeit | `python launcher.py p0-gate` |
| P1 RAG-Fähigkeit | `python launcher.py p1-gate` |
| Release-/Entwicklungsablauf | `docs/RELEASE_WORKFLOW_v18_9.md` |
| technische Detaildoku | `docs/` |

## Sicherheitsmodell

- keine destruktiven Aktionen ohne explizite Aktivierung
- keine externen Aktionen ohne konfigurierte Provider/Connectoren
- lokale Artefakte in `runtime/`, `logs/`, `release/` nicht als Produktcode behandeln
- maschinenlesbare Reports bleiben lokale Audit-Artefakte

## Aktuelle technische Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| Core ist standard-library-only, optionale Features brauchen Extras | optionale Parser/Provider fehlen ohne Extra-Install | `pip install -e ".[all]"` oder gezielte Extras |
| Runtime-/Cache-Dateien im Repository | Merge-Noise, falsche Deltas | RepoDoctor blockiert Root-Patch/Changelog/Validation, Logs, PID, pycache |
| PostgreSQL/pgvector fehlt | keine produktive skalierbare Persistenz | Sprint 3 |
| echte Connectoren fehlen | kein automatischer SecondBrain-Datenfluss | Sprint 4 |
| optionale Provider-Abhängigkeiten | unnötige Pflichtinstallationen | Provider separat klassifizieren |

## Empfohlener Entwicklungsablauf

```powershell
git status
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

Erst danach Featurepaket starten.
