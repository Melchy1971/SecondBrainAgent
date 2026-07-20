from secondbrain.desktop_native.job_surface import JobSurface
from secondbrain.native.job_queue_center.service import JobQueueService


def test_surface_shows_running_and_blocked_jobs_without_payloads(tmp_path):
    service = JobQueueService(tmp_path)
    running = service.add_job("import", "Dokument importieren", payload={"path": "C:/secret/private.pdf"})
    service.update_status(running.id, "running")
    service.add_job("approval", "Freigabe abwarten", approval_required=True, payload={"token": "secret"})
    snapshot = JobSurface(service).snapshot()
    assert snapshot["running_count"] == 1
    assert snapshot["blocked_count"] == 1
    assert snapshot["workspace_isolated"] is True
    assert snapshot["payloads_exposed"] is False
    rendered = repr(snapshot)
    assert "private.pdf" not in rendered
    assert "token" not in rendered


def test_surface_is_read_only_and_limits_visible_rows(tmp_path):
    service = JobQueueService(tmp_path)
    first = service.add_job("system", "Erster Job")
    service.add_job("system", "Zweiter Job")
    snapshot = JobSurface(service, limit=1).snapshot()
    assert snapshot["total"] == 2
    assert snapshot["visible_count"] == 1
    assert service.get_job(first.id).status == "pending"
