# Delta v30.65 anwenden – Agent Goal Tracking

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/goals/__init__.py`
- `secondbrain/agent/goals/models.py`
- `secondbrain/agent/goals/store.py`
- `secondbrain/agent/goals/tracker.py`
- `secondbrain/agent/goals/service.py`
- `secondbrain/agent/goals/cli.py`
- `tests/_goal_fakes.py`
- `tests/test_goal_tracking.py`
- `tests/test_goal_metrics.py`
- `tests/test_goal_reporting.py`
- `docs/releases/v30_65_goal_tracking.md`

Geändert:

- `launcher.py` (Dispatch `goal-*`)
- `README_PATCH.md`, `RELEASE_NOTES.md`

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_goal_tracking.py tests/test_goal_metrics.py tests/test_goal_reporting.py -q
```

Erwartung: 28 passed. Zielinterpreter Python 3.11+.

## 3. Funktion prüfen

```powershell
python launcher.py goal-create --title "SAP Migration Q3" --metric "tasks:10:4" --milestone "Analyse" --decompose
python launcher.py goal-update <goal_id> --metric tasks=8 --complete-milestone <milestone_id>
python launcher.py goal-report <goal_id>
python launcher.py goal-list
```

## 4. Hinweise

- Zerlegung nutzt den bestehenden `AgentPlanService`; Pläne bleiben in `runtime/agent/plans.json` (keine zweite Plan-Haltung).
- Fortschritt = Mittel aus Meilenstein-, Metrik- und Plan-Fortschritt.
- Persistenz unter `runtime/agent/goals/` (goals.json, reviews.jsonl, atomar).
- `close` verlangt 100 % Fortschritt oder `--force`.
- Dashboard-Anbindung über `GoalTracker.dashboard_snapshot()` (read-only Aggregat).
