from pathlib import Path

from secondbrain.native.chat import ConversationStore
from secondbrain.native.chat import conversation_cli_main


def test_conversation_store_layout_and_lifecycle(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path)
    conversation = store.create("Projektstatus", workspace="chat", provider="ollama", model="llama3.2")
    root = tmp_path / "runtime" / "chat" / conversation["id"]
    assert (root / "conversation.json").is_file()
    assert (root / "messages.jsonl").is_file()
    assert (root / "attachments").is_dir()
    assert (root / "exports").is_dir()
    message = store.append_message(conversation["id"], "user", "Hallo")
    assert message["id"]
    assert store.messages(conversation["id"])[0]["content"] == "Hallo"
    assert store.update(conversation["id"], pinned=True, favorite=True)["pinned"] is True
    assert store.search("Hallo")[0]["id"] == conversation["id"]
    assert store.export(conversation["id"], format="md")["ok"] is True


def test_provider_change_creates_conversation_version(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path)
    original = store.create("Version", provider="ollama", model="a")
    store.append_message(original["id"], "user", "Kontext")
    version = store.version(original["id"], provider="openai", model="b")
    assert version["id"] != original["id"]
    assert version["parent_id"] == original["id"]
    assert store.messages(version["id"])[0]["content"] == "Kontext"


def test_conversation_cli_lifecycle(tmp_path: Path, capsys) -> None:
    store = ConversationStore(tmp_path)
    conversation = store.create("CLI")
    assert conversation_cli_main(["conversation-list", "--project-root", str(tmp_path)]) == 0
    assert conversation_cli_main(["conversation-open", conversation["id"], "--project-root", str(tmp_path)]) == 0
    assert conversation_cli_main(["conversation-pin", conversation["id"], "--project-root", str(tmp_path)]) == 0
    assert conversation_cli_main(["conversation-export", conversation["id"], "--format", "json", "--project-root", str(tmp_path)]) == 0
    assert conversation_cli_main(["conversation-search", "CLI", "--project-root", str(tmp_path)]) == 0
    assert conversation_cli_main(["conversation-delete", conversation["id"], "--project-root", str(tmp_path)]) == 0
    assert "deleted" in capsys.readouterr().out


def test_launcher_routes_conversation_commands(tmp_path: Path, capsys) -> None:
    import launcher

    assert launcher.main(["conversation-list", "--project-root", str(tmp_path)]) == 0
    assert '"conversations"' in capsys.readouterr().out
