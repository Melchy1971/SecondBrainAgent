# Delta v30.67 anwenden – Phase 3 Stabilisierung

Dieser Delta ist bewusst **nicht-destruktiv**: kein Bestands-Quellcode wurde gelöscht (Begründung: alle Dubletten sind noch in Benutzung, siehe Bericht). Enthalten sind sichere Cleanups, Validierung und Berichte.

## 1. Änderungen

Geändert:

- `.gitignore` (Root) und `SecondBrain-Agent/.gitignore` – Muster `.pytest_tmp*/` ergänzt.
- Git-Index: 2455 fälschlich getrackte Dateien in neun `.pytest_tmp_v3045_*`-Ordnern via `git rm -r --cached` entfernt (Arbeitsdateien bleiben).

Neu:

- `docs/releases/v30_67_phase3_stabilization.md` – Completion Report, Known Limitations, Remaining Risks, Phase 4 Readiness, Dubletten-Inventur + Deprecation-Plan.
- `README_PATCH.md`, `RELEASE_NOTES.md` (aktualisiert).

## 2. Übernehmen / Nachvollziehen

Falls nur die Doku/gitignore übernommen werden: Dateien kopieren. Für die Git-Bereinigung im eigenen Klon:

```powershell
git rm -r --cached SecondBrain-Agent/.pytest_tmp_v3045_a SecondBrain-Agent/.pytest_tmp_v3045_b `
  SecondBrain-Agent/.pytest_tmp_v3045_fix_a SecondBrain-Agent/.pytest_tmp_v3045_fix_b `
  SecondBrain-Agent/.pytest_tmp_v3045_fix_nested SecondBrain-Agent/.pytest_tmp_v3045_nested `
  SecondBrain-Agent/.pytest_tmp_v3045_probe_a SecondBrain-Agent/.pytest_tmp_v3045_probe_b `
  SecondBrain-Agent/.pytest_tmp_v3045_probe_nested
python scripts/p0_cleanup_artifacts.py
```

## 3. Validieren

```powershell
python -m compileall .
pytest -q
python launcher.py repo-doctor --project-root .
```

Erwartung (auf 3.13 mit installierten Deps): `compileall` fehlerfrei; `pytest` grün; RepoDoctor `ok: true`. Agent-Framework-Set (v30.61–v30.66) in dieser Umgebung: 170 passed.

## 4. Wichtige Hinweise

- **Git-Diffs vor Commit prüfen** – die Umgebung hat mehrfach Datei-Enden abgeschnitten (repariert + verifiziert), besonders `launcher.py` und `secondbrain/native/ai_workspace/service.py`.
- **2455 gestagte Löschungen** sind Untracking, keine Datei-Löschung. `git status` prüfen.
- **Keine Dubletten gelöscht.** Deprecation-Plan im Bericht (Reihenfolge: v107-Kernel → alter workflow_executor/ApprovalSystem → tool_registry_v121 → agent/background).
