"""Parallel, cancellable source orchestration for the existing dashboard."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Event, Lock
from time import monotonic
from typing import Any, Callable, Mapping

from secondbrain.personal_dashboard.models import DashboardConfig, DashboardSnapshot
from secondbrain.personal_dashboard.service import Dashboard

SourceProvider = Callable[..., Any]


@dataclass
class DashboardPerformance:
    first_content_ms: float = 0.0
    complete_ms: float = 0.0
    source_ms: dict[str, float] = field(default_factory=dict)
    timed_out: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"first_content_ms": round(self.first_content_ms, 3),
                "complete_ms": round(self.complete_ms, 3),
                "source_ms": {key: round(value, 3) for key, value in self.source_ms.items()},
                "timed_out": list(self.timed_out)}


class DashboardRuntime:
    def __init__(self, dashboard: Dashboard | None = None, *, parallelism: int = 8,
                 source_timeout_seconds: float = 1.0) -> None:
        self.dashboard = dashboard or Dashboard(slow_cards=[])
        self.parallelism = max(1, int(parallelism))
        self.source_timeout_seconds = max(0.01, float(source_timeout_seconds))
        self._requests: dict[str, Event] = {}
        self._lock = Lock()

    def load(self, *, request_id: str, config: DashboardConfig,
             providers: Mapping[str, SourceProvider], now: datetime | None = None,
             page: int = 1, page_size: int = 50) -> tuple[DashboardSnapshot, DashboardPerformance]:
        if page < 1 or page_size < 1:
            raise ValueError("invalid_pagination")
        started = monotonic()
        cancel_event = Event()
        with self._lock:
            previous = self._requests.pop(request_id, None)
            if previous is not None:
                previous.set()
            self._requests[request_id] = cancel_event
        context: dict[str, Any] = {}
        status: dict[str, str] = {}
        performance = DashboardPerformance()

        def fetch(name: str, provider: SourceProvider):
            source_started = monotonic()
            value = provider(workspace_id=config.workspace_id, timeframe=config.timeframe,
                             offset=(page - 1) * page_size, limit=page_size,
                             cancel_event=cancel_event)
            return name, value, (monotonic() - source_started) * 1000

        pool = ThreadPoolExecutor(max_workers=min(self.parallelism, max(1, len(providers))),
                                  thread_name_prefix="dashboard-source")
        futures = {pool.submit(fetch, name, provider): name for name, provider in providers.items()}
        done, pending = wait(futures, timeout=self.source_timeout_seconds)
        performance.first_content_ms = (monotonic() - started) * 1000
        for future in done:
            name = futures[future]
            try:
                _, value, elapsed = future.result()
            except Exception:  # noqa: BLE001 - source error is isolated and redacted
                context[name] = {"error": "source_unavailable"}
                status[name] = "error"
            else:
                context[name] = value
                status[name] = "ok"
                performance.source_ms[name] = elapsed
        for future in pending:
            name = futures[future]
            future.cancel()
            context[name] = {"error": "timeout"}
            status[name] = "timeout"
            performance.timed_out.append(name)
        pool.shutdown(wait=False, cancel_futures=True)
        moment = now or datetime.now(timezone.utc)
        cards = self.dashboard.build(config=config, context=context, now=moment)
        snapshot = DashboardSnapshot(workspace=config.workspace_id,
                                     generated_at=moment.isoformat(timespec="seconds"),
                                     cards=cards, source_status=status)
        performance.complete_ms = (monotonic() - started) * 1000
        with self._lock:
            self._requests.pop(request_id, None)
        return snapshot, performance

    def cancel(self, request_id: str) -> bool:
        with self._lock:
            event = self._requests.get(request_id)
        if event is None:
            return False
        event.set()
        return True

    def refresh_card(self, *, card_id: str, config: DashboardConfig,
                     provider: SourceProvider, source_key: str,
                     now: datetime | None = None) -> Any:
        event = Event()
        value = provider(workspace_id=config.workspace_id, timeframe=config.timeframe,
                         offset=0, limit=50, cancel_event=event)
        return self.dashboard.resolve_async(card_id=card_id, config=config,
                                            context={source_key: value}, now=now)
