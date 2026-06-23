"""P1.3.3 - PDF/OCR parser facade.

The facade makes PDF parser outcomes explicit for the ingestion pipeline. A PDF
that has no extractable text is not silently treated as an empty document; it is
marked as OCR-required unless an OCR parser is wired and succeeds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from .parser_contract import ParsedDocument, ParseStatus, build_parsed_document
from .parsers import PdfTextParser


@runtime_checkable
class PdfParserLike(Protocol):
    def parse(self, path: str | Path) -> ParsedDocument:
        ...


class PdfOcrParserFacade:
    """Run text extraction first and OCR only when the PDF requires it.

    Rules:
    - text parser with non-empty text wins
    - text parser reporting OCR_REQUIRED triggers OCR parser if available
    - missing OCR parser returns deterministic OCR_REQUIRED
    - failed OCR does not mask the original OCR-required state
    """

    supported_extensions = {".pdf"}

    def __init__(self, text_parser: PdfParserLike | None = None, ocr_parser: PdfParserLike | None = None) -> None:
        self.text_parser = text_parser or PdfTextParser()
        self.ocr_parser = ocr_parser

    def parse(self, path: str | Path) -> ParsedDocument:
        text_result = self.text_parser.parse(path)
        if text_result.status == ParseStatus.PARSED and text_result.char_count > 0:
            return text_result
        if text_result.status not in {ParseStatus.OCR_REQUIRED, ParseStatus.EMPTY}:
            return text_result
        if self.ocr_parser is None:
            return build_parsed_document(
                title=text_result.title,
                text="",
                mime_type="application/pdf",
                source_path=text_result.source_path or str(path),
                pages=list(text_result.pages),
                metadata={**text_result.metadata, "ocr_required": True, "ocr_available": False},
                errors=[*text_result.errors, "ocr_parser_not_configured"],
                status=ParseStatus.OCR_REQUIRED,
            )

        ocr_result = self.ocr_parser.parse(path)
        if ocr_result.status == ParseStatus.PARSED and ocr_result.char_count > 0:
            return build_parsed_document(
                title=ocr_result.title or text_result.title,
                text=ocr_result.text,
                mime_type="application/pdf",
                source_path=ocr_result.source_path or text_result.source_path or str(path),
                pages=list(ocr_result.pages),
                metadata={**text_result.metadata, **ocr_result.metadata, "ocr_applied": True},
                errors=[*text_result.errors, *ocr_result.errors],
                status=ParseStatus.PARSED,
            )
        return build_parsed_document(
            title=text_result.title,
            text="",
            mime_type="application/pdf",
            source_path=text_result.source_path or str(path),
            pages=list(text_result.pages),
            metadata={**text_result.metadata, "ocr_required": True, "ocr_available": True},
            errors=[*text_result.errors, *ocr_result.errors, "ocr_parser_failed_or_empty"],
            status=ParseStatus.OCR_REQUIRED,
        )
