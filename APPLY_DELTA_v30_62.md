# Delta v30.62 anwenden – Agent Workflow Engine

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/workflow/__init__.py`
- `secondbrain/agent/workflow/models.py`
- `secondbrain/agent/workflow/store.py`
- `secondbrain/agent/workflow/audit.py`
- `secondbrain/agent/workflow/recovery.py`
- `secondbrain/agent/workflow/executor.py`
- `secondbrain/agent/workflow/service.py`
- `secondbrain/agent/workflow/cli.py`
- `tests/_workflow_fakes.py`
- `tests/test_workflow_engine.py`
- `tests/test_workflow_checkpoint.py`
- `tests/test_workflow_recovery.py`
- `tests/test_workflow_approval.py`
- `docs/releases/v30_62_workflow_engine.md`

Geändert:

- `launcher.py` (Dispatch `workflow-*`)
- `README_PATCH.md`, `RELEASE_NOTES.md`

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_workflow_engine.py tests/test_workflow_checkpoint.py tests/test_workflow_recovery.py tests/test_workflow_approval.py -q
```

Erwartung: 21 passed. Zielinterpreter Python 3.11+.

## 3. Funktion prüfen

```powershell
python launcher.py workflow-create --objective "Demo" --steps-json "[{\"id\":\"s1\",\"name\":\"A\"},{\"id\":\"s2\",\"name\":\"B\",\"dependencies\":[\"s1\"]}]"
python launcher.py workflow-run <workflow_id>
python launcher.py workflow-status <workflow_id>
python launcher.py workflow-audit <workflow_id>
```

## 4. Hinweise

- **Keine zweite Approval Queue**: Freigabe-Schritte nutzen die v30.61-`SafetyService`/`NativeApprovalQueue` (`runtime/native/approval_queue.jsonl`).
- Der Workflow wird als `agent`-Job in der bestehenden Job Queue gespiegelt; Meldungen laufen über das Notification Center.
- Checkpoints: `runtime/agent/workflows/<id>.json` (atomar). Audit: `runtime/agent/workflows/workflow_audit.jsonl`.
- `resume` ist zustandsabhängig: `WAITING_APPROVAL` → Freigabe prüfen; `RUNNING`/`RETRYING`/`PENDING` → Absturz-Fortsetzung ab Checkpoint.
- Rollback wird nur **vorbereitet** (`workflow-rollback`), nicht automatisch ausgeführt.
