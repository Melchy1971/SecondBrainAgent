"""Document comparison via unified diff."""

from __future__ import annotations

import difflib


def diff_documents(left: str, right: str, *, left_label: str = "a", right_label: str = "b") -> dict:
    left_lines = left.splitlines()
    right_lines = right.splitlines()
    unified = list(difflib.unified_diff(left_lines, right_lines,
                                        fromfile=left_label, tofile=right_label, lineterm=""))
    added = sum(1 for l in unified if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in unified if l.startswith("-") and not l.startswith("---"))
    ratio = difflib.SequenceMatcher(None, left, right).ratio()
    return {"unified": unified, "added": added, "removed": removed,
            "changed": added + removed, "similarity": round(ratio, 4), "identical": left == right}
