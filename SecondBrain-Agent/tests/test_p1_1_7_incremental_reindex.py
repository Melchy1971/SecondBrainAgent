from secondbrain.rag.indexing import (
    ChangeAction,
    ChangeDetector,
    DocumentSnapshot,
    InMemoryIndexRepository,
    ReindexService,
)


def test_change_detector_plans_new_changed_deleted_and_unchanged_documents():
    old = [
        DocumentSnapshot.from_text("a", "same"),
        DocumentSnapshot.from_text("b", "old"),
        DocumentSnapshot.from_text("c", "delete me"),
    ]
    current = [
        DocumentSnapshot.from_text("a", "same"),
        DocumentSnapshot.from_text("b", "new"),
        DocumentSnapshot.from_text("d", "new doc"),
    ]

    changes = ChangeDetector().plan(old, current)
    by_id = {change.document_id: change for change in changes}

    assert by_id["a"].action == ChangeAction.SKIP
    assert by_id["b"].action == ChangeAction.REINDEX
    assert by_id["c"].action == ChangeAction.DELETE
    assert by_id["d"].action == ChangeAction.REINDEX
    assert by_id["b"].old_hash != by_id["b"].new_hash


def test_reindex_service_applies_only_required_operations():
    repository = InMemoryIndexRepository(
        snapshots={
            "a": DocumentSnapshot.from_text("a", "same"),
            "b": DocumentSnapshot.from_text("b", "old"),
            "c": DocumentSnapshot.from_text("c", "delete me"),
        }
    )
    indexed = []
    service = ReindexService(repository, on_reindex=lambda snapshot: indexed.append(snapshot.document_id))

    plan = service.apply(
        [
            DocumentSnapshot.from_text("a", "same"),
            DocumentSnapshot.from_text("b", "new"),
            DocumentSnapshot.from_text("d", "new doc"),
        ]
    )

    assert plan.summary() == {"total": 4, "reindex": 2, "delete": 1, "skip": 1}
    assert repository.upserted_document_ids == ["b", "d"]
    assert repository.deleted_document_ids == ["c"]
    assert indexed == ["b", "d"]
    assert sorted(repository.snapshots) == ["a", "b", "d"]


def test_document_hash_normalizes_line_endings():
    left = DocumentSnapshot.from_text("doc", "a\r\nb")
    right = DocumentSnapshot.from_text("doc", "a\nb")

    assert left.content_hash == right.content_hash
