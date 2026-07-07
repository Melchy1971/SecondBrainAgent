from secondbrain.vision.desktop import DesktopAnalyzer
from secondbrain.vision.engines.fake import FakeOcrEngine, FakeScreenSource
from secondbrain.vision.classify import HeuristicTextClassifier
from secondbrain.vision.ports import Image
from secondbrain.connectors.import_bridge import InMemoryImportJobSink


def test_analyze_image_classifies_and_ingests():
    sink = InMemoryImportJobSink()
    analyzer = DesktopAnalyzer(FakeOcrEngine("INVOICE\nAmount due 99\nIBAN DE"), sink=sink,
                               text_classifier=HeuristicTextClassifier())
    result = analyzer.analyze_image(Image(data=b"x", source_uri="file:///a.png"))
    assert result["top_class"] == "invoice"
    assert result["import"]["imported"] == 1
    assert len(sink.jobs) == 1


def test_analyze_screen_and_watch():
    analyzer = DesktopAnalyzer(FakeOcrEngine("From: a@b\nSubject: hi"),
                               screen=FakeScreenSource(), text_classifier=HeuristicTextClassifier())
    single = analyzer.analyze_screen()
    assert single["source_uri"] == "screenshot://desktop"
    runs = analyzer.watch(1.0, stop=lambda: False, sleeper=lambda _s: None, max_cycles=3)
    assert len(runs) == 3


def test_analyze_screen_without_source_raises():
    import pytest
    analyzer = DesktopAnalyzer(FakeOcrEngine("x"))
    with pytest.raises(RuntimeError):
        analyzer.analyze_screen()
