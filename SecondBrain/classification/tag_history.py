"""Tag-Historie: jede Änderung an Typ/Tags ist append-only nachvollziehbar."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TagHistory:
    def __init__(self, project_root: str | Path = "."):
        self.path = Path(project_root) / "runtime" / "classification" / "tag_history.jsonl"

    def record(
        self,
        doc_ref: str,
        *,
        old_type: str = "",
        new_type: str = "",
        old_tags: list[str] | None = None,
        new_tags: list[str] | None = None,
        source: str = "suggestion",   # suggestion | manual
        editor: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        entry = {
            "schema": "secondbrain.classification.tag_change.v1",
            "ts": datetime.now(timezone.utc).isoformat(),
            "doc_ref": doc_ref,
            "old_type": old_type,
            "new_type": new_type,
            "old_tags": old_tags or [],
            "new_tags": new_tags or [],
            "source": source,
            "editor": editor,
            "note": note[:300],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def for_document(self, doc_ref: str, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("doc_ref") == doc_ref:
                entries.append(entry)
        return entries[-limit:]
