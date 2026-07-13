from __future__ import annotations

import json

from secondbrain.native.knowledge_graph_foundation import (
    GraphQueryAPI,
    KnowledgeGraphFoundation,
    RELATIONSHIP_TYPES,
)


def test_foundation_extracts_entities_and_required_relationship_types(tmp_path):
    foundation = KnowledgeGraphFoundation()
    suggestion = foundation.suggest(
        document_id="doc-1",
        title="Atlas Import Plan",
        text="Markus created the Atlas plan and assigned to Ada. This supersedes Legacy and depends on Security.",
        metadata={"project": "Atlas", "author": "Markus", "tags": ["architecture", "migration"]},
        source="upload",
    )

    payload = suggestion.to_dict()
    assert payload["entities"]
    assert payload["relationships"]

    relationship_types = {row["type"] for row in payload["relationships"]}
    assert relationship_types <= set(RELATIONSHIP_TYPES)
    assert "mentions" in relationship_types
    assert "belongs_to" in relationship_types
    assert "created_by" in relationship_types

    assert all("evidence" in row for row in payload["relationships"])
    assert all("source" in row["evidence"] for row in payload["relationships"])
    assert all(0.0 <= float(row["confidence"]) <= 1.0 for row in payload["relationships"])


def test_foundation_export_json(tmp_path):
    foundation = KnowledgeGraphFoundation()
    suggestion = foundation.suggest(
        document_id="doc-2",
        title="Release Notes",
        text="Project Atlas review approved.",
        metadata={"project": "Atlas", "author": "Ada"},
        source="import",
    )
    target = tmp_path / "graph" / "suggestion.json"
    exported = foundation.export_json(suggestion, target)
    assert exported == target
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["version"] == foundation.VERSION
    assert payload["entities"]


def test_query_api_is_non_blocking_and_filters():
    api = GraphQueryAPI()
    api.update(
        nodes=[
            {"id": "document:1", "label": "Atlas Plan", "type": "document", "metadata": {}},
            {"id": "project:1", "label": "Atlas", "type": "project", "metadata": {}},
        ],
        edges=[
            {
                "id": "edge:1",
                "source": "document:1",
                "target": "project:1",
                "type": "belongs_to",
                "confidence": 0.9,
                "evidence": "Atlas Plan",
                "source_ref": "import",
            }
        ],
    )

    result = api.query("atlas", relationship_types=["belongs_to"])
    assert result["ok"] is True
    assert result["non_blocking"] is True
    assert result["result_count"] >= 1
    assert all(edge["type"] == "belongs_to" for edge in result["edges"])
