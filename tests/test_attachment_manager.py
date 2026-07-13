from pathlib import Path

from secondbrain.native.chat import AttachmentManager, ConversationStore


def test_attachment_manager_reuses_document_explorer_without_file_copy(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Kontext", encoding="utf-8")
    store = ConversationStore(tmp_path)
    conversation = store.create("Attachment")
    manager = AttachmentManager(tmp_path, store)
    attached = manager.attach(conversation["id"], source)
    assert attached["ok"] is True
    assert attached["import"]["copy"] is False
    assert not (tmp_path / "documents" / source.name).exists()
    duplicate = manager.attach(conversation["id"], source)
    assert duplicate["status"] == "duplicate"
    assert len(manager.list(conversation["id"])) == 1


def test_attachment_manager_rejects_unsupported_files(tmp_path: Path) -> None:
    source = tmp_path / "payload.exe"
    source.write_bytes(b"no")
    store = ConversationStore(tmp_path)
    conversation = store.create("Attachment")
    result = AttachmentManager(tmp_path, store).attach(conversation["id"], source)
    assert result["status"] == "unsupported_type"
