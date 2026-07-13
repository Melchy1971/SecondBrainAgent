from pathlib import Path

from secondbrain.desktop_app.runtime import DesktopAppRuntime
from secondbrain.gui.chat_view import ChatView
from secondbrain.native.chat import ChatEngine, ConversationStore, NativeChatService, NativeChatStore
from secondbrain.voice.conversation_manager import VoiceConversationManager


def test_native_chat_service_is_compatibility_alias() -> None:
    assert NativeChatService is ChatEngine


def test_all_chat_surfaces_use_canonical_engine(tmp_path: Path) -> None:
    engine = ChatEngine(tmp_path)
    assert isinstance(ChatView(tmp_path, engine=engine).engine, ChatEngine)
    assert isinstance(VoiceConversationManager(tmp_path, engine=engine).engine, ChatEngine)
    assert isinstance(DesktopAppRuntime(tmp_path).chat_engine, ChatEngine)


def test_legacy_store_writes_only_to_conversation_store(tmp_path: Path) -> None:
    legacy = NativeChatStore(tmp_path)
    legacy.append({"role": "user", "content": "vereinheitlicht"})
    assert not legacy.path.exists()
    conversations = ConversationStore(tmp_path).list()
    assert len(conversations) == 1
    assert ConversationStore(tmp_path).messages(conversations[0]["id"])[0]["content"] == "vereinheitlicht"


def test_desktop_and_voice_share_conversation_format(tmp_path: Path) -> None:
    desktop = DesktopAppRuntime(tmp_path)
    desktop.chat("Desktop")
    voice = VoiceConversationManager(tmp_path)
    voice.add("user", "Voice")
    rows = NativeChatStore(tmp_path).list(limit=20)
    assert {row["content"] for row in rows} >= {"Desktop", "Echo: Desktop", "Voice"}
