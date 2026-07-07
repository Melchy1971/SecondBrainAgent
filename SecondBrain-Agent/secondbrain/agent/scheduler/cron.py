"""v30.71 Scheduler - cron and interval schedules.

A small, dependency-free 5-field cron implementation (minute hour day-of-month
month day-of-week) supporting ``*``, ``*/n``, ranges ``a-b`` and lists ``a,b``.
Plus a simple interval schedule. Both answer the two questions the scheduler
needs: "did this fire since last_run?" and "when does it next fire?".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

_FIELD_BOUNDS = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]


def _parse_field(spec: str, lo: int, hi: int) -> set[int]:
    values: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            base, step_s = part.split("/", 1)
            step = int(step_s)
        else:
            base = part
        if base in ("*", ""):
            start, end = lo, hi
        elif "-" in base:
            a, b = base.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(base)
        for v in range(start, end + 1, step):
            if lo <= v <= hi:
                values.add(v)
    return values


class CronSchedule:
    def __init__(self, expression: str):
        self.expression = expression.strip()
        fields = self.expression.split()
        if len(fields) != 5:
            raise ValueError(f"cron_needs_5_fields:{expression!r}")
        self.minute, self.hour, self.dom, self.month, self.dow = (
            _parse_field(f, lo, hi) for f, (lo, hi) in zip(fields, _FIELD_BOUNDS)
        )
        self._raw = fields

    def _dom_restricted(self) -> bool:
        return self._raw[2] != "*"

    def _dow_restricted(self) -> bool:
        return self._raw[4] != "*"

    def matches(self, dt: datetime) -> bool:
        if dt.minute not in self.minute or dt.hour not in self.hour or dt.month not in self.month:
            return False
        cron_dow = dt.isoweekday() % 7  # 0 = Sunday
        dom_ok = dt.day in self.dom
        dow_ok = cron_dow in self.dow
        if self._dom_restricted() and self._dow_restricted():
            return dom_ok or dow_ok      # standard cron OR semantics
        return dom_ok and dow_ok

    def due(self, last_run: datetime | None, now: datetime) -> bool:
        """Did the schedule fire in (last_run, now]? Bounded to a 1-day window."""
        end = now.replace(second=0, microsecond=0)
        if last_run is None:
            return self.matches(end)
        start = max(last_run.replace(second=0, microsecond=0) + timedelta(minutes=1),
                    end - timedelta(days=1))
        cur = start
        while cur <= end:
            if self.matches(cur):
                return True
            cur += timedelta(minutes=1)
        return False

    def next_after(self, dt: datetime) -> datetime | None:
        cur = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
        limit = cur + timedelta(days=366)
        while cur <= limit:
            if self.matches(cur):
                return cur
            cur += timedelta(minutes=1)
        return None


class IntervalSchedule:
    def __init__(self, seconds: int):
        self.seconds = int(seconds)

    def due(self, last_run: datetime | None, now: datetime) -> bool:
        if self.seconds <= 0:
            return False
        if last_run is None:
            return True
        return (now - last_run).total_seconds() >= self.seconds

    def next_after(self, dt: datetime) -> datetime | None:
        if self.seconds <= 0:
            return None
        from datetime import timedelta as _td
        return dt + _td(seconds=self.seconds)


def parse_schedule(spec: dict | str) -> CronSchedule | IntervalSchedule:
    if isinstance(spec, str):
        return CronSchedule(spec)
    if "cron" in spec:
        return CronSchedule(spec["cron"])
    if "interval_seconds" in spec:
        return IntervalSchedule(int(spec["interval_seconds"]))
    raise ValueError(f"unknown_schedule:{spec!r}")


def utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
