# Release Workflow v18.9

## Ziel

Diese Datei definiert den verbindlichen lokalen Release- und Entwicklungsablauf für SecondBrain-Agent v18.x.

## Arbeitsverzeichnis

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

## Gate-Kette

```powershell
python launcher.py repo-doctor
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

## Bedeutung der Gates

| Gate | Zweck | Blockiert bei |
|---|---|---|
| `repo-doctor` | Repository-Struktur und Hygiene | fehlenden Pflichtdateien, kaputter pytest-Konfiguration |
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
| Befehlskatalog | `python launcher.py command-index` |
| Modul-/Command-Zuordnung | `secondbrain/module_registry.py` |
| Repo-Hygiene | `secondbrain/release/repo_doctor.py` |
| Dependency-Inventar | `secondbrain/release/dependency_inventory.py` |
| Paketverlauf | `CHANGELOG_*.md` |
| Detaildoku | `docs/` |

## Merge-Regel

Vor Merge in `main`:

1. Branch gegen aktuellen `main` prüfen.
2. Laufzeit-/Cache-Dateien nicht mergen.
3. Gate-Kette ausführen.
4. Changelog aktualisieren.
5. README nur ändern, wenn sich Bedienung oder Gate-Reihenfolge ändert.

## Nicht ins Repository committen

```text
runtime/
logs/
__pycache__/
.pytest_cache/
release/*_latest.json
*.pid
*.log
```

## Bekannte aktuelle Repo-Hygiene-Lücke

Im `main`-Zweig befinden sich Laufzeit-/Cache-Artefakte. Diese erzeugen Merge-Noise und sollten separat entfernt werden:

```text
SecondBrain-Agent/logs/jarvis_gui.log
SecondBrain-Agent/runtime/jarvis_hud.pid
SecondBrain-Agent/secondbrain/__pycache__/*.pyc
SecondBrain-Agent/tests/__pycache__/*.pyc
```

## Entwicklungsregel für neue Pakete

Jedes Paket muss liefern:

- Codeänderung
- Testabdeckung oder begründete Testgrenze
- Doku/Changelog
- lokale Validierungsbefehle
- bekannte Risiken

## Entscheidung

v18.9 macht die README zur aktuellen Betriebsquelle. Historische Versionsblöcke aus v8 bis v12 werden nicht mehr als Startpunkt geführt, sondern über Changelogs und Detaildokumente nachvollziehbar gehalten.
