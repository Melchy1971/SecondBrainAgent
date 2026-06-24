![Jarvis](../jarvis.jpg)

# SecondBrain-Agent v18.x

Lokaler Jarvis-/SecondBrain-Agent mit modularer Runtime, Desktop/HUD, Mobile Companion, Voice, Knowledge Graph, P0/P1-Gates und Release-Hygiene-Werkzeugen.

## Projektwurzel

Alle Befehle in dieser README laufen aus dem Projektordner:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Wenn Befehle aus `H:\SecondBrainAgent` gestartet werden, findet Python `launcher.py`, `pytest.ini` und `requirements.txt` nicht zuverlässig.

## Schnellstart

```powershell
python -m pip install -r requirements-dev.txt
python launcher.py repo-doctor
python launcher.py dependency-inventory
python launcher.py health
python launcher.py command-index
```

Minimal ohne Dev-Datei:

```powershell
python -m pip install -r requirements.txt
python launcher.py health
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
python launcher.py repo-doctor
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

Prüft Repository-Struktur, Pflichtdateien, pytest-Konfiguration, README-Basis und optionale Launcher-Smokes.

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
python launcher.py graph-ingest-text "Jarvis nutzt Gmail am 2026-06-19"
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

## Requirements

| Datei | Zweck |
|---|---|
| `requirements.txt` | historischer Minimalpfad |
| `requirements-dev.txt` | Test-/Entwicklungsinstallation |
| `requirements-runtime.txt` | kuratierte Runtime-Abhängigkeiten |

`dependency-inventory` erzeugt Vorschläge, aber befüllt Requirements nicht automatisch. Provider-Abhängigkeiten dürfen nicht ungeprüft Pflichtabhängigkeiten werden.

## Source of Truth

| Bereich | Quelle |
|---|---|
| Launcher-Befehle | `python launcher.py command-index` |
| Modulzuordnung | `secondbrain/module_registry.py` |
| Repository-Hygiene | `python launcher.py repo-doctor` |
| Dependency-Inventar | `python launcher.py dependency-inventory` |
| P0 Releasefähigkeit | `python launcher.py p0-gate` |
| P1 RAG-Fähigkeit | `python launcher.py p1-gate` |
| Paketverlauf | `CHANGELOG_*.md` |
| technische Doku | `docs/` |

## Sicherheitsmodell

- keine destruktiven Aktionen ohne explizite Aktivierung
- keine externen Aktionen ohne konfigurierte Provider/Connectoren
- lokale Artefakte in `runtime/`, `logs/`, `release/` nicht als Produktcode behandeln
- Markdown und maschinenlesbare Reports bleiben auditierbare Artefakte

## Aktuelle technische Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| `requirements.txt` historisch minimal | neue Installationen können brechen | `dependency-inventory` ausführen und `requirements-runtime.txt` kuratieren |
| Runtime-/Cache-Dateien im Repository | Merge-Noise, falsche Deltas | `.gitignore` pflegen, Artefakte entfernen |
| alte v10/v11/v12 Doku-Fragmente | Bedienfehler | README als aktuelle Betriebsquelle nutzen |
| optionale Provider-Abhängigkeiten | unnötige Pflichtinstallationen | Provider separat klassifizieren |

## Empfohlener Entwicklungsablauf

```powershell
git status
python launcher.py repo-doctor
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

Erst danach Featurepaket starten.
