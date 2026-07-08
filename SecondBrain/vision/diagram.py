"""Offline diagram structure extraction: detections + OCR -> node/edge graph.

Deterministic and stdlib-only (given detector output + OCR result), so it is fully
unit-testable green. No VLM required. Feeds a Knowledge Graph via KnowledgeGraphSink
and Memory/RAG via the existing ConnectorImportBridge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from secondbrain.connectors.adapter_contract import ConnectorItem
from secondbrain.connectors.import_bridge import ConnectorImportBridge, ImportJobSink, InMemoryImportJobSink
from secondbrain.vision.ports import Box, OcrResult, OcrEngine, ObjectDetector, Image
from datetime import datetime, timezone
from hashlib import sha256

NODE_LABELS = {"node", "box", "process", "decision", "start", "end", "state", "entity", "rectangle", "ellipse"}
EDGE_LABELS = {"arrow", "edge", "line", "connector", "link"}


@dataclass(frozen=True)
class DiagramNode:
    id: str
    label: str
    kind: str
    box: tuple[int, int, int, int]


@dataclass(frozen=True)
class DiagramEdge:
    source: str
    target: str
    kind: str = "arrow"


@dataclass(frozen=True)
class DiagramGraph:
    nodes: list[DiagramNode] = field(default_factory=list)
    edges: list[DiagramEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [{"id": n.id, "label": n.label, "kind": n.kind, "box": list(n.box)} for n in self.nodes],
            "edges": [{"source": e.source, "target": e.target, "kind": e.kind} for e in self.edges],
        }


@runtime_checkable
class KnowledgeGraphSink(Protocol):
    def add_nodes(self, nodes: list[dict]) -> None: ...
    def add_edges(self, edges: list[dict]) -> None: ...


class InMemoryKnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: list[dict] = []
        self.edges: list[dict] = []

    def add_nodes(self, nodes: list[dict]) -> None:
        self.nodes.extend(nodes)

    def add_edges(self, edges: list[dict]) -> None:
        self.edges.extend(edges)


# ---- geometry helpers -----------------------------------------------------
def _center_xyxy(b: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = b
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _wh_to_xyxy(bbox) -> tuple[int, int, int, int]:
    x, y, w, h = bbox
    return (x, y, x + w, y + h)


def _inside(px: float, py: float, box: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = box
    return x1 <= px <= x2 and y1 <= py <= y2


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def build_diagram(boxes: list[Box], ocr: OcrResult) -> DiagramGraph:
    node_boxes = [b for b in boxes if b.label.lower() in NODE_LABELS]
    edge_boxes = [b for b in boxes if b.label.lower() in EDGE_LABELS]

    nodes: list[DiagramNode] = []
    for i, b in enumerate(node_boxes):
        texts = []
        for blk in ocr.blocks:
            if not blk.bbox:
                continue
            cx, cy = _center_xyxy(_wh_to_xyxy(blk.bbox))
            if _inside(cx, cy, b.xyxy):
                texts.append(blk.text)
        label = " ".join(t for t in texts if t.strip()) or b.label.lower()
        nodes.append(DiagramNode(id=f"n{i}", label=label, kind=b.label.lower(), box=b.xyxy))

    def nearest(point: tuple[float, float]) -> str | None:
        if not nodes:
            return None
        return min(nodes, key=lambda n: _dist(point, _center_xyxy(n.box))).id

    edges: list[DiagramEdge] = []
    for eb in edge_boxes:
        x1, y1, x2, y2 = eb.xyxy
        src = nearest((x1, y1))
        dst = nearest((x2, y2))
        if src and dst and src != dst:
            edges.append(DiagramEdge(source=src, target=dst, kind=eb.label.lower()))
    return DiagramGraph(nodes=nodes, edges=edges)


def diagram_to_item(graph: DiagramGraph, *, source_uri: str) -> ConnectorItem:
    lines = [f"[{n.kind}] {n.label}" for n in graph.nodes]
    lines += [f"{e.source} -{e.kind}-> {e.target}" for e in graph.edges]
    content = "\n".join(lines) or "(empty diagram)"
    ext = sha256(f"{source_uri}\n{content}".encode("utf-8")).hexdigest()
    return ConnectorItem(
        external_id=ext, source="vision_diagram",
        title=f"Diagram: {len(graph.nodes)} nodes / {len(graph.edges)} edges",
        content=content, updated_at=datetime.now(timezone.utc), uri=source_uri,
        metadata={"nodes": len(graph.nodes), "edges": len(graph.edges)},
    )


class DiagramAnalyzer:
    def __init__(self, detector: ObjectDetector, ocr: OcrEngine, *,
                 sink: ImportJobSink | None = None, kg: KnowledgeGraphSink | None = None) -> None:
        self.detector = detector
        self.ocr = ocr
        self.sink = sink or InMemoryImportJobSink()
        self.kg = kg or InMemoryKnowledgeGraph()

    def analyze_image(self, image: Image, *, source_uri: str | None = None, lang: str = "eng") -> dict[str, Any]:
        uri = source_uri or image.source_uri or "image://inline"
        boxes = self.detector.detect(image)
        ocr = self.ocr.recognize(image, lang=lang)
        graph = build_diagram(boxes, ocr)
        gd = graph.to_dict()
        self.kg.add_nodes(gd["nodes"])
        self.kg.add_edges(gd["edges"])
        item = diagram_to_item(graph, source_uri=uri)
        bridge = ConnectorImportBridge(sink=self.sink)
        bridge.process_item(item)
        return {"source_uri": uri, "graph": gd, "item": item.external_id, "import": bridge.snapshot()}
