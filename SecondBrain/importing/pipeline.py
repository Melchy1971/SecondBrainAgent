"""Parallel import stages backed by the existing native runtime queue.

.. deprecated::
    Dieser Pfad ist nicht mehr der produktive Standard fuer Importe. Grosse
    Chat- und Dokumentimporte laufen ueber die kanonische Job-Runtime
    (``SecondBrain/jobs/import_runtime.py``) mit Checkpoints in der
    Job-Repository. Dieses Modul bleibt vorerst fuer Kompatibilitaet erhalten
    und wird in einer spaeteren Phase entfernt. Beim Import wird eine
    ``DeprecationWarning`` ausgeloest.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "SecondBrain.importing.pipeline ist deprecated; nutze die kanonische "
    "Job-Runtime SecondBrain.jobs.import_runtime fuer produktive Importe.",
    DeprecationWarning,
    stacklevel=2,
)

import json
import hashlib
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Mapping

from secondbrain.native.job_queue_center.models import JobKind, QueueJob
from secondbrain.native.job_queue_center.service import JobQueueService
from secondbrain.p1_embeddings import embedding_index_provider, provider_from_profile
from secondbrain.p1_rag_runtime import chunk_text, tokenize
from secondbrain.p3_rag_store import RagChunkRecord, RagDocumentRecord, RagVectorRecord, create_rag_store
from secondbrain.importing.quality import ImportQualityEvaluator
from secondbrain.native.knowledge_graph_foundation import KnowledgeGraphFoundation

PIPELINE_STAGES: tuple[JobKind, ...] = ("chunk", "embedding", "memory", "graph", "search")


@dataclass(frozen=True, slots=True)
class Backoff:
    base_seconds: float = 1.0
    maximum_seconds: float = 300.0

    def delay(self, attempt: int) -> float:
        return min(self.maximum_seconds, self.base_seconds * (2 ** max(0, int(attempt) - 1)))


class QueueManager:
    """Pipeline facade over JobQueueService; it creates no additional queue."""

    def __init__(self, root: str | Path = ".", service: JobQueueService | None = None) -> None:
        self.service = service or JobQueueService(root)

    @property
    def queue_path(self) -> Path:
        return self.service.queue_path

    def enqueue(self, stage: JobKind, *, payload: dict, priority: int = 50, max_attempts: int = 3, parent_job_id: str | None = None) -> QueueJob:
        if stage not in PIPELINE_STAGES:
            raise ValueError(f"unknown import stage: {stage}")
        key = str(payload.get("pipeline_key") or "")
        if key:
            existing = next((job for job in self.service.list_jobs(kind=stage) if (job.payload or {}).get("pipeline_key") == key and job.status not in {"failed", "cancelled", "dead_letter"}), None)
            if existing:
                return existing
        return self.service.add_job(stage, f"Import {stage.title()}", priority=priority, payload=payload, max_attempts=max_attempts, parent_job_id=parent_job_id)

    def claim(self) -> QueueJob | None:
        return self.service.claim_next(kinds=set(PIPELINE_STAGES))

    def complete(self, job: QueueJob) -> QueueJob:
        return self.service.update_status(job.id, "success")


class DeadLetterQueue:
    """Dead letters are a status in the same runtime queue, not a second store."""

    def __init__(self, queue: QueueManager) -> None:
        self.queue = queue

    def list(self) -> list[QueueJob]:
        return self.queue.service.list_jobs(status="dead_letter")

    def requeue(self, job_id: str) -> QueueJob:
        return self.queue.service.update_job(job_id, status="pending", attempts=0, available_at=0.0, error=None)


class RetryManager:
    def __init__(self, queue: QueueManager, backoff: Backoff | None = None) -> None:
        self.queue = queue
        self.backoff = backoff or Backoff()

    def fail(self, job: QueueJob, error: BaseException) -> QueueJob:
        message = f"{type(error).__name__}: {error}"[:2000]
        if job.attempts >= job.max_attempts:
            return self.queue.service.update_job(job.id, status="dead_letter", error=message, available_at=0.0)
        return self.queue.service.update_job(job.id, status="retry", error=message, available_at=time.time() + self.backoff.delay(job.attempts))


class WorkerPool:
    def __init__(self, queue: QueueManager, handlers: Mapping[str, Callable[[QueueJob], None]], *, workers: int | None = None, retry: RetryManager | None = None, poll_interval: float = 0.05) -> None:
        configured = os.getenv("SECONDBRAIN_IMPORT_WORKERS")
        default_workers = max(1, min(8, (os.cpu_count() or 2) - 1))
        self.workers = max(1, int(workers if workers is not None else (configured or default_workers)))
        self.queue = queue
        self.handlers = dict(handlers)
        self.retry = retry or RetryManager(queue)
        self.poll_interval = max(0.005, float(poll_interval))
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if any(thread.is_alive() for thread in self._threads):
            return
        self._stop.clear()
        self._threads = [threading.Thread(target=self._run, name=f"import-worker-{index + 1}", daemon=True) for index in range(self.workers)]
        for thread in self._threads:
            thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        deadline = time.monotonic() + timeout
        for thread in self._threads:
            thread.join(max(0.0, deadline - time.monotonic()))

    def run_until_idle(self, timeout: float = 30.0) -> None:
        self.start()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            jobs = [job for job in self.queue.service.list_jobs() if job.kind in PIPELINE_STAGES]
            if jobs and all(job.status in {"success", "failed", "cancelled", "dead_letter"} for job in jobs):
                self.stop(); return
            if not jobs:
                self.stop(); return
            time.sleep(self.poll_interval)
        self.stop()
        raise TimeoutError("import worker pool did not become idle")

    def _run(self) -> None:
        while not self._stop.is_set():
            job = self.queue.claim()
            if job is None:
                self._stop.wait(self.poll_interval); continue
            try:
                handler = self.handlers.get(job.kind)
                if handler is None:
                    raise LookupError(f"no handler for stage {job.kind}")
                handler(job)
                self.queue.complete(job)
            except Exception as exc:
                self.retry.fail(job, exc)


class ImportScheduler:
    """Schedules stage hand-offs without joining them from the import thread."""

    def __init__(self, root: str | Path = ".", *, db_path: str | Path | None = None, workers: int | None = None, embedding_provider=None, queue: QueueManager | None = None) -> None:
        self.root = Path(root).resolve()
        self.db_path = Path(db_path) if db_path else self.root / "runtime" / "p1_rag" / "rag.sqlite3"
        self.queue = queue or QueueManager(self.root)
        self.embedding_provider = embedding_provider
        self.selected_store = create_rag_store(self.root, sqlite_db_path=self.db_path)
        self.graph_foundation = KnowledgeGraphFoundation()
        self.pool = WorkerPool(self.queue, {"chunk": self._chunk, "embedding": self._embedding, "memory": self._memory, "graph": self._graph, "search": self._search}, workers=workers)

    def schedule(self, session_id: str, document_ids: list[str], *, batch_position: int, parent_job_id: str | None = None) -> QueueJob:
        key = f"{session_id}:{batch_position}"
        return self.queue.enqueue("chunk", payload={"session_id": session_id, "document_ids": document_ids, "pipeline_key": f"{key}:chunk", "batch_key": key, "db_path": str(self.db_path)}, priority=30, parent_job_id=parent_job_id)

    def start(self) -> None:
        self.pool.start()

    def stop(self) -> None:
        self.pool.stop()

    def _next(self, job: QueueJob, stage: JobKind, **extra) -> None:
        payload = dict(job.payload or {})
        payload.update(extra)
        payload["pipeline_key"] = f"{payload['batch_key']}:{stage}"
        self.queue.enqueue(stage, payload=payload, priority=job.priority, parent_job_id=job.id)

    def _chunk(self, job: QueueJob) -> None:
        ids = list((job.payload or {}).get("document_ids") or [])
        if not ids:
            raise ValueError("chunk job has no documents")
        marks = ",".join("?" for _ in ids)
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as connection:
            records = connection.execute(f"SELECT document_id,content FROM import_stage_records WHERE document_id IN ({marks}) ORDER BY document_id", ids).fetchall()
            chunks = []
            for document_id, content in records:
                cursor = 0
                for ordinal, text in enumerate(chunk_text(content)):
                    start = content.find(text[:80], cursor)
                    start = cursor if start < 0 else start
                    end = start + len(text); cursor = end
                    tokens = tokenize(text)
                    chunk_id = f"chk_{hashlib.sha256(f'{document_id}|{ordinal}|{text}'.encode('utf-8')).hexdigest()[:24]}"
                    chunks.append((chunk_id, document_id, ordinal, text, start, end, json.dumps(tokens, ensure_ascii=False), len(tokens), now))
            connection.execute(f"DELETE FROM chunk_embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id IN ({marks}))", ids)
            connection.execute(f"DELETE FROM chunks WHERE document_id IN ({marks})", ids)
            connection.executemany("INSERT INTO chunks(id,document_id,ordinal,text,char_start,char_end,token_json,token_count,created_at) VALUES(?,?,?,?,?,?,?,?,?)", chunks)
            connection.execute(f"UPDATE import_stage_records SET state='chunked',updated_at=? WHERE document_id IN ({marks})", [now, *ids])
            session_id = str((job.payload or {}).get("session_id") or "")
            connection.execute("UPDATE import_sessions SET chunks=(SELECT COUNT(*) FROM chunks c JOIN documents d ON d.id=c.document_id WHERE json_extract(d.metadata_json,'$.import_session')=?),updated_at=? WHERE session_id=?", (session_id, now, session_id))
            document_rows = connection.execute(f"SELECT id,source,title,content_hash,created_at,metadata_json FROM documents WHERE id IN ({marks})", ids).fetchall()
        # Persist a baseline score even when the external embedding provider later fails.
        ImportQualityEvaluator(self.db_path).evaluate(ids)
        if self.selected_store.backend == "pgvector":
            documents = [RagDocumentRecord(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), json.loads(row[5] or "{}")) for row in document_rows]
            chunk_records = [RagChunkRecord(str(row[0]), str(row[1]), int(row[2]), str(row[3]), int(row[4]), int(row[5]), json.loads(row[6]), int(row[7]), str(row[8])) for row in chunks]
            for result in (self.selected_store.copy_documents(documents), self.selected_store.copy_chunks(chunk_records)):
                if not result.get("ok"):
                    raise RuntimeError(f"postgres_copy_failed: {result.get('error', 'unknown')}")
        self._next(job, "embedding", chunk_ids=[row[0] for row in chunks])

    def _embedding(self, job: QueueJob) -> None:
        chunk_ids = list((job.payload or {}).get("chunk_ids") or [])
        if chunk_ids:
            marks = ",".join("?" for _ in chunk_ids)
            with sqlite3.connect(self.db_path) as connection:
                rows = connection.execute(f"SELECT id,text FROM chunks WHERE id IN ({marks}) ORDER BY id", chunk_ids).fetchall()
                provider = self.embedding_provider or provider_from_profile(self.root)
                provider_name = embedding_index_provider(provider)
                now = datetime.now(UTC).isoformat()
                vectors = [(row[0], provider_name, len(vector), json.dumps(vector), now) for row in rows for vector in [provider.embed(row[1])]]
                connection.executemany("INSERT OR REPLACE INTO chunk_embeddings(chunk_id,provider,dimensions,vector_json,created_at) VALUES(?,?,?,?,?)", vectors)
                session_id = str((job.payload or {}).get("session_id") or "")
                connection.execute("UPDATE import_sessions SET embeddings=(SELECT COUNT(*) FROM chunk_embeddings e JOIN chunks c ON c.id=e.chunk_id JOIN documents d ON d.id=c.document_id WHERE json_extract(d.metadata_json,'$.import_session')=?), updated_at=? WHERE session_id=?", (session_id, now, session_id))
            if self.selected_store.backend == "pgvector":
                vector_records = [RagVectorRecord(str(row[0]), str(row[1]), int(row[2]), json.loads(row[3]), str(row[4])) for row in vectors]
                result = self.selected_store.copy_vectors(vector_records)
                if not result.get("ok"):
                    raise RuntimeError(f"pgvector_update_failed: {result.get('error', 'unknown')}")
        self._next(job, "memory")

    def _memory(self, job: QueueJob) -> None:
        self._mark_projection(job, "memory_indexed_at")
        self._next(job, "graph")

    def _graph(self, job: QueueJob) -> None:
        self._mark_projection(job, "graph_indexed_at")
        payload = job.payload or {}
        db_path = payload.get("db_path")
        document_ids = list(payload.get("document_ids") or [])
        if db_path and document_ids:
            self._extract_graph_suggestions(db_path, document_ids)
        self._next(job, "search")

    def _extract_graph_suggestions(self, db_path: str | Path, document_ids: list[str]) -> None:
        marks = ",".join("?" for _ in document_ids)
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                f"SELECT d.id,d.source,d.title,d.metadata_json,s.content FROM documents d "
                f"JOIN import_stage_records s ON s.document_id=d.id "
                f"WHERE d.id IN ({marks})",
                document_ids,
            ).fetchall()
            for row in rows:
                document_id, source, title, metadata_json, content = row
                try:
                    metadata = json.loads(metadata_json or "{}")
                    metadata = metadata if isinstance(metadata, dict) else {}
                except (TypeError, ValueError, json.JSONDecodeError):
                    metadata = {}
                suggestion = self.graph_foundation.suggest(
                    document_id=str(document_id),
                    title=str(title or document_id),
                    text=str(content or ""),
                    metadata=metadata,
                    source=str(source or "import"),
                ).to_dict()
                metadata["graph_entity_suggestions"] = suggestion["entities"]
                metadata["graph_relationship_suggestions"] = suggestion["relationships"]
                metadata["graph_foundation_version"] = self.graph_foundation.VERSION
                connection.execute(
                    "UPDATE documents SET metadata_json=? WHERE id=?",
                    (json.dumps(metadata, ensure_ascii=False), document_id),
                )

    def _search(self, job: QueueJob) -> None:
        # Search reads the existing RAG store; terminal payloads can be released.
        payload = job.payload or {}
        db_path = payload.get("db_path")
        if db_path:
            with sqlite3.connect(db_path) as connection:
                ids = list(payload.get("document_ids") or [])
                if ids:
                    ImportQualityEvaluator(db_path).evaluate(ids)
                    marks = ",".join("?" for _ in ids)
                    now = datetime.now(UTC).isoformat()
                    if self.selected_store.backend == "pgvector":
                        rows = connection.execute(f"SELECT id,source,title,content_hash,created_at,metadata_json FROM documents WHERE id IN ({marks})", ids).fetchall()
                        documents = [RagDocumentRecord(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), json.loads(row[5] or "{}")) for row in rows]
                        result = self.selected_store.copy_documents(documents)
                        if not result.get("ok"):
                            raise RuntimeError(f"postgres_quality_update_failed: {result.get('error', 'unknown')}")
                    connection.execute(f"UPDATE documents SET metadata_json=json_set(metadata_json,'$.search_indexed_at',?) WHERE id IN ({marks})", [now, *ids])
                    connection.execute(f"DELETE FROM import_stage_records WHERE document_id IN ({marks})", ids)

    @staticmethod
    def _mark_projection(job: QueueJob, field: str) -> None:
        payload = job.payload or {}
        ids = list(payload.get("document_ids") or [])
        db_path = payload.get("db_path")
        if not db_path or not ids:
            return
        marks = ",".join("?" for _ in ids)
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(db_path) as connection:
            connection.execute(f"UPDATE documents SET metadata_json=json_set(metadata_json,'$.{field}',?) WHERE id IN ({marks})", [now, *ids])
