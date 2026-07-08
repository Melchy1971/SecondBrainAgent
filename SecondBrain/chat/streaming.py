"""v30.46.1 - StreamingManager: non-blocking Chat-Streaming.

Konsolidiert aus secondbrain.gui.chat_stream.ChatStream (v30.46). Die alte
Importadresse bleibt als Kompatibilitaets-Alias bestehen.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import Event, Lock, Thread
from typing import Any


class StreamingManager:
    def __init__(self):
        self._chunks = []
        self._cancel = Event()
        self._lock = Lock()
        self._thread: Thread | None = None
        self._factory: Callable[[Event], Iterable[Any]] | None = None
        self.error: Exception | None = None
        self.status = "idle"

    def push(self, chunk: str):
        with self._lock:
            self._chunks.append(chunk)

    def content(self) -> str:
        with self._lock:
            return "".join(self._chunks)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def cancel_event(self) -> Event:
        return self._cancel

    def start(
        self,
        factory: Callable[[Event], Iterable[Any]],
        *,
        on_chunk: Callable[[str], None] | None = None,
        on_done: Callable[[str, bool], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        reset: bool = True,
    ) -> bool:
        if self.running:
            return False
        if reset:
            with self._lock:
                self._chunks.clear()
        self._cancel.clear()
        self.error = None
        self.status = "running"
        self._factory = factory

        def consume() -> None:
            try:
                iterator = iter(factory(self._cancel))
                for item in iterator:
                    if self._cancel.is_set():
                        break
                    text = str(getattr(item, "delta", item))
                    self.push(text)
                    if on_chunk is not None:
                        on_chunk(text)
                close = getattr(iterator, "close", None)
                if self._cancel.is_set() and callable(close):
                    close()
                self.status = "cancelled" if self._cancel.is_set() else "completed"
                if on_done is not None:
                    on_done(self.content(), self._cancel.is_set())
            except Exception as exc:  # background boundary; surfaced through callback/state
                self.error = exc
                self.status = "failed"
                if on_error is not None:
                    on_error(exc)

        self._thread = Thread(target=consume, name="secondbrain-chat-stream", daemon=True)
        self._thread.start()
        return True

    def cancel(self) -> bool:
        if not self.running:
            return False
        self._cancel.set()
        return True

    def retry(self, **callbacks: Any) -> bool:
        if self._factory is None:
            return False
        return self.start(self._factory, **callbacks)

    def wait(self, timeout: float | None = None) -> bool:
        if self._thread is None:
            return True
        self._thread.join(timeout)
        return not self._thread.is_alive()
