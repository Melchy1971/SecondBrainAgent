"""Preview resolution: map a file to a preview kind + lightweight renderers.

Additive; does not touch the existing document center. Stdlib-only (optional
pygments used only if installed).
"""

from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass
from pathlib import Path

IMAGE = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "svg", "tiff", "ico"}
VIDEO = {"mp4", "webm", "mov", "mkv", "avi", "m4v"}
AUDIO = {"mp3", "wav", "ogg", "flac", "m4a", "aac"}
MARKDOWN = {"md", "markdown"}
PDF = {"pdf"}
OFFICE = {"docx", "xlsx", "pptx", "doc", "xls", "ppt", "odt", "ods", "odp"}
CODE = {"py", "js", "ts", "tsx", "jsx", "java", "c", "h", "cpp", "hpp", "go", "rs",
        "sh", "bash", "json", "yaml", "yml", "toml", "ini", "html", "css", "sql", "xml"}
TEXT = {"txt", "log", "csv", "rst"}


@dataclass(frozen=True)
class PreviewKind:
    kind: str          # image|video|audio|markdown|pdf|office|code|text|unknown
    mime: str
    renderer: str      # which viewer widget/handler to use
    language: str | None = None


def _ext(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def resolve(filename: str) -> PreviewKind:
    e = _ext(filename)
    if e in IMAGE:
        return PreviewKind("image", f"image/{'jpeg' if e in {'jpg','jpeg'} else e}", "image_viewer")
    if e in VIDEO:
        return PreviewKind("video", f"video/{e}", "video_player")
    if e in AUDIO:
        return PreviewKind("audio", f"audio/{e}", "audio_player")
    if e in MARKDOWN:
        return PreviewKind("markdown", "text/markdown", "markdown_view")
    if e in PDF:
        return PreviewKind("pdf", "application/pdf", "pdf_view")
    if e in OFFICE:
        return PreviewKind("office", "application/octet-stream", "office_view")
    if e in CODE:
        return PreviewKind("code", "text/plain", "code_view", language=e)
    if e in TEXT:
        return PreviewKind("text", "text/plain", "text_view")
    return PreviewKind("unknown", "application/octet-stream", "none")


# ---- markdown -> html (minimal, deterministic) ----------------------------
def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_list = False
    for line in lines:
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            if in_list:
                out.append("</ul>"); in_list = False
            level = len(h.group(1))
            out.append(f"<h{level}>{_inline(h.group(2))}</h{level}>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                out.append("<ul>"); in_list = True
            item = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<li>{_inline(item)}</li>")
            continue
        if in_list:
            out.append("</ul>"); in_list = False
        if line.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{_inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _inline(text: str) -> str:
    text = _html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


# ---- syntax highlighting (token classification) ---------------------------
_KEYWORDS = {
    "py": {"def", "class", "return", "import", "from", "if", "else", "elif", "for",
           "while", "try", "except", "with", "as", "in", "not", "and", "or", "None", "True", "False"},
    "js": {"function", "const", "let", "var", "return", "if", "else", "for", "while",
           "class", "import", "export", "from", "async", "await", "new", "null", "true", "false"},
}


@dataclass(frozen=True)
class Token:
    text: str
    type: str          # keyword|string|comment|number|name|other


def highlight(code: str, language: str | None = None) -> list[Token]:
    """Optional pygments if installed; otherwise a deterministic classifier."""
    try:  # pragma: no cover - only when pygments present
        import pygments
        from pygments.lexers import get_lexer_by_name, guess_lexer
        from pygments.token import Token as PT
        lexer = get_lexer_by_name(language) if language else guess_lexer(code)
        out = []
        for ttype, value in lexer.get_tokens(code):
            name = "other"
            if ttype in PT.Keyword: name = "keyword"
            elif ttype in PT.String: name = "string"
            elif ttype in PT.Comment: name = "comment"
            elif ttype in PT.Number: name = "number"
            elif ttype in PT.Name: name = "name"
            if value:
                out.append(Token(value, name))
        return out
    except Exception:
        return _fallback_highlight(code, language)


def _fallback_highlight(code: str, language: str | None) -> list[Token]:
    kw = _KEYWORDS.get(language or "", set())
    tokens: list[Token] = []
    for raw in re.findall(r"#[^\n]*|//[^\n]*|\"[^\"]*\"|'[^']*'|\b\d+(?:\.\d+)?\b|\w+|\s+|.", code):
        if raw.startswith("#") or raw.startswith("//"):
            tokens.append(Token(raw, "comment"))
        elif (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            tokens.append(Token(raw, "string"))
        elif re.fullmatch(r"\d+(?:\.\d+)?", raw):
            tokens.append(Token(raw, "number"))
        elif raw in kw:
            tokens.append(Token(raw, "keyword"))
        elif raw.strip() == "":
            tokens.append(Token(raw, "other"))
        elif re.fullmatch(r"\w+", raw):
            tokens.append(Token(raw, "name"))
        else:
            tokens.append(Token(raw, "other"))
    return tokens
