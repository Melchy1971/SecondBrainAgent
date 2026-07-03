from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from secondbrain.native.ai_workspace.service import AIWorkspaceService
from secondbrain.native.semantic_explorer import SemanticExplorerService

ROOT = Path(__file__).resolve().parents[1]


def _seed_rag(root: Path) -> None:
    path = root / "runtime" / "p1_rag" / "rag.sqlite3"
    path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            create table documents(id text primary key, source text, title text, content_hash text, created_at text, metadata_json text);
            create table chunks(id text primary key, document_id text, text text);
        """)
        metadata = json.dumps({"tags": ["alpha"], "workspace_id": "w1", "project": "Atlas", "owner": "Ada"})
        connection.execute("insert into documents values(?,?,?,?,?,?)", ("doc1", "upload", "Architektur", "hash1", "2026-07-03", metadata))
        connection.execute("insert into chunks values(?,?,?)", ("chunk1", "doc1", "Architektur fuer Atlas"))


def _seed_memory(root: Path) -> None:
    path = root / "runtime" / "native" / "memory_entries.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"memory_id": "mem1", "content": "Bob arbeitet an Atlas", "kind": "semantic", "source": "journal",
           "created_at": 1, "tags": ["beta"], "workspace_id": "w1", "project": "Atlas", "person": "Bob"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_empty_explorer_is_read_only_and_creates_no_storage(tmp_path):
    payload = SemanticExplorerService(tmp_path).snapshot()
    assert payload["mode"] == "read_only_rag_memory_projection"
    assert payload["storage"] is None
    assert payload["node_count"] == 0
    assert list(tmp_path.rglob("*")) == []


def test_graph_projects_existing_rag_and_memory_metadata(tmp_path):
    _seed_rag(tmp_path); _seed_memory(tmp_path)
    service = SemanticExplorerService(tmp_path)
    graph = service.graph()
    types = {node["type"] for node in graph["nodes"]}
    assert {"document", "memory", "workspace", "project", "person", "tag", "source"}.issubset(types)
    assert {edge["type"] for edge in graph["edges"]} >= {"tagged_as", "belongs_to_workspace", "belongs_to_project", "mentions_person", "sourced_from"}
    assert {source["kind"] for source in graph["data_sources"]} == {"rag", "memory"}


def test_views_search_filters_relationships_and_navigation(tmp_path):
    _seed_rag(tmp_path); _seed_memory(tmp_path)
    service = SemanticExplorerService(tmp_path)
    documents = service.explore(view="documents")
    assert any(node["type"] == "document" for node in documents["nodes"])
    assert any(node["type"] == "tag" for node in documents["nodes"])
    people = service.explore(view="people", query="Ada")
    assert any(node["label"] == "Ada" for node in people["nodes"])
    filtered = service.explore(view="knowledge", node_types=["memory"])
    assert {node["type"] for node in filtered["nodes"]} == {"memory"}
    tagged = service.explore(view="knowledge", tags=["beta"])
    assert [node["type"] for node in tagged["nodes"]] == ["memory"]
    relation = service.explore(view="relationships", relationship_types=["belongs_to_project"])
    assert relation["edges"] and {edge["type"] for edge in relation["edges"]} == {"belongs_to_project"}
    memory_id = next(node["id"] for node in service.graph()["nodes"] if node["type"] == "memory")
    neighborhood = service.neighbors(memory_id)
    assert neighborhood["ok"] is True and len(neighborhood["nodes"]) > 1


def test_ai_workspace_registers_semantic_explorer():
    workspace = AIWorkspaceService(ROOT)
    modules = {module.id: module for module in workspace.snapshot().modules}
    assert modules["semantic"].status == "ready"
    payload = workspace.module_payload("semantic")
    assert payload["mode"] == "read_only_rag_memory_projection"
    assert AIWorkspaceService.VERSION == "v30.50"
