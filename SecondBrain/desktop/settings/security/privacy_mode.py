from __future__ import annotations

from .security_models import PrivacyMode


class PrivacyModeService:
    def __init__(self, mode: PrivacyMode | str = PrivacyMode.OFF) -> None:
        self._mode = PrivacyMode(mode)

    @property
    def mode(self) -> PrivacyMode:
        return self._mode

    def set_mode(self, mode: PrivacyMode | str) -> PrivacyMode:
        self._mode = PrivacyMode(mode)
        return self._mode

    def enabled(self) -> bool:
        return self._mode != PrivacyMode.OFF

    def require_not_privacy_mode(self, operation: str) -> None:
        if self.enabled():
            raise PermissionError(f"operation blocked by privacy mode: {operation}")
