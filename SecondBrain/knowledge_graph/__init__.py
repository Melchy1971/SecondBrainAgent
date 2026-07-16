"""Knowledge graph package exports."""

from .runtime import KnowledgeGraphRuntime
from .service import KnowledgeGraph
from .persistence import KnowledgeGraphSnapshotRepository

# Stable public service names used by release gates and integrations.
KnowledgeGraphService = KnowledgeGraph
GraphService = KnowledgeGraph

__all__ = [
    "KnowledgeGraphRuntime",
    "KnowledgeGraph",
    "KnowledgeGraphService",
    "GraphService",
    "KnowledgeGraphSnapshotRepository",
]
