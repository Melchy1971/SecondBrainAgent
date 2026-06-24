# Repo Doctor v18.11

## Ziel

Repo Doctor ist das vorgelagerte Hygiene- und Reproduzierbarkeits-Gate vor P0/P1-Featureentwicklung.

Es prüft nicht die fachliche Produktreife, sondern ob das Repository selbst in einem belastbaren Zustand ist.

## Befehl

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python launcher.py repo-doctor
```

Mit Runtime-Smoke:

```powershell
python launcher.py repo-doctor --execute-runtime-checks
```

Mit Report-Datei:

```powershell
python launcher.py repo-doctor --write-report
```

Zielartefakt:

```text
release/repo_doctor_latest.json
```

## Prüfmatrix

| Check | Typ | Wirkung |
|---|---:|---|
| Projektwurzel existiert | blocking | Fehler blockiert Gate |
| `launcher.py` existiert | blocking | Fehler blockiert Gate |
| `pyproject.toml` existiert | blocking | Fehler blockiert Gate |
| `pytest.ini` existiert | blocking | Fehler blockiert Gate |
| `requirements.txt` existiert | blocking | Fehler blockiert Gate |
| `requirements-dev.txt` existiert | blocking | Fehler blockiert Gate |
| `requirements-runtime.txt` existiert | blocking | Fehler blockiert Gate |
| `README.md` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/module_registry.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/launcher_runtime_v126.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/p0_runtime.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/p1_rag_runtime.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/release/dependency_inventory.py` existiert | blocking | Fehler blockiert Gate |
| `docs/RELEASE_WORKFLOW_v18_9.md` existiert | blocking | Fehler blockiert Gate |
| `pytest.ini` enthält `testpaths = tests` | blocking | Fehler blockiert Gate |
| `pytest.ini` enthält `pythonpath = .` | blocking | Fehler blockiert Gate |
| `pyproject.toml` enthält Build-System | blocking | Fehler blockiert Gate |
| `pyproject.toml` enthält Package-Metadaten | blocking | Fehler blockiert Gate |
| `pyproject.toml` enthält `secondbrain` Entry Point | blocking | Fehler blockiert Gate |
| `pyproject.toml` enthält Package-Find-Konfiguration | blocking | Fehler blockiert Gate |
| `requirements-runtime.txt` enthält Runtime-Policy | blocking | Fehler blockiert Gate |
| README enthält Health-Befehl | documentation | Warnung, kein Blocker |
| README enthält editable install | documentation | Warnung, kein Blocker |
| README verweist nicht auf gelöschte `CHANGELOG_*.md` | blocking | Fehler blockiert Gate |
| keine Root-Dateien mit `PATCH_`, `CHANGELOG_`, `VALIDATION_` | blocking | Fehler blockiert Gate |
| keine Cache-/Log-/PID-Artefakte im Arbeitsbaum | blocking | Fehler blockiert Gate |
| optionale Launcher-Smokes | blocking | Fehler blockiert Gate bei Aktivierung |

## Verbotene Artefakte

Repo Doctor blockiert:

```text
PATCH_*.md
CHANGELOG_*.md
VALIDATION_*.md
__pycache__/*
.pytest_cache/*
*.pid
*.log
*.pyc
```

Nicht pauschal blockiert werden lokal erzeugte `runtime/`-Datenbanken oder Reports, weil normale RAG-/P1-Läufe diese lokal erzeugen können. Diese Dateien bleiben über `.gitignore` vom Repository ausgeschlossen.

## Exit Codes

| Exit Code | Bedeutung |
|---:|---|
| 0 | keine blockierenden Fehler |
| 1 | mindestens ein blockierender Fehler |
| 2 | falsche Argumente / unbekannter Kommandozustand |

## Designentscheidung

Repo Doctor nutzt nur die Python-Standardbibliothek.

Grund: Der Check muss auch dann laufen, wenn externe Abhängigkeiten, virtuelle Umgebung oder Provider-Konfigurationen defekt sind.

## Abgrenzung

Repo Doctor ersetzt nicht:

- `p0-gate`
- `p1-gate`
- Fachtests
- Provider-Integrationstests
- Security-Governance-Gates

Repo Doctor läuft davor.

## Empfohlene Gate-Reihenfolge

```text
repo-doctor --execute-runtime-checks
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
