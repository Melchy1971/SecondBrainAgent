"""Review Queue: Klassifikationen mit niedriger Confidence zur manuellen Prüfung.

Manuelle Korrekturen überschreiben Vorschläge und werden in der Tag-Historie
nachvollziehbar dokumentiert (source=manual, editor, alte -> neue Werte).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.classification.tag_history import TagHistory


class ReviewQueue:
    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root)
        self.path = self.project_root / "runtime" / "classification" / "review_queue.json"
        self.tag_history = TagHistory(self.project_root)

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self, items: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, indent=2, ensure_ascii=False, sort_keys=True),
                             encoding="utf-8")

    def add(self, doc_ref: str, suggestion: dict[str, Any], *, job_id: str = "") -> dict[str, Any]:
        items = self._load()
        review_id = f"rev_{uuid.uuid4().hex[:12]}"
        item = {
            "review_id": review_id,
            "doc_ref": doc_ref,
            "job_id": job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "open",
            "suggestion": {
                "document_type": suggestion.get("document_type", ""),
                "tags": suggestion.get("tags", []),
                "confidence": suggestion.get("confidence", 0.0),
            },
        }
        items[review_id] = item
        self._write(items)
        return item

    def list_open(self, limit: int = 100) -> list[dict[str, Any]]:
        items = [i for i in self._load().values() if i.get("status") == "open"]
        items.sort(key=lambda i: i.get("created_at", ""))
        return items[-limit:]

    def resolve(
        self,
        review_id: str,
        *,
        document_type: str,
        tags: list[str],
        editor: str,
        note: str = "",
    ) -> dict[str, Any]:
        """Manuelle Entscheidung: überschreibt den Vorschlag nachvollziehbar."""
        items = self._load()
        item = items.get(review_id)
        if item is None:
            raise KeyError(f"unbekanntes Review: {review_id}")
        suggestion = item.get("suggestion", {})
        self.tag_history.record(
            item["doc_ref"],
            old_type=suggestion.get("document_type", ""),
            new_type=document_type,
            old_tags=list(suggestion.get("tags", [])),
            new_tags=list(tags),
            source="manual",
            editor=editor,
            note=note or f"Review {review_id} aufgelöst",
        )
        item.update({
            "status": "resolved",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolution": {"document_type": document_type, "tags": tags, "editor": editor},
        })
        items[review_id] = item
        self._write(items)
        return item
