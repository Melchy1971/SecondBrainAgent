"""v30.51 resumable, bounded-memory imports into the existing P1 RAG store."""
from __future__ import annotations

import codecs
import json
import os
import sqlite3
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Callable, Iterable, Iterator
from zipfile import ZipFile

import ijson

from secondbrain.native.job_queue_center.service import JobQueueService
from secondbrain.importing.pipeline import ImportScheduler
from secondbrain.importing.normalization import Conversation, document_record, normalize_conversation
from secondbrain.document_understanding.orchestrator import default_multi_format_orchestrator
from secondbrain.document_understanding.parser_contract import ParsedDocument, ParseStatus
from secondbrain.p3_rag_store import SQLiteRagStore
from secondbrain.rag.indexing.change_detector import ChangeAction, ChangeDetector, DocumentSnapshot, hash_document_text


DOCUMENT_SUFFIXES = {".pst", ".eml", ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".markdown",
                     ".json", ".jsonl", ".png", ".jpg", ".jpeg", ".one"}
SUPPORTED_SUFFIXES = {".json", ".jsonl", ".ndjson", ".html", ".zip", *DOCUMENT_SUFFIXES}
DEFAULT_BATCH_SIZE = 500


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ImportSession:
    session_id: str
    file_path: str
    source: str
    file_size: int
    file_mtime_ns: int = 0
    bytes_processed: int = 0
    position: int = 0
    imported_chats: int = 0
    chunks: int = 0
    embeddings: int = 0
    new_documents: int = 0
    updated_documents: int = 0
    skipped_documents: int = 0
    status: str = "pending"
    control_state: str = "running"
    error: str = ""
    batch_size: int = DEFAULT_BATCH_SIZE
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ImportProgress:
    session_id: str
    bytes_processed: int
    total_bytes: int
    position: int
    imported_chats: int
    chunks: int
    embeddings: int
    status: str

    @property
    def percent(self) -> float:
        return round(min(100.0, 100.0 * self.bytes_processed / max(1, self.total_bytes)), 2)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "percent": self.percent}


class CheckpointManager:
    """Persists import checkpoints in the existing RAG SQLite database."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        migrations = Path(__file__).resolve().parents[1] / "storage" / "migrations"
        with self.connect() as connection:
            for name in ("004_import_sessions.sql", "005_parallel_import.sql", "006_delta_import.sql"):
                connection.executescript((migrations / name).read_text(encoding="utf-8"))
            columns = {row[1] for row in connection.execute("PRAGMA table_info(import_sessions)")}
            if "control_state" not in columns:
                connection.execute("ALTER TABLE import_sessions ADD COLUMN control_state TEXT NOT NULL DEFAULT 'running'")
            for column in ("new_documents", "updated_documents", "skipped_documents", "file_mtime_ns"):
                if column not in columns:
                    connection.execute(f"ALTER TABLE import_sessions ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0")

    def create(self, file_path: str | Path, source: str, *, batch_size=DEFAULT_BATCH_SIZE) -> ImportSession:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(str(path))
        now = _now()
        session = ImportSession(
            session_id=f"imp_{uuid.uuid4().hex}", file_path=str(path), source=source.strip().lower() or "file",
            file_size=path.stat().st_size, file_mtime_ns=path.stat().st_mtime_ns,
            batch_size=max(1, int(batch_size)), created_at=now, updated_at=now,
        )
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO import_sessions
                (session_id,file_path,source,file_size,file_mtime_ns,bytes_processed,position,imported_chats,chunks,embeddings,new_documents,updated_documents,skipped_documents,status,control_state,error,batch_size,created_at,updated_at)
                VALUES (:session_id,:file_path,:source,:file_size,:file_mtime_ns,:bytes_processed,:position,:imported_chats,:chunks,:embeddings,:new_documents,:updated_documents,:skipped_documents,:status,:control_state,:error,:batch_size,:created_at,:updated_at)""",
                session.to_dict(),
            )
        return session

    def get(self, session_id: str) -> ImportSession | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM import_sessions WHERE session_id=?", (session_id,)).fetchone()
        return ImportSession(**dict(row)) if row else None

    def save(self, session: ImportSession, connection: sqlite3.Connection | None = None) -> None:
        sql = """UPDATE import_sessions SET file_path=:file_path,source=:source,file_size=:file_size,file_mtime_ns=:file_mtime_ns,
            bytes_processed=:bytes_processed,position=:position,imported_chats=:imported_chats,chunks=:chunks,
            embeddings=:embeddings,new_documents=:new_documents,updated_documents=:updated_documents,skipped_documents=:skipped_documents,
            status=:status,control_state=:control_state,error=:error,batch_size=:batch_size,updated_at=:updated_at
            WHERE session_id=:session_id"""
        if connection is not None:
            connection.execute(sql, session.to_dict())
            return
        with self.connect() as own_connection:
            own_connection.execute(sql, session.to_dict())

    def latest_for_file(self, file_path: str | Path) -> ImportSession | None:
        path = str(Path(file_path).expanduser().resolve())
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM import_sessions WHERE file_path=? ORDER BY updated_at DESC LIMIT 1", (path,)).fetchone()
        return ImportSession(**dict(row)) if row else None

    def list(self, limit: int = 100) -> list[ImportSession]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM import_sessions ORDER BY updated_at DESC LIMIT ?", (max(0, int(limit)),)).fetchall()
        return [ImportSession(**dict(row)) for row in rows]


class BatchWriter:
    """Uses executemany for documents/chunks and checkpoints in one transaction."""

    def __init__(self, db_path: str | Path, checkpoints: CheckpointManager) -> None:
        self.db_path = Path(db_path)
        self.checkpoints = checkpoints
        self.change_detector = ChangeDetector()

    def write(self, records: list[dict[str, Any]], session: ImportSession, *, bytes_processed: int, position: int) -> tuple[ImportSession, list[str]]:
        if not records:
            return session, []
        documents: list[tuple[Any, ...]] = []
        staged: list[tuple[Any, ...]] = []
        document_ids: list[str] = []
        deltas: list[tuple[Any, ...]] = []
        new_count = updated_count = skipped_count = 0
        now = _now()
        with self.checkpoints.connect() as connection:
            control_row = connection.execute("SELECT control_state FROM import_sessions WHERE session_id=?", (session.session_id,)).fetchone()
            control_state = str(control_row[0]) if control_row else session.control_state
            batch_hashes: set[str] = set()
            for record in records:
                content = str(record.get("content") or "")
                content_hash = hash_document_text(content)
                document_id = str(record["id"])
                title = str(record.get("title") or document_id)
                existing = connection.execute("SELECT id,title,content_hash,metadata_json FROM documents WHERE id=?", (document_id,)).fetchone()
                duplicate = connection.execute("SELECT id FROM documents WHERE content_hash=? AND id<>? LIMIT 1", (content_hash, document_id)).fetchone()
                previous_hash = str(existing["content_hash"]) if existing else ""
                previous = [DocumentSnapshot(document_id, previous_hash)] if existing else []
                planned = self.change_detector.plan(previous, [DocumentSnapshot(document_id, content_hash)])[0]
                if planned.action == ChangeAction.SKIP or (not existing and (duplicate or content_hash in batch_hashes)):
                    skipped_count += 1
                    action = "unchanged" if existing else "duplicate"
                    deltas.append((session.session_id, document_id, action, content_hash, previous_hash, now))
                    continue

                max_version = int(connection.execute("SELECT COALESCE(MAX(version_number),0) FROM document_versions WHERE document_id=?", (document_id,)).fetchone()[0])
                if existing and max_version == 0:
                    old_content = "\n\n".join(row[0] for row in connection.execute("SELECT text FROM chunks WHERE document_id=? ORDER BY ordinal", (document_id,)))
                    connection.execute("INSERT INTO document_versions(document_id,version_number,content_hash,title,content,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)",
                                       (document_id, 1, previous_hash, str(existing["title"]), old_content, str(existing["metadata_json"]), now))
                    max_version = 1
                version_number = max_version + 1 if existing else 1
                metadata = {**dict(record.get("metadata") or {}), "import_session": session.session_id,
                            "position": record["position"], "version_number": version_number, "previous_hash": previous_hash}
                metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str)
                connection.execute("INSERT INTO document_versions(document_id,version_number,content_hash,title,content,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)",
                                   (document_id, version_number, content_hash, title, content, metadata_json, now))
                documents.append((document_id, session.source, title, content_hash, now, metadata_json))
                staged.append((document_id, session.session_id, content, "pending", now, now))
                document_ids.append(document_id)
                batch_hashes.add(content_hash)
                if existing:
                    updated_count += 1; action = "updated"
                else:
                    new_count += 1; action = "new"
                deltas.append((session.session_id, document_id, action, content_hash, previous_hash, now))

            placeholders = ",".join("?" for _ in document_ids)
            if document_ids:
                connection.execute(f"DELETE FROM chunk_embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id IN ({placeholders}))", document_ids)
                connection.execute(f"DELETE FROM chunks WHERE document_id IN ({placeholders})", document_ids)
            connection.executemany(
                """INSERT INTO documents(id,source,title,content_hash,created_at,metadata_json) VALUES(?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET source=excluded.source,title=excluded.title,content_hash=excluded.content_hash,metadata_json=excluded.metadata_json""",
                documents,
            )
            connection.executemany("""INSERT INTO import_stage_records(document_id,session_id,content,state,created_at,updated_at)
                VALUES(?,?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET session_id=excluded.session_id,content=excluded.content,state='pending',updated_at=excluded.updated_at""", staged)
            connection.executemany("INSERT INTO import_delta_entries(session_id,document_id,action,content_hash,previous_hash,created_at) VALUES(?,?,?,?,?,?)", deltas)
            updated = replace(
                session, bytes_processed=max(session.bytes_processed, int(bytes_processed)), position=int(position),
                imported_chats=session.imported_chats + new_count + updated_count,
                new_documents=session.new_documents + new_count, updated_documents=session.updated_documents + updated_count,
                skipped_documents=session.skipped_documents + skipped_count,
                status="paused" if control_state == "paused" else ("stopped" if control_state == "stopped" else "running"),
                control_state=control_state, error="", updated_at=_now(),
            )
            self.checkpoints.save(updated, connection)
        return updated, document_ids


class StreamingImportService:
    """The single file/chat import engine used by CLI, modules and Import Center."""

    def __init__(self, project_root: str | Path = ".", *, batch_size=DEFAULT_BATCH_SIZE, db_path: str | Path | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.batch_size = max(1, int(batch_size))
        self.db_path = Path(db_path) if db_path else self.project_root / "runtime" / "p1_rag" / "rag.sqlite3"
        SQLiteRagStore(self.db_path)  # existing RAG schema and database layer
        self.checkpoints = CheckpointManager(self.db_path)
        self.writer = BatchWriter(self.db_path, self.checkpoints)
        self.queue = JobQueueService(self.project_root)
        self.scheduler = ImportScheduler(self.project_root, db_path=self.db_path)
        self.document_parser = default_multi_format_orchestrator()

    def import_file(
        self,
        file_path: str | Path,
        *,
        source: str | None = None,
        session_id: str | None = None,
        progress: Callable[[ImportProgress], None] | None = None,
        stop_after_batches: int | None = None,
        workspace_id: str = "default",
        version: str | None = None,
        document_mode: bool = False,
        auto_resume: bool = True,
        auto_retry: int = 2,
        _retry_attempt: int = 0,
    ) -> ImportSession:
        path = Path(file_path).expanduser().resolve()
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise ValueError(f"unsupported streaming format: {path.suffix.lower()}")
        session = self.checkpoints.get(session_id) if session_id else None
        if session is None and session_id is None and auto_resume:
            latest = self.checkpoints.latest_for_file(path)
            if latest and latest.status in {"running", "failed"} and latest.control_state == "running" and latest.file_size == path.stat().st_size and latest.file_mtime_ns in {0, path.stat().st_mtime_ns}:
                session = latest
        if session_id and session is None:
            raise KeyError(session_id)
        if session is None:
            resolved_source = self._source(path) if not source or source == "manual" else source
            session = self.checkpoints.create(path, resolved_source, batch_size=self.batch_size)
        elif Path(session.file_path) != path:
            raise ValueError("session file does not match requested file")
        elif path.stat().st_size != session.file_size:
            raise ValueError("source file changed since checkpoint")
        elif session.file_mtime_ns and path.stat().st_mtime_ns != session.file_mtime_ns:
            raise ValueError("source file changed since checkpoint")
        if session.status == "completed":
            return session
        session = replace(session, status="running", control_state="running", error="", updated_at=_now())
        self.checkpoints.save(session)
        queue_job = self.queue.add_job("import", f"Streaming Import: {path.name}", priority=20, payload={"session_id": session.session_id, "file": str(path)})
        self.queue.update_status(queue_job.id, "running")
        batch: list[dict[str, Any]] = []
        batches = 0
        last_bytes = session.bytes_processed
        last_position = session.position
        try:
            for raw, position, bytes_processed in self._records(path, start_position=session.position, source=session.source, document_mode=document_mode):
                control = self.checkpoints.get(session.session_id)
                if control and control.control_state in {"paused", "stopped"}:
                    self.queue.update_status(queue_job.id, "blocked" if control.control_state == "paused" else "cancelled")
                    return control
                batch.append(self._normalize(raw, session.source, path, position, workspace_id=workspace_id, version=version))
                last_bytes, last_position = bytes_processed, position
                if len(batch) >= session.batch_size:
                    session, document_ids = self.writer.write(batch, session, bytes_processed=last_bytes, position=last_position)
                    if document_ids:
                        self.scheduler.schedule(session.session_id, document_ids, batch_position=last_position, parent_job_id=queue_job.id)
                    batch.clear(); batches += 1
                    self._notify(session, progress)
                    if session.control_state in {"paused", "stopped"}:
                        self.queue.update_status(queue_job.id, "blocked" if session.control_state == "paused" else "cancelled")
                        return session
                    if stop_after_batches is not None and batches >= stop_after_batches:
                        session = replace(session, status="paused", control_state="paused", updated_at=_now())
                        self.checkpoints.save(session); self.queue.update_status(queue_job.id, "cancelled")
                        return session
            if batch:
                session, document_ids = self.writer.write(batch, session, bytes_processed=last_bytes, position=last_position)
                if document_ids:
                    self.scheduler.schedule(session.session_id, document_ids, batch_position=last_position, parent_job_id=queue_job.id)
            session = replace(session, bytes_processed=session.file_size, status="completed", control_state="running", updated_at=_now())
            self.checkpoints.save(session); self.queue.update_status(queue_job.id, "success"); self._notify(session, progress)
            return session
        except Exception as exc:
            session = replace(session, status="failed", error=f"{type(exc).__name__}: {exc}"[:2000], updated_at=_now())
            self.checkpoints.save(session); self.queue.update_status(queue_job.id, "failed", error=session.error)
            if _retry_attempt < max(0, int(auto_retry)):
                time.sleep(min(1.0, 0.05 * (2 ** _retry_attempt)))
                return self.import_file(path, source=session.source, session_id=session.session_id, progress=progress,
                    stop_after_batches=stop_after_batches, workspace_id=workspace_id, version=version,
                    document_mode=document_mode, auto_resume=False, auto_retry=auto_retry, _retry_attempt=_retry_attempt + 1)
            raise

    def resume(self, session_id: str, *, progress: Callable[[ImportProgress], None] | None = None) -> ImportSession:
        session = self.checkpoints.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return self.import_file(session.file_path, source=session.source, session_id=session_id, progress=progress)

    def import_document(self, file_path: str | Path, *, source: str = "document", workspace_id: str = "default",
                        version: str | None = None, progress: Callable[[ImportProgress], None] | None = None) -> ImportSession:
        """Import one document through the existing parser registry and pipeline."""
        return self.import_file(file_path, source=source, workspace_id=workspace_id.strip() or "default",
                                version=version, progress=progress, document_mode=True)

    def import_workspace(self, root: str | Path, *, source: str, workspace_id: str = "default") -> list[ImportSession]:
        """Import an Obsidian/Notion/Paperless/OneNote export without another import path."""
        path = Path(root).expanduser().resolve()
        if path.is_file():
            return [self.import_document(path, source=source, workspace_id=workspace_id)]
        if not path.is_dir():
            raise FileNotFoundError(str(path))
        return [self.import_document(item, source=source, workspace_id=workspace_id)
                for item in sorted(path.rglob("*")) if item.is_file() and item.suffix.lower() in DOCUMENT_SUFFIXES]

    def pause(self, session_id: str) -> ImportSession:
        session = self._require_session(session_id)
        updated = replace(session, status="paused", control_state="paused", updated_at=_now())
        self.checkpoints.save(updated)
        self._set_session_jobs(session_id, {"pending", "retry", "running"}, "blocked")
        return updated

    def continue_import(self, session_id: str, *, progress: Callable[[ImportProgress], None] | None = None) -> ImportSession:
        session = self._require_session(session_id)
        updated = replace(session, status="running", control_state="running", error="", updated_at=_now())
        self.checkpoints.save(updated)
        self._set_session_jobs(session_id, {"blocked"}, "pending")
        self.scheduler.start()
        if updated.bytes_processed < updated.file_size:
            return self.resume(session_id, progress=progress)
        completed = replace(updated, status="completed", updated_at=_now())
        self.checkpoints.save(completed)
        return completed

    def retry(self, session_id: str, *, progress: Callable[[ImportProgress], None] | None = None) -> ImportSession:
        session = self._require_session(session_id)
        self._set_session_jobs(session_id, {"failed", "dead_letter", "blocked"}, "pending", reset_attempts=True)
        updated = replace(session, status="running", control_state="running", error="", updated_at=_now())
        self.checkpoints.save(updated)
        self.scheduler.start()
        if updated.bytes_processed < updated.file_size:
            return self.resume(session_id, progress=progress)
        return updated

    def stop(self, session_id: str) -> ImportSession:
        session = self._require_session(session_id)
        updated = replace(session, status="stopped", control_state="stopped", updated_at=_now())
        self.checkpoints.save(updated)
        self._set_session_jobs(session_id, {"pending", "retry", "running", "blocked"}, "cancelled")
        return updated

    def _require_session(self, session_id: str) -> ImportSession:
        session = self.checkpoints.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def _set_session_jobs(self, session_id: str, from_statuses: set[str], target: str, *, reset_attempts: bool = False) -> None:
        for job in self.queue.list_jobs():
            if str((job.payload or {}).get("session_id") or "") != session_id or job.status not in from_statuses:
                continue
            resolved_target = "cancelled" if target == "pending" and job.kind == "import" else target
            changes: dict[str, Any] = {"status": resolved_target}
            if reset_attempts:
                changes.update(attempts=0, available_at=0.0, error=None)
            self.queue.update_job(job.id, **changes)

    def status(self) -> dict[str, Any]:
        sessions = self.checkpoints.list()
        return {"ok": True, "version": "30.57", "mode": "quality_scored_import_runtime",
                "database": str(self.db_path), "batch_size": self.batch_size,
                "sessions": [session.to_dict() for session in sessions],
                "counts": {status: sum(item.status == status for item in sessions) for status in ("pending", "running", "paused", "completed", "failed")}}

    @staticmethod
    def _source(path: Path) -> str:
        value = f"{path.parent.name} {path.name}".lower()
        aliases = (("anythingllm", "anythingllm"), ("openwebui", "openwebui"), ("librechat", "librechat"),
                   ("perplexity", "perplexity"), ("chatgpt", "chatgpt"), ("openai", "openai_export"),
                   ("claude", "claude"), ("gemini", "gemini"))
        return next((provider for marker, provider in aliases if marker in value), "file")

    def _records(self, path: Path, *, start_position: int, source: str = "file", document_mode: bool = False) -> Iterator[tuple[Any, int, int]]:
        position = 0
        if path.suffix.lower() in DOCUMENT_SUFFIXES and (document_mode or path.suffix.lower() in {".pst", ".eml", ".pdf", ".docx", ".xlsx", ".csv"}):
            parsed = self.document_parser.parse(path).parsed
            if start_position < 1:
                yield parsed, 1, path.stat().st_size
            return
        if path.suffix.lower() == ".zip":
            with ZipFile(path) as archive:
                allowed = DOCUMENT_SUFFIXES if document_mode else SUPPORTED_SUFFIXES - {".zip"}
                members = [item for item in archive.infolist() if not item.is_dir() and Path(item.filename).suffix.lower() in allowed]
                consumed = 0
                for member in members:
                    suffix = Path(member.filename).suffix.lower()
                    if document_mode:
                        temporary = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                        try:
                            with temporary, archive.open(member, "r") as source_stream:
                                while block := source_stream.read(1024 * 1024):
                                    temporary.write(block)
                            position += 1
                            if position > start_position:
                                parsed = self.document_parser.parse(temporary.name).parsed
                                parsed = replace(parsed, title=Path(member.filename).name, source_path=f"{path}!{member.filename}",
                                                 metadata={**parsed.metadata, "archive_member": member.filename})
                                yield parsed, position, min(path.stat().st_size, consumed + member.file_size)
                        finally:
                            os.unlink(temporary.name)
                    else:
                        opener = lambda member=member: archive.open(member, "r")
                        for raw, offset in self._stream(opener, suffix):
                            position += 1
                            if position > start_position:
                                yield raw, position, min(path.stat().st_size, consumed + offset)
                    consumed += member.file_size
            return
        opener = lambda: path.open("rb")
        for raw, offset in self._stream(opener, path.suffix.lower()):
            position += 1
            if position > start_position:
                yield raw, position, offset

    def _stream(self, opener: Callable[[], BinaryIO], suffix: str) -> Iterator[tuple[Any, int]]:
        if suffix in {".md", ".markdown", ".txt", ".html"}:
            with opener() as stream:
                decoder = codecs.getincrementaldecoder("utf-8")("replace")
                index = 0
                while block := stream.read(64 * 1024):
                    index += 1
                    text = decoder.decode(block, final=False)
                    if text:
                        yield {"title": f"Markdown Teil {index}", "content": text}, stream.tell()
                tail = decoder.decode(b"", final=True)
                if tail:
                    yield {"title": f"Markdown Teil {index + 1}", "content": tail}, stream.tell()
            return
        if suffix in {".jsonl", ".ndjson"}:
            with opener() as stream:
                for item in ijson.items(stream, "", multiple_values=True):
                    yield item, stream.tell()
            return
        mode = self._json_mode(opener)
        with opener() as stream:
            if mode == "item":
                iterator: Iterable[Any] = ijson.items(stream, "item")
            elif mode.endswith(".item"):
                iterator = ijson.items(stream, mode)
            else:
                iterator = ({"name": key, "value": value} for key, value in ijson.kvitems(stream, ""))
            for item in iterator:
                yield item, stream.tell()

    @staticmethod
    def _json_mode(opener: Callable[[], BinaryIO]) -> str:
        with opener() as stream:
            for index, (prefix, event, _value) in enumerate(ijson.parse(stream)):
                if event == "start_array" and prefix.count(".") == 0:
                    return f"{prefix}.item" if prefix else "item"
                if index >= 1000:
                    break
        return "kvitems"

    @staticmethod
    def _normalize(raw: Any, source: str, path: Path, position: int, *, workspace_id: str = "default", version: str | None = None) -> dict[str, Any]:
        if isinstance(raw, ParsedDocument):
            resolved_version = str(version or path.stat().st_mtime_ns)
            ocr_status = "completed" if raw.metadata.get("ocr_engine") else ("required" if raw.status == ParseStatus.OCR_REQUIRED else ("failed" if raw.status == ParseStatus.FAILED else "not_required"))
            content = raw.text or f"[{raw.status.value}: {raw.title}]"
            seed = f"{raw.source_path or path}|{workspace_id}"
            return {"id": f"doc_{uuid.uuid5(uuid.NAMESPACE_URL, seed).hex[:24]}", "title": raw.title,
                    "content": content, "position": position,
                    "metadata": {"schema": "secondbrain.document.v1", "source": {"provider": source, "file": str(path)},
                                 "document": {"mime_type": raw.mime_type, "parse_status": raw.status.value, "pages": raw.page_count},
                                 "metadata": raw.metadata, "attachments": list(raw.metadata.get("attachments") or []),
                                 "ocr_status": ocr_status, "version": resolved_version, "workspace": workspace_id,
                                 "errors": list(raw.errors)}}
        return document_record(normalize_conversation(raw, source, path, position), path, position)

    @staticmethod
    def normalize(raw: Any, source: str, path: str | Path = "export.json", position: int = 1) -> Conversation:
        """Public canonical normalization boundary used by every importer."""
        return normalize_conversation(raw, source, Path(path), position)

    @staticmethod
    def _notify(session: ImportSession, callback: Callable[[ImportProgress], None] | None) -> None:
        if callback:
            callback(ImportProgress(session.session_id, session.bytes_processed, session.file_size, session.position,
                                    session.imported_chats, session.chunks, session.embeddings, session.status))
