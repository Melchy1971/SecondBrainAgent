"""v30.46.1 - MarkdownRenderer der gemeinsamen Chat-Architektur.

Konsolidiert aus secondbrain.markdown (dort seit v30.46.1 nur noch
Kompatibilitaets-Re-Export). Dependency-frei: parse() liefert Bloecke fuer
beliebige Frontends, render_into() bedient Tk-Text-Widgets.
"""
from __future__ import annotations

import re
from typing import Any


class MarkdownRenderer:
    """Dependency-free Markdown parser and Tk text renderer for native chat."""

    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")

    def parse(self, markdown: str) -> list[dict[str, Any]]:
        lines = (markdown or "").splitlines()
        blocks: list[dict[str, Any]] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.startswith("```"):
                language = line[3:].strip()
                index += 1
                code: list[str] = []
                while index < len(lines) and not lines[index].startswith("```"):
                    code.append(lines[index])
                    index += 1
                blocks.append({"type": "code", "language": language, "text": "\n".join(code)})
            elif self._is_table(lines, index):
                header = self._table_cells(lines[index])
                index += 2
                rows: list[list[str]] = []
                while index < len(lines) and "|" in lines[index] and lines[index].strip():
                    rows.append(self._table_cells(lines[index]))
                    index += 1
                blocks.append({"type": "table", "header": header, "rows": rows})
                continue
            elif line.startswith(">"):
                blocks.append({"type": "blockquote", "text": line[1:].strip()})
            elif re.match(r"^\s*[-*]\s+\[[ xX]\]\s+", line):
                checked = "[x]" in line.lower()
                text = re.sub(r"^\s*[-*]\s+\[[ xX]\]\s+", "", line)
                blocks.append({"type": "checklist", "checked": checked, "text": text, "inline": self.inline(text)})
            elif re.match(r"^\s*(?:[-*+] |\d+\. )", line):
                text = re.sub(r"^\s*(?:[-*+] |\d+\. )", "", line)
                blocks.append({"type": "list", "text": text, "inline": self.inline(text)})
            elif line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line[level:].strip()
                blocks.append({"type": "heading", "level": min(level, 6), "text": text})
            elif line.strip():
                blocks.append({"type": "paragraph", "text": line, "inline": self.inline(line)})
            else:
                blocks.append({"type": "blank", "text": ""})
            index += 1
        return blocks

    def inline(self, text: str) -> list[dict[str, str]]:
        tokens: list[dict[str, str]] = []
        cursor = 0
        matches = sorted(
            [(*match.span(), "link", match.group(1), match.group(2)) for match in self.LINK_PATTERN.finditer(text)]
            + [(*match.span(), "inline_code", match.group(1), "") for match in self.INLINE_CODE_PATTERN.finditer(text)],
            key=lambda item: item[0],
        )
        for start, end, kind, value, target in matches:
            if start < cursor:
                continue
            if start > cursor:
                tokens.append({"type": "text", "text": text[cursor:start]})
            token = {"type": kind, "text": value}
            if target:
                token["target"] = target
            tokens.append(token)
            cursor = end
        if cursor < len(text):
            tokens.append({"type": "text", "text": text[cursor:]})
        return tokens or [{"type": "text", "text": text}]

    def render_into(self, widget: Any, markdown: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.tag_configure("heading", font=("Segoe UI", 13, "bold"), spacing1=8)
        widget.tag_configure("code", font=("Consolas", 10), background="#111827", foreground="#E5E7EB")
        widget.tag_configure("inline_code", font=("Consolas", 10), background="#E5E7EB")
        widget.tag_configure("blockquote", lmargin1=18, foreground="#64748B")
        widget.tag_configure("link", foreground="#2563EB", underline=True)
        for block in self.parse(markdown):
            kind = block["type"]
            if kind == "blank":
                widget.insert("end", "\n")
            elif kind == "heading":
                widget.insert("end", block["text"] + "\n", "heading")
            elif kind == "code":
                widget.insert("end", block["text"] + "\n", ("code", f"language:{block['language'] or 'plain'}"))
            elif kind == "blockquote":
                widget.insert("end", block["text"] + "\n", "blockquote")
            elif kind == "table":
                widget.insert("end", " | ".join(block["header"]) + "\n", "heading")
                for row in block["rows"]:
                    widget.insert("end", " | ".join(row) + "\n")
            else:
                prefix = "☑ " if kind == "checklist" and block.get("checked") else "☐ " if kind == "checklist" else "• " if kind == "list" else ""
                widget.insert("end", prefix)
                for token in block.get("inline", [{"type": "text", "text": block.get("text", "")}]):
                    widget.insert("end", token["text"], token["type"] if token["type"] != "text" else ())
                widget.insert("end", "\n")
        widget.configure(state="disabled")

    @staticmethod
    def _table_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    @staticmethod
    def _is_table(lines: list[str], index: int) -> bool:
        if index + 1 >= len(lines) or "|" not in lines[index]:
            return False
        separator = lines[index + 1].strip().strip("|")
        cells = [cell.strip() for cell in separator.split("|")]
        return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)
