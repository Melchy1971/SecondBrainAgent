from secondbrain.gui.chat_view import ChatView
from secondbrain.gui.connector_center import ConnectorCenter


def test_chat_history():
    chat = ChatView()
    chat.add_message("user", "hello")
    assert len(chat.history()) == 1


def test_connector_center():
    result = ConnectorCenter().render(["gmail", "github"])
    assert result["count"] == 2
