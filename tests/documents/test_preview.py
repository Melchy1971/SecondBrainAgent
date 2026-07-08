import pytest
from secondbrain.documents.preview import resolve, markdown_to_html, highlight


@pytest.mark.parametrize("name,kind", [
    ("a.pdf", "pdf"), ("b.docx", "office"), ("c.md", "markdown"), ("d.py", "code"),
    ("e.png", "image"), ("f.mp4", "video"), ("g.mp3", "audio"), ("h.txt", "text"),
    ("i.unknownext", "unknown"),
])
def test_resolve_kind(name, kind):
    assert resolve(name).kind == kind


def test_markdown_headings_lists_inline():
    html = markdown_to_html("# Title\n- a\n- b\n\n**bold** and `code` and [x](http://y)")
    assert "<h1>Title</h1>" in html
    assert "<ul>" in html and "<li>a</li>" in html
    assert "<strong>bold</strong>" in html and "<code>code</code>" in html
    assert '<a href="http://y">x</a>' in html


def test_markdown_escapes_html():
    assert "&lt;script&gt;" in markdown_to_html("<script>")


def test_highlight_classifies_tokens():
    toks = {(t.text, t.type) for t in highlight("def f(): return 42", "py")}
    assert ("def", "keyword") in toks
    assert ("return", "keyword") in toks
    assert ("42", "number") in toks


def test_highlight_strings_and_comments():
    toks = [t for t in highlight('x = \"hi\"  # note', "py")]
    types = {t.type for t in toks}
    assert "string" in types and "comment" in types
