from __future__ import annotations

import inspect
import json

from launcher import main as launcher_main
from secondbrain.importing import ImportCenterService, StreamingImportService
from secondbrain.module_registry import ModuleRegistry
from secondbrain.native.streaming_import_panel import StreamingImportFrame


def _source(tmp_path, count=3):
    path = tmp_path / "conversations.jsonl"
    path.write_text("\n".join(json.dumps({"title": f"C{i}", "content": "text"}) for i in range(count)) + "\n", encoding="utf-8")
    return path


def test_import_center_status_contains_gui_metrics(tmp_path):
    engine = StreamingImportService(tmp_path, batch_size=1)
    session = engine.import_file(_source(tmp_path, 1), source="chatgpt")
    payload = ImportCenterService(tmp_path, engine=engine).status()
    row = payload["sessions"][0]
    assert row["session_id"] == session.session_id
    assert {"file", "eta", "progress", "imported_chats", "documents", "chunks", "embeddings", "workers"} <= row.keys()
    assert {"configured", "active"} <= payload["workers"].keys()
    assert {"cores", "percent"} <= payload["cpu"].keys()
    assert {"rss_bytes", "percent"} <= payload["ram"].keys()


def test_pause_continue_retry_stop_control_existing_session_and_queue(tmp_path):
    engine = StreamingImportService(tmp_path, batch_size=1)
    session = engine.import_file(_source(tmp_path), source="chatgpt", stop_after_batches=1)
    center = ImportCenterService(tmp_path, engine=engine)
    assert session.control_state == "paused"
    assert center.pause(session.session_id).status == "paused"
    continued = center.continue_import(session.session_id)
    assert continued.status == "completed"
    failed_job = next(job for job in engine.queue.list_jobs() if (job.payload or {}).get("session_id") == session.session_id and job.kind == "chunk")
    engine.queue.update_job(failed_job.id, status="dead_letter", attempts=3, error="test")
    retried = center.retry(session.session_id)
    assert retried.error == ""
    stopped = center.stop(session.session_id)
    assert stopped.status == "stopped" and stopped.control_state == "stopped"
    engine.scheduler.stop()


def test_import_history_reuses_queue_history(tmp_path):
    engine = StreamingImportService(tmp_path)
    session = engine.import_file(_source(tmp_path, 1), source="chatgpt")
    payload = ImportCenterService(tmp_path, engine=engine).history()
    assert payload["ok"] is True
    assert any((event.get("payload") or {}).get("session_id") == session.session_id for event in payload["events"])


def test_native_gui_exposes_required_import_center_controls_and_columns():
    source = inspect.getsource(StreamingImportFrame)
    for label in ("Datei", "ETA", "Fortschritt", "Importierte Chats", "Dokumente", "Chunks", "Embeddings", "Worker", "CPU", "RAM", "Pause", "Continue", "Retry", "Stop", "Logs", "Fehler"):
        assert label in source


def test_launcher_import_status_history_and_command_index(tmp_path, capsys):
    assert launcher_main(["import-status", "--project-root", str(tmp_path)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["mode"] == "native_import_center"
    assert launcher_main(["import-history", "--project-root", str(tmp_path)]) == 0
    history = json.loads(capsys.readouterr().out)
    assert history["ok"] is True
    index = ModuleRegistry().command_index()
    assert {"import-center", "import-status", "import-history"} <= index.keys()
