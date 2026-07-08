from pathlib import Path

from secondbrain.document_understanding import ParsedPage, ParseStatus, PdfOcrParserFacade, build_parsed_document


class StaticParser:
    def __init__(self, document):
        self.document = document

    def parse(self, path: str | Path):
        return self.document


def test_pdf_facade_returns_text_result_without_ocr(tmp_path: Path):
    pdf = tmp_path / "text.pdf"
    pdf.write_bytes(b"%PDF")
    parsed = build_parsed_document(title="text.pdf", text="Extracted text", mime_type="application/pdf", source_path=pdf)

    result = PdfOcrParserFacade(text_parser=StaticParser(parsed)).parse(pdf)

    assert result.status == ParseStatus.PARSED
    assert result.text == "Extracted text"
    assert result.metadata.get("ocr_applied") is None


def test_pdf_facade_marks_ocr_required_when_text_empty_and_no_ocr(tmp_path: Path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF")
    text_result = build_parsed_document(
        title="scan.pdf",
        text="",
        mime_type="application/pdf",
        source_path=pdf,
        pages=[ParsedPage(number=1, text="")],
        metadata={"parser": "pypdf"},
        errors=["pdf_text_empty_ocr_required"],
        status=ParseStatus.OCR_REQUIRED,
    )

    result = PdfOcrParserFacade(text_parser=StaticParser(text_result)).parse(pdf)

    assert result.status == ParseStatus.OCR_REQUIRED
    assert result.ok is False
    assert result.metadata["ocr_required"] is True
    assert result.metadata["ocr_available"] is False
    assert "ocr_parser_not_configured" in result.errors


def test_pdf_facade_uses_ocr_parser_when_configured(tmp_path: Path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF")
    text_result = build_parsed_document(
        title="scan.pdf",
        text="",
        mime_type="application/pdf",
        source_path=pdf,
        status=ParseStatus.OCR_REQUIRED,
        errors=["pdf_text_empty_ocr_required"],
    )
    ocr_result = build_parsed_document(
        title="scan.pdf",
        text="OCR text",
        mime_type="application/pdf",
        source_path=pdf,
        metadata={"parser": "ocr_stub"},
    )

    result = PdfOcrParserFacade(text_parser=StaticParser(text_result), ocr_parser=StaticParser(ocr_result)).parse(pdf)

    assert result.status == ParseStatus.PARSED
    assert result.text == "OCR text"
    assert result.metadata["ocr_applied"] is True
    assert "pdf_text_empty_ocr_required" in result.errors


def test_pdf_facade_preserves_failed_text_parser(tmp_path: Path):
    pdf = tmp_path / "broken.pdf"
    pdf.write_bytes(b"not really pdf")
    failed = build_parsed_document(
        title="broken.pdf",
        text="",
        mime_type="application/pdf",
        source_path=pdf,
        status=ParseStatus.FAILED,
        errors=["parser_crash"],
    )

    result = PdfOcrParserFacade(text_parser=StaticParser(failed)).parse(pdf)

    assert result.status == ParseStatus.FAILED
    assert result.errors == ("parser_crash",)
