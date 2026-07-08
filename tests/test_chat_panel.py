"""v30.46.3 - Tests fuer das ChatPanel-Modell (Mitte: Conversation/Markdown)."""
from secondbrain.native.ai_workspace.panels import ChatPanel


def test_transcript_markdown_renders_roles_as_headings() -> None:
    messages = [
        {"role": "user", "content": "Frage"},
        {"role": "assistant", "content": "Antwort"},
    ]
    markdown = ChatPanel.transcript_markdown(messages)
    assert "## User" in markdown
    assert "## Assistant" in markdown
    assert markdown.index("Frage") < markdown.index("Antwort")


def test_latest_citations_come_from_last_assistant_message() -> None:
    messages = [
        {"role": "assistant", "content": "alt", "metadata": {"citations": [{"document": "alt"}]}},
        {"role": "user", "content": "Frage"},
        {"role": "assistant", "content": "neu", "metadata": {"citations": [{"document": "neu"}]}},
    ]
    citations = ChatPanel.latest_citations(messages)
    assert citations == [{"document": "neu"}]


def test_latest_citations_empty_without_assistant() -> None:
    assert ChatPanel.latest_citations([{"role": "user", "content": "x"}]) == []
    assert ChatPanel.latest_citations([]) == []
