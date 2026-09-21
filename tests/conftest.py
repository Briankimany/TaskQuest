"""Shared fixtures for the TaskQuest test module.

The database URL is pinned BEFORE app imports so ``app.config`` binds to a
throwaway SQLite file for the whole session; every test gets a fresh schema
via ``db.drop_all``/``db.create_all``.
"""
import json
import os
import tempfile

import pytest

_TMP_DIR = tempfile.mkdtemp(prefix="taskquest_tests_")
_DB_FILE = os.path.join(_TMP_DIR, "test.db")

os.environ.setdefault("TASKQUEST_DATABASE_URL", "sqlite:///" + _DB_FILE.replace("\\", "/"))
os.environ.setdefault("OMNIROUTE_URL", "http://127.0.0.1:9/v1")   # unreachable -> OFF
os.environ.setdefault("OMNIROUTE_TIMEOUT", "0.3")
os.environ.setdefault("FLASK_DEBUG", "0")

from app.init import create_app  # noqa: E402
from app.models import db, User, Level, Activity, SubActivity, Timetable, TimetableEntry, CompletionLog  # noqa: E402
from app.models.judge import JudgeReview  # noqa: E402
from datetime import date, time  # noqa: E402

SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_backup.json")


@pytest.fixture()
def app():
    application = create_app()
    ctx = application.app_context()
    ctx.push()
    db.drop_all()
    db.create_all()
    for n in range(1, 11):
        db.session.add(Level(level_number=n, required_exp=500 * n,
                             reward_description=f"Level {n}"))
    db.session.commit()
    yield application
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture()
def seed_payload():
    with open(SEED_FILE, encoding="utf-8") as f:
        return json.load(f)


def add_user(username="kim", email=None, timezone="Africa/Nairobi", password="TestPass123!"):
    user = User(username=username, email=email or f"{username}@example.com")
    user.password = password
    user.timezone = timezone
    db.session.add(user)
    db.session.flush()
    return user


def add_activity(user, name, subs=()):
    activity = Activity(name=name, user_id=user.id)
    db.session.add(activity)
    db.session.flush()
    for sub_name, exp in subs:
        db.session.add(SubActivity(
            name=sub_name, activity_id=activity.id, base_exp=exp,
            difficulty_multiplier=1.0,
            attribute_weights={"INT": 1.0} if exp == 100 else {"FCS": 1.0},
            scheduled_time=45,
        ))
    db.session.flush()
    return activity


@pytest.fixture()
def kim(app):
    """Target account with School>Math (09-21 08:00, exp 100) and Context Switch."""
    user = add_user("kim")
    school = add_activity(user, "School", [("Math", 100)])
    add_activity(user, "Context Switch", [("Deep Work", 80)])
    tt = Timetable(user_id=user.id, date=date(2026, 9, 21))
    db.session.add(tt)
    db.session.flush()
    math = school.sub_activities[0]
    entry = TimetableEntry(timetable_id=tt.id, sub_activity_id=math.id,
                           start_time=time(8, 0), end_time=time(9, 0))
    db.session.add(entry)
    db.session.flush()
    db.session.add(CompletionLog(user_id=user.id, sub_activity_id=math.id,
                                 timetable_entry_id=entry.id,
                                 completed_on=date(2026, 9, 21),
                                 status="completed", exp_impact=100, reason="done"))
    user.total_exp = 100
    user.level = 1
    db.session.commit()
    return user


@pytest.fixture()
def client(app, kim):
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["user_id"] = kim.id
    return test_client


@pytest.fixture()
def login_client(app):
    """A test client that can log any fixture user in via session_by_id()."""

    class _L:
        def __init__(self, application):
            self.application = application
            self.client = application.test_client()

        def as_user(self, user):
            with self.client.session_transaction() as sess:
                sess["user_id"] = user.id
            return self.client

    return _L(app)