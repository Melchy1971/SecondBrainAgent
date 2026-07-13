from pathlib import Path

from secondbrain.desktop.documents import (
    DesktopDocument,
    DocumentActionType,
    DocumentEventType,
    DocumentFilter,
    DocumentPersistence,
    DocumentRepository,
    DocumentService,
    DocumentStatus,
)


def doc(document_id="d1", title="Alpha", workspace_id="w1", **kw):
    return DesktopDocument(
        document_id=document_id,
        title=title,
        workspace_id=workspace_id,
        source=kw.pop("source", "upload"),
        tags=tuple(kw.pop("tags", ())),
        metadata=kw.pop("metadata", {}),
        status=kw.pop("status", DocumentStatus.IMPORTED),
    )


def test_repository_saves_lists_and_requires_documents():
    repo = DocumentRepository()
    repo.save(doc())
    assert repo.count() == 1
    assert repo.require("d1").title == "Alpha"
    assert repo.delete("d1") is True
    assert repo.get("d1") is None


def test_filter_supports_workspace_status_tags_text_and_sorting():
    service = DocumentService()
    service.add_document(doc("d1", "Alpha Invoice", tags=("finance",), metadata={"vendor": "Acme"}))
    service.add_document(doc("d2", "Beta Note", workspace_id="w2", status=DocumentStatus.FAILED))
    result = service.list_documents(DocumentFilter(workspace_id="w1", statuses=(DocumentStatus.IMPORTED,), tags=("finance",), text="acme"))
    assert [d.document_id for d in result] == ["d1"]


def test_selection_validates_existing_document_and_publishes_event():
    service = DocumentService()
    service.add_document(doc())
    service.select("d1")
    assert service.selection.to_list() == ["d1"]
    assert service.event_bus.events[-1].type == DocumentEventType.DOCUMENT_SELECTED


def test_bulk_archive_and_reindex_are_isolated():
    service = DocumentService()
    service.add_document(doc("d1"))
    result = service.bulk_execute(DocumentActionType.ARCHIVE, ["d1", "missing"])
    assert result.affected == 1
    assert "missing" in result.failed
    assert service.repository.require("d1").status == DocumentStatus.ARCHIVED
    service.bulk_execute(DocumentActionType.REINDEX, ["d1"])
    assert service.repository.require("d1").status == DocumentStatus.INDEXING


def test_bulk_tags_move_and_export_metadata():
    service = DocumentService()
    service.add_document(doc("d1", tags=("old",)))
    service.bulk_execute(DocumentActionType.ADD_TAGS, ["d1"], tags=("new", "old"))
    assert service.repository.require("d1").tags == ("old", "new")
    service.bulk_execute(DocumentActionType.REMOVE_TAGS, ["d1"], tags=("old",))
    assert service.repository.require("d1").tags == ("new",)
    service.bulk_execute(DocumentActionType.MOVE_WORKSPACE, ["d1"], workspace_id="w2")
    assert service.repository.require("d1").workspace_id == "w2"
    exported = service.bulk_execute(DocumentActionType.EXPORT_METADATA, ["d1"])
    assert exported.payload["documents"][0]["document_id"] == "d1"


def test_persistence_roundtrip(tmp_path: Path):
    persistence = DocumentPersistence(tmp_path)
    persistence.save_selection(["d2", "d1"])
    assert persistence.load_selection() == ["d2", "d1"]
    persistence.save_json("filters.json", {"workspace_id": "w1"})
    assert persistence.load_json("filters.json")["workspace_id"] == "w1"


def test_document_dict_roundtrip_normalizes_status_and_tags():
    original = doc(tags=("a", "a", "b"), status=DocumentStatus.INDEXED)
    restored = DesktopDocument.from_dict(original.to_dict())
    assert restored.status == DocumentStatus.INDEXED
    assert restored.tags == ("a", "a", "b")
    updated = restored.with_update(tags=("a", "a", "b"), status="FAILED")
    assert updated.tags == ("a", "b")
    assert updated.status == DocumentStatus.FAILED
