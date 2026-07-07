"""Read-only graph views over the existing RAG and Memory data."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from secondbrain.native.memory_explorer import MemoryExplorer


VIEW_TYPES: dict[str, set[str] | None] = {
    "knowledge": None,
    "entities": {"document", "memory", "workspace", "project", "person", "tag"},
    "documents": {"document"},
    "workspaces": {"workspace"},
    "memory": {"memory"},
    "people": {"person"},
    "projects": {"project"},
    "tags": {"tag"},
    "relationships": None,
    "timeline": {"timeline"},
    "evidence": {"evidence"},
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

    VERSION = "30.72"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.rag_path = self.project_root / "runtime" / "p1_rag" / "rag.sqlite3"

    def graph(self, *, include_evidence=False, evidence_query="", evidence_limit=5000) -> dict[str, Any]:
        nodes: dict[str, dict[str, Any]] = {}
        edges: dict[str, dict[str, Any]] = {}
        data_sources: list[dict[str, Any]] = []
        safe_evidence_limit = max(1, min(int(evidence_limit), 5000))
        self._read_rag(nodes, edges, data_sources, include_evidence, evidence_query, safe_evidence_limit)
        self._read_memory(nodes, edges, data_sources, include_evidence, evidence_query, safe_evidence_limit)
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

    def _timeline_edge(self, nodes, edges, owner_id: str, value: Any, source_ref: str) -> None:
        """Project a timestamp onto a shared UTC calendar-day node."""
        if value in (None, ""):
            return
        normalized = ""
        try:
            if isinstance(value, (int, float)):
                normalized = datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
            else:
                text = str(value).strip()
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                normalized = parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc).isoformat()
        except (OverflowError, OSError, TypeError, ValueError):
            return
        day = normalized[:10]
        node_id = f"timeline:{day}"
        self._node(nodes, node_id, day, "timeline", source=source_ref, metadata={"date": day})
        self._edge(edges, owner_id, node_id, "occurred_on", source_ref=source_ref, evidence=normalized)

    def _evidence_node(self, nodes, edges, owner_id: str, evidence_id: str, text: str, source_ref: str, metadata: dict[str, Any]) -> None:
        label = " ".join(str(text).split())[:100] or evidence_id
        node_id = f"evidence:{evidence_id}"
        self._node(nodes, node_id, label, "evidence", source=source_ref, metadata=metadata)
        self._edge(edges, node_id, owner_id, "supports", source_ref=source_ref, evidence=label)

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

    def _read_rag(self, nodes, edges, data_sources, include_evidence: bool, evidence_query: str, evidence_limit: int) -> None:
        rows: list[dict[str, Any]] = []
        chunks: list[dict[str, Any]] = []
        chunk_count = 0
        error = ""
        if self.rag_path.exists():
            try:
                uri = f"file:{self.rag_path.resolve().as_posix()}?mode=ro"
                with sqlite3.connect(uri, uri=True) as connection:
                    connection.row_factory = sqlite3.Row
                    query = "select d.*, count(c.id) as chunks from documents d left join chunks c on c.document_id=d.id group by d.id"
                    rows = [dict(row) for row in connection.execute(query).fetchall()]
                    chunk_columns = {str(row[1]) for row in connection.execute("pragma table_info(chunks)").fetchall()}
                    if include_evidence and {"id", "document_id", "text"}.issubset(chunk_columns):
                        chunk_count = int(connection.execute("select count(*) from chunks").fetchone()[0])
                        if evidence_query:
                            chunk_query = "select id, document_id, text from chunks where instr(lower(text), ?) > 0 order by document_id, id limit ?"
                            parameters = (evidence_query.lower(), evidence_limit)
                        else:
                            chunk_query = "select id, document_id, text from chunks order by document_id, id limit ?"
                            parameters = (evidence_limit,)
                        chunks = [dict(row) for row in connection.execute(chunk_query, parameters).fetchall()]
            except (sqlite3.Error, OSError) as exc:
                error = str(exc)
        data_sources.append({"kind": "rag", "path": str(self.rag_path), "exists": self.rag_path.exists(), "records": len(rows),
                             "evidence_records": len(chunks), "evidence_total": chunk_count,
                             "evidence_truncated": chunk_count > len(chunks) and not evidence_query, "read_only": True, "error": error})
        document_sources: dict[str, str] = {}
        for row in rows:
            raw_metadata = row.get("metadata_json") or "{}"
            try:
                parsed = json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata
                metadata = dict(parsed) if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError, ValueError):
                metadata = {}
            document_id = f"document:{row['id']}"
            source = str(row.get("source") or "rag")
            document_sources[str(row["id"])] = source
            self._node(nodes, document_id, str(row.get("title") or row["id"]), "document", source=source,
                       metadata={**metadata, "document_id": row["id"], "chunks": int(row.get("chunks") or 0), "content_hash": row.get("content_hash")})
            self._source_node(nodes, edges, document_id, source)
            self._metadata_edges(nodes, edges, document_id, metadata, source)
            self._timeline_edge(nodes, edges, document_id, row.get("created_at"), source)
        for chunk in chunks:
            raw_document_id = str(chunk.get("document_id") or "")
            owner_id = f"document:{raw_document_id}"
            if owner_id not in nodes:
                continue
            source = document_sources.get(raw_document_id, "rag")
            text = str(chunk.get("text") or "")
            self._evidence_node(nodes, edges, owner_id, f"rag:{chunk['id']}", text, source,
                                {"evidence_kind": "rag_chunk", "chunk_id": chunk["id"], "document_id": raw_document_id})

    def _read_memory(self, nodes, edges, data_sources, include_evidence: bool, evidence_query: str, evidence_limit: int) -> None:
        explorer = MemoryExplorer(self.project_root, ensure_dirs=False)
        rows = explorer.entries(include_archived=True, limit=100_000)["memories"]
        source_rows = explorer.sources()
        data_sources.extend({"kind": "memory", "path": row["path"], "exists": row["exists"], "records": row["entries"], "read_only": True} for row in source_rows)
        evidence_count = 0
        for row in rows:
            memory_id = f"memory:{row['memory_id']}"
            source = str(row.get("source") or "memory")
            label = str(row.get("content") or row["memory_id"]).strip().replace("\n", " ")[:100]
            metadata = {**dict(row.get("metadata") or {}), **row}
            self._node(nodes, memory_id, label, "memory", source=source, metadata=metadata)
            self._source_node(nodes, edges, memory_id, source)
            self._metadata_edges(nodes, edges, memory_id, metadata, source)
            self._timeline_edge(nodes, edges, memory_id, row.get("created_at"), source)
            content = str(row.get("content") or "")
            if include_evidence and evidence_count < evidence_limit and (not evidence_query or evidence_query.lower() in content.lower()):
                self._evidence_node(nodes, edges, memory_id, f"memory:{row['memory_id']}", content, source,
                                    {"evidence_kind": "memory", "memory_id": row["memory_id"]})
                evidence_count += 1

    def explore(self, *, view="knowledge", query="", node_types=(), relationship_types=(), sources=(), tags=(), limit=500) -> dict[str, Any]:
        if view not in VIEW_TYPES:
            raise ValueError(f"unknown semantic view: {view}")
        include_evidence = view in {"evidence", "relationships"}
        graph = self.graph(include_evidence=include_evidence,
                           evidence_query=query if view == "evidence" else "", evidence_limit=limit)
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

    def entity_graph(self, **filters: Any) -> dict[str, Any]:
        return self.explore(view="entities", **filters)

    def relationship_graph(self, **filters: Any) -> dict[str, Any]:
        return self.explore(view="relationships", **filters)

    def project_graph(self, **filters: Any) -> dict[str, Any]:
        return self.explore(view="projects", **filters)

    def people_graph(self, **filters: Any) -> dict[str, Any]:
        return self.explore(view="people", **filters)

    def timeline_graph(self, **filters: Any) -> dict[str, Any]:
        return self.explore(view="timeline", **filters)

    def evidence_graph(self, **filters: Any) -> dict[str, Any]:
        return self.explore(view="evidence", **filters)

    def graph_explorer(self, **filters: Any) -> dict[str, Any]:
        """Stable API used by the embedded AI Workspace explorer."""
        return self.explore(**filters)

    def search(self, query: str, *, node_types=(), relationship_types=(), limit=50) -> dict[str, Any]:
        """Rank graph nodes and relationships without building another search index."""
        term = query.strip().lower()
        if not term:
            return {"ok": False, "status": "query_required", "query": "", "results": [], "nodes": [], "edges": []}
        graph = self.graph(include_evidence=True, evidence_query=term,
                           evidence_limit=max(500, min(int(limit) * 10, 5000)))
        nodes = {row["id"]: row for row in graph["nodes"]}
        wanted_nodes, wanted_edges = set(node_types), set(relationship_types)
        related: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in nodes}
        scores: dict[str, int] = {}
        for edge in graph["edges"]:
            if wanted_edges and edge["type"] not in wanted_edges:
                continue
            related.get(edge["source"], []).append(edge)
            related.get(edge["target"], []).append(edge)
            edge_text = f"{edge['type']} {edge['evidence']} {edge['source_ref']}".lower()
            if term in edge_text:
                scores[edge["source"]] = max(scores.get(edge["source"], 0), 35)
                scores[edge["target"]] = max(scores.get(edge["target"], 0), 35)
        for node_id, node in nodes.items():
            if wanted_nodes and node["type"] not in wanted_nodes:
                continue
            label = node["label"].lower()
            metadata = json.dumps(node["metadata"], ensure_ascii=False, default=str).lower()
            sources_text = " ".join(node["sources"]).lower()
            score = 100 if label == term else 80 if label.startswith(term) else 60 if term in label else 25 if term in metadata or term in sources_text else 0
            if score:
                scores[node_id] = max(scores.get(node_id, 0), score)
        if wanted_nodes:
            scores = {node_id: score for node_id, score in scores.items() if nodes[node_id]["type"] in wanted_nodes}
        ranked = sorted(((score, node_id) for node_id, score in scores.items() if node_id in nodes), key=lambda item: (-item[0], nodes[item[1]]["label"].lower(), item[1]))
        ranked = ranked[:max(1, min(int(limit), 500))]
        selected = {node_id for _, node_id in ranked}
        selected_edges = [edge for edge in graph["edges"] if edge["source"] in selected and edge["target"] in selected]
        results = [{"score": score, "node": nodes[node_id], "relationships": related.get(node_id, [])} for score, node_id in ranked]
        return {"ok": True, "version": self.VERSION, "query": term, "results": results,
                "nodes": [nodes[node_id] for _, node_id in ranked], "edges": selected_edges,
                "result_count": len(results), "data_sources": graph["data_sources"]}

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
                "graphs": ["entity", "relationship", "project", "people", "timeline", "evidence"],
                "capabilities": ["graph_search", "graph_explorer"],
                "available": self._available(graph), "data_sources": graph["data_sources"]}
