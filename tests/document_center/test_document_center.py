"""Tests for the Document Center extension (Task 4)."""

from __future__ import annotations

from pathlib import Path

from secondbrain.document_center import (
    DocumentCenter,
    ItemState,
    OcrStatus,
    PreviewBuilder,
    PreviewKind,
)


def _make_files(tmp_path: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    (tmp_path / "a.txt").write_text("plain text content here", encoding="utf-8")
    files["txt"] = tmp_path / "a.txt"
    (tmp_path / "b.md").write_text("# Heading\n\nmarkdown body", encoding="utf-8")
    files["md"] = tmp_path / "b.md"

    from PIL import Image
    img = Image.new("RGB", (4, 4), (255, 0, 0))
    img.save(tmp_path / "c.png")
    files["png"] = tmp_path / "c.png"

    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with (tmp_path / "d.pdf").open("wb") as handle:
        writer.write(handle)
    files["pdf"] = tmp_path / "d.pdf"

    (tmp_path / "broken.docx").write_bytes(b"this is not a real docx zip")
    files["broken"] = tmp_path / "broken.docx"
    return files


def test_multi_import_produces_ready_items(tmp_path):
    files = _make_files(tmp_path)
    center = DocumentCenter(tmp_path / "dc")
    items = center.import_paths([files["txt"], files["md"]])
    assert len(items) == 2
    assert all(i.state == ItemState.READY for i in items)
    kinds = {i.preview.kind for i in items}
    assert kinds == {PreviewKind.TEXT, PreviewKind.MARKDOWN}
    assert any("markdown body" in i.preview.preview_text for i in items)


def test_pdf_md_txt_image_are_previewable(tmp_path):
    files = _make_files(tmp_path)
    builder = PreviewBuilder()
    assert builder.build(files["txt"]).kind == PreviewKind.TEXT
    assert builder.build(files["md"]).kind == PreviewKind.MARKDOWN
    assert builder.build(files["pdf"]).kind == PreviewKind.PDF
    img = builder.build(files["png"])
    assert img.kind == PreviewKind.IMAGE
    assert img.ocr_status in (OcrStatus.REQUIRED, OcrStatus.DONE, OcrStatus.PENDING)
    assert "width" in img.metadata  # office/image metadata surfaced


def test_faulty_file_shows_controlled_error_state(tmp_path):
    files = _make_files(tmp_path)
    center = DocumentCenter(tmp_path / "dc")
    items = center.import_paths([files["broken"]])
    item = items[0]
    assert item.state == ItemState.ERROR
    assert item.preview.is_error is True
    assert item.preview.kind == PreviewKind.ERROR
    assert item.preview.parser_errors


def test_import_status_appears_in_job_monitor(tmp_path):
    files = _make_files(tmp_path)
    center = DocumentCenter(tmp_path / "dc")
    center.import_paths([files["txt"]])
    states = [e["state"] for e in center.job_monitor_rows()]
    assert "queued" in states
    assert "parsing" in states
    assert "ready" in states


def test_tags_edit_and_history(tmp_path):
    files = _make_files(tmp_path)
    center = DocumentCenter(tmp_path / "dc")
    item = center.import_paths([files["txt"]])[0]
    center.set_tags(item.doc_id, ["telekom", "sap", "sap"])
    assert center.get_tags(item.doc_id) == ["sap", "telekom"]
    events = {e["event"] for e in center.document_history(item.doc_id)}
    assert {"imported", "tagged"} <= events


def test_async_import_does_not_block_and_delivers_items(tmp_path):
    files = _make_files(tmp_path)
    center = DocumentCenter(tmp_path / "dc")
    delivered = []
    scheduled = []
    thread = center.import_paths_async(
        [files["txt"], files["md"]],
        on_item=lambda it: delivered.append(it.state),
        scheduler=lambda fn: (scheduled.append(1), fn()),
    )
    thread.join(timeout=5)
    assert len(delivered) == 2
    assert scheduled  # callbacks were routed through the UI scheduler


def test_missing_file_yields_error_preview(tmp_path):
    center = DocumentCenter(tmp_path / "dc")
    result = center.preview(tmp_path / "does_not_exist.txt")
    assert result.is_error is True
    assert result.ocr_status == OcrStatus.UNAVAILABLE
