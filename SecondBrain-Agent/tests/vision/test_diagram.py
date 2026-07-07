from secondbrain.vision.diagram import (
    build_diagram, DiagramAnalyzer, InMemoryKnowledgeGraph,
)
from secondbrain.vision.ports import Box, OcrResult, OcrBlock, Image
from secondbrain.vision.engines.fake import FakeOcrEngine, FakeObjectDetector
from secondbrain.connectors.import_bridge import InMemoryImportJobSink


def test_build_diagram_nodes_edges_and_text():
    boxes = [Box("node", 0.9, (0, 0, 50, 50)), Box("node", 0.9, (0, 200, 50, 250)),
             Box("arrow", 0.8, (25, 50, 25, 200))]
    ocr = OcrResult.from_blocks([OcrBlock("Start", 0.9, (10, 10, 20, 10)),
                                 OcrBlock("End", 0.9, (10, 210, 20, 10))])
    g = build_diagram(boxes, ocr)
    assert [n.label for n in g.nodes] == ["Start", "End"]
    assert len(g.edges) == 1
    assert (g.edges[0].source, g.edges[0].target, g.edges[0].kind) == ("n0", "n1", "arrow")


def test_no_self_edges_when_connector_touches_one_node():
    boxes = [Box("node", 0.9, (0, 0, 100, 100)), Box("arrow", 0.8, (10, 10, 20, 20))]
    g = build_diagram(boxes, OcrResult.from_blocks([]))
    assert g.nodes[0].label == "node"  # fallback to kind
    assert g.edges == []


def test_analyzer_ingests_and_populates_kg():
    detector = FakeObjectDetector(boxes=[Box("node", 0.9, (0, 0, 50, 50)),
                                         Box("node", 0.9, (0, 200, 50, 250)),
                                         Box("arrow", 0.8, (25, 50, 25, 200))])
    sink = InMemoryImportJobSink()
    kg = InMemoryKnowledgeGraph()
    analyzer = DiagramAnalyzer(detector, FakeOcrEngine(""), sink=sink, kg=kg)
    result = analyzer.analyze_image(Image(data=b"x", source_uri="file:///d.png"))
    assert len(result["graph"]["nodes"]) == 2
    assert len(result["graph"]["edges"]) == 1
    assert result["import"]["imported"] == 1
    assert len(kg.nodes) == 2 and len(kg.edges) == 1
    assert len(sink.jobs) == 1
