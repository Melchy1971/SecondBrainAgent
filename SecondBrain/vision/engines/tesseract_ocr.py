"""Tesseract OCR adapter (offline). Lazy-imports optional deps; integration-only.

Optional deps (see requirements-vision.txt): pytesseract, pillow, and the system
`tesseract` binary. Kept out of the standard import path so core tests need no models.
"""

from __future__ import annotations

import io

from secondbrain.vision.ports import Image, OcrBlock, OcrResult


class TesseractOcrEngine:
    name = "tesseract"

    def __init__(self, *, min_confidence: float = 0.0) -> None:
        self.min_confidence = min_confidence
        try:
            import pytesseract  # noqa: F401
            from PIL import Image as _PILImage  # noqa: F401
        except Exception as exc:  # pragma: no cover - exercised only without deps
            raise RuntimeError(
                "TesseractOcrEngine requires optional deps: pip install -r requirements-vision.txt "
                "and the system 'tesseract' binary."
            ) from exc

    def recognize(self, image: Image, *, lang: str = "eng") -> OcrResult:
        import pytesseract
        from PIL import Image as PILImage

        pil = PILImage.open(io.BytesIO(image.data))
        data = pytesseract.image_to_data(pil, lang=lang, output_type=pytesseract.Output.DICT)
        blocks: list[OcrBlock] = []
        for i, text in enumerate(data.get("text", [])):
            if not str(text).strip():
                continue
            conf = float(data.get("conf", ["-1"])[i]) / 100.0
            if conf < self.min_confidence:
                continue
            bbox = (int(data["left"][i]), int(data["top"][i]), int(data["width"][i]), int(data["height"][i]))
            blocks.append(OcrBlock(text=str(text), confidence=max(conf, 0.0), bbox=bbox))
        return OcrResult.from_blocks(blocks, language=lang)
