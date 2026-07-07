"""Screen capture adapter using mss (offline, cross-platform). Lazy, integration-only."""

from __future__ import annotations

from secondbrain.vision.ports import Image


class MssScreenSource:
    name = "mss"

    def __init__(self, monitor: int = 1, region: dict | None = None) -> None:
        try:
            import mss  # noqa: F401
        except Exception as exc:  # pragma: no cover - only without optional dep
            raise RuntimeError(
                "MssScreenSource requires the optional 'mss' dep: pip install -r requirements-vision.txt"
            ) from exc
        self.monitor = monitor
        self.region = region

    def capture(self) -> Image:
        import mss
        import mss.tools
        with mss.mss() as sct:
            grab = sct.grab(self.region or sct.monitors[self.monitor])
            png = mss.tools.to_png(grab.rgb, grab.size)
        return Image(data=png, mime_type="image/png", source_uri="screenshot://desktop")
