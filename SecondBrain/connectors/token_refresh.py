"""P4 v22.1 - Token Refresh."""

from time import time


class TokenRefreshService:
    def should_refresh(self, expires_at: float, refresh_window_seconds: int = 300) -> bool:
        return expires_at <= (time() + refresh_window_seconds)
