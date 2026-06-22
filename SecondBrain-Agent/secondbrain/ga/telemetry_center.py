"""v28.0 - Telemetry and Tracing."""

from time import time


class TelemetryCenter:
    def __init__(self):
        self._traces = []

    def trace(self, operation: str):
        self._traces.append({
            "operation": operation,
            "timestamp": time(),
        })

    def list(self):
        return list(self._traces)
