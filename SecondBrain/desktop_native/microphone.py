from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from importlib import import_module
from typing import Any, Callable, Mapping


def _number(source: Mapping[str, str], name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(source.get(name, default))
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, value))


@dataclass(frozen=True, slots=True)
class MicrophoneConfig:
    device_index: int | None = None
    calibration_seconds: float = 0.4
    timeout_seconds: float = 5.0
    phrase_time_limit_seconds: float = 8.0

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> "MicrophoneConfig":
        source = os.environ if environ is None else environ
        raw_index = str(source.get("SECONDBRAIN_MICROPHONE_DEVICE_INDEX", "")).strip()
        try:
            device_index = max(0, int(raw_index)) if raw_index else None
        except ValueError:
            device_index = None
        return cls(
            device_index=device_index,
            calibration_seconds=_number(source, "SECONDBRAIN_MICROPHONE_CALIBRATION_SECONDS", 0.4, 0.0, 5.0),
            timeout_seconds=_number(source, "SECONDBRAIN_MICROPHONE_TIMEOUT_SECONDS", 5.0, 0.1, 60.0),
            phrase_time_limit_seconds=_number(
                source, "SECONDBRAIN_MICROPHONE_PHRASE_LIMIT_SECONDS", 8.0, 0.5, 120.0
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MicrophoneInventory:
    """Read-only microphone discovery that remains safe when audio dependencies are absent."""

    def __init__(self, module_loader: Callable[[str], Any] = import_module) -> None:
        self._module_loader = module_loader

    def status(self, selected_index: int | None = None) -> dict[str, Any]:
        try:
            module = self._module_loader("speech_recognition")
            names = [str(name) for name in module.Microphone.list_microphone_names()]
        except Exception as exc:
            return {"available": False, "devices": [], "selected_index": selected_index, "error": str(exc)}
        selected_available = selected_index is None or selected_index < len(names)
        return {
            "available": bool(names) and selected_available,
            "devices": [{"index": index, "name": name} for index, name in enumerate(names)],
            "selected_index": selected_index,
            "selected_available": selected_available,
        }
