# Release Workflow v18.11

## Ziel

Diese Datei definiert den verbindlichen lokalen Release- und Entwicklungsablauf für SecondBrain-Agent v18.x.

Sprint 1 verschärft den Ablauf auf reproduzierbare Installation und Packaging.

## Arbeitsverzeichnis

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

## Installation vor Gate-Lauf

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Gate-Kette

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

## Bedeutung der Gates

| Gate | Zweck | Blockiert bei |
|---|---|---|
| `repo-doctor` | Repository-Struktur, Packaging, Requirements-Policy, Artefakthygiene | fehlenden Pflichtdateien, fehlendem `pyproject.toml`, kaputter pytest-Konfiguration, veralteten Root-Artefakten |
| `dependency-inventory` | statisches Import-/Dependency-Inventar | unbekannten Imports, fehlender Projektwurzel |
| `p0-gate` | Runtime-Basisfähigkeit | blockierenden P0-Problemen |
| `p1-gate` | RAG-/Retrieval-Fähigkeit | blockierenden P1-Problemen |
| `pytest -q` | Testregressionen | fehlschlagenden Tests |

## Report-Artefakte

```powershell
python launcher.py repo-doctor --write-report
python launcher.py dependency-inventory --write-report
```

Erzeugt:

```text
release/repo_doctor_latest.json
release/dependency_inventory_latest.json
```

Diese `*_latest.json` Dateien sind lokale Laufzeitartefakte und werden über `.gitignore` ausgeschlossen.

## Source of Truth

| Thema | Quelle |
|---|---|
| aktuelle Bedienung | `README.md` |
| Packaging / Entry Point / Extras | `pyproject.toml` |
| Befehlskatalog | `python launcher.py command-index` |
| Modul-/Command-Zuordnung | `secondbrain/module_registry.py` |
| Repo-Hygiene | `secondbrain/release/repo_doctor.py` |
| Dependency-Inventar | `secondbrain/release/dependency_inventory.py` |
| Release-/Entwicklungsablauf | `docs/RELEASE_WORKFLOW_v18_9.md` |
| Detaildoku | `docs/` |
| Paketverlauf | Git-History und `docs/releases/` |

## Merge-Regel

Vor Merge in `main`:

1. Branch gegen aktuellen `main` prüfen.
2. Laufzeit-/Cache-Dateien nicht mergen.
3. Editable install prüfen.
4. Gate-Kette ausführen.
5. README nur ändern, wenn sich Bedienung, Packaging oder Gate-Reihenfolge ändert.

## Nicht ins Repository committen

```text
runtime/
logs/
__pycache__/
.pytest_cache/
release/*_latest.json
*.pid
*.log
PATCH_*.md
CHANGELOG_*.md
VALIDATION_*.md
```

## CI Smoke

GitHub Actions Workflow:

```text
.github/workflows/p0-reproducibility.yml
```

Prüft Python 3.11 und 3.12:

```powershell
pip install -e ".[dev]"
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
pytest -q tests/test_repo_doctor_v18_7.py
pytest -q tests/test_dependency_inventory_v18_8.py
```

## Entwicklungsregel für neue Pakete

Jedes Paket muss liefern:

- Codeänderung
- Testabdeckung oder begründete Testgrenze
- Dokuänderung, wenn Bedienung/Gates/Architektur betroffen sind
- lokale Validierungsbefehle
- bekannte Risiken

## Entscheidung

Ab Sprint 1 ist `pyproject.toml` die Packaging-Quelle. Historische Root-Dateien `PATCH_*`, `CHANGELOG_*` und `VALIDATION_*` sind keine Source of Truth mehr und werden durch RepoDoctor blockiert.
