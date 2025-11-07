from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso(timestamp: str) -> Optional[datetime]:
    if not timestamp:
        return None
    try:
        return _ensure_utc(datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
    except ValueError:
        return None


def format_iso(dt: datetime) -> str:
    return _ensure_utc(dt).isoformat()


def is_recurring(schedule: Dict[str, any]) -> bool:
    if not schedule:
        return False
    if schedule.get("recurring"):
        return True
    return schedule.get("frequency") in {"interval", "monthly"}


def _next_monthly(reference: datetime, day_of_month: int) -> datetime:
    day = max(1, min(31, int(day_of_month)))
    year = reference.year
    month = reference.month
    while True:
        last_day = monthrange(year, month)[1]
        run_day = min(day, last_day)
        candidate = datetime(
            year,
            month,
            run_day,
            reference.hour,
            reference.minute,
            reference.second,
            tzinfo=timezone.utc,
        )
        if candidate > reference:
            return candidate
        month += 1
        if month > 12:
            month = 1
            year += 1


def next_run(schedule: Dict[str, any], reference: Optional[datetime] = None) -> Optional[str]:
    if not schedule:
        return None
    reference_dt = _ensure_utc(reference or datetime.now(timezone.utc))
    freq = schedule.get("frequency")
    if freq == "interval":
        seconds = int(schedule.get("intervalSeconds", 0))
        if seconds <= 0:
            return None
        return format_iso(reference_dt + timedelta(seconds=seconds))
    if freq == "monthly":
        day = schedule.get("dayOfMonth", 1)
        try:
            next_dt = _next_monthly(reference_dt, int(day))
        except (TypeError, ValueError):
            return None
        return format_iso(next_dt)
    return None


__all__ = ["parse_iso", "format_iso", "next_run", "is_recurring"]
