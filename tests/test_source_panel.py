"""v30.46.3 - Tests fuer Source-/Memory-/Document-Panel (Rechts)."""
from secondbrain.native.ai_workspace.panels import DocumentPanel, MemoryPanel, SourcePanel


def test_source_panel_rows_match_citation_renderer_contract() -> None:
    citations = [
        {
            "document": "Plan",
            "document_id": "doc-1",
            "chunk": "c-1",
            "score": 0.8,
            "workspace": "chat",
            "source": "plan.md",
            "provider": "hybrid",
        }
    ]
    rows = SourcePanel().rows(citations)
    assert rows[0]["iid"] == "citation-0"
    assert rows[0]["document"] == "Plan"
    assert rows[0]["values"] == ("c-1", 0.8, "chat", "plan.md", "hybrid")
    assert rows[0]["tag"] == "doc-1"


def test_memory_panel_skips_empty_entries() -> None:
    lines = MemoryPanel.lines([{"content": "Fakt"}, {"content": "  "}, {"content": ""}, {}])
    assert lines == ["Fakt"]


def test_document_panel_combines_selection_and_attachments() -> None:
    lines = DocumentPanel.lines(
        ["doc-1"],
        [{"name": "plan.pdf", "extension": ".pdf", "size": 123}],
    )
    assert lines == [
        "Auswahl: doc-1",
        "Anhang: plan.pdf (.pdf, 123 Bytes)",
    ]


def test_document_panel_handles_empty_inputs() -> None:
    assert DocumentPanel.lines([], []) == []
