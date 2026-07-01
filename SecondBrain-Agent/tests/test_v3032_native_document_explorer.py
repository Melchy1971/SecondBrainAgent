from __future__ import annotations

from pathlib import Path

from secondbrain.native.document_explorer import DocumentExplorer


def test_document_explorer_status_counts_documents(tmp_path: Path) -> None:
    docs = tmp_path / 'documents'
    docs.mkdir()
    (docs / 'alpha.md').write_text('# Alpha\nJarvis Wissen', encoding='utf-8')
    (docs / 'scan.png').write_bytes(b'fake')
    explorer = DocumentExplorer(tmp_path)

    status = explorer.status()

    assert status['ok'] is True
    assert status['version'] == '30.32'
    assert status['documents'] == 2
    assert status['ocr_required'] == 1


def test_document_explorer_list_and_search(tmp_path: Path) -> None:
    docs = tmp_path / 'documents'
    docs.mkdir()
    (docs / 'rechnung.md').write_text('Betrag 42', encoding='utf-8')
    (docs / 'notiz.txt').write_text('Termin', encoding='utf-8')
    explorer = DocumentExplorer(tmp_path)

    listing = explorer.list_documents(limit=10)
    result = explorer.search('rechnung')

    assert listing['count'] == 2
    assert result['ok'] is True
    assert result['results'][0]['name'] == 'rechnung.md'


def test_document_explorer_preview_and_info(tmp_path: Path) -> None:
    docs = tmp_path / 'documents'
    docs.mkdir()
    file = docs / 'wissen.txt'
    file.write_text('Hallo Jarvis', encoding='utf-8')
    explorer = DocumentExplorer(tmp_path)

    info = explorer.info('wissen.txt')
    preview = explorer.preview(info['document']['document_id'])

    assert info['ok'] is True
    assert preview['ok'] is True
    assert 'Hallo Jarvis' in preview['preview']


def test_document_explorer_tag_persists_metadata(tmp_path: Path) -> None:
    docs = tmp_path / 'documents'
    docs.mkdir()
    (docs / 'projekt.md').write_text('Projekt', encoding='utf-8')
    explorer = DocumentExplorer(tmp_path)

    tagged = explorer.tag('projekt.md', ['Projekt', ' Wichtig ', 'projekt'])
    listing = explorer.list_documents(query='wichtig')

    assert tagged['ok'] is True
    assert tagged['tags'] == ['projekt', 'wichtig']
    assert listing['count'] == 1


def test_document_explorer_import_file(tmp_path: Path) -> None:
    source_dir = tmp_path / 'source'
    source_dir.mkdir()
    source = source_dir / 'extern.txt'
    source.write_text('Import', encoding='utf-8')
    explorer = DocumentExplorer(tmp_path)

    payload = explorer.import_file(str(source))

    assert payload['ok'] is True
    assert (tmp_path / 'documents' / 'extern.txt').exists()
