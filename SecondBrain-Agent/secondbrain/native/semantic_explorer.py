"""v30.50 read-only semantic views over existing RAG and Memory data."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from secondbrain.native.memory_explorer import MemoryExplorer


VIEW_TYPES: dict[str, set[str] | None] = {
    "knowledge": None,
    "documents": {"document"},
    "workspaces": {"workspace"},
    "memory": {"memory"},
    "people": {"person"},
    "projects": {"project"},
    "tags": {"tag"},
    "relationships": None,
    "sources": {"source"},
}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def _values(metadata: dict[str, Any], keys: Iterable[str]) -> list[str]:
    result: list[str] = []
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str):
            result.extend(part.strip() for part in value.replace(";", ",").split(",") if part.strip())
        elif isinstance(value, (list, tuple, set)):
            result.extend(str(part).strip() for part in value if str(part).strip())
    return list(dict.fromkeys(result))


class SemanticExplorerService:
    """Builds an in-memory projection without creating an index or graph store."""

    VERSION = "30.50"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.rag_path = self.project_root / "runtime" / "p1_rag" / "rag.sqlite3"

    def graph(self) -> dict[str, Any]:
        nodes: dict[str, dict[str, Any]] = {}
        edges: dict[str, dict[str, Any]] = {}
        data_sources: list[dict[str, Any]] = []
        self._read_rag(nodes, edges, data_sources)
        self._read_memory(nodes, edges, data_sources)
        return {
            "nodes": sorted(nodes.values(), key=lambda row: (row["type"], row["label"].lower(), row["id"])),
            "edges": sorted(edges.values(), key=lambda row: (row["type"], row["source"], row["target"])),
            "data_sources": data_sources,
        }

    def _node(self, nodes: dict[str, dict[str, Any]], node_id: str, label: str, kind: str, *, source="", metadata=None) -> str:
        current = nodes.get(node_id)
        sources = sorted({*(current.get("sources", []) if current else []), *([source] if source else [])})
        merged = {**(current.get("metadata", {}) if current else {}), **(metadata or {})}
        nodes[node_id] = {"id": node_id, "label": label or node_id, "type": kind or "concept", "sources": sources, "metadata": merged}
        return node_id

    def _edge(self, edges: dict[str, dict[str, Any]], source: str, target: str, kind: str, *, source_ref="", evidence="") -> None:
        if not source or not target or source == target:
            return
        edge_id = f"edge:{_hash(f'{source}|{target}|{kind}|{source_ref}')}"
        edges[edge_id] = {"id": edge_id, "source": source, "target": target, "type": kind or "related_to", "source_ref": source_ref, "evidence": evidence}

    def _source_node(self, nodes, edges, owner_id: str, source: str) -> None:
        if not source:
            return
        node_id = f"source:{_hash(source)}"
        self._node(nodes, node_id, source, "source", source=source)
        self._edge(edges, owner_id, node_id, "sourced_from", source_ref=source)

    def _metadata_edges(self, nodes, edges, owner_id: str, metadata: dict[str, Any], source_ref: str) -> None:
        groups = (
            ("tag", ("tags", "tag"), "tagged_as"),
            ("workspace", ("workspace", "workspace_id"), "belongs_to_workspace"),
            ("project", ("project", "project_id", "projects"), "belongs_to_project"),
            ("person", ("person", "people", "persons", "owner", "author", "participants"), "mentions_person"),
        )
        for kind, keys, relation in groups:
            for value in _values(metadata, keys):
                node_id = f"{kind}:{_hash(value.lower())}"
                self._node(nodes, node_id, value, kind, source=source_ref)
                self._edge(edges, owner_id, node_id, relation, source_ref=source_ref)

    def _read_rag(self, nodes, edges, data_sources) -> None:
        rows: list[dict[str, Any]] = []
        error = ""
        if self.rag_path.exists():
            try:
                uri = f"file:{self.rag_path.resolve().as_posix()}?mode=ro"
                with sqlite3.connect(uri, uri=True) as connection:
                    connection.row_factory = sqlite3.Row
                    query = "select d.*, count(c.id) as chunks from documents d left join chunks c on c.document_id=d.id group by d.id"
                    rows = [dict(row) for row in connection.execute(query).fetchall()]
            except (sqlite3.Error, OSError) as exc:
                error = str(exc)
        data_sources.append({"kind": "rag", "path": str(self.rag_path), "exists": self.rag_path.exists(), "records": len(rows), "read_only": True, "error": error})
        for row in rows:
            raw_metadata = row.get("metadata_json") or "{}"
            try:
                parsed = json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata
                metadata = dict(parsed) if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError, ValueError):
                metadata = {}
            document_id = f"document:{row['id']}"
            source = str(row.get("source") or "rag")
            self._node(nodes, document_id, str(row.get("title") or row["id"]), "document", source=source,
                       metadata={**metadata, "document_id": row["id"], "chunks": int(row.get("chunks") or 0), "content_hash": row.get("content_hash")})
            self._source_node(nodes, edges, document_id, source)
            self._metadata_edges(nodes, edges, document_id, metadata, source)

    def _read_memory(self, nodes, edges, data_sources) -> None:
        explorer = MemoryExplorer(self.project_root, ensure_dirs=False)
        rows = explorer.entries(include_archived=True, limit=100_000)["memories"]
        source_rows = explorer.sources()
        data_sources.extend({"kind": "memory", "path": row["path"], "exists": row["exists"], "records": row["entries"], "read_only": True} for row in source_rows)
        for row in rows:
            memory_id = f"memory:{row['memory_id']}"
            source = str(row.get("source") or "memory")
            label = str(row.get("content") or row["memory_id"]).strip().replace("\n", " ")[:100]
            metadata = {**dict(row.get("metadata") or {}), **row}
            self._node(nodes, memory_id, label, "memory", source=source, metadata=metadata)
            self._source_node(nodes, edges, memory_id, source)
            self._metadata_edges(nodes, edges, memory_id, metadata, source)

    def explore(self, *, view="knowledge", query="", node_types=(), relationship_types=(), sources=(), tags=(), limit=500) -> dict[str, Any]:
        if view not in VIEW_TYPES:
            raise ValueError(f"unknown semantic view: {view}")
        graph = self.graph()
        all_nodes = {row["id"]: row for row in graph["nodes"]}
        all_edges = graph["edges"]
        anchor_types = VIEW_TYPES[view]
        selected = {node_id for node_id, row in all_nodes.items() if anchor_types is None or row["type"] in anchor_types}
        query = query.strip().lower()
        wanted_types, wanted_relations = set(node_types), set(relationship_types)
        wanted_sources, wanted_tags = set(sources), {str(tag).lower() for tag in tags}
        def matches(row: dict[str, Any]) -> bool:
            text = f"{row['label']} {row['type']} {' '.join(row['sources'])} {json.dumps(row['metadata'], ensure_ascii=False)}".lower()
            if query and query not in text: return False
            if wanted_types and row["type"] not in wanted_types: return False
            if wanted_sources and not wanted_sources.intersection(row["sources"]): return False
            row_tags = {str(tag).lower() for tag in row["metadata"].get("tags", [])}
            if wanted_tags and not wanted_tags.issubset(row_tags): return False
            return True
        selected = {node_id for node_id in selected if matches(all_nodes[node_id])}
        candidate_edges = [row for row in all_edges if not wanted_relations or row["type"] in wanted_relations]
        context = set(selected)
        if not (wanted_types or wanted_sources or wanted_tags):
            for edge in candidate_edges:
                if edge["source"] in selected or edge["target"] in selected:
                    context.update((edge["source"], edge["target"]))
        limited_ids = set(sorted(context)[:max(1, min(int(limit), 5000))])
        nodes = [all_nodes[node_id] for node_id in limited_ids if node_id in all_nodes]
        edges = [row for row in candidate_edges if row["source"] in limited_ids and row["target"] in limited_ids]
        return {"ok": True, "version": self.VERSION, "view": view, "query": query, "nodes": nodes, "edges": edges,
                "node_count": len(nodes), "edge_count": len(edges), "filters": {"node_types": sorted(wanted_types), "relationship_types": sorted(wanted_relations), "sources": sorted(wanted_sources), "tags": sorted(wanted_tags)},
                "available": self._available(graph), "data_sources": graph["data_sources"]}

    def neighbors(self, node_id: str, depth=1) -> dict[str, Any]:
        graph = self.graph()
        nodes = {row["id"]: row for row in graph["nodes"]}
        if node_id not in nodes:
            return {"ok": False, "status": "node_not_found", "node_id": node_id}
        edges, selected, frontier = graph["edges"], {node_id}, {node_id}
        for _ in range(max(1, min(int(depth), 5))):
            next_frontier = set()
            for edge in edges:
                if edge["source"] in frontier: next_frontier.add(edge["target"])
                if edge["target"] in frontier: next_frontier.add(edge["source"])
            frontier = next_frontier - selected
            selected.update(next_frontier)
        return {"ok": True, "root": node_id, "nodes": [nodes[item] for item in selected],
                "edges": [edge for edge in edges if edge["source"] in selected and edge["target"] in selected]}

    @staticmethod
    def _available(graph: dict[str, Any]) -> dict[str, list[str]]:
        return {"views": list(VIEW_TYPES), "node_types": sorted({row["type"] for row in graph["nodes"]}),
                "relationship_types": sorted({row["type"] for row in graph["edges"]}),
                "sources": sorted({source for row in graph["nodes"] for source in row["sources"]}),
                "tags": sorted({row["label"] for row in graph["nodes"] if row["type"] == "tag"})}

    def snapshot(self) -> dict[str, Any]:
        graph = self.graph()
        counts = Counter(row["type"] for row in graph["nodes"])
        return {"ok": True, "version": self.VERSION, "mode": "read_only_rag_memory_projection", "storage": None,
                "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]), "by_type": dict(sorted(counts.items())),
                "available": self._available(graph), "data_sources": graph["data_sources"]}
