from pathlib import Path

from secondbrain.gui.document_center_runtime import document_center_status


def test_document_center_status_degrades_without_crash(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "runtime" / "imports").mkdir(parents=True)
    (tmp_path / "runtime" / "imports" / "sample.txt").write_text("hello", encoding="utf-8")
    payload = document_center_status(tmp_path)
    assert payload["schema"] == "secondbrain.gui.document_center.v1"
    assert payload["status"] in {"pass", "warning", "blocked"}
    assert "summary" in payload
    assert payload["summary"]["pending_imports"] == 1
    assert ".pdf" in payload["parsers"]["supported_extensions"]


def test_document_center_endpoint_registered():
    text = Path("secondbrain/jarvis_hud_server.py").read_text(encoding="utf-8")
    assert "/api/document-center/status" in text
    assert "document_center_status(ROOT)" in text


def test_document_center_gui_surface_present():
    html = Path("web/jarvis_hud/index.html").read_text(encoding="utf-8")
    assert "DOCUMENT CENTER" in html
    assert "doc-rt-index" in html
    assert "loadDocumentCenterStatus" in html


def test_document_center_launcher_command_registered():
    text = Path("launcher.py").read_text(encoding="utf-8")
    assert "document-center-status" in text
    assert "document_center_status" in text
