# Repo Doctor v18.7

## Ziel

Repo Doctor ist ein vorgelagertes Hygiene-Gate vor P0/P1-Featureentwicklung.

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
| `pytest.ini` existiert | blocking | Fehler blockiert Gate |
| `requirements.txt` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/module_registry.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/launcher_runtime_v126.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/p0_runtime.py` existiert | blocking | Fehler blockiert Gate |
| `secondbrain/p1_rag_runtime.py` existiert | blocking | Fehler blockiert Gate |
| `pytest.ini` enthält `testpaths = tests` | blocking | Fehler blockiert Gate |
| `pytest.ini` enthält `pythonpath = .` | blocking | Fehler blockiert Gate |
| Runtime Dependencies sind explizit | release-risk | Warnung, kein Blocker |
| README enthält Health-Befehl | documentation | Warnung, kein Blocker |
| optionale Launcher-Smokes | blocking | Fehler blockiert Gate bei Aktivierung |

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
repo-doctor
  ↓
p0-gate
  ↓
p1-gate
  ↓
feature-specific tests
  ↓
release report
```
