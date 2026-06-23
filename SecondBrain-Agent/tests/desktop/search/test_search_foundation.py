from pathlib import Path

import pytest

from secondbrain.desktop.search import (
    InMemorySearchBackend,
    SearchHistory,
    SearchQuery,
    SearchResult,
    SearchService,
)
from secondbrain.desktop.search.search_events import SEARCH_COMPLETED, SEARCH_FAILED
from secondbrain.desktop.search.search_filters import SearchFilters
from secondbrain.desktop.search.search_persistence import SearchPersistence


def sample_docs():
    return [
        SearchResult("1", "Projektplan", "RAG Suche und Connector Index", 0.8, ["rag", "p1"], "import", "w1"),
        SearchResult("2", "Fehleranalyse", "Connector Sync failed retry", 0.7, ["connector"], "gmail", "w1", status="FAILED"),
        SearchResult("3", "Training", "Tischtennis Notizen", 0.5, ["sport"], "manual", "w2"),
    ]


def test_query_normalization_deduplicates_and_bounds_limit():
    q = SearchQuery("  RAG   Suche ", tags=["rag", "rag", ""], status=["indexed"], limit=999, offset=-5)
    n = q.normalized()
    assert n.text == "RAG Suche"
    assert n.tags == ["rag"]
    assert n.status == ["INDEXED"]
    assert n.limit == 100
    assert n.offset == 0


def test_in_memory_backend_filters_workspace_and_text():
    service = SearchService(InMemorySearchBackend(sample_docs()))
    results, facets = service.search(SearchQuery("Connector", workspace_id="w1"))
    assert [r.document_id for r in results] == ["2", "1"]
    assert facets.workspaces[0].value == "w1"


def test_result_sanitizing_removes_technical_metadata_and_limits_snippet():
    result = SearchResult(
        "1",
        "Doc",
        "x " * 500,
        1.0,
        metadata={"ownerUserId": "u1", "visible": "ok"},
    ).sanitized(max_snippet_chars=20)
    assert "ownerUserId" not in result.metadata
    assert result.metadata["visible"] == "ok"
    assert len(result.snippet) <= 20


def test_filters_match_tags_status_source_and_workspace():
    result = sample_docs()[1]
    filters = SearchFilters(workspace_id="w1", tags=["connector"], status=["failed"], sources=["gmail"])
    assert filters.matches(result) is True
    assert SearchFilters(workspace_id="w2").matches(result) is False


def test_history_keeps_recent_unique_texts():
    history = SearchHistory(max_entries=2)
    history.add(SearchQuery("alpha"), 1)
    history.add(SearchQuery("beta"), 2)
    history.add(SearchQuery("alpha"), 3)
    assert len(history.entries) == 2
    assert history.recent_texts() == ["alpha", "beta"]


def test_persistence_roundtrip(tmp_path: Path):
    persistence = SearchPersistence(tmp_path)
    history = SearchHistory()
    history.add(SearchQuery("persist me"), 4)
    persistence.save_history(history)
    loaded = persistence.load_history()
    assert loaded.entries[0]["text"] == "persist me"


def test_search_service_updates_state_and_events():
    service = SearchService(InMemorySearchBackend(sample_docs()))
    results, _ = service.search(SearchQuery("RAG"))
    assert service.state.loading is False
    assert service.state.results == results
    assert service.events.by_type(SEARCH_COMPLETED)[0]["payload"]["count"] == 1


def test_search_service_failure_sets_error_and_event():
    class BrokenBackend:
        def search(self, query):
            raise RuntimeError("backend down")

    service = SearchService(BrokenBackend())
    with pytest.raises(RuntimeError):
        service.search(SearchQuery("x"))
    assert service.state.error == "backend down"
    assert service.events.by_type(SEARCH_FAILED)[0]["payload"]["error"] == "backend down"
