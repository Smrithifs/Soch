"""Per-student virtual clock. The active student's time-travel offset is set once per request;
every service reads time through here so forgetting, due dates, streaks and plans all move together."""
from contextvars import ContextVar
from datetime import date, datetime, timedelta

_offset_days: ContextVar[float] = ContextVar("offset_days", default=0.0)


def set_offset(days: float) -> None:
    _offset_days.set(float(days or 0))


def offset() -> float:
    return _offset_days.get()


def now() -> datetime:
    return datetime.utcnow() + timedelta(days=_offset_days.get())


def today() -> date:
    return date.today() + timedelta(days=int(_offset_days.get()))
