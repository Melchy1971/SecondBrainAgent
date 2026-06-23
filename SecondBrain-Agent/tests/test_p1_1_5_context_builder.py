import pytest

from secondbrain.rag.context_builder import (
    ContextBuilder,
    ContextBuilderConfig,
    estimate_tokens,
    truncate_to_token_budget,
)
from secondbrain.rag.retrieval.score_fusion import SearchResult


def test_context_builder_orders_by_score_and_renders_sources():
    results = [
        SearchResult("doc2", "c2", "less relevant", 0.2),
        SearchResult("doc1", "c1", "most relevant context", 0.9),
    ]

    context = ContextBuilder().build(results)

    assert [chunk.document_id for chunk in context.chunks] == ["doc1", "doc2"]
    assert "[Source 1: document=doc1, chunk=c1, score=0.9000]" in context.text
    assert context.total_tokens == 5


def test_context_builder_deduplicates_normalized_text():
    results = [
        SearchResult("doc1", "c1", "duplicate   text", 0.9),
        SearchResult("doc2", "c2", "duplicate text", 0.8),
    ]

    context = ContextBuilder().build(results)

    assert len(context.chunks) == 1
    assert context.skipped_duplicates == 1


def test_context_builder_respects_chunk_limit():
    results = [SearchResult(f"doc{i}", f"c{i}", f"text {i}", float(10 - i)) for i in range(5)]

    context = ContextBuilder(ContextBuilderConfig(max_chunks=2)).build(results)

    assert len(context.chunks) == 2
    assert [chunk.document_id for chunk in context.chunks] == ["doc0", "doc1"]


def test_context_builder_respects_token_budget():
    results = [
        SearchResult("doc1", "c1", "one two three", 0.9),
        SearchResult("doc2", "c2", "four five six", 0.8),
    ]

    context = ContextBuilder(ContextBuilderConfig(max_tokens=4)).build(results)

    assert [chunk.document_id for chunk in context.chunks] == ["doc1"]
    assert context.skipped_budget == 1
    assert context.total_tokens == 3


def test_context_builder_truncates_single_oversized_chunk():
    result = SearchResult("doc1", "c1", "one two three four five", 0.9)

    context = ContextBuilder(ContextBuilderConfig(max_tokens=3)).build([result])

    assert context.chunks[0].text == "one two three"
    assert context.total_tokens == 3


def test_context_builder_handles_empty_and_blank_results():
    context = ContextBuilder().build([SearchResult("doc1", "c1", "   ", 1.0)])

    assert context.is_empty
    assert context.text == ""
    assert context.total_tokens == 0


def test_token_helpers_are_deterministic():
    assert estimate_tokens(" one   two\nthree ") == 3
    assert truncate_to_token_budget("one two three", 2) == "one two"
    with pytest.raises(ValueError):
        truncate_to_token_budget("one", 0)


def test_context_builder_rejects_invalid_config():
    with pytest.raises(ValueError):
        ContextBuilderConfig(max_chunks=0)
    with pytest.raises(ValueError):
        ContextBuilderConfig(max_tokens=0)
