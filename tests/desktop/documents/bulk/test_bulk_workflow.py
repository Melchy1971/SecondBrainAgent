from secondbrain.desktop.documents import DesktopDocument, DocumentRepository, DocumentStatus
from secondbrain.desktop.documents.bulk import BulkEngine, BulkJobState, BulkQueue, BulkValidationError
from secondbrain.desktop.documents.bulk.bulk_events import BULK_ITEM_FAILED, BULK_JOB_COMPLETED, BULK_PROGRESS_UPDATED


def repo_with_documents():
    return DocumentRepository([
        DesktopDocument("d1", "Doc 1", "w1", "manual", tags=("a",)),
        DesktopDocument("d2", "Doc 2", "w1", "manual", tags=("b",)),
    ])


def test_bulk_job_requires_action_and_document_ids():
    engine = BulkEngine(repo_with_documents())
    try:
        engine.create_job("", ["d1"])
        assert False
    except BulkValidationError:
        pass
    try:
        engine.create_job("archive", [])
        assert False
    except BulkValidationError:
        pass


def test_bulk_queue_is_fifo_and_marks_jobs_queued():
    engine = BulkEngine(repo_with_documents())
    first = engine.create_job("archive", ["d1"])
    second = engine.create_job("archive", ["d2"])
    queue = BulkQueue()
    queued_first = queue.enqueue(first)
    queue.enqueue(second)
    assert queued_first.state == BulkJobState.QUEUED
    assert queue.dequeue().job_id == first.job_id
    assert queue.dequeue().job_id == second.job_id


def test_archive_bulk_action_updates_all_documents():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("archive", ["d1", "d2"])
    assert job.state == BulkJobState.COMPLETED
    assert job.processed_items == 2
    assert job.failed_items == 0
    assert repo.require("d1").status == DocumentStatus.ARCHIVED
    assert repo.require("d2").status == DocumentStatus.ARCHIVED


def test_partial_failure_is_isolated_per_document():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("archive", ["d1", "missing"])
    assert job.state == BulkJobState.PARTIAL_FAILURE
    assert job.processed_items == 2
    assert job.failed_items == 1
    assert repo.require("d1").status == DocumentStatus.ARCHIVED
    assert any(event.event_type == BULK_ITEM_FAILED for event in engine.events.events)


def test_move_workspace_requires_target_workspace():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("move_workspace", ["d1"])
    assert job.state == BulkJobState.PARTIAL_FAILURE
    assert job.failed_items == 1
    assert repo.require("d1").workspace_id == "w1"


def test_move_workspace_updates_repository():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("move_workspace", ["d1", "d2"], target_workspace_id="w2")
    assert job.state == BulkJobState.COMPLETED
    assert repo.require("d1").workspace_id == "w2"
    assert repo.require("d2").workspace_id == "w2"


def test_add_and_remove_tags_are_deduplicated():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    engine.run_immediately("add_tags", ["d1"], tags=["a", "x", "x"])
    assert repo.require("d1").tags == ("a", "x")
    engine.run_immediately("remove_tags", ["d1"], tags=["a"])
    assert repo.require("d1").tags == ("x",)


def test_delete_bulk_action_removes_documents():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("delete", ["d1"])
    assert job.state == BulkJobState.COMPLETED
    assert repo.get("d1") is None
    assert repo.count() == 1


def test_enqueue_and_run_next_records_history_and_events():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    queued = engine.enqueue(engine.create_job("reindex", ["d1", "d2"]))
    assert queued.state == BulkJobState.QUEUED
    completed = engine.run_next()
    assert completed is not None
    assert completed.state == BulkJobState.COMPLETED
    assert engine.history.get(completed.job_id) == completed
    event_types = [event.event_type for event in engine.events.events]
    assert BULK_PROGRESS_UPDATED in event_types
    assert BULK_JOB_COMPLETED in event_types
    assert repo.require("d1").status == DocumentStatus.INDEXING


def test_rollback_restores_documents_after_destructive_action():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("delete", ["d1"])
    engine.history.record(job)
    assert repo.get("d1") is None
    restored_job = engine.rollback(job.job_id)
    assert restored_job.state == BulkJobState.ROLLBACK
    assert repo.require("d1").title == "Doc 1"


def test_progress_percent_tracks_items():
    repo = repo_with_documents()
    engine = BulkEngine(repo)
    job = engine.run_immediately("archive", ["d1", "missing"])
    assert job.progress_percent == 100
    assert [result.success for result in job.item_results] == [True, False]
