"""ONNX Runtime object detector (GPU, offline). Lazy deps; integration-only.

Generic YOLOv8-style single-output postprocessing. Provide a model path + label map.
Optional deps (requirements-vision.txt): onnxruntime-gpu, numpy, pillow.
"""

from __future__ import annotations

from secondbrain.vision.ports import Image, Box


class OnnxObjectDetector:
    name = "onnx"

    def __init__(self, model_path: str, labels: list[str], *, providers: list[str] | None = None,
                 conf_threshold: float = 0.25, input_size: int = 640) -> None:
        try:
            import onnxruntime  # noqa: F401
            import numpy  # noqa: F401
            from PIL import Image as _PILImage  # noqa: F401
        except Exception as exc:  # pragma: no cover - only without optional deps
            raise RuntimeError(
                "OnnxObjectDetector requires optional deps: pip install onnxruntime-gpu numpy pillow "
                "(see requirements-vision.txt)."
            ) from exc
        import onnxruntime
        self.labels = labels
        self.conf_threshold = conf_threshold
        self.input_size = input_size
        self.session = onnxruntime.InferenceSession(
            model_path, providers=providers or ["CUDAExecutionProvider", "CPUExecutionProvider"])

    def detect(self, image: Image) -> list[Box]:  # pragma: no cover - integration path
        import io
        import numpy as np
        from PIL import Image as PILImage

        pil = PILImage.open(io.BytesIO(image.data)).convert("RGB").resize((self.input_size, self.input_size))
        arr = np.asarray(pil, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
        outputs = self.session.run(None, {self.session.get_inputs()[0].name: arr})
        preds = np.squeeze(outputs[0])
        if preds.ndim == 2 and preds.shape[0] < preds.shape[1]:
            preds = preds.T
        boxes: list[Box] = []
        for row in preds:
            cx, cy, w, h = row[:4]
            scores = row[4:]
            cls = int(np.argmax(scores))
            score = float(scores[cls])
            if score < self.conf_threshold:
                continue
            x1, y1 = int(cx - w / 2), int(cy - h / 2)
            x2, y2 = int(cx + w / 2), int(cy + h / 2)
            label = self.labels[cls] if cls < len(self.labels) else str(cls)
            boxes.append(Box(label=label, score=score, xyxy=(x1, y1, x2, y2)))
        return boxes
