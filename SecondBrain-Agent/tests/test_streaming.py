import time

from secondbrain.gui.chat_stream import ChatStream


def test_streaming_runs_off_thread_and_can_cancel() -> None:
    stream = ChatStream()

    def producer(cancel):
        for chunk in ("a", "b", "c"):
            if cancel.is_set():
                return
            time.sleep(0.01)
            yield chunk

    assert stream.start(producer) is True
    assert stream.running is True
    assert stream.cancel() is True
    assert stream.wait(1) is True
    assert stream.status == "cancelled"


def test_streaming_retry_reuses_factory() -> None:
    stream = ChatStream()
    assert stream.start(lambda _cancel: iter(("Hello", " World"))) is True
    assert stream.wait(1) is True
    assert stream.content() == "Hello World"
    assert stream.retry() is True
    assert stream.wait(1) is True
    assert stream.content() == "Hello World"

