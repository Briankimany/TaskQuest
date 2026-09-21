"""Timezone unit tests — UTC instants vs user-calendar days."""
from datetime import datetime, date

import pytest

from app.utils import timezones as tz
from app.utils.timezones import (
    utc_now_naive,
    get_tz,
    user_tz,
    today_for,
    today_for_id,
    now_for,
    to_user_dt,
    format_user_dt,
    validate_timezone_name,
    DEFAULT_TIMEZONE,
)
from conftest import add_user


def test_utc_now_naive_is_naive():
    assert utc_now_naive().tzinfo is None


def test_get_tz_default_fallback():
    assert get_tz(None).zone == DEFAULT_TIMEZONE
    assert get_tz("Not/AZone").zone == DEFAULT_TIMEZONE
    assert get_tz("America/New_York").zone == "America/New_York"


def test_user_tz_defaults_for_none():
    assert user_tz(None).zone == DEFAULT_TIMEZONE


def test_validate_timezone_name():
    assert validate_timezone_name("Africa/Nairobi")
    assert validate_timezone_name("America/New_York")
    assert not validate_timezone_name("")
    assert not validate_timezone_name("Nope/Nope")


def test_today_for_uses_account_timezone(app):
    utc_instant = datetime(2026, 12, 31, 23, 30)  # naive UTC
    kiritimati = add_user("kiri", timezone="Pacific/Kiritimati")   # UTC+14
    nairobi = add_user("nbo", timezone="Africa/Nairobi")          # UTC+3
    new_york = add_user("nyc", timezone="America/New_York")       # UTC-5
    assert today_for(kiritimati, now=utc_instant) == date(2027, 1, 1)
    assert today_for(nairobi, now=utc_instant) == date(2027, 1, 1)
    assert today_for(new_york, now=utc_instant) == date(2026, 12, 31)


def test_today_for_id_uses_account_timezone(app, kim):
    assert today_for_id(kim.id, now=datetime(2026, 9, 21, 20, 0)) == date(2026, 9, 21)  # Nairobi +3
    kim.timezone = "Pacific/Kiritimati"
    assert today_for_id(kim.id, now=datetime(2026, 12, 31, 23, 30)) == date(2027, 1, 1)


def test_now_for_is_aware_and_local(app, kim):
    aware = now_for(kim, now=datetime(2026, 7, 1, 12, 0))
    assert aware.tzinfo is not None
    assert aware.utcoffset().total_seconds() == 3 * 3600  # Africa/Nairobi is UTC+3


def test_to_user_dt_renders_local_clock(app):
    naive_utc = datetime(2026, 7, 15, 12, 0)
    assert to_user_dt(naive_utc, "America/New_York").hour == 8  # July = EDT (UTC-4)
    assert to_user_dt(naive_utc, "Africa/Nairobi").hour == 15
    assert to_user_dt(None, "Africa/Nairobi") is None


def test_format_user_dt(app):
    naive_utc = datetime(2026, 7, 15, 12, 0)
    assert format_user_dt(None) == ""
    assert format_user_dt(naive_utc, "Africa/Nairobi", fmt="%H:%M") == "15:00"
    assert format_user_dt(naive_utc, "America/New_York", fmt="%H:%M") == "08:00"


def test_user_timezone_column_defaults_to_nairobi(app):
    user = add_user("default-tz")
    assert user.timezone == "Africa/Nairobi"


def test_prefs_timezone_endpoint(client):
    r = client.get("/api/prefs/timezone")
    assert r.status_code == 200
    assert r.get_json()["timezone"] == "Africa/Nairobi"

    bad = client.post("/api/prefs/timezone", json={"timezone": "Mars/Olympus"})
    assert bad.status_code == 400

    good = client.post("/api/prefs/timezone", json={"timezone": "Asia/Tokyo"})
    assert good.status_code == 200
    assert good.get_json()["timezone"] == "Asia/Tokyo"

    reread = client.get("/api/prefs/timezone")
    assert reread.get_json()["timezone"] == "Asia/Tokyo"


def test_profile_requires_auth(app):
    test_client = app.test_client()
    assert test_client.post("/api/prefs/timezone",
                            json={"timezone": "Asia/Tokyo"}).status_code in (401, 403, 302)