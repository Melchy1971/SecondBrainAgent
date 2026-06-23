from pathlib import Path

import pytest

from secondbrain.desktop.search.saved_searches import (
    SavedSearch,
    SavedSearchError,
    SavedSearchRepository,
    SavedSearchService,
)


def service(tmp_path: Path) -> SavedSearchService:
    return SavedSearchService(SavedSearchRepository(tmp_path / "saved_searches.json"))


def test_create_normalizes_and_persists_saved_search(tmp_path: Path):
    svc = service(tmp_path)
    item = svc.create(SavedSearch(name="  Fehler   Suche ", query_text="  connector   failed  ", tags=["A", "a", "B"]))

    assert item.name == "Fehler   Suche"
    assert item.query_text == "connector failed"
    assert item.tags == ["A", "B"]

    reloaded = service(tmp_path)
    assert reloaded.get(item.search_id).query_text == "connector failed"


def test_saved_search_to_query_payload_is_ui_free(tmp_path: Path):
    svc = service(tmp_path)
    item = svc.create(
        SavedSearch(
            name="PDFs",
            query_text="rechnung",
            workspace_id="ws1",
            tags=["finance"],
            status=["INDEXED"],
            sources=["upload"],
            limit=10,
            metadata={"ui_color": "blue"},
        )
    )

    assert svc.as_query(item.search_id) == {
        "text": "rechnung",
        "workspace_id": "ws1",
        "tags": ["finance"],
        "status": ["INDEXED"],
        "sources": ["upload"],
        "limit": 10,
        "offset": 0,
    }


def test_duplicate_names_are_rejected_case_insensitive(tmp_path: Path):
    svc = service(tmp_path)
    svc.create(SavedSearch(name="Invoices", query_text="invoice"))

    with pytest.raises(SavedSearchError):
        svc.create(SavedSearch(name=" invoices ", query_text="rechnung"))


def test_update_preserves_id_and_created_at(tmp_path: Path):
    svc = service(tmp_path)
    item = svc.create(SavedSearch(name="Old", query_text="old"))

    updated = svc.update(item.search_id, name="New", query_text="new query", limit=50)

    assert updated.search_id == item.search_id
    assert updated.created_at == item.created_at
    assert updated.updated_at >= item.updated_at
    assert updated.name == "New"
    assert updated.limit == 50


def test_delete_removes_saved_search(tmp_path: Path):
    svc = service(tmp_path)
    item = svc.create(SavedSearch(name="Remove", query_text="x"))

    removed = svc.delete(item.search_id)

    assert removed.search_id == item.search_id
    with pytest.raises(SavedSearchError):
        svc.get(item.search_id)


def test_validation_rejects_empty_query_and_invalid_limit(tmp_path: Path):
    svc = service(tmp_path)

    with pytest.raises(SavedSearchError):
        svc.create(SavedSearch(name="Empty", query_text=" "))

    with pytest.raises(SavedSearchError):
        svc.create(SavedSearch(name="Too many", query_text="x", limit=500))
