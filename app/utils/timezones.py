"""
Timezone helpers.

Convention:
- All stored *instants* are UTC (naive, matching the existing DateTime columns).
- All *calendar-day* logic uses the user's IANA timezone (default Africa/Nairobi).
- Schedule wall-clock times (TimetableEntry.start_time/end_time) stay in the
  user's local day and are not converted; only instant timestamps are.
"""
from datetime import datetime, date, timezone as _dt_timezone

import pytz

DEFAULT_TIMEZONE = "Africa/Nairobi"


def utc_now_naive() -> datetime:
    """Current UTC instant, naive (for storage into naive DateTime columns)."""
    return datetime.now(_dt_timezone.utc).replace(tzinfo=None)


def get_tz(tz_name):
    """Return a pytz timezone for ``tz_name``; invalid names fall back to default."""
    if not tz_name:
        return pytz.timezone(DEFAULT_TIMEZONE)
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone(DEFAULT_TIMEZONE)


def _cache_key(user_id):
    return f"tz:{user_id}"


def _load_tz(user_id):
    from flask import g
    from app.models.user import User
    key = _cache_key(user_id)
    cache = getattr(g, "_tz_cache", None)
    if cache is None:
        cache = g._tz_cache = {}
    if key in cache:
        return cache[key]
    user = User.query.get(user_id) if user_id is not None else None
    value = user_tz(user)
    cache[key] = value
    return value


def _as_aware_utc(now):
    """Treat a naive ``now`` as UTC (the storage convention); else normalize."""
    if now.tzinfo is None:
        return now.replace(tzinfo=_dt_timezone.utc)
    return now.astimezone(_dt_timezone.utc)


def tz_for_id(user_id):
    """The user's timezone object for ``user_id`` (request-cached)."""
    return _load_tz(user_id)


def today_for_id(user_id, now=None) -> date:
    """The user's calendar day for ``user_id`` (request-cached)."""
    now = _as_aware_utc(now or datetime.now(_dt_timezone.utc))
    return now.astimezone(_load_tz(user_id)).date()


def user_tz(user) -> pytz.BaseTzInfo:
    """Return the user's timezone object (account value, else default)."""
    if user is None:
        return pytz.timezone(DEFAULT_TIMEZONE)
    return get_tz(getattr(user, "timezone", None))


def today_for(user, now=None) -> date:
    """The user's current calendar day, never the server wall clock."""
    now = _as_aware_utc(now or datetime.now(_dt_timezone.utc))
    return now.astimezone(user_tz(user)).date()


def now_for(user, now=None) -> datetime:
    """Current instant expressed in the user's timezone (aware)."""
    now = _as_aware_utc(now or datetime.now(_dt_timezone.utc))
    return now.astimezone(user_tz(user))


def to_user_dt(naive_utc: datetime, tz_name=None) -> datetime:
    """Interpret a naive UTC instant as UTC then express it in ``tz_name``."""
    if naive_utc is None:
        return None
    aware_utc = naive_utc.replace(tzinfo=_dt_timezone.utc) \
        if naive_utc.tzinfo is None else naive_utc.astimezone(_dt_timezone.utc)
    return aware_utc.astimezone(get_tz(tz_name))


def format_user_dt(naive_utc: datetime, tz_name=None, fmt="%b %d %H:%M") -> str:
    """Render a naive-UTC instant in ``tz_name`` ('' for None)."""
    if naive_utc is None:
        return ""
    return to_user_dt(naive_utc, tz_name).strftime(fmt)


def format_user_date(value, fmt="%Y-%m-%d") -> str:
    """Render a date (already a user-local calendar day) as a string."""
    if value is None:
        return ""
    return value.strftime(fmt)


def validate_timezone_name(tz_name):
    return bool(tz_name) and tz_name in pytz.all_timezones