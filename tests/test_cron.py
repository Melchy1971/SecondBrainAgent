from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.agent.scheduler import CronSchedule, IntervalSchedule, parse_schedule


def _dt(h, m, day=6, month=7):
    return datetime(2026, month, day, h, m, tzinfo=timezone.utc)


def test_cron_requires_five_fields():
    with pytest.raises(ValueError):
        CronSchedule("* * * *")


def test_every_15_minutes():
    c = CronSchedule("*/15 * * * *")
    assert c.matches(_dt(12, 0))
    assert c.matches(_dt(12, 15))
    assert not c.matches(_dt(12, 7))


def test_specific_hour_and_minute():
    c = CronSchedule("30 3 * * *")
    assert c.matches(_dt(3, 30))
    assert not c.matches(_dt(4, 30))


def test_ranges_and_lists():
    c = CronSchedule("0 9-17 * * 1,2,3,4,5")   # workday business hours
    assert c.matches(datetime(2026, 7, 6, 9, 0, tzinfo=timezone.utc))    # Monday 09:00
    assert not c.matches(datetime(2026, 7, 6, 8, 0, tzinfo=timezone.utc))
    # 2026-07-11 is a Saturday
    assert not c.matches(datetime(2026, 7, 11, 10, 0, tzinfo=timezone.utc))


def test_next_after():
    c = CronSchedule("0 * * * *")   # top of every hour
    nxt = c.next_after(_dt(12, 30))
    assert nxt == _dt(13, 0)


def test_cron_due_within_window():
    c = CronSchedule("0 * * * *")
    # last run at 12:00, now 13:05 -> the 13:00 firing is due
    assert c.due(_dt(12, 0), _dt(13, 5)) is True
    # last run at 13:00, now 13:30 -> not due yet
    assert c.due(_dt(13, 0), _dt(13, 30)) is False


def test_cron_due_first_run():
    c = CronSchedule("*/15 * * * *")
    assert c.due(None, _dt(12, 0)) is True
    assert c.due(None, _dt(12, 7)) is False


def test_interval_schedule():
    s = IntervalSchedule(3600)
    assert s.due(None, _dt(12, 0)) is True
    assert s.due(_dt(12, 0), _dt(12, 30)) is False
    assert s.due(_dt(12, 0), _dt(13, 1)) is True
    assert s.next_after(_dt(12, 0)) == _dt(13, 0)


def test_parse_schedule_dispatch():
    assert isinstance(parse_schedule("*/5 * * * *"), CronSchedule)
    assert isinstance(parse_schedule({"cron": "0 0 * * *"}), CronSchedule)
    assert isinstance(parse_schedule({"interval_seconds": 60}), IntervalSchedule)
