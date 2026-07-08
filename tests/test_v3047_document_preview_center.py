"""v30.47 - Tests fuer das Document Preview Center.

Abdeckung laut Briefing: PDF, DOCX, Images, Markdown, GUI.
Service/Modelle laufen headless; der Tk-Smoke-Test laeuft nur mit Display.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import tkinter as tk
except Exception:  # pragma: no cover - Umgebungen ohne Tk
    tk = None  # type: ignore[assignment]

from secondbrain.document_understanding.parser_contract import ParseStatus
from secondbrain.document_understanding.parsers import default_parser_registry
from secondbrain.native.ai_workspace.service import AIWorkspaceService
from secondbrain.native.document_preview.models import (
    SUPPORTED_PREVIEW_EXTENSIONS,
    OcrOverlayModel,
    PreviewAnnotation,
    PreviewSearchModel,
    PreviewState,
    ZoomModel,
)
from secondbrain.native.document_preview.service import DocumentPreviewService

ROOT = Path(__file__).resolve().parents[1]

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 60>>stream\n"
    b"BT /F1 12 Tf 72 712 Td (Preview Center Testdokument) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)

MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082"
)


def _project(tmp_path: Path) -> Path:
    (tmp_path / "documents").mkdir()
    return tmp_path


def _write(tmp_path: Path, name: str, data: bytes | str) -> Path:
    target = tmp_path / "documents" / name
    if isinstance(data, str):
        target.write_text(data, encoding="utf-8")
    else:
        target.write_bytes(data)
    return target


# --- Parser-Erweiterung (kein zweiter Parser-Stack) ---------------------------------

def test_registry_covers_all_briefing_extensions() -> None:
    registry = default_parser_registry()
    for extension in SUPPORTED_PREVIEW_EXTENSIONS:
        assert extension.lstrip(".")  # sanity
    assert set(registry._parsers) >= {
        ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".png", ".jpg", ".jpeg", ".md", ".json",
    }


def test_docx_parser_uses_office_import(tmp_path: Path) -> None:
    docx = pytest.importorskip("docx")
    target = tmp_path / "brief.docx"
    document = docx.Document()
    document.add_paragraph("Prozessdesign Abnahmekriterium")
    document.save(str(target))
    parsed = default_parser_registry().parse(target)
    assert parsed.status == ParseStatus.PARSED
    assert "Prozessdesign" in parsed.text
    assert parsed.metadata["parser"] == "docx"


def test_docx_parser_reports_missing_dependency_deterministically(tmp_path: Path, monkeypatch) -> None:
    import builtins

    target = tmp_path / "brief.docx"
    target.write_bytes(b"PK\x03\x04dummy")
    original_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "docx":
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked)
    parsed = default_parser_registry().parse(target)
    assert parsed.status == ParseStatus.FAILED
    assert any("docx_reader_missing" in error for error in parsed.errors)


def test_image_parser_returns_ocr_required_without_engine(tmp_path: Path) -> None:
    target = tmp_path / "scan.png"
    target.write_bytes(MINIMAL_PNG)
    parsed = default_parser_registry().parse(target)
    assert parsed.status in {ParseStatus.OCR_REQUIRED, ParseStatus.PARSED}
    if parsed.status == ParseStatus.OCR_REQUIRED:
        assert "image_text_requires_ocr" in parsed.errors


# --- Modelle -------------------------------------------------------------------------

def test_zoom_model_clamps_and_steps() -> None:
    assert ZoomModel.clamp(1.0) == 1.0
    assert ZoomModel.clamp(99.0) == ZoomModel.MAX
    assert ZoomModel.clamp(-1.0) == ZoomModel.MIN
    assert ZoomModel.clamp("kaputt") == ZoomModel.DEFAULT
    assert ZoomModel.zoom_in(1.0) == 1.25
    assert ZoomModel.zoom_out(0.25) == 0.25
    assert ZoomModel.levels()[0] == ZoomModel.MIN
    assert ZoomModel.levels()[-1] == ZoomModel.MAX


def test_preview_state_page_bounds() -> None:
    state = PreviewState(page_count=3)
    assert state.set_page(99) == 3
    assert state.set_page(-5) == 1
    assert state.set_zoom(2.0) == 2.0


def test_search_model_finds_hits_with_page_and_line() -> None:
    pages = [
        {"number": 1, "text": "erste Zeile\nSAP Prozess"},
        {"number": 2, "text": "noch ein SAP Eintrag\nletzte Zeile"},
    ]
    hits = PreviewSearchModel.hits(pages, "sap")
    assert [(hit["page"], hit["line"]) for hit in hits] == [(1, 2), (2, 1)]
    assert PreviewSearchModel.hits(pages, "") == []


def test_annotation_model_validates_input() -> None:
    annotation = PreviewAnnotation.create("doc_x", "Klaeren mit IT", page=2, region=[1, 2, 3, 4])
    assert annotation.page == 2
    assert annotation.region == (1.0, 2.0, 3.0, 4.0)
    with pytest.raises(ValueError):
        PreviewAnnotation.create("doc_x", "   ")
    with pytest.raises(ValueError):
        PreviewAnnotation.create("doc_x", "text", region=[1, 2])


def test_ocr_overlay_normalizes_tesseract_dict() -> None:
    raw = {
        "text": ["", "Wort", "Zwei"],
        "conf": ["-1", "88.5", "nope"],
        "left": [0, 10, 30],
        "top": [0, 20, 40],
        "width": [0, 50, 60],
        "height": [0, 12, 14],
    }
    items = OcrOverlayModel.normalize_items(raw)
    assert len(items) == 2
    assert items[0] == {"text": "Wort", "confidence": 88.5, "bbox": [10, 20, 60, 32]}
    assert items[1]["confidence"] == -1.0


# --- Service: Vorschau je Format ------------------------------------------------------

def test_markdown_preview_strips_frontmatter(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "notiz.md", "---\ntitle: x\n---\n# Ueberschrift\n\nInhalt der Notiz")
    service = DocumentPreviewService(project)
    payload = service.preview("notiz.md")
    assert payload["ok"] is True
    assert payload["status"] == "parsed"
    assert payload["renderer"] == "text"
    assert "Inhalt der Notiz" in payload["text"]
    assert "title: x" not in payload["text"]


def test_pdf_preview_extracts_text_or_flags_ocr(tmp_path: Path) -> None:
    pytest.importorskip("fitz", reason="PyMuPDF nicht installiert")
    project = _project(tmp_path)
    _write(project, "doc.pdf", MINIMAL_PDF)
    payload = DocumentPreviewService(project).preview("doc.pdf")
    assert payload["ok"] is True
    assert payload["status"] in {"parsed", "ocr_required"}
    assert payload["renderer"] == "canvas_pdf"
    if payload["status"] == "parsed":
        assert "Preview Center Testdokument" in payload["text"]
        assert payload["page_count"] == 1


def test_image_preview_reports_renderer_and_ocr(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "bild.png", MINIMAL_PNG)
    payload = DocumentPreviewService(project).preview("bild.png")
    assert payload["ok"] is True
    assert payload["status"] in {"ocr_required", "parsed"}
    assert payload["renderer"] in {"canvas_image", "none"}


def test_unsupported_extension_is_rejected(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "daten.bin", b"\x00\x01")
    payload = DocumentPreviewService(project).preview("daten.bin")
    assert payload["ok"] is False
    assert payload["status"] == "unsupported_extension"


def test_service_search_finds_text(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "log.txt", "zeile eins\nSuchbegriff hier\nzeile drei")
    payload = DocumentPreviewService(project).search("log.txt", "suchbegriff")
    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["hits"][0]["line"] == 2


def test_metadata_composes_explorer_and_parser(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "notiz.md", "# T\n\nInhalt")
    payload = DocumentPreviewService(project).metadata("notiz.md")
    assert payload["ok"] is True
    assert payload["document"]["name"] == "notiz.md"
    assert payload["parse_status"] == "parsed"
    assert payload["char_count"] > 0
    assert len(payload["content_hash"]) == 64


# --- Service: OCR Overlay --------------------------------------------------------------

def test_ocr_overlay_degrades_without_engine(tmp_path: Path, monkeypatch) -> None:
    project = _project(tmp_path)
    _write(project, "bild.png", MINIMAL_PNG)
    monkeypatch.setattr(OcrOverlayModel, "engine_available", staticmethod(lambda: False))
    payload = DocumentPreviewService(project).ocr_overlay("bild.png")
    assert payload["ok"] is True
    assert payload["status"] == "ocr_engine_missing"
    assert payload["items"] == []


def test_ocr_overlay_not_required_for_text(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "notiz.txt", "text")
    payload = DocumentPreviewService(project).ocr_overlay("notiz.txt")
    assert payload["ok"] is True
    assert payload["status"] == "ocr_not_required"


# --- Service: Versionen und Annotationen -----------------------------------------------

def test_version_snapshot_is_hash_deduplicated(tmp_path: Path) -> None:
    project = _project(tmp_path)
    target = _write(project, "notiz.md", "Stand 1")
    service = DocumentPreviewService(project)
    first = service.snapshot_version("notiz.md")
    assert first["status"] == "snapshotted"
    assert Path(first["version"]["snapshot_path"]).is_file()
    again = service.snapshot_version("notiz.md")
    assert again["status"] == "unchanged"
    target.write_text("Stand 2", encoding="utf-8")
    second = service.snapshot_version("notiz.md")
    assert second["status"] == "snapshotted"
    versions = service.versions("notiz.md")
    assert versions["count"] == 2
    assert versions["current_is_snapshotted"] is True


def test_version_preview_reads_snapshot(tmp_path: Path) -> None:
    project = _project(tmp_path)
    target = _write(project, "notiz.md", "Alter Stand")
    service = DocumentPreviewService(project)
    version_id = service.snapshot_version("notiz.md")["version"]["version_id"]
    target.write_text("Neuer Stand", encoding="utf-8")
    payload = service.version_preview(version_id)
    assert payload["ok"] is True
    assert "Alter Stand" in payload["text"]
    assert service.version_preview("ver_gibtsnicht")["ok"] is False


def test_annotation_roundtrip(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write(project, "notiz.md", "Inhalt")
    service = DocumentPreviewService(project)
    created = service.annotate("notiz.md", "Mit Fachbereich klaeren", page=1)
    assert created["ok"] is True
    listing = service.annotations("notiz.md")
    assert listing["count"] == 1
    assert listing["annotations"][0]["text"] == "Mit Fachbereich klaeren"
    removed = service.remove_annotation(created["annotation"]["annotation_id"])
    assert removed["ok"] is True
    assert service.annotations("notiz.md")["count"] == 0
    assert service.remove_annotation("ann_fehlt")["ok"] is False


def test_dropped_file_import_uses_existing_explorer(tmp_path: Path) -> None:
    project = _project(tmp_path)
    external = tmp_path / "extern.txt"
    external.write_text("von aussen", encoding="utf-8")
    service = DocumentPreviewService(project)
    payload = service.import_dropped_file(str(external))
    assert payload["ok"] is True
    assert (project / "documents" / "extern.txt").is_file()
    assert service.preview("extern.txt")["ok"] is True


# --- Integration in den AI Workspace ----------------------------------------------------

def test_preview_module_is_registered_in_ai_workspace() -> None:
    service = AIWorkspaceService(ROOT)
    modules = {module.id: module for module in service.snapshot().modules}
    assert "preview" in modules
    assert modules["preview"].status == "ready"
    assert modules["preview"].command == "document-preview-gui"
    payload = service.module_payload("preview")
    assert payload.get("status") != "module_error", payload
    assert payload["mode"] == "native_document_preview_center"
    assert payload["catalog"] == "document_explorer"


def test_preview_status_reports_capabilities_and_no_second_catalog(tmp_path: Path) -> None:
    payload = DocumentPreviewService(_project(tmp_path)).status()
    assert payload["ok"] is True
    assert payload["version"] == "30.47"
    assert payload["parser_registry"] == "document_understanding.default_parser_registry"
    assert set(payload["capabilities"]) == {
        "pdf_render", "pdf_text", "image_render", "docx", "xlsx", "ocr_engine", "os_drag_drop",
    }
    assert sorted(payload["supported_extensions"]) == sorted(SUPPORTED_PREVIEW_EXTENSIONS)


def test_preview_cli_status_returns_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "launcher.py"), "document-preview-status", "--project-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["version"] == "30.47"


# --- GUI (Tk-Smoke mit Display-Skip) -----------------------------------------------------

def _display_available() -> bool:
    if tk is None:
        return False
    try:
        root = tk.Tk()
    except Exception:  # noqa: BLE001 - TclError oder fehlendes Display
        return False
    root.destroy()
    return True


@pytest.mark.skipif(not _display_available(), reason="kein Display verfuegbar")
def test_preview_frame_builds_and_opens_markdown(tmp_path: Path) -> None:
    from secondbrain.native.document_preview.gui import DocumentPreviewFrame

    project = _project(tmp_path)
    _write(project, "notiz.md", "# Titel\n\nGUI Inhalt")
    root = tk.Tk()
    try:
        frame = DocumentPreviewFrame(root, project)
        frame.open_document("notiz.md")
        assert frame.state.path is not None
        assert "GUI Inhalt" in frame.text.get("1.0", "end")
        frame.zoom_in()
        assert frame.state.zoom == 1.25
        frame.search_var.set("Inhalt")
        frame.run_search()
        assert frame.state.search_hits
    finally:
        root.destroy()


@pytest.mark.skipif(not _display_available(), reason="kein Display verfuegbar")
def test_ai_workspace_embeds_preview_module(tmp_path: Path) -> None:
    from secondbrain.native.ai_workspace.gui import AIWorkspaceApp

    app = AIWorkspaceApp(ROOT, initial_module="chat")
    try:
        app.navigate("preview")
        assert app.state.active_module == "preview"
        assert app.preview_workspace is not None
    finally:
        app.destroy()


# Ende v30.47
