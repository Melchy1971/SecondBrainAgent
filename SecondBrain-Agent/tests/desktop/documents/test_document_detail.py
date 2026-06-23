from datetime import datetime, timezone

import pytest

from secondbrain.desktop.documents import (
    DesktopDocument,
    DocumentDetailNotFound,
    DocumentDetailService,
    DocumentStatus,
    build_document_detail,
    sanitize_metadata,
)
from secondbrain.desktop.documents.document_repository import DocumentRepository


def sample_document(**changes):
    base = dict(
        document_id="doc-123",
        title="Quarterly Plan",
        workspace_id="workspace-9",
        source="upload",
        status=DocumentStatus.INDEXED,
        created_at=datetime(2026, 6, 23, 8, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 23, 9, 30, tzinfo=timezone.utc),
        tags=("planning", "q3"),
        metadata={
            "author": "Markus",
            "document_id": "doc-123",
            "workspace_id": "workspace-9",
            "ownerUserId": "hidden-by-camel-case-gap",
            "api_key": "secret",
            "summary": "usable metadata",
        },
    )
    base.update(changes)
    return DesktopDocument(**base)


def test_detail_model_contains_user_facing_fields_only():
    detail = build_document_detail(sample_document())

    assert detail.title == "Quarterly Plan"
    assert detail.status == "Indexed"
    assert "Titel" in detail.visible_labels()
    assert "Status" in detail.visible_labels()
    assert "Quelle" in detail.visible_labels()
    assert "document_id" not in detail.visible_labels()
    assert "workspace_id" not in detail.visible_labels()


def test_detail_keeps_technical_reference_outside_visible_fields():
    detail = build_document_detail(sample_document())

    assert detail.technical_reference == "doc-123"
    assert all(field.value != "doc-123" for field in detail.fields)


def test_sanitize_metadata_removes_ids_and_secrets():
    metadata = sanitize_metadata(
        {
            "document_id": "doc-1",
            "workspace_id": "ws-1",
            "tenant_id": "tenant",
            "password": "pw",
            "access_token": "token",
            "author": "A",
            "category": "Plan",
        }
    )

    assert metadata == {"author": "A", "category": "Plan"}


def test_sanitize_metadata_truncates_long_values():
    metadata = sanitize_metadata({"description": "x" * 300}, max_value_length=20)

    assert metadata["description"] == "x" * 19 + "…"


def test_build_detail_can_filter_groups():
    detail = build_document_detail(sample_document(), include_groups={"timeline"})

    assert detail.visible_labels() == ("Erstellt", "Aktualisiert")


def test_detail_service_loads_from_repository():
    repository = DocumentRepository()
    repository.save(sample_document())

    detail = DocumentDetailService(repository).get_detail("doc-123")

    assert detail.title == "Quarterly Plan"
    assert detail.metadata["author"] == "Markus"


def test_detail_service_raises_for_missing_document():
    service = DocumentDetailService(DocumentRepository())

    with pytest.raises(DocumentDetailNotFound):
        service.get_detail("missing")
