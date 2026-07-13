from secondbrain.vision.pipeline import VisionPipeline
from secondbrain.vision.engines.fake import FakeOcrEngine, FakeClassifier, FakeScreenSource
from secondbrain.vision.ports import Image
from secondbrain.connectors.import_bridge import InMemoryImportJobSink


def test_pipeline_ocrs_and_ingests_into_sink():
    sink = InMemoryImportJobSink()
    pipe = VisionPipeline(FakeOcrEngine("Meeting notes\nline two"), sink=sink, classifier=FakeClassifier())
    result = pipe.process_image(Image(data=b"img", source_uri="file:///a.png"))
    assert result["ocr"]["blocks"] == 2
    assert result["import"]["imported"] == 1
    assert result["labels"][0]["name"] == "document"
    assert len(sink.jobs) == 1


def test_pipeline_screenshot_source():
    pipe = VisionPipeline(FakeOcrEngine("desktop text"))
    result = pipe.process_screenshot(FakeScreenSource())
    assert result["source_uri"] == "screenshot://capture"
    assert result["import"]["imported"] == 1


def test_duplicate_scan_is_idempotent():
    sink = InMemoryImportJobSink()
    pipe = VisionPipeline(FakeOcrEngine("same"), sink=sink)
    img = Image(data=b"img", source_uri="file:///same.png")
    first = pipe.process_image(img)
    second = pipe.process_image(img)
    assert first["import"]["imported"] == 1
    assert second["import"]["skipped"] == 1  # same content_hash -> deduped by sink
    assert len(sink.jobs) == 1
