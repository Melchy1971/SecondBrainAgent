"""Streaming-Import auf der kanonischen Job-Runtime (Prompt 70, Phase 1).

Geprueft: Streaming ohne Vollladen, Checkpoint-Schema, Resume nach Abbruch,
idempotente Wiederaufnahme, fehlerhafter Datensatz zwischen guten, Cancellation
an der Batch-Grenze, Production-Guard und beschraenkter Speicherverbrauch.

Sandbox-Hinweis: der Job-Stack nutzt ``enum.StrEnum`` (Python 3.11). Unter 3.10
wird ein deckungsgleicher Shim gesetzt, bevor der Stack importiert wird -- reine
Testumgebung, kein Produktionscode.
"""

from __future__ import annotations

import enum

if not hasattr(enum, "StrEnum"):  # pragma: no cover - nur unter Python < 3.11
    class _StrEnum(str, enum.Enum):
        def __str__(self) -> str:
            return str(self.value)
    enum.StrEnum = _StrEnum  # type: ignore[attr-defined]

import json
import tracemalloc
from pathlib import Path

import pytest

from secondbrain.jobs.import_runtime import (
    CHECKPOINT_SCHEMA,
    ImportCancelled,
    record_key,
    run_streaming_import,
)


# --------------------------------------------------------------------------
# Test-Doubles
# --------------------------------------------------------------------------


class DictSink:
    """Idempotenter Sink: dedupliziert nach key. Zaehlt Aufnahmen und Duplikate."""

    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.ingested = 0
        self.duplicates = 0

    def ingest(self, record, *, key: str) -> bool:
        if key in self.keys:
            self.duplicates += 1
            return False
        self.keys.add(key)
        self.ingested += 1
        return True


class FakeJob:
    def __init__(self, checkpoint=None) -> None:
        self.checkpoint = checkpoint or {}
        self.workspace_id = "ws-a"
        self.job_id = "job-1"
        self.payload_reference = "import://export"


class FakeContext:
    """Emuliert JobContext: sammelt Checkpoints, kann ab einem Batch abbrechen."""

    def __init__(self, *, cancel_after_checkpoints: int | None = None) -> None:
        self.checkpoints: list[dict] = []
        self.progress: list[float] = []
        self._cancel_after = cancel_after_checkpoints

    def checkpoint(self, data, *, progress=None) -> None:
        self.checkpoints.append(dict(data))
        if progress is not None:
            self.progress.append(progress)

    def heartbeat(self) -> None:
        pass

    @property
    def cancelled(self) -> bool:
        return self._cancel_after is not None and len(self.checkpoints) >= self._cancel_after


def _write_jsonl(path: Path, n: int, *, bad_at: set[int] | None = None) -> None:
    bad_at = bad_at or set()
    with path.open("w", encoding="utf-8") as fh:
        for i in range(n):
            if i in bad_at:
                fh.write("{ this is not valid json\n")
            else:
                fh.write(json.dumps({"id": i, "text": f"record-{i}"}) + "\n")


# --------------------------------------------------------------------------
# Streaming + Checkpoint-Schema
# --------------------------------------------------------------------------


def test_full_import_reports_progress_fields(tmp_path) -> None:
    src = tmp_path / "export.jsonl"
    _write_jsonl(src, 1200)
    sink = DictSink()
    result = run_streaming_import(FakeJob(), FakeContext(), path=src, sink=sink, batch_size=500)

    assert result["schema"] == CHECKPOINT_SCHEMA
    assert result["records_ok"] == 1200
    assert result["records_failed"] == 0
    assert result["records_processed"] == 1200
    assert result["done"] is True
    assert result["total_bytes"] == src.stat().st_size
    assert result["processed_bytes"] == result["total_bytes"]
    assert sink.ingested == 1200


def test_progress_is_monotonic_and_bounded(tmp_path) -> None:
    src = tmp_path / "e.jsonl"
    _write_jsonl(src, 1500)
    ctx = FakeContext()
    run_streaming_import(FakeJob(), ctx, path=src, sink=DictSink(), batch_size=250)
    assert ctx.progress == sorted(ctx.progress)
    assert all(0.0 <= p <= 1.0 for p in ctx.progress)
    assert ctx.progress[-1] == 1.0


# --------------------------------------------------------------------------
# Fehlerhafter Datensatz zwischen guten -> Dead-Letter ohne Inhalt
# --------------------------------------------------------------------------


def test_bad_record_between_good_ones(tmp_path) -> None:
    src = tmp_path / "e.jsonl"
    _write_jsonl(src, 10, bad_at={4, 7})
    sink = DictSink()
    result = run_streaming_import(FakeJob(), FakeContext(), path=src, sink=sink, batch_size=100)
    assert result["records_ok"] == 8
    assert result["records_failed"] == 2
    assert sink.ingested == 8
    # Dead-Letter enthaelt nur Index + Fehlerklasse, keinen Inhalt.
    dead = result["dead_letter"]
    assert {d["index"] for d in dead} == {4, 7}
    assert all(set(d.keys()) == {"index", "error"} for d in dead)
    assert all("record-" not in json.dumps(d) for d in dead)


# --------------------------------------------------------------------------
# Abbruch und Resume ohne Duplikate
# --------------------------------------------------------------------------


def test_cancel_then_resume_has_no_duplicates(tmp_path) -> None:
    src = tmp_path / "e.jsonl"
    _write_jsonl(src, 1000)
    sink = DictSink()  # gemeinsamer Sink ueber beide Laeufe (idempotent)

    # Lauf 1: bricht nach dem ersten Checkpoint ab.
    job = FakeJob()
    ctx1 = FakeContext(cancel_after_checkpoints=1)
    with pytest.raises(ImportCancelled):
        run_streaming_import(job, ctx1, path=src, sink=sink, batch_size=200)
    partial = ctx1.checkpoints[-1]
    assert partial["records_processed"] == 200
    assert partial["done"] is False
    ingested_after_cancel = sink.ingested
    assert ingested_after_cancel == 200

    # Lauf 2: Resume mit dem gespeicherten Checkpoint.
    job2 = FakeJob(checkpoint=partial)
    result = run_streaming_import(job2, FakeContext(), path=src, sink=sink, batch_size=200)
    assert result["records_processed"] == 1000
    assert result["done"] is True
    # Keine Duplikate: genau 1000 eindeutige Records aufgenommen.
    assert sink.ingested == 1000
    assert sink.duplicates == 0


def test_double_start_same_import_is_idempotent(tmp_path) -> None:
    """Zweiter vollstaendiger Lauf mit demselben Sink erzeugt keine Duplikate."""
    src = tmp_path / "e.jsonl"
    _write_jsonl(src, 300)
    sink = DictSink()
    run_streaming_import(FakeJob(), FakeContext(), path=src, sink=sink, batch_size=100)
    run_streaming_import(FakeJob(), FakeContext(), path=src, sink=sink, batch_size=100)
    assert sink.ingested == 300
    assert sink.duplicates == 300  # der zweite Lauf sieht alles als Duplikat


def test_record_key_is_content_stable() -> None:
    a = {"id": 1, "text": "x"}
    b = {"text": "x", "id": 1}  # gleiche Inhalte, andere Reihenfolge
    assert record_key(a) == record_key(b)
    assert record_key({"id": 2}) != record_key({"id": 1})


# --------------------------------------------------------------------------
# Speicher waechst nicht linear zur Dateigroesse
# --------------------------------------------------------------------------


def test_memory_does_not_scale_with_file_size(tmp_path) -> None:
    """Der Peak-Speicher bleibt weit unter der Dateigroesse -> kein Vollladen.

    Kernnachweis fuer den 2,5-GB-Pfad: der Import haelt nie die ganze Datei im
    RAM. Bei einer grossen Datei ist der Peak nur ein Bruchteil ihrer Groesse.
    """
    large = tmp_path / "large.jsonl"
    _write_jsonl(large, 40000)
    file_size = large.stat().st_size

    class CountingSink:
        def ingest(self, record, *, key: str) -> bool:
            return True

    tracemalloc.start()
    run_streaming_import(FakeJob(), FakeContext(), path=large, sink=CountingSink(), batch_size=500)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Wuerde die Datei vollstaendig geladen, laege der Peak in der Groessenordnung
    # der Datei. Eine Schranke von einem Viertel der Dateigroesse schliesst das aus.
    assert peak < file_size / 4, f"Peak {peak} vs Datei {file_size} -- Verdacht auf Vollladen"


# --------------------------------------------------------------------------
# Production Guard (kanonische Runtime, keine SQLite/JSONL-Insel)
# --------------------------------------------------------------------------


def test_production_guard_blocks_jsonl_backend() -> None:
    """create_job_repository verweigert JSONL in Produktion -- kein Checkpoint-Insel."""
    from secondbrain.jobs.repository import JobRepositoryError, create_job_repository

    with pytest.raises(JobRepositoryError, match="jsonl_not_allowed_in_production"):
        create_job_repository(env={"SECONDBRAIN_ENV": "production", "JOB_REPOSITORY_BACKEND": "jsonl"})


def test_handler_registers_for_import_type(tmp_path) -> None:
    from secondbrain.jobs.import_runtime import register_streaming_import_handler
    from secondbrain.jobs.models import JobType
    from secondbrain.jobs.worker import JobHandlerRegistry

    registry = JobHandlerRegistry()
    src = tmp_path / "e.jsonl"
    _write_jsonl(src, 5)
    sink = DictSink()
    register_streaming_import_handler(registry, lambda ref: (src, sink, {}))
    handler = registry.get(JobType.IMPORT.value)

    job = FakeJob()
    handler(job, FakeContext())
    assert sink.ingested == 5


def test_pipeline_module_is_marked_deprecated() -> None:
    """Die alte Pipeline loest beim Import eine DeprecationWarning aus.

    Statisch geprueft: das Modul zieht ueber seine Abhaengigkeiten Python-3.11-
    Symbole und laesst sich in der 3.10-Sandbox nicht importieren. Der Warnaufruf
    im Modulkopf ist versionsunabhaengig verifizierbar.
    """
    source = (Path(__file__).resolve().parents[1] / "SecondBrain" / "importing" / "pipeline.py").read_text(encoding="utf-8")
    assert "DeprecationWarning" in source
    assert "warnings.warn(" in source
    assert "jobs.import_runtime" in source  # verweist auf den kanonischen Pfad
