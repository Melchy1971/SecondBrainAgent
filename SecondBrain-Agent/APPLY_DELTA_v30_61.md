# Delta v30.61 anwenden – Agent Approval & Safety Layer

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/safety/__init__.py`
- `secondbrain/agent/safety/risk.py`
- `secondbrain/agent/safety/policy.py`
- `secondbrain/agent/safety/models.py`
- `secondbrain/agent/safety/audit.py`
- `secondbrain/agent/safety/guard.py`
- `secondbrain/agent/safety/cli.py`
- `tests/test_agent_safety.py`
- `tests/test_approval_policy.py`
- `tests/test_action_guard.py`
- `docs/releases/v30_61_agent_safety.md`

Geändert:

- `secondbrain/native/approval.py` (rückwärtskompatible Erweiterung `create()`)
- `launcher.py` (Dispatch `approval-*`)
- `README_PATCH.md`, `RELEASE_NOTES.md`

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_agent_safety.py tests/test_approval_policy.py tests/test_action_guard.py -q
```

Erwartung: 41 passed. Zielinterpreter Python 3.11+.

## 3. Funktion prüfen

```powershell
python launcher.py approval-list
python launcher.py approval-audit --limit 5
```

## 4. Hinweise

- Es wird **keine zweite Approval Queue** angelegt. Alle Freigaben liegen weiterhin in `runtime/native/approval_queue.jsonl`, alle Audit-Einträge in `runtime/native/action_audit.jsonl`.
- Bestandsaufrufer von `NativeApprovalQueue.create()` (z.B. `AgentPlanService`) bleiben unverändert lauffähig.
- Abgelaufene Freigaben können per `python launcher.py approval-expire --ttl <sekunden>` als `expired` markiert werden (für geplante Läufe).
