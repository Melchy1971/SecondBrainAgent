"""v30.47 - Document Preview Center Service.

Komposition statt Neubau:
- Katalog/Import:  secondbrain.native.document_explorer.DocumentExplorer
- Parsing:         secondbrain.document_understanding (ParserRegistry, ParseStatus)
- Office:          secondbrain.office_import (via DocxParser/XlsxParser)

Der Service ist offline-sicher und dependency-light. PyMuPDF, Pillow,
python-docx, openpyxl, pytesseract und tkinterdnd2 bleiben optional und werden
als Capability-Flags gemeldet statt Exceptions zu werfen.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from secondbrain.document_understanding.parser_contract import ParseStatus
from secondbrain.document_understanding.parsers import default_parser_registry
from secondbrain.native.document_explorer import DocumentExplorer

from .models import (
    IMAGE_EXTENSIONS,
    SUPPORTED_PREVIEW_EXTENSIONS,
    OcrOverlayModel,
    PreviewAnnotation,
    PreviewSearchModel,
    PreviewVersion,
    ZoomModel,
)


class DocumentPreviewService:
    """Eine Vorschau-Schicht ueber dem bestehenden Dokumentbestand."""

    VERSION = "30.47"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.explorer = DocumentExplorer(self.project_root)
        self.registry = default_parser_registry()
        self.runtime_dir = self.project_root / "runtime" / "native" / "document_preview"
        self.versions_dir = self.runtime_dir / "versions"
        self.annotations_path = self.runtime_dir / "annotations.json"
        self.versions_index_path = self.runtime_dir / "versions.json"
        self.activity_path = self.runtime_dir / "preview_activity.jsonl"

    # --- Infrastruktur ---------------------------------------------------------

    def ensure_dirs(self) -> None:
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def capabilities(self) -> dict[str, bool]:
        return {
            "pdf_render": _importable("fitz"),
            "pdf_text": _importable("fitz") or _importable("pypdf"),
            "image_render": _importable("PIL"),
            "docx": _importable("docx"),
            "xlsx": _importable("openpyxl"),
            "ocr_engine": OcrOverlayModel.engine_available(),
            "os_drag_drop": _importable("tkinterdnd2"),
        }

    def status(self) -> dict[str, Any]:
        explorer_status = self.explorer.status()
        annotations = self._load_annotations()
        versions = self._load_versions_index()
        return {
            "ok": True,
            "version": self.VERSION,
            "mode": "native_document_preview_center",
            "project_root": str(self.project_root),
            "catalog": "document_explorer",
            "parser_registry": "document_understanding.default_parser_registry",
            "supported_extensions": list(SUPPORTED_PREVIEW_EXTENSIONS),
            "documents": explorer_status.get("documents", 0),
            "annotations": sum(len(rows) for rows in annotations.values()),
            "versions": sum(len(rows) for rows in versions.values()),
            "zoom_levels": ZoomModel.levels(),
            "capabilities": self.capabilities(),
            "runtime_dir": str(self.runtime_dir),
        }

    # --- Vorschau / Metadaten / Suche -------------------------------------------

    def resolve(self, document_ref: str) -> Path | None:
        return self.explorer._resolve_document(document_ref)

    def preview(self, document_ref: str, *, max_chars: int = 20000) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        suffix = resolved.suffix.lower()
        if suffix not in SUPPORTED_PREVIEW_EXTENSIONS:
            return {
                "ok": False,
                "status": "unsupported_extension",
                "document_ref": document_ref,
                "path": str(resolved),
                "extension": suffix,
                "supported_extensions": list(SUPPORTED_PREVIEW_EXTENSIONS),
            }
        parsed = self.registry.parse(resolved)
        payload = parsed.to_ingestion_payload()
        pages = [{"number": page.number, "text": page.text} for page in parsed.pages]
        text = parsed.text[:max_chars]
        result = {
            "ok": parsed.status in {ParseStatus.PARSED, ParseStatus.OCR_REQUIRED, ParseStatus.EMPTY},
            "status": parsed.status.value,
            "document_ref": document_ref,
            "path": str(resolved),
            "extension": suffix,
            "title": parsed.title,
            "mime_type": parsed.mime_type,
            "text": text,
            "truncated": len(parsed.text) > max_chars,
            "pages": pages,
            "page_count": max(1, parsed.page_count),
            "metadata": payload.get("metadata", {}),
            "errors": list(parsed.errors),
            "renderer": self._renderer_for(suffix),
        }
        self._append_activity("preview.opened", {"path": str(resolved), "status": parsed.status.value})
        return result

    def _renderer_for(self, suffix: str) -> str:
        if suffix == ".pdf":
            return "canvas_pdf" if _importable("fitz") else "text"
        if suffix in IMAGE_EXTENSIONS:
            return "canvas_image" if _importable("PIL") else "none"
        return "text"

    def metadata(self, document_ref: str) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        info = self.explorer.info(str(resolved))
        document = info.get("document") or {}
        doc_id = str(document.get("document_id", ""))
        parsed = self.registry.parse(resolved)
        stat = resolved.stat()
        return {
            "ok": True,
            "document": document,
            "parse_status": parsed.status.value,
            "parse_metadata": dict(parsed.metadata),
            "page_count": max(1, parsed.page_count),
            "char_count": parsed.char_count,
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
            "content_hash": _content_hash(resolved),
            "annotations": len(self._load_annotations().get(doc_id, [])),
            "versions": len(self._load_versions_index().get(doc_id, [])),
        }

    def search(self, document_ref: str, query: str, *, limit: int = 200) -> dict[str, Any]:
        preview = self.preview(document_ref)
        if not preview.get("ok"):
            return {"ok": False, "status": preview.get("status", "preview_failed"), "query": query}
        pages = PreviewSearchModel.pages_from_parsed(preview)
        hits = PreviewSearchModel.hits(pages, query, limit=limit)
        return {
            "ok": True,
            "query": query,
            "path": preview["path"],
            "count": len(hits),
            "hits": hits,
        }

    # --- OCR Overlay -------------------------------------------------------------

    def ocr_overlay(self, document_ref: str, *, page: int = 1) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        suffix = resolved.suffix.lower()
        if suffix not in IMAGE_EXTENSIONS and suffix != ".pdf":
            return {"ok": True, "status": "ocr_not_required", "path": str(resolved), "items": []}
        if not OcrOverlayModel.engine_available():
            return {
                "ok": True,
                "status": "ocr_engine_missing",
                "path": str(resolved),
                "hint": "pip install pytesseract Pillow (plus Tesseract-Binary)",
                "items": [],
            }
        try:
            import pytesseract  # type: ignore[import-not-found]
            from PIL import Image  # type: ignore[import-not-found]

            if suffix == ".pdf":
                if not _importable("fitz"):
                    return {"ok": True, "status": "pdf_render_missing", "path": str(resolved), "items": []}
                import fitz  # type: ignore[import-not-found]

                with fitz.open(resolved) as doc:
                    index = max(0, min(int(page) - 1, doc.page_count - 1))
                    pixmap = doc[index].get_pixmap(dpi=150)
                    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            else:
                image = Image.open(resolved)
            with image:
                raw = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        except Exception as exc:  # noqa: BLE001 - OCR bleibt optional
            return {"ok": False, "status": "ocr_failed", "path": str(resolved), "error": str(exc), "items": []}
        items = OcrOverlayModel.normalize_items(raw)
        self._append_activity("preview.ocr_overlay", {"path": str(resolved), "page": page, "items": len(items)})
        return {"ok": True, "status": "overlay", "path": str(resolved), "page": int(page), "items": items}

    # --- Versionen (Hash-Snapshots) ------------------------------------------------

    def snapshot_version(self, document_ref: str) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        self.ensure_dirs()
        doc_id = self._document_id(resolved)
        content_hash = _content_hash(resolved)
        index = self._load_versions_index()
        rows = index.setdefault(doc_id, [])
        for row in rows:
            if row.get("content_hash") == content_hash:
                return {"ok": True, "status": "unchanged", "version": row, "document_id": doc_id}
        snapshot_dir = self.versions_dir / doc_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{content_hash[:16]}{resolved.suffix.lower()}"
        snapshot_path.write_bytes(resolved.read_bytes())
        version = PreviewVersion(
            version_id=f"ver_{content_hash[:16]}",
            document_id=doc_id,
            source_path=str(resolved),
            snapshot_path=str(snapshot_path),
            size_bytes=resolved.stat().st_size,
            content_hash=content_hash,
            created_at=time.time(),
        )
        rows.append(version.to_dict())
        self._save_versions_index(index)
        self._append_activity("preview.version_snapshot", {"path": str(resolved), "version_id": version.version_id})
        return {"ok": True, "status": "snapshotted", "version": version.to_dict(), "document_id": doc_id}

    def versions(self, document_ref: str) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        doc_id = self._document_id(resolved)
        rows = self._load_versions_index().get(doc_id, [])
        current_hash = _content_hash(resolved)
        return {
            "ok": True,
            "document_id": doc_id,
            "path": str(resolved),
            "current_hash": current_hash,
            "count": len(rows),
            "current_is_snapshotted": any(row.get("content_hash") == current_hash for row in rows),
            "versions": sorted(rows, key=lambda row: row.get("created_at", 0.0), reverse=True),
        }

    def version_preview(self, version_id: str, *, max_chars: int = 20000) -> dict[str, Any]:
        for rows in self._load_versions_index().values():
            for row in rows:
                if row.get("version_id") == version_id:
                    snapshot = Path(str(row.get("snapshot_path", "")))
                    if not snapshot.is_file():
                        return {"ok": False, "status": "snapshot_missing", "version_id": version_id}
                    parsed = self.registry.parse(snapshot)
                    return {
                        "ok": True,
                        "status": parsed.status.value,
                        "version_id": version_id,
                        "snapshot_path": str(snapshot),
                        "text": parsed.text[:max_chars],
                        "page_count": max(1, parsed.page_count),
                    }
        return {"ok": False, "status": "version_not_found", "version_id": version_id}

    # --- Annotationen ---------------------------------------------------------------

    def annotate(self, document_ref: str, text: str, *, page: int | None = None,
                 region: list[float] | None = None) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        doc_id = self._document_id(resolved)
        try:
            annotation = PreviewAnnotation.create(doc_id, text, page=page, region=region)
        except ValueError as exc:
            return {"ok": False, "status": str(exc), "document_ref": document_ref}
        annotations = self._load_annotations()
        annotations.setdefault(doc_id, []).append(annotation.to_dict())
        self._save_annotations(annotations)
        self._append_activity("preview.annotated", {"path": str(resolved), "annotation_id": annotation.annotation_id})
        return {"ok": True, "status": "annotated", "annotation": annotation.to_dict(), "document_id": doc_id}

    def annotations(self, document_ref: str) -> dict[str, Any]:
        resolved = self.resolve(document_ref)
        if resolved is None:
            return {"ok": False, "status": "not_found", "document_ref": document_ref}
        doc_id = self._document_id(resolved)
        rows = self._load_annotations().get(doc_id, [])
        return {"ok": True, "document_id": doc_id, "path": str(resolved), "count": len(rows), "annotations": rows}

    def remove_annotation(self, annotation_id: str) -> dict[str, Any]:
        annotations = self._load_annotations()
        for doc_id, rows in annotations.items():
            remaining = [row for row in rows if row.get("annotation_id") != annotation_id]
            if len(remaining) != len(rows):
                annotations[doc_id] = remaining
                self._save_annotations(annotations)
                self._append_activity("preview.annotation_removed", {"annotation_id": annotation_id})
                return {"ok": True, "status": "removed", "annotation_id": annotation_id, "document_id": doc_id}
        return {"ok": False, "status": "annotation_not_found", "annotation_id": annotation_id}

    # --- Import (Drag & Drop / Kontextmenue) -----------------------------------------

    def import_dropped_file(self, source_path: str) -> dict[str, Any]:
        """DnD/Rechtsklick-Import laeuft ueber den bestehenden Explorer-Import."""
        result = self.explorer.import_file(source_path)
        if result.get("ok"):
            self._append_activity("preview.file_dropped", {"source": source_path, "target": result.get("target_path")})
        return result

    # --- intern -----------------------------------------------------------------------

    def _document_id(self, resolved: Path) -> str:
        from secondbrain.native.document_explorer import _document_id

        return _document_id(self.project_root, resolved)

    def _load_annotations(self) -> dict[str, list[dict[str, Any]]]:
        return _load_json_dict(self.annotations_path)

    def _save_annotations(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.ensure_dirs()
        self.annotations_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )

    def _load_versions_index(self) -> dict[str, list[dict[str, Any]]]:
        return _load_json_dict(self.versions_index_path)

    def _save_versions_index(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.ensure_dirs()
        self.versions_index_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )

    def _append_activity(self, event: str, payload: dict[str, Any]) -> None:
        self.ensure_dirs()
        row = {"ts": time.time(), "event": event, **payload}
        with self.activity_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _importable(module_name: str) -> bool:
    try:
        __import__(module_name)
    except Exception:  # noqa: BLE001 - capability probe
        return False
    return True


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json_dict(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - defekte Datei blockiert die Vorschau nicht
        return {}
    return data if isinstance(data, dict) else {}
