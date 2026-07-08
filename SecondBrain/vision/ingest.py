"""Bridge vision results into the existing Memory/RAG ingestion boundary.

OCR/classification output is normalized to ConnectorItem, exactly like connector
sync items, so it flows through ConnectorImportBridge into document/RAG storage
without a second ingestion path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from secondbrain.connectors.adapter_contract import ConnectorItem
from secondbrain.vision.ports import OcrResult, Label

SOURCE = "vision_ocr"


def ocr_to_item(result: OcrResult, *, source_uri: str, doc_id: str | None = None,
                title: str | None = None, labels: list[Label] | None = None) -> ConnectorItem:
    content = result.text
    external_id = doc_id or sha256(f"{source_uri}\n{content}".encode("utf-8")).hexdigest()
    first_line = next((line for line in content.splitlines() if line.strip()), "")
    return ConnectorItem(
        external_id=external_id,
        source=SOURCE,
        title=title or (first_line[:80] if first_line else "(scan)"),
        content=content or first_line or "(empty scan)",
        updated_at=datetime.now(timezone.utc),
        uri=source_uri,
        metadata={
            "ocr_language": result.language,
            "ocr_mean_confidence": round(result.mean_confidence, 2),
            "ocr_block_count": len(result.blocks),
            "labels": [{"name": l.name, "score": round(l.score, 3)} for l in (labels or [])],
        },
    )


def result_to_items(results, *, source_uri: str) -> list[ConnectorItem]:
    return [ocr_to_item(r, source_uri=f"{source_uri}#p{i}") for i, r in enumerate(results)]
