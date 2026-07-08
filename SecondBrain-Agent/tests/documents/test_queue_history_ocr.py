from secondbrain.documents.upload_queue import UploadQueue, UploadStatus
from secondbrain.documents.import_history import ImportHistoryStore
from secondbrain.documents.ocr_status import OcrStatusTracker, OcrState


def test_upload_queue_lifecycle():
    q = UploadQueue()
    q.enqueue_many(["a.pdf", "b.png", "c.md"])
    assert q.summary()["pending"] == 3
    item = q.next_pending()
    q.mark_running(item.id); q.set_progress(item.id, 0.5)
    assert q.items()[0].progress == 0.5
    q.mark_done(item.id, doc_id="d1")
    q.mark_failed(q.items()[1].id, "boom")
    s = q.summary()
    assert s["done"] == 1 and s["failed"] == 1 and s["pending"] == 1 and s["total"] == 3


def test_import_history_persist(tmp_path):
    h = ImportHistoryStore(tmp_path / "hist.json")
    h.record(path="a.pdf", status="imported", doc_id="d1")
    h.record(path="b.pdf", status="failed")
    assert len(h.all()) == 2
    assert h.by_status("failed")[0]["path"] == "b.pdf"
    assert ImportHistoryStore(tmp_path / "hist.json").all()[0]["path"] == "a.pdf"
    assert h.recent(1)[0]["path"] == "b.pdf"


def test_ocr_status_tracker():
    t = OcrStatusTracker()
    t.mark_pending("d1"); t.mark_running("d1")
    t.mark_done("d1", pages=3, chars=1200, mean_confidence=0.9)
    t.mark_failed("d2", "no text")
    assert t.get("d1").state is OcrState.DONE and t.get("d1").pages == 3
    assert t.get("d2").state is OcrState.FAILED
    assert t.summary()["done"] == 1 and t.summary()["failed"] == 1
