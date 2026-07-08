from secondbrain.native.job_queue_center.service import JobQueueService


def test_add_and_snapshot(tmp_path):
    service = JobQueueService(tmp_path)
    job = service.add_job("import", "Importiere Dokument")
    snap = service.snapshot()
    assert job.id.startswith("job_")
    assert snap["total"] == 1
    assert snap["counts"]["pending"] == 1


def test_approval_job_is_blocked_then_pending(tmp_path):
    service = JobQueueService(tmp_path)
    job = service.add_job("reindex", "Repariere Index", approval_required=True)
    assert service.get_job(job.id).status == "blocked"
    approved = service.approve(job.id)
    assert approved.status == "pending"


def test_status_transition_and_history(tmp_path):
    service = JobQueueService(tmp_path)
    job = service.add_job("agent", "Analysiere Projekt")
    running = service.update_status(job.id, "running")
    assert running.status == "running"
    assert service.history_path.exists()


def test_clear_finished_keeps_active(tmp_path):
    service = JobQueueService(tmp_path)
    done = service.add_job("system", "Fertig")
    active = service.add_job("voice", "Zuhören")
    service.update_status(done.id, "success")
    assert service.clear_finished() == 1
    assert service.get_job(active.id) is not None


def test_cancel(tmp_path):
    service = JobQueueService(tmp_path)
    job = service.add_job("update", "Update prüfen")
    assert service.cancel(job.id).status == "cancelled"
