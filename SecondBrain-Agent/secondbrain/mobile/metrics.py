"""P7 v25.1 - Mobile Metrics."""

class MobileMetrics:
    def summarize(self, sessions: int, notifications: int):
        return {
            "sessions": sessions,
            "notifications": notifications,
            "engagement_score": sessions + notifications,
        }
