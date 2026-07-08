import pytest
pytest.importorskip("onnxruntime", reason="vision optional dep 'onnxruntime' not installed")
pytest.importorskip("numpy")


def test_onnx_detector_requires_model(tmp_path):
    from secondbrain.vision.engines.onnx_detector import OnnxObjectDetector
    with pytest.raises(Exception):
        OnnxObjectDetector(str(tmp_path / "missing.onnx"), ["node", "arrow"])
