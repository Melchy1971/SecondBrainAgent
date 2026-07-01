# APPLY DELTA v30.44 – Native Job & Queue Center

## Ziel
Zentrale native Queue-/Job-Übersicht für Imports, Reindex, Agent Tasks, Voice Actions, Updates und Approval-gated Actions.

## Dateien kopieren
- `secondbrain/native/job_queue_center/`
- `tests/test_v3044_native_job_queue_center.py`

## Launcher ergänzen
Folgende Aliase auf `secondbrain.native.job_queue_center.cli:main` mappen:

```text
job-queue-status -> status
job-queue-add -> add
job-queue-list -> list
job-queue-run -> run
job-queue-approve -> approve
job-queue-cancel -> cancel
job-queue-clear-finished -> clear-finished
job-queue-center-gui -> secondbrain.native.job_queue_center.gui:launch
```

## Validierung
```bash
python -m compileall secondbrain
pytest tests/test_v3044_native_job_queue_center.py -q
python -m secondbrain.native.job_queue_center.cli status
```
