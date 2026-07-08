"""Thin document/source adapters for the single StreamingImportService."""
from __future__ import annotations

from pathlib import Path

from .streaming import ImportSession, StreamingImportService


def import_document(path: str | Path, *, project_root: str | Path = ".", source: str = "document",
                    workspace_id: str = "default", version: str | None = None) -> ImportSession:
    return StreamingImportService(project_root).import_document(path, source=source, workspace_id=workspace_id, version=version)


def import_pst(path, **kwargs): return import_document(path, source="pst", **kwargs)
def import_eml(path, **kwargs): return import_document(path, source="eml", **kwargs)
def import_pdf(path, **kwargs): return import_document(path, source="pdf", **kwargs)
def import_docx(path, **kwargs): return import_document(path, source="docx", **kwargs)
def import_xlsx(path, **kwargs): return import_document(path, source="xlsx", **kwargs)
def import_csv(path, **kwargs): return import_document(path, source="csv", **kwargs)
def import_txt(path, **kwargs): return import_document(path, source="txt", **kwargs)
def import_markdown(path, **kwargs): return import_document(path, source="markdown", **kwargs)


def _workspace(path: str | Path, source: str, *, project_root: str | Path = ".", workspace_id: str = "default") -> list[ImportSession]:
    return StreamingImportService(project_root).import_workspace(path, source=source, workspace_id=workspace_id)


def import_obsidian(path, **kwargs): return _workspace(path, "obsidian", **kwargs)
def import_notion(path, **kwargs): return _workspace(path, "notion", **kwargs)
def import_paperless(path, **kwargs): return _workspace(path, "paperless", **kwargs)
def import_onenote_export(path, **kwargs): return _workspace(path, "onenote", **kwargs)
