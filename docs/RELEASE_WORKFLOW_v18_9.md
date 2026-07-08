# Release Workflow

Der historische Dateiname bleibt erhalten, weil Repo Doctor ihn als Pflichtdatei prueft. Der Inhalt gilt fuer den aktuellen Projektstand.

## Arbeitsverzeichnis und Installation

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Gate-Kette

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

## Zweck

| Gate | Prueft |
|---|---|
| Repo Doctor | Repository-Struktur, Packaging, Artefakthygiene und Pflichtdateien |
| Dependency Inventory | statische Import- und Dependency-Klassen |
| GUI Bootstrap/Doctor | Startpfade, lokale Defaults und Runtime-Voraussetzungen |
| P0 Gate | Runtime-Basisfaehigkeit |
| P1 Gate | RAG-, Provider- und Retrieval-Faehigkeit |
| pytest | Regressionen und Vertraege |

## Reports

```powershell
python launcher.py repo-doctor --write-report
python launcher.py dependency-inventory --write-report
python launcher.py p0-production --write-report
python launcher.py p1-production --write-report
```

Generierte `*_latest.json`-Dateien sind Laufzeitartefakte und keine statische Dokumentation.

## Source of Truth

| Thema | Quelle |
|---|---|
| Bedienung | Root-`README.md`, `docs/README.md` und `docs/04_STARTBEFEHLE.md` |
| Packaging | `pyproject.toml` |
| Befehle | `python launcher.py command-index` |
| Module | `secondbrain/module_registry.py` |
| Repo-Hygiene | `secondbrain/release/repo_doctor.py` |
| Release-Historie | Git und `docs/releases/` |

## Merge-Regeln

1. Nur beabsichtigte Dateien aufnehmen; fremde Working-Tree-Aenderungen erhalten.
2. Keine Secrets, Runtime-Daten, Caches, Logs oder PID-Dateien committen.
3. Neue Logik mit fokussierten Tests und relevanten Gates absichern.
4. Dokumentation aktualisieren, wenn sich Bedienung, Architektur oder Gates aendern.
5. Nicht ausgefuehrte Checks und Restrisiken explizit dokumentieren.

## Produktive Datenbankaenderungen

Schema-Apply, Migration und Reindex brauchen vorab:

- gepruefte Zielkonfiguration ohne Secret-Ausgabe,
- SQL-/Migrationsreview,
- Backup und Restore-Plan,
- Live-Readiness ohne Blocker,
- dokumentierte Dimensionen und Provider-Identitaet.
