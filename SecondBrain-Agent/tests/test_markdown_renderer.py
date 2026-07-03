from secondbrain.markdown import MarkdownRenderer


def test_markdown_renderer_supports_chat_blocks() -> None:
    markdown = """# Titel

- Punkt
- [x] Fertig
> Hinweis

| A | B |
|---|---|
| 1 | 2 |

```python
print('x')
```
"""
    blocks = MarkdownRenderer().parse(markdown)
    types = {block["type"] for block in blocks}
    assert {"heading", "list", "checklist", "blockquote", "table", "code"}.issubset(types)
    code = next(block for block in blocks if block["type"] == "code")
    assert code["language"] == "python"


def test_markdown_renderer_supports_links_and_inline_code() -> None:
    tokens = MarkdownRenderer().inline("Siehe [Quelle](https://example.test) und `code`")
    assert any(token["type"] == "link" and token["target"] == "https://example.test" for token in tokens)
    assert any(token["type"] == "inline_code" for token in tokens)


def test_markdown_renderer_canonical_home_is_chat_package() -> None:
    # v30.46.1: secondbrain.markdown re-exportiert nur noch.
    from secondbrain.chat import MarkdownRenderer as CanonicalRenderer

    assert MarkdownRenderer is CanonicalRenderer

