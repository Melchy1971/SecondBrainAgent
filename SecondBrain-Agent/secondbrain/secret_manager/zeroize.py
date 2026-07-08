"""Best-effort memory zeroization for key material held in bytearrays."""

from __future__ import annotations

from contextlib import contextmanager


def zeroize(buffer: bytearray) -> None:
    """Overwrite a mutable buffer in place with zeros."""
    if buffer is None:
        return
    for i in range(len(buffer)):
        buffer[i] = 0


@contextmanager
def zeroizing(data: bytes):
    """Yield a mutable copy of `data` and zero it on exit."""
    buf = bytearray(data)
    try:
        yield buf
    finally:
        zeroize(buf)


class SecretBytes:
    """Holds key material in a bytearray so it can be explicitly zeroized."""

    __slots__ = ("_buf",)

    def __init__(self, data: bytes) -> None:
        self._buf = bytearray(data)

    def bytes(self) -> bytes:
        if self._buf is None:
            raise ValueError("secret has been zeroized")
        return bytes(self._buf)

    def zeroize(self) -> None:
        if self._buf is not None:
            zeroize(self._buf)
            self._buf = None

    @property
    def cleared(self) -> bool:
        return self._buf is None

    def __repr__(self) -> str:            # never leak content
        return "<SecretBytes cleared>" if self._buf is None else "<SecretBytes ****>"

    def __del__(self) -> None:
        try:
            self.zeroize()
        except Exception:
            pass
