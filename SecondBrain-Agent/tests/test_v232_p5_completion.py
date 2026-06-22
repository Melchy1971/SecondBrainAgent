from secondbrain.gui.chat_stream import ChatStream
from secondbrain.gui.agent_live_console import AgentLiveConsole
from secondbrain.gates.p5_completion_report import build_p5_completion_report


def test_chat_stream():
    stream = ChatStream()
    stream.push("Hello")
    stream.push(" World")
    assert stream.content() == "Hello World"


def test_live_console():
    console = AgentLiveConsole()
    console.write("INFO", "Started")
    assert len(console.history()) == 1


def test_completion_report():
    report = build_p5_completion_report()
    assert report["status"] == "PASS"
    assert report["next_phase"] == "P6_VOICE"
