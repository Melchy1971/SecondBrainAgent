from secondbrain.vision.ports import OcrBlock, OcrResult, Image, Label
from secondbrain.vision.ingest import ocr_to_item, SOURCE
from secondbrain.connectors.adapter_contract import ConnectorItem


def test_ocrresult_from_blocks_aggregates():
    r = OcrResult.from_blocks([OcrBlock("Hello", 0.9), OcrBlock("World", 0.7)])
    assert r.text == "Hello\nWorld"
    assert abs(r.mean_confidence - 0.8) < 1e-9


def test_ocr_to_item_is_connector_item():
    r = OcrResult.from_blocks([OcrBlock("Invoice 42", 0.95)])
    item = ocr_to_item(r, source_uri="file:///scan.png", labels=[Label("document", 0.9)])
    assert isinstance(item, ConnectorItem)
    assert item.source == SOURCE
    assert item.title == "Invoice 42"
    assert item.metadata["ocr_mean_confidence"] == 0.95
    assert item.metadata["labels"][0]["name"] == "document"


def test_image_from_path(tmp_path):
    p = tmp_path / "x.png"
    p.write_bytes(b"\x89PNG\r\n")
    img = Image.from_path(p)
    assert img.mime_type == "image/png" and img.data.startswith(b"\x89PNG")
