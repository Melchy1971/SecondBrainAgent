"""v30.1 - database metrics helpers."""

from __future__ import annotations


class DatabaseMetrics:
    def summarize_pool(self, engine) -> dict:
        pool = engine.pool
        return {
            "pool_class": pool.__class__.__name__,
            "checked_in": getattr(pool, "checkedin", lambda: None)(),
            "checked_out": getattr(pool, "checkedout", lambda: None)(),
            "overflow": getattr(pool, "overflow", lambda: None)(),
            "size": getattr(pool, "size", lambda: None)(),
        }
