from __future__ import annotations

import threading
import time
import json
import sqlite3

from secondbrain.importing import StreamingImportService
from secondbrain.importing.pipeline import Backoff, DeadLetterQueue, ImportScheduler, QueueManager, RetryManager, WorkerPool


def test_queue_manager_reuses_native_queue_and_claim_is_atomic(tmp_path):
    queue = QueueManager(tmp_path)
    created = queue.enqueue("chunk", payload={"pipeline_key": "s:1:chunk", "document_ids": ["d1"]})
    duplicate = queue.enqueue("chunk", payload={"pipeline_key": "s:1:chunk", "document_ids": ["d1"]})
    assert created.id == duplicate.id
    assert queue.queue_path == tmp_path.resolve() / "runtime" / "native" / "job_queue" / "jobs.jsonl"
    assert queue.claim().id == created.id
    assert queue.claim() is None


def test_worker_pool_processes_jobs_concurrently(tmp_path):
    queue = QueueManager(tmp_path)
    lock = threading.Lock()
    active = 0
    maximum = 0

    def handler(_job):
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
        time.sleep(0.04)
        with lock:
            active -= 1

    for index in range(4):
        queue.enqueue("chunk", payload={"pipeline_key": f"s:{index}:chunk", "document_ids": [str(index)]})
    pool = WorkerPool(queue, {"chunk": handler}, workers=2, poll_interval=0.005)
    pool.run_until_idle(timeout=3)
    assert maximum == 2
    assert all(job.status == "success" for job in queue.service.list_jobs(kind="chunk"))


def test_retry_backoff_and_dead_letter_use_same_queue(tmp_path):
    queue = QueueManager(tmp_path)
    retry = RetryManager(queue, Backoff(base_seconds=0, maximum_seconds=0))
    queue.enqueue("chunk", payload={"pipeline_key": "s:retry:chunk", "document_ids": ["d"]}, max_attempts=2)

    first = queue.claim()
    retried = retry.fail(first, RuntimeError("temporary"))
    assert retried.status == "retry"
    second = queue.claim()
    dead = retry.fail(second, RuntimeError("permanent"))
    assert dead.status == "dead_letter"
    assert DeadLetterQueue(queue).list()[0].id == dead.id
    assert DeadLetterQueue(queue).requeue(dead.id).status == "pending"


def test_streaming_service_delegates_jobs_to_canonical_import_runtime(tmp_path):
    source = tmp_path / "items.jsonl"
    source.write_text(json.dumps({"content": "one"}) + "\n", encoding="utf-8")
    service = StreamingImportService(tmp_path, batch_size=1)

    class Job:
        checkpoint = {}

    class Context:
        cancelled = False

        def checkpoint(self, value, *, progress):
            self.value = value
            self.progress = progress

    class Sink:
        def __init__(self):
            self.records = []

        def ingest(self, record, *, key):
            self.records.append((record, key))
            return True

    context = Context()
    sink = Sink()
    result = service.run_job(Job(), context, file_path=source, sink=sink)
    assert result["done"] is True
    assert len(sink.records) == 1
    assert context.progress == 1.0


def test_import_hands_content_to_canonical_runtime_before_chunking(tmp_path):
    source = tmp_path / "queued.jsonl"
    source.write_text(json.dumps({"content": "queued"}) + "\n", encoding="utf-8")
    service = StreamingImportService(tmp_path, batch_size=1)
    session = service.import_file(source)
    with sqlite3.connect(service.db_path) as connection:
        chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        staged = connection.execute("SELECT COUNT(*) FROM import_stage_records").fetchone()[0]
    assert session.status == "completed"
    assert chunks == 0 and staged == 1
    assert service.queue.list_jobs(kind="chunk")[0].status == "pending"
    assert service.scheduler.__class__.__module__ == "secondbrain.jobs.import_runtime"
