"""v30.72 Knowledge Graph - node/edge/graph model.

The graph is a read-only projection computed from existing Memory (and RAG) at
query time. It is never persisted - "keine neue Datenhaltung".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

# Node types.
N_ENTITY = "entity"
N_PERSON = "person"
N_PROJECT = "project"
N_MEMORY = "memory"
N_SOURCE = "source"
N_EVENT = "event"
N_DATE = "date"

# Common relations.
R_CO_OCCURS = "co_occurs"
R_MENTIONS = "mentions"
R_MEMBER_OF = "member_of"
R_RELATED_TO = "related_to"
R_NEXT = "next"
R_ON_DATE = "on_date"
R_SOURCED_FROM = "sourced_from"


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "label": self.label, "metadata": self.metadata}


@dataclass
class Edge:
    source: str
    target: str
    relation: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.source, self.target, self.relation)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Graph:
    def __init__(self, kind: str = "graph"):
        self.kind = kind
        self.nodes: dict[str, Node] = {}
        self._edges: dict[tuple[str, str, str], Edge] = {}

    # -- mutation ----------------------------------------------------------
    def add_node(self, node_id: str, type: str, label: str = "", **metadata) -> Node:
        existing = self.nodes.get(node_id)
        if existing is not None:
            if metadata:
                merged = {**existing.metadata, **metadata}
                self.nodes[node_id] = Node(existing.id, existing.type, existing.label or label, merged)
            return self.nodes[node_id]
        node = Node(node_id, type, label or node_id, dict(metadata))
        self.nodes[node_id] = node
        return node

    def add_edge(self, source: str, target: str, relation: str, *, weight: float = 1.0,
                 **metadata) -> Edge:
        key = (source, target, relation)
        if key in self._edges:
            edge = self._edges[key]
            edge.weight += weight            # accumulate co-occurrence weight
            return edge
        edge = Edge(source, target, relation, weight=weight, metadata=dict(metadata))
        self._edges[key] = edge
        return edge

    # -- access ------------------------------------------------------------
    @property
    def edges(self) -> list[Edge]:
        return list(self._edges.values())

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def neighbors(self, node_id: str) -> list[str]:
        out: list[str] = []
        for edge in self._edges.values():
            if edge.source == node_id and edge.target not in out:
                out.append(edge.target)
            elif edge.target == node_id and edge.source not in out:
                out.append(edge.source)
        return out

    def nodes_of_type(self, node_type: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.type == node_type]

    def degree(self, node_id: str) -> int:
        return sum(1 for e in self._edges.values() if node_id in (e.source, e.target))

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "node_count": len(self.nodes),
            "edge_count": len(self._edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }

    def subgraph(self, node_ids: Iterable[str]) -> "Graph":
        keep = set(node_ids)
        g = Graph(f"{self.kind}:subgraph")
        for nid in keep:
            if nid in self.nodes:
                n = self.nodes[nid]
                g.add_node(n.id, n.type, n.label, **n.metadata)
        for edge in self._edges.values():
            if edge.source in keep and edge.target in keep:
                g.add_edge(edge.source, edge.target, edge.relation, weight=edge.weight, **edge.metadata)
        return g
