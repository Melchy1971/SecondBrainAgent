from dataclasses import dataclass, field

from secondbrain.desktop.search.preview import SearchPreviewBuilder, SearchPreviewSettings


@dataclass
class FakeSearchResult:
    document_id: str = "doc-1"
    title: str = "Process Notes"
    snippet: str = "The connector sync imports documents and the semantic search highlights matching content."
    metadata: dict = field(default_factory=dict)


def test_preview_highlights_query_terms() -> None:
    preview = SearchPreviewBuilder().build(FakeSearchResult(), "semantic connector")

    assert preview.document_id == "doc-1"
    assert "<mark>connector</mark>" in preview.highlighted_snippet
    assert "<mark>semantic</mark>" in preview.highlighted_snippet
    assert len(preview.highlights) == 2


def test_preview_uses_content_over_result_snippet() -> None:
    preview = SearchPreviewBuilder().build(FakeSearchResult(), "invoice", content="PDF invoice content")

    assert preview.snippet == "PDF invoice content"
    assert preview.metadata["preview_source"] == "content"


def test_preview_truncates_around_first_match() -> None:
    text = "A" * 200 + " target " + "B" * 200
    builder = SearchPreviewBuilder(SearchPreviewSettings(max_snippet_chars=80, context_chars=10))
    preview = builder.build(FakeSearchResult(snippet=text), "target")

    assert preview.truncated is True
    assert "target" in preview.snippet
    assert preview.snippet.startswith("…")
    assert preview.snippet.endswith("…")


def test_preview_escapes_html_by_default() -> None:
    preview = SearchPreviewBuilder().build(FakeSearchResult(snippet="<script>semantic</script>"), "semantic")

    assert "<script>" not in preview.highlighted_snippet
    assert "&lt;script&gt;" in preview.highlighted_snippet
    assert "<mark>semantic</mark>" in preview.highlighted_snippet


def test_preview_limits_highlights() -> None:
    builder = SearchPreviewBuilder(SearchPreviewSettings(max_highlights=1))
    preview = builder.build(FakeSearchResult(snippet="alpha beta gamma"), "alpha beta gamma")

    assert len(preview.highlights) == 1


def test_preview_serializes_to_dict() -> None:
    preview = SearchPreviewBuilder().build(FakeSearchResult(), "connector")
    payload = preview.as_dict()

    assert payload["document_id"] == "doc-1"
    assert payload["highlights"][0]["term"].lower() == "connector"
