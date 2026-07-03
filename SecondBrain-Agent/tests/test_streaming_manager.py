"""v30.46.1 - Tests fuer StreamingManager (gemeinsame Chat-Architektur)."""
from __future__ import annotations

import time
from threading import Event

from secondbrain.chat.streaming import StreamingManager


def _wait_for(manager: StreamingManager, timeout: float = 5.0) -> None:
    assert manager.wait(timeout), "stream thread did not finish in time"


def test_streaming_manager_collects_chunks_and_completes() -> None:
    manager = StreamingManager()
    seen: list[str] = []
    done: list[tuple[str, bool]] = []
    assert manager.start(
        lambda cancel: iter(["Ant", "wort"]),
        on_chunk=seen.append,
        on_done=lambda content, cancelled: done.append((content, cancelled)),
    )
    _wait_for(manager)
    assert manager.status == "completed"
    assert manager.content() == "Antwort"
    assert seen == ["Ant", "wort"]
    assert done == [("Antwort", False)]


def test_streaming_manager_rejects_parallel_start() -> None:
    manager = StreamingManager()
    release = Event()

    def factory(cancel: Event):
        release.wait(5)
        yield "x"

    assert manager.start(factory) is True
    assert manager.start(factory) is False  # laeuft bereits
    release.set()
    _wait_for(manager)


def test_streaming_manager_cancel_stops_consumption() -> None:
    manager = StreamingManager()
    started = Event()

    def factory(cancel: Event):
        for index in range(1000):
            started.set()
            if cancel.is_set():
                return
            yield f"chunk-{index} "
            time.sleep(0.005)

    manager.start(factory)
    assert started.wait(5)
    assert manager.cancel() is True
    _wait_for(manager)
    assert manager.status == "cancelled"


def test_streaming_manager_error_is_surfaced() -> None:
    manager = StreamingManager()
    errors: list[Exception] = []

    def factory(cancel: Event):
        yield "ok"
        raise ValueError("provider kaputt")

    manager.start(factory, on_error=errors.append)
    _wait_for(manager)
    assert manager.status == "failed"
    assert isinstance(manager.error, ValueError)
    assert errors and str(errors[0]) == "provider kaputt"


def test_streaming_manager_retry_reuses_factory() -> None:
    manager = StreamingManager()
    calls: list[int] = []

    def factory(cancel: Event):
        calls.append(1)
        yield "a"

    manager.start(factory)
    _wait_for(manager)
    assert manager.retry() is True
    _wait_for(manager)
    assert len(calls) == 2
    assert manager.content() == "a"


def test_legacy_chat_stream_alias_points_to_streaming_manager() -> None:
    from secondbrain.gui.chat_stream import ChatStream

    assert ChatStream is StreamingManager
