from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

TEXT_EXTENSIONS = {'.txt', '.md', '.markdown', '.json', '.jsonl', '.csv', '.log', '.py', '.yaml', '.yml'}
PREVIEW_EXTENSIONS = TEXT_EXTENSIONS | {'.pdf', '.png', '.jpg', '.jpeg', '.webp', '.gif'}
DEFAULT_SCAN_DIRS = ('documents', 'data/documents', 'imports', 'runtime/imports', 'runtime/documents')


@dataclass(frozen=True)
class DocumentItem:
    document_id: str
    path: str
    name: str
    extension: str
    mime_type: str
    size_bytes: int
    modified_at: float
    preview_supported: bool
    parser_hint: str
    ocr_status: str
    index_status: str
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['tags'] = list(self.tags)
        return data


class DocumentExplorer:
    """Native file-backed document explorer for first-class desktop usage.

    This module is intentionally independent from the web HUD. It gives the
    native shell a stable document surface even when PostgreSQL, pgvector or a
    connector runtime are not available yet.
    """

    def __init__(self, project_root: str | Path = '.') -> None:
        self.project_root = Path(project_root).resolve()
        self.runtime_dir = self.project_root / 'runtime' / 'native'
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.meta_path = self.runtime_dir / 'document_explorer_meta.json'
        self.activity_path = self.runtime_dir / 'activity_log.jsonl'

    def status(self) -> dict[str, Any]:
        docs = self.list_documents(limit=100000)['documents']
        by_extension: dict[str, int] = {}
        by_parser: dict[str, int] = {}
        ocr_required = 0
        indexed = 0
        for doc in docs:
            by_extension[doc['extension']] = by_extension.get(doc['extension'], 0) + 1
            by_parser[doc['parser_hint']] = by_parser.get(doc['parser_hint'], 0) + 1
            if doc['ocr_status'] == 'required':
                ocr_required += 1
            if doc['index_status'] == 'indexed':
                indexed += 1
        return {
            'ok': True,
            'version': '30.32',
            'mode': 'native_document_explorer',
            'project_root': str(self.project_root),
            'scan_dirs': [str(path) for path in self._scan_roots()],
            'documents': len(docs),
            'indexed_documents': indexed,
            'ocr_required': ocr_required,
            'by_extension': by_extension,
            'by_parser': by_parser,
            'metadata_path': str(self.meta_path),
        }

    def list_documents(self, *, query: str = '', limit: int = 100, offset: int = 0) -> dict[str, Any]:
        query_norm = query.strip().lower()
        meta = self._load_meta()
        rows: list[dict[str, Any]] = []
        for path in self._iter_candidate_files():
            item = self._document_item(path, meta)
            row = item.to_dict()
            haystack = ' '.join([row['name'], row['path'], row['extension'], ' '.join(row.get('tags', []))]).lower()
            if not query_norm or query_norm in haystack:
                rows.append(row)
        rows.sort(key=lambda row: (row['modified_at'], row['name']), reverse=True)
        return {'ok': True, 'query': query, 'count': len(rows), 'limit': limit, 'offset': offset, 'documents': rows[offset: offset + limit]}

    def search(self, query: str, *, limit: int = 25) -> dict[str, Any]:
        listing = self.list_documents(query=query, limit=limit)
        results = []
        query_norm = query.strip().lower()
        for row in listing['documents']:
            score = 0
            name = row['name'].lower()
            path = row['path'].lower()
            tags = ' '.join(row.get('tags', [])).lower()
            if query_norm and query_norm == name:
                score += 100
            if query_norm and query_norm in name:
                score += 50
            if query_norm and query_norm in tags:
                score += 30
            if query_norm and query_norm in path:
                score += 10
            row = dict(row)
            row['score'] = score
            results.append(row)
        results.sort(key=lambda row: (row['score'], row['modified_at']), reverse=True)
        return {'ok': True, 'query': query, 'count': len(results), 'results': results[:limit]}

    def info(self, document_ref: str) -> dict[str, Any]:
        resolved = self._resolve_document(document_ref)
        if resolved is None:
            return {'ok': False, 'status': 'not_found', 'document_ref': document_ref}
        meta = self._load_meta()
        item = self._document_item(resolved, meta).to_dict()
        item['preview'] = self.preview(document_ref, max_chars=4000).get('preview')
        return {'ok': True, 'document': item}

    def preview(self, document_ref: str, *, max_chars: int = 4000) -> dict[str, Any]:
        resolved = self._resolve_document(document_ref)
        if resolved is None:
            return {'ok': False, 'status': 'not_found', 'document_ref': document_ref}
        suffix = resolved.suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            return {
                'ok': True,
                'status': 'binary_or_external_preview',
                'document_ref': document_ref,
                'path': str(resolved),
                'preview': None,
                'hint': 'Native Vorschau verfügbar über Dateizuordnung/PDF-Viewer, Textvorschau nicht erzeugt.',
            }
        try:
            text = resolved.read_text(encoding='utf-8', errors='replace')[:max_chars]
        except Exception as exc:
            return {'ok': False, 'status': 'preview_error', 'error': str(exc), 'path': str(resolved)}
        return {'ok': True, 'status': 'text_preview', 'path': str(resolved), 'preview': text, 'truncated': resolved.stat().st_size > max_chars}

    def tag(self, document_ref: str, tags: Iterable[str]) -> dict[str, Any]:
        resolved = self._resolve_document(document_ref)
        if resolved is None:
            return {'ok': False, 'status': 'not_found', 'document_ref': document_ref}
        meta = self._load_meta()
        doc_id = _document_id(self.project_root, resolved)
        clean_tags = sorted({str(tag).strip().lower() for tag in tags if str(tag).strip()})
        doc_meta = meta.setdefault(doc_id, {})
        doc_meta['tags'] = clean_tags
        doc_meta['updated_at'] = time.time()
        self._save_meta(meta)
        payload = {'ok': True, 'status': 'tagged', 'document_id': doc_id, 'path': str(resolved), 'tags': clean_tags}
        self._append_activity({'type': 'document.tagged', **payload})
        return payload

    def import_file(self, source_path: str, *, copy: bool = True) -> dict[str, Any]:
        source = Path(source_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            return {'ok': False, 'status': 'source_not_found', 'source_path': str(source)}
        target_dir = self.project_root / 'documents'
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if copy:
            target.write_bytes(source.read_bytes())
        else:
            target = source
        payload = {'ok': True, 'status': 'imported', 'source_path': str(source), 'target_path': str(target), 'copy': copy}
        self._append_activity({'type': 'document.imported', **payload})
        return payload

    def _scan_roots(self) -> list[Path]:
        roots = []
        for rel in DEFAULT_SCAN_DIRS:
            path = self.project_root / rel
            if path.exists() and path.is_dir():
                roots.append(path)
        return roots

    def _iter_candidate_files(self) -> Iterable[Path]:
        seen: set[Path] = set()
        for root in self._scan_roots():
            for path in root.rglob('*'):
                if path.is_file() and not _is_runtime_noise(path):
                    resolved = path.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield resolved

    def _document_item(self, path: Path, meta: dict[str, Any]) -> DocumentItem:
        stat = path.stat()
        suffix = path.suffix.lower() or '<none>'
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        doc_id = _document_id(self.project_root, path)
        meta_row = meta.get(doc_id, {}) if isinstance(meta.get(doc_id, {}), dict) else {}
        parser_hint = _parser_hint(suffix, mime)
        return DocumentItem(
            document_id=doc_id,
            path=str(path),
            name=path.name,
            extension=suffix,
            mime_type=mime,
            size_bytes=stat.st_size,
            modified_at=stat.st_mtime,
            preview_supported=suffix in PREVIEW_EXTENSIONS,
            parser_hint=parser_hint,
            ocr_status=_ocr_status(suffix, mime),
            index_status=str(meta_row.get('index_status') or 'unknown'),
            tags=tuple(meta_row.get('tags') or ()),
        )

    def _resolve_document(self, document_ref: str) -> Path | None:
        ref = document_ref.strip()
        if not ref:
            return None
        candidate = Path(ref).expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
        listing = self.list_documents(limit=100000)['documents']
        for row in listing:
            if ref in {row['document_id'], row['name'], row['path']}:
                return Path(row['path']).resolve()
        lowered = ref.lower()
        matches = [Path(row['path']).resolve() for row in listing if lowered in row['name'].lower()]
        return matches[0] if matches else None

    def _load_meta(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {}
        try:
            data = json.loads(self.meta_path.read_text(encoding='utf-8'))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _save_meta(self, data: dict[str, Any]) -> None:
        self.meta_path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf-8')

    def _append_activity(self, payload: dict[str, Any]) -> None:
        payload = {'ts': time.time(), **payload}
        with self.activity_path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n')


def _document_id(project_root: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(project_root.resolve()).as_posix()
    except Exception:
        rel = str(path.resolve())
    digest = hashlib.sha1(rel.encode('utf-8')).hexdigest()[:16]
    return f'doc_{digest}'


def _parser_hint(extension: str, mime: str) -> str:
    if extension in {'.txt', '.md', '.markdown', '.log'}:
        return 'text'
    if extension == '.pdf':
        return 'pdf'
    if extension in {'.json', '.jsonl'}:
        return 'json'
    if extension == '.csv':
        return 'csv'
    if mime.startswith('image/'):
        return 'image_ocr'
    return 'binary_or_external'


def _ocr_status(extension: str, mime: str) -> str:
    if mime.startswith('image/'):
        return 'required'
    if extension == '.pdf':
        return 'unknown'
    return 'not_required'


def _is_runtime_noise(path: Path) -> bool:
    parts = set(path.parts)
    if '__pycache__' in parts or path.suffix == '.pyc':
        return True
    if path.name.startswith('.'):
        return True
    return False
