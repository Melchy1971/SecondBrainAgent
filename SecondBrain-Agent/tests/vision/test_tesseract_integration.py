import pytest

# Integration test: only runs where the optional engine + system binary exist.
pytest.importorskip("pytesseract", reason="vision optional deps not installed (requirements-vision.txt)")
pytest.importorskip("PIL", reason="pillow not installed")


def test_tesseract_engine_constructs():
    from secondbrain.vision.engines.tesseract_ocr import TesseractOcrEngine
    engine = TesseractOcrEngine()
    assert engine.name == "tesseract"
