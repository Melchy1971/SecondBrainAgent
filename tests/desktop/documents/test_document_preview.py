from secondbrain.desktop.documents import (
    DesktopDocument,
    DocumentPreviewNotFoundError,
    DocumentPreviewService,
    DocumentRepository,
    DocumentStatus,
    PreviewStatus,
    build_document_preview,
)


def test_text_preview_is_ready_and_bounded():
    doc = DesktopDocument(
        document_id="doc-1",
        title="Notes.md",
        workspace_id="ws-1",
        source="upload",
        status=DocumentStatus.INDEXED,
        metadata={"mime_type": "text/markdown", "preview_text": "\n# Titel\nZeile 2\nZeile 3"},
    )

    preview = build_document_preview(doc, max_chars=12, max_lines=10)

    assert preview.status == PreviewStatus.READY
    assert preview.can_render is True
    assert preview.truncated is True
    assert preview.content.endswith("…")
    assert "doc-1" not in preview.content


def test_preview_limits_line_count():
    doc = DesktopDocument(
        document_id="doc-1",
        title="log.txt",
        workspace_id="ws-1",
        source="upload",
        metadata={"content": "a\nb\nc\nd"},
    )

    preview = build_document_preview(doc, max_lines=2)

    assert preview.content == "a\nb"
    assert preview.line_count == 2
    assert preview.truncated is True


def test_unsupported_binary_type_returns_status_object():
    doc = DesktopDocument(
        document_id="doc-1",
        title="photo.png",
        workspace_id="ws-1",
        source="upload",
        metadata={"mime_type": "image/png", "content": "binary"},
    )

    preview = build_document_preview(doc)

    assert preview.status == PreviewStatus.UNSUPPORTED
    assert preview.can_render is False
    assert preview.content == ""


def test_failed_document_returns_error_message():
    doc = DesktopDocument(
        document_id="doc-1",
        title="broken.pdf",
        workspace_id="ws-1",
        source="upload",
        status=DocumentStatus.FAILED,
        metadata={"mime_type": "application/pdf", "error": "Parser failed"},
    )

    preview = build_document_preview(doc)

    assert preview.status == PreviewStatus.FAILED
    assert preview.message == "Parser failed"


def test_archived_document_is_not_rendered():
    doc = DesktopDocument(
        document_id="doc-1",
        title="old.txt",
        workspace_id="ws-1",
        source="upload",
        status=DocumentStatus.ARCHIVED,
        metadata={"content": "hidden"},
    )

    preview = build_document_preview(doc)

    assert preview.status == PreviewStatus.ARCHIVED
    assert preview.content == ""


def test_preview_metadata_allowlist_excludes_secret_and_ids():
    doc = DesktopDocument(
        document_id="doc-1",
        title="notes.txt",
        workspace_id="ws-1",
        source="upload",
        metadata={
            "filename": "notes.txt",
            "mime_type": "text/plain",
            "workspace_id": "ws-1",
            "api_token": "secret",
            "content": "hello",
        },
    )

    preview = build_document_preview(doc)

    assert preview.metadata == {"filename": "notes.txt", "mime_type": "text/plain"}


def test_preview_service_returns_preview_and_raises_not_found():
    repo = DocumentRepository()
    repo.save(
        DesktopDocument(
            document_id="doc-1",
            title="notes.txt",
            workspace_id="ws-1",
            source="upload",
            metadata={"content": "hello"},
        )
    )
    service = DocumentPreviewService(repo)

    assert service.get_preview("doc-1").status == PreviewStatus.READY

    try:
        service.get_preview("missing")
    except DocumentPreviewNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected DocumentPreviewNotFoundError")


def test_invalid_limits_raise_value_error():
    doc = DesktopDocument(document_id="doc-1", title="x.txt", workspace_id="ws-1", source="upload")

    try:
        build_document_preview(doc, max_chars=0)
    except ValueError as exc:
        assert "max_chars" in str(exc)
    else:
        raise AssertionError("expected ValueError")
