"""Streaming-Import auf der kanonischen Job-Runtime (Prompt 70, Phase 1).

Grosse ChatGPT-Exporte und Dokumentimporte laufen record-weise ueber die
Job-Runtime. Die Checkpoints liegen ausschliesslich in der kanonischen
Job-Repository (job.checkpoint) -- keine SQLite-Insel. Resume nach Abbruch
setzt am letzten Checkpoint auf; ein idempotenter Sink verhindert Duplikate.

Eigenschaften
-------------
* Streaming: die Exportdatei wird nie vollstaendig in den RAM gelesen.
  JSONL/NDJSON zeilenweise, JSON-Arrays via ijson, ZIP-Member als Stream.
* Fortschritt: processed_bytes, total_bytes, records_ok, records_failed.
* Cancellation nur an Batch-Grenzen (sichere Grenze).
* Dead-Letter: nur Index und Fehlerklasse, niemals Inhaltsdaten.
* Idempotenz: Skip-Count beim Resume plus inhaltsbasierter Idempotenzschluessel,
  den der Sink zum Deduplizieren nutzt.

Checkpoint-Schema (in job.checkpoint):
    {
      "schema": "secondbrain.jobs.import.checkpoint.v1",
      "processed_bytes": int,
      "total_bytes": int,
      "records_ok": int,
      "records_failed": int,
      "records_processed": int,   # ok + failed -> Skip-Anzahl beim Resume
      "dead_letter": [{"index": int, "error": "ExceptionClass"}],  # gedeckelt
      "source_suffix": str,
      "done": bool
    }
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Protocol

CHECKPOINT_SCHEMA = "secondbrain.jobs.import.checkpoint.v1"
DEFAULT_BATCH_SIZE = 500
DEAD_LETTER_CAP = 100  # begrenzt die Checkpoint-Groesse; darueber wird nur gezaehlt

_JSONL_SUFFIXES = {".jsonl", ".ndjson"}
_JSON_SUFFIXES = {".json"}


class ImportCancelled(RuntimeError):
    """Sauberer Abbruch an einer Batch-Grenze. Der Job bleibt wiederaufnehmbar."""


class RecordSink(Protocol):
    """Zielsenke fuer Records. Muss idempotent nach ``key`` sein."""

    def ingest(self, record: Any, *, key: str) -> bool:
        """True bei erstmaliger Aufnahme, False bei Duplikat/Skip."""
        ...


def record_key(record: Any) -> str:
    """Inhaltsbasierter Idempotenzschluessel. Gleicher Record -> gleicher Key."""
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:32]


# --------------------------------------------------------------------------
# Streaming-Iteratoren -- laden die Datei nie vollstaendig in den RAM
# --------------------------------------------------------------------------


def _iter_jsonl(stream) -> Iterator[tuple[int, Any]]:
    for raw in stream:  # zeilenweise, kein readlines()
        line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        nbytes = len(line.encode("utf-8")) if isinstance(line, str) else len(raw)
        stripped = line.strip()
        if not stripped:
            yield nbytes, _SKIP
            continue
        try:
            yield nbytes, json.loads(stripped)
        except json.JSONDecodeError:
            yield nbytes, _BadRecord()


def _iter_json_array(stream) -> Iterator[tuple[int, Any]]:
    import ijson  # optionaler Streaming-Parser
    # ijson streamt Array-Elemente; die Bytegroesse pro Element ist nicht exakt
    # verfuegbar, daher wird sie aus dem serialisierten Element geschaetzt.
    for item in ijson.items(stream, "item"):
        approx = len(json.dumps(item, ensure_ascii=False, default=str).encode("utf-8"))
        yield approx, item


class _BadRecord:
    """Marker fuer eine nicht parsebare Zeile -- zaehlt als records_failed."""


_SKIP = object()  # Leerzeile, wird nur fuer processed_bytes gezaehlt


def iter_records(path: Path) -> Iterator[tuple[int, Any]]:
    """Dispatcht nach Suffix und streamt. Der Aufrufer schliesst nichts."""
    suffix = path.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            members = [m for m in zf.namelist() if not m.endswith("/")]
            for member in members:
                inner = Path(member).suffix.lower()
                with zf.open(member) as fh:
                    if inner in _JSONL_SUFFIXES:
                        yield from _iter_jsonl(fh)
                    elif inner in _JSON_SUFFIXES:
                        yield from _iter_json_array(fh)
        return
    if suffix in _JSONL_SUFFIXES:
        with path.open("rb") as fh:
            yield from _iter_jsonl(fh)
        return
    if suffix in _JSON_SUFFIXES:
        with path.open("rb") as fh:
            yield from _iter_json_array(fh)
        return
    raise ValueError(f"unsupported_import_suffix:{suffix}")


# --------------------------------------------------------------------------
# Kernlauf
# --------------------------------------------------------------------------


@dataclass
class _State:
    processed_bytes: int = 0
    records_ok: int = 0
    records_failed: int = 0
    records_processed: int = 0
    dead_letter: list[dict[str, Any]] | None = None

    def as_checkpoint(self, *, total_bytes: int, suffix: str, done: bool) -> dict[str, Any]:
        return {
            "schema": CHECKPOINT_SCHEMA,
            "processed_bytes": self.processed_bytes,
            "total_bytes": total_bytes,
            "records_ok": self.records_ok,
            "records_failed": self.records_failed,
            "records_processed": self.records_processed,
            "dead_letter": list(self.dead_letter or []),
            "source_suffix": suffix,
            "done": done,
        }


def _resume_state(job: Any) -> _State:
    cp = getattr(job, "checkpoint", None) or {}
    if str(cp.get("schema")) != CHECKPOINT_SCHEMA:
        return _State(dead_letter=[])
    return _State(
        processed_bytes=int(cp.get("processed_bytes", 0)),
        records_ok=int(cp.get("records_ok", 0)),
        records_failed=int(cp.get("records_failed", 0)),
        records_processed=int(cp.get("records_processed", 0)),
        dead_letter=list(cp.get("dead_letter", [])),
    )


def run_streaming_import(job: Any, context: Any, *, path: str | Path, sink: RecordSink,
                         batch_size: int = DEFAULT_BATCH_SIZE) -> dict[str, Any]:
    """Streamt ``path`` in ``sink``. Checkpointet in die Job-Repository.

    Resume: bereits verarbeitete Records werden per Skip-Count uebersprungen; der
    Sink dedupliziert zusaetzlich nach Idempotenzschluessel -- doppelte Aufnahme
    ist damit ausgeschlossen, auch wenn der Skip-Count nicht exakt trifft.
    """
    file_path = Path(path)
    total_bytes = file_path.stat().st_size if file_path.exists() else 0
    suffix = file_path.suffix.lower()
    state = _resume_state(job)
    skip = state.records_processed
    since_checkpoint = 0
    index = -1

    def _persist(done: bool) -> None:
        checkpoint = state.as_checkpoint(total_bytes=total_bytes, suffix=suffix, done=done)
        progress = min(1.0, state.processed_bytes / total_bytes) if total_bytes else (1.0 if done else 0.0)
        context.checkpoint(checkpoint, progress=progress)

    for nbytes, record in iter_records(file_path):
        index += 1
        if record is _SKIP:
            # Leerzeile: nur Bytes zaehlen, kein Record.
            if index >= skip:
                state.processed_bytes += nbytes
            continue
        if index < skip:
            # Bereits in einem frueheren Lauf verarbeitet -> ueberspringen.
            continue

        state.processed_bytes += nbytes
        state.records_processed += 1
        since_checkpoint += 1

        if isinstance(record, _BadRecord):
            state.records_failed += 1
            _record_dead_letter(state, index, "JSONDecodeError")
        else:
            try:
                sink.ingest(record, key=record_key(record))
                state.records_ok += 1
            except Exception as exc:  # noqa: BLE001 - Fehlerklasse, kein Inhalt
                state.records_failed += 1
                _record_dead_letter(state, index, type(exc).__name__)

        if since_checkpoint >= batch_size:
            _persist(done=False)
            since_checkpoint = 0
            # Cancellation nur hier -- an einer sicheren Grenze mit Checkpoint.
            if context.cancelled:
                raise ImportCancelled("cancelled_at_batch_boundary")

    _persist(done=True)
    return state.as_checkpoint(total_bytes=total_bytes, suffix=suffix, done=True)


def _record_dead_letter(state: _State, index: int, error_class: str) -> None:
    if state.dead_letter is None:
        state.dead_letter = []
    if len(state.dead_letter) < DEAD_LETTER_CAP:
        state.dead_letter.append({"index": index, "error": error_class})


# --------------------------------------------------------------------------
# Handler-Registrierung fuer die kanonische Runtime
# --------------------------------------------------------------------------


def register_streaming_import_handler(
    registry: Any,
    resolver: Callable[[str], tuple[str | Path, RecordSink, Mapping[str, Any]]],
) -> None:
    """Registriert den Streaming-Import fuer JobType.IMPORT.

    ``resolver(payload_reference)`` liefert (Pfad, Sink, Optionen). Der Sink
    muss idempotent sein; der Pfad wird nur referenziert, nie in den Job-Record
    geschrieben.
    """
    from secondbrain.jobs.models import JobType

    def handle(job: Any, context: Any) -> None:
        path, sink, options = resolver(job.payload_reference)
        run_streaming_import(job, context, path=path, sink=sink,
                             batch_size=int(options.get("batch_size", DEFAULT_BATCH_SIZE)))

    registry.register(JobType.IMPORT.value, handle)
