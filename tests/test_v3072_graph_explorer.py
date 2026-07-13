from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from secondbrain.native.semantic_explorer import SemanticExplorerService


def _seed_sources(root: Path) -> SemanticExplorerService:
    rag_path = root / "runtime" / "p1_rag" / "rag.sqlite3"
    rag_path.parent.mkdir(parents=True)
    with sqlite3.connect(rag_path) as connection:
        connection.executescript(
            """
            create table documents(
                id text primary key, source text, title text, content_hash text,
                created_at text, metadata_json text
            );
            create table chunks(id text primary key, document_id text, text text);
            """
        )
        metadata = json.dumps(
            {"workspace": "Research", "project": "Atlas", "people": ["Ada"], "tags": ["architecture"]}
        )
        connection.execute(
            "insert into documents values(?,?,?,?,?,?)",
            ("doc-1", "upload", "Atlas Architecture", "hash-1", "2026-07-05T10:15:00Z", metadata),
        )
        connection.execute(
            "insert into chunks values(?,?,?)",
            ("chunk-1", "doc-1", "Ada approved the Atlas architecture."),
        )

    memory_path = root / "runtime" / "native" / "memory_entries.jsonl"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(
        json.dumps(
            {
                "memory_id": "memory-1",
                "content": "Ada owns Project Atlas",
                "kind": "semantic",
                "source": "journal",
                "created_at": "2026-07-06T08:00:00+00:00",
                "project": "Atlas",
                "person": "Ada",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return SemanticExplorerService(root)


def test_all_graph_views_reuse_rag_and_memory(tmp_path: Path) -> None:
    service = _seed_sources(tmp_path)

    views = {
        "entity": service.entity_graph(),
        "relationship": service.relationship_graph(),
        "project": service.project_graph(),
        "people": service.people_graph(),
        "timeline": service.timeline_graph(),
        "evidence": service.evidence_graph(),
    }

    assert all(payload["ok"] for payload in views.values())
    assert any(node["type"] == "project" for node in views["project"]["nodes"])
    assert any(node["type"] == "person" for node in views["people"]["nodes"])
    assert {node["label"] for node in views["timeline"]["nodes"] if node["type"] == "timeline"} == {
        "2026-07-05",
        "2026-07-06",
    }
    assert {node["metadata"]["evidence_kind"] for node in views["evidence"]["nodes"] if node["type"] == "evidence"} == {
        "rag_chunk",
        "memory",
    }
    assert {edge["type"] for edge in views["relationship"]["edges"]} >= {
        "belongs_to_project",
        "mentions_person",
        "occurred_on",
        "supports",
    }


def test_graph_foundation_relationships_include_source_and_confidence(tmp_path: Path) -> None:
    service = _seed_sources(tmp_path)
    export = service.export_json()
    assert export["ok"] is True

    payload = service.relationship_graph(query="atlas")
    edges = payload["edges"]
    assert edges
    assert all("source_ref" in edge for edge in edges)
    assert all("confidence" in edge for edge in edges)


def test_graph_query_api_and_document_preview(tmp_path: Path) -> None:
    service = _seed_sources(tmp_path)
    query = service.graph_query("atlas", relationship_types=["belongs_to", "mentions"]) 
    assert query["ok"] is True
    assert query["non_blocking"] is True

    preview = service.document_relationship_preview("Atlas Architecture")
    assert preview["ok"] is True
    assert preview["nodes"]
    assert preview["edges"]


def test_graph_search_ranks_entities_and_relationship_evidence(tmp_path: Path) -> None:
    service = _seed_sources(tmp_path)

    exact = service.search("Atlas")
    evidence = service.search("approved")
    filtered = service.search("Atlas", node_types=["project"])

    assert exact["ok"] is True
    assert exact["results"][0]["node"]["label"] == "Atlas"
    assert exact["results"][0]["score"] == 100
    assert any(result["node"]["type"] == "evidence" for result in evidence["results"])
    assert {result["node"]["type"] for result in filtered["results"]} == {"project"}
    returned = {node["id"] for node in exact["nodes"]}
    assert all(edge["source"] in returned and edge["target"] in returned for edge in exact["edges"])


def test_graph_explorer_and_snapshot_do_not_create_graph_storage(tmp_path: Path) -> None:
    service = _seed_sources(tmp_path)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}

    payload = service.graph_explorer(view="evidence", query="architecture")
    snapshot = service.snapshot()

    assert payload["ok"] is True
    assert snapshot["version"] == "30.72"
    assert snapshot["storage"] is None
    assert snapshot["graphs"] == ["entity", "relationship", "project", "people", "timeline", "evidence"]
    assert {path.relative_to(tmp_path) for path in tmp_path.rglob("*")} == before


def test_graph_search_requires_a_query(tmp_path: Path) -> None:
    result = SemanticExplorerService(tmp_path).search("  ")
    assert result == {
        "ok": False,
        "status": "query_required",
        "query": "",
        "results": [],
        "nodes": [],
        "edges": [],
    }
