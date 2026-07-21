from __future__ import annotations

import os
import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from secondbrain.calendar_assistant.models import parse_dt

TIMEZONE_ENV = "SECONDBRAIN_CALENDAR_TIMEZONE"
DEFAULT_TIMEZONE = "Europe/Berlin"
_GERMAN_TIME = re.compile(
    r"^(?P<day>heute|morgen|übermorgen|uebermorgen|\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"(?P<um>um\s+)?(?P<hour>[01]?\d|2[0-3])"
    r"(?:(?P<separator>[:.])(?P<minute>[0-5]\d))?\s*(?P<uhr>uhr)?$",
    re.IGNORECASE,
)


def resolve_german_calendar_time(
    value: str,
    *,
    now: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime | None:
    """Resolve a small, unambiguous German date/time grammar.

    Existing timezone-aware ISO values remain unchanged. Natural values require
    a numeric time and either ``um``, ``Uhr`` or explicit minutes. Ambiguous and
    non-existent local DST times are rejected instead of guessed.
    """

    text = " ".join(str(value or "").strip().split())
    parsed = parse_dt(text)
    if parsed is not None and parsed.tzinfo is not None:
        return parsed
    match = _GERMAN_TIME.fullmatch(text)
    if match is None:
        return None
    if not match.group("um") and not match.group("uhr") and not match.group("minute"):
        return None

    zone = _zone(timezone_name)
    if zone is None:
        return None
    if now is None:
        moment = datetime.now(zone)
    elif now.tzinfo is None:
        return None
    else:
        moment = now.astimezone(zone)

    target_date = _target_date(match.group("day"), moment.date())
    if target_date is None:
        return None
    local = datetime.combine(
        target_date,
        time(hour=int(match.group("hour")), minute=int(match.group("minute") or 0)),
    )
    candidates = _valid_local_times(local, zone)
    if len(candidates) != 1 or candidates[0] <= moment:
        return None
    return candidates[0]


def _zone(timezone_name: str | None) -> ZoneInfo | None:
    name = str(timezone_name or os.environ.get(TIMEZONE_ENV) or DEFAULT_TIMEZONE).strip()
    try:
        return ZoneInfo(name)
    except (ValueError, ZoneInfoNotFoundError):
        return None


def _target_date(value: str, today: date) -> date | None:
    relative_days = {
        "heute": 0,
        "morgen": 1,
        "übermorgen": 2,
        "uebermorgen": 2,
    }
    normalized = value.casefold()
    if normalized in relative_days:
        return today + timedelta(days=relative_days[normalized])
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        return None


def _valid_local_times(local: datetime, zone: ZoneInfo) -> list[datetime]:
    valid: list[datetime] = []
    for fold in (0, 1):
        candidate = local.replace(tzinfo=zone, fold=fold)
        round_trip = candidate.astimezone(UTC).astimezone(zone)
        if round_trip.replace(tzinfo=None) == local and round_trip.fold == fold:
            valid.append(candidate)
    return valid
