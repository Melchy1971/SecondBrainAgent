# PATCH P2.5.3 — Connector Jobs & Monitoring

## Scope
- Added connector sync job lifecycle model.
- Added connector job runner with deterministic success/failure path.
- Added connector job history and monitoring snapshots.
- Added job service for queue/run/cancel operations.
- Added tests for completion, failure, cancellation, active snapshots, history filtering.

## Validation
- `5 passed in 0.23s`

## Files
- `secondbrain/desktop/connectors/jobs/connector_job_models.py`
- `secondbrain/desktop/connectors/jobs/connector_job_runner.py`
- `secondbrain/desktop/connectors/jobs/connector_job_history.py`
- `secondbrain/desktop/connectors/jobs/connector_job_monitor.py`
- `secondbrain/desktop/connectors/jobs/connector_job_service.py`
- `tests/desktop/connectors/test_connector_jobs_monitoring.py`
