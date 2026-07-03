"""v30.51 resumable, bounded-memory imports into the existing P1 RAG store."""
from __future__ import annotations

import codecs
import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Callable, Iterable, Iterator
from zipfile import ZipFile

import ijson

from secondbrain.native.job_queue_center.service import JobQueueService
from secondbrain.p1_rag_runtime import chunk_text, fingerprint, tokenize
from secondbrain.p3_rag_store import SQLiteRagStore


SUPPORTED_SUFFIXES = {".json", ".jsonl", ".ndjson", ".md", ".markdown", ".zip"}
DEFAULT_BATCH_SIZE = 500


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ImportSession:
    session_id: str
    file_path: str
    source: str
    file_size: int
    bytes_processed: int = 0
    position: int = 0
    imported_chats: int = 0
    chunks: int = 0
    embeddings: int = 0
    status: str = "pending"
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
        migration = Path(__file__).resolve().parents[1] / "storage" / "migrations" / "004_import_sessions.sql"
        with self.connect() as connection:
            connection.executescript(migration.read_text(encoding="utf-8"))

    def create(self, file_path: str | Path, source: str, *, batch_size=DEFAULT_BATCH_SIZE) -> ImportSession:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(str(path))
        now = _now()
        session = ImportSession(
            session_id=f"imp_{uuid.uuid4().hex}", file_path=str(path), source=source.strip().lower() or "file",
            file_size=path.stat().st_size, batch_size=max(1, int(batch_size)), created_at=now, updated_at=now,
        )
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO import_sessions
                (session_id,file_path,source,file_size,bytes_processed,position,imported_chats,chunks,embeddings,status,error,batch_size,created_at,updated_at)
                VALUES (:session_id,:file_path,:source,:file_size,:bytes_processed,:position,:imported_chats,:chunks,:embeddings,:status,:error,:batch_size,:created_at,:updated_at)""",
                session.to_dict(),
            )
        return session

    def get(self, session_id: str) -> ImportSession | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM import_sessions WHERE session_id=?", (session_id,)).fetchone()
        return ImportSession(**dict(row)) if row else None

    def save(self, session: ImportSession, connection: sqlite3.Connection | None = None) -> None:
        sql = """UPDATE import_sessions SET file_path=:file_path,source=:source,file_size=:file_size,
            bytes_processed=:bytes_processed,position=:position,imported_chats=:imported_chats,chunks=:chunks,
            embeddings=:embeddings,status=:status,error=:error,batch_size=:batch_size,updated_at=:updated_at
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

    def write(self, records: list[dict[str, Any]], session: ImportSession, *, bytes_processed: int, position: int) -> ImportSession:
        if not records:
            return session
        documents: list[tuple[Any, ...]] = []
        chunks: list[tuple[Any, ...]] = []
        document_ids: list[str] = []
        now = _now()
        for record in records:
            content = str(record.get("content") or "")
            document_id = str(record["id"])
            document_ids.append(document_id)
            metadata = {**dict(record.get("metadata") or {}), "import_session": session.session_id, "position": record["position"]}
            documents.append((document_id, session.source, str(record.get("title") or document_id), fingerprint(content), now, json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
            cursor = 0
            for ordinal, text in enumerate(chunk_text(content)):
                start = content.find(text[:80], cursor)
                start = cursor if start < 0 else start
                end = start + len(text)
                cursor = end
                tokens = tokenize(text)
                chunk_id = f"chk_{hashlib.sha256(f'{document_id}|{ordinal}|{text}'.encode('utf-8')).hexdigest()[:24]}"
                chunks.append((chunk_id, document_id, ordinal, text, start, end, json.dumps(tokens, ensure_ascii=False), len(tokens), now))
        placeholders = ",".join("?" for _ in document_ids)
        with self.checkpoints.connect() as connection:
            if document_ids:
                connection.execute(f"DELETE FROM chunk_embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id IN ({placeholders}))", document_ids)
                connection.execute(f"DELETE FROM chunks WHERE document_id IN ({placeholders})", document_ids)
            connection.executemany(
                """INSERT INTO documents(id,source,title,content_hash,created_at,metadata_json) VALUES(?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET source=excluded.source,title=excluded.title,content_hash=excluded.content_hash,metadata_json=excluded.metadata_json""",
                documents,
            )
            connection.executemany(
                """INSERT INTO chunks(id,document_id,ordinal,text,char_start,char_end,token_json,token_count,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                chunks,
            )
            updated = replace(
                session, bytes_processed=max(session.bytes_processed, int(bytes_processed)), position=int(position),
                imported_chats=session.imported_chats + len(records), chunks=session.chunks + len(chunks),
                status="running", error="", updated_at=_now(),
            )
            self.checkpoints.save(updated, connection)
        return updated


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

    def import_file(
        self,
        file_path: str | Path,
        *,
        source: str | None = None,
        session_id: str | None = None,
        progress: Callable[[ImportProgress], None] | None = None,
        stop_after_batches: int | None = None,
    ) -> ImportSession:
        path = Path(file_path).expanduser().resolve()
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise ValueError(f"unsupported streaming format: {path.suffix.lower()}")
        session = self.checkpoints.get(session_id) if session_id else None
        if session is None:
            session = self.checkpoints.create(path, source or self._source(path), batch_size=self.batch_size)
        elif Path(session.file_path) != path:
            raise ValueError("session file does not match requested file")
        elif path.stat().st_size != session.file_size:
            raise ValueError("source file changed since checkpoint")
        if session.status == "completed":
            return session
        session = replace(session, status="running", error="", updated_at=_now())
        self.checkpoints.save(session)
        queue_job = self.queue.add_job("import", f"Streaming Import: {path.name}", priority=20, payload={"session_id": session.session_id, "file": str(path)})
        self.queue.update_status(queue_job.id, "running")
        batch: list[dict[str, Any]] = []
        batches = 0
        last_bytes = session.bytes_processed
        last_position = session.position
        try:
            for raw, position, bytes_processed in self._records(path, start_position=session.position):
                batch.append(self._normalize(raw, session.source, path, position))
                last_bytes, last_position = bytes_processed, position
                if len(batch) >= session.batch_size:
                    session = self.writer.write(batch, session, bytes_processed=last_bytes, position=last_position)
                    batch.clear(); batches += 1
                    self._notify(session, progress)
                    if stop_after_batches is not None and batches >= stop_after_batches:
                        session = replace(session, status="paused", updated_at=_now())
                        self.checkpoints.save(session); self.queue.update_status(queue_job.id, "cancelled")
                        return session
            if batch:
                session = self.writer.write(batch, session, bytes_processed=last_bytes, position=last_position)
            session = replace(session, bytes_processed=session.file_size, status="completed", updated_at=_now())
            self.checkpoints.save(session); self.queue.update_status(queue_job.id, "success"); self._notify(session, progress)
            return session
        except Exception as exc:
            session = replace(session, status="failed", error=f"{type(exc).__name__}: {exc}"[:2000], updated_at=_now())
            self.checkpoints.save(session); self.queue.update_status(queue_job.id, "failed", error=session.error)
            raise

    def resume(self, session_id: str, *, progress: Callable[[ImportProgress], None] | None = None) -> ImportSession:
        session = self.checkpoints.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return self.import_file(session.file_path, source=session.source, session_id=session_id, progress=progress)

    def status(self) -> dict[str, Any]:
        sessions = self.checkpoints.list()
        return {"ok": True, "version": "30.51", "mode": "enterprise_streaming_import",
                "database": str(self.db_path), "batch_size": self.batch_size,
                "sessions": [session.to_dict() for session in sessions],
                "counts": {status: sum(item.status == status for item in sessions) for status in ("pending", "running", "paused", "completed", "failed")}}

    @staticmethod
    def _source(path: Path) -> str:
        value = f"{path.parent.name} {path.name}".lower()
        return next((name for name in ("chatgpt", "claude", "gemini") if name in value), "file")

    def _records(self, path: Path, *, start_position: int) -> Iterator[tuple[Any, int, int]]:
        position = 0
        if path.suffix.lower() == ".zip":
            with ZipFile(path) as archive:
                members = [item for item in archive.infolist() if not item.is_dir() and Path(item.filename).suffix.lower() in SUPPORTED_SUFFIXES - {".zip"}]
                consumed = 0
                for member in members:
                    suffix = Path(member.filename).suffix.lower()
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
        if suffix in {".md", ".markdown"}:
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
    def _normalize(raw: Any, source: str, path: Path, position: int) -> dict[str, Any]:
        if source == "chatgpt" and isinstance(raw, dict) and "mapping" in raw:
            from modules.chatgpt_importer.importer import conversation_to_markdown
            title, content = conversation_to_markdown(raw)
        elif isinstance(raw, dict):
            title = str(raw.get("title") or raw.get("name") or f"{source.title()} Import {position}")
            if "content" in raw and isinstance(raw["content"], str):
                content = raw["content"]
            else:
                messages = raw.get("messages") or raw.get("chat_messages")
                if isinstance(messages, list):
                    parts = []
                    for message in messages:
                        if isinstance(message, dict):
                            role = message.get("role") or message.get("sender") or message.get("author") or "unknown"
                            text = message.get("text") or message.get("content") or message.get("message") or ""
                            parts.append(f"## {role}\n\n{text}")
                    content = "\n\n".join(parts)
                else:
                    content = json.dumps(raw, ensure_ascii=False, default=str)
        else:
            title, content = f"{source.title()} Import {position}", str(raw)
        seed = f"{path}|{position}|{title}"
        return {"id": f"doc_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:24]}", "title": title,
                "content": content, "position": position, "metadata": {"import_source_file": str(path), "provider": source}}

    @staticmethod
    def _notify(session: ImportSession, callback: Callable[[ImportProgress], None] | None) -> None:
        if callback:
            callback(ImportProgress(session.session_id, session.bytes_processed, session.file_size, session.position,
                                    session.imported_chats, session.chunks, session.embeddings, session.status))
