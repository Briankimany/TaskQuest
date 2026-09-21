"""
Parameterized data seeding for e2e tests and given-date demos.

Every scenario runs inside an app context against whatever database the app is
configured with. The e2e runner points ``TASKQUEST_DATABASE_URL`` at a throwaway
sqlite file in a temp directory, so the development database is never touched.

Usage:
    python -m app.seed.e2e_seeds --user kim --scenario mission-day
    python -m app.seed.e2e_seeds --user kim --date 2026-09-15 --scenario full-week

Scenarios:
    mission-day   - one day with a mixed state (done / 2 active / late) so the
                    dashboard shows ACTIVE missions that can be completed in a
                    headed browser during the e2e run.
    full-week     - mission-day today plus the previous 6 days fully completed,
                    giving a coherent streak and a dated XP-flow chart.
"""
from datetime import datetime, date, time, timedelta

from app.models import db, User, Level, Activity, SubActivity
from app.models import Timetable, TimetableEntry, CompletionLog
from app.utils.managers.timetable_manager import TimetableManager
from app.config import ATTRIBUTES_LIST
from app.utils.timezones import now_for

SCENARIOS = ("mission-day", "full-week")

# Deterministic standard library keyed by sub-activity name.
# (name, scheduled_time_minutes, difficulty_multiplier, attribute_weights)
LIBRARY = {
    "Fitness": [
        ("Morning Run", 40, 1.0, {"INT": 0.1, "STA": 0.6, "FCS": 0.1, "CHA": 0.1, "DSC": 0.1}),
        ("Yoga", 30, 0.8, {"INT": 0.1, "STA": 0.4, "FCS": 0.3, "CHA": 0.1, "DSC": 0.1}),
    ],
    "Learning": [
        ("Read Book", 60, 1.0, {"INT": 0.7, "STA": 0.0, "FCS": 0.2, "CHA": 0.0, "DSC": 0.1}),
        ("Study Language", 45, 1.1, {"INT": 0.6, "STA": 0.0, "FCS": 0.3, "CHA": 0.1, "DSC": 0.0}),
    ],
    "Projects": [
        ("Build Project", 90, 1.2, {"INT": 0.1, "STA": 0.0, "FCS": 0.6, "CHA": 0.1, "DSC": 0.2}),
        ("Side Project Code", 60, 1.15, {"INT": 0.2, "STA": 0.0, "FCS": 0.6, "CHA": 0.0, "DSC": 0.2}),
    ],
    "Discipline": [
        ("Meditation", 20, 0.7, {"INT": 0.0, "STA": 0.0, "FCS": 0.7, "CHA": 0.0, "DSC": 0.3}),
        ("Journal Entry", 15, 0.6, {"INT": 0.5, "STA": 0.0, "FCS": 0.0, "CHA": 0.1, "DSC": 0.4}),
    ],
}


def ensure_levels(count: int = 40):
    """Create level rows up to ``count`` if they do not exist yet."""
    existing = {l.level_number for l in Level.query.all()}
    created = 0
    for n in range(1, count + 1):
        if n in existing:
            continue
        db.session.add(Level(
            level_number=n,
            required_exp=500 * n,  # level N requires entering XP threshold of 500*N
            reward_description=f"Level {n} unlocked",
        ))
        created += 1
    if created:
        db.session.commit()
    return created


def seed_user(username: str = "kim", email: str = "kim@taskquest.dev",
              password: str = "TestPass123!", level: int = 4, **attrs) -> User:
    """Create (or update) a user with fixed attributes/level/exp."""
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, email=email)
        user.password = password
        db.session.add(user)
    else:
        user.email = email
        user.password = password
    db.session.commit()
    user.level = level
    next_level = Level.query.filter(Level.level_number > level).order_by(Level.level_number).first()
    user.total_exp = int(next_level.required_exp * 0.82) if next_level else user.total_exp
    for k in ATTRIBUTES_LIST:
        setattr(user, k, attrs.get(k, {"INT": 62, "STA": 55, "FCS": 58, "CHA": 48, "DSC": 53}[k]))
    db.session.commit()
    return user


def seed_library(user_id: int):
    """Create the standard activity/sub-activity library once per user."""
    subs = {}
    for activity_name, items in LIBRARY.items():
        activity = Activity.query.filter_by(user_id=user_id, name=activity_name).first()
        if not activity:
            activity = Activity(name=activity_name, user_id=user_id)
            db.session.add(activity)
            db.session.flush()
        for sub_name, minutes, difficulty, weights in items:
            sub = SubActivity.query.filter_by(activity_id=activity.id, name=sub_name).first()
            if not sub:
                sub = SubActivity(
                    name=sub_name,
                    activity_id=activity.id,
                    difficulty_multiplier=difficulty,
                    base_exp=100,
                    attribute_weights=weights,
                    scheduled_time=minutes,
                )
                db.session.add(sub)
                db.session.flush()
            subs[sub_name] = sub
    db.session.commit()
    return subs


def _potential_exp(sub: SubActivity, start: time, end: time) -> int:
    minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
    return int(sub.base_exp * (minutes / 60) * sub.difficulty_multiplier)


def _log(user_id: int, entry: TimetableEntry, status: str, reason: str = None):
    sub = entry.sub_activity
    potential = _potential_exp(sub, entry.start_time, entry.end_time)
    if status in ("completed", "done"):
        exp = potential
    elif status == "late":
        exp = -max(5, int(potential * 0.35))
    elif status == "skipped":
        exp = -max(10, int(potential * 0.8))
    else:
        return None
    log = CompletionLog(
        user_id=user_id,
        sub_activity_id=sub.id,
        timetable_entry_id=entry.id,
        completed_on=entry.timetable.date,
        actual_time_taken=max(0, (entry.end_time.hour * 60 + entry.end_time.minute) -
                              (entry.start_time.hour * 60 + entry.start_time.minute)),
        status=("completed" if status in ("completed", "done", "late") else "skipped"),
        reason=reason,
        exp_impact=exp,
        comment=("E2E_SEED" if status in ("completed", "late", "skipped") else None),
    )
    db.session.add(log)
    return log


def _clear_day(user_id: int, day: date):
    """Drop a day's timetables, entries and logs so reseeding is idempotent."""
    for tt in Timetable.query.filter_by(user_id=user_id, date=day).all():
        db.session.delete(tt)
    for log in CompletionLog.query.filter_by(user_id=user_id, completed_on=day).all():
        db.session.delete(log)
    db.session.commit()


def seed_day(user_id: int, day: date, plan):
    """Seed a timetable for ``day`` with the given plan.

    ``plan`` is a list of dicts: {name, start, end, status, reason}.
    Status in {'done', 'active', 'late', 'skipped'}.
    Idempotent: drops that day's timetable/logs first when reseeding.
    """
    _clear_day(user_id, day)

    subs = seed_library(user_id)
    timetable = TimetableManager.get_or_create_timetable(user_id, day)

    for item in plan:
        sub = subs[item["name"]]
        start = item["start"]
        end = item["end"]
        entry = TimetableEntry(
            timetable_id=timetable.id,
            sub_activity_id=sub.id,
            start_time=start,
            end_time=end,
            cyclic=False,
            weekday=None,
        )
        db.session.add(entry)
        db.session.flush()
        if item["status"] != "active":
            _log(user_id, entry, item["status"], item.get("reason"))

    db.session.commit()
    return timetable


def future_slot(name: str, end_minutes_from_now: int, duration_minutes: int = 45, now=None):
    """A plan slot whose window ends ``end_minutes_from_now`` minutes from now.

    Expected to be completed by the browser shortly after seeding, so it must
    end inside the ±15-minute grace window to avoid any LLM penalty lookup.
    """
    now = now or datetime.now()
    end = (now + timedelta(minutes=end_minutes_from_now))
    end = end.replace(second=0, microsecond=0)
    if end.hour == 23 and end.minute > 50:  # never cross midnight
        end = end.replace(hour=23, minute=50)
    start = (end - timedelta(minutes=duration_minutes))
    return {"name": name, "start": start.time(), "end": end.time(), "status": "active"}


def mission_day_plan(now=None):
    """Mixed day: 1 done (past morning), 2 active (future), 1 late (past).
    Gives DCP = 2 scheduled-with-logs / 4 non-buffer = 0.5 -> STABLE."""
    now = now or datetime.now()
    morning_end = now.replace(hour=8, minute=0, second=0, microsecond=0)
    late_end = now.replace(hour=9, minute=30, second=0, microsecond=0)
    if late_end >= now:  # late task must already be past
        late_end = now - timedelta(hours=2)
        morning_end = now - timedelta(hours=3)
    morning_start = morning_end - timedelta(minutes=40)
    late_start = late_end - timedelta(minutes=20)
    return [
        {"name": "Morning Run", "start": morning_start.time(), "end": morning_end.time(),
         "status": "done"},
        future_slot("Read Book", 10, now=now),
        future_slot("Build Project", 14, duration_minutes=60, now=now),
        {"name": "Meditation", "start": late_start.time(), "end": late_end.time(),
         "status": "late", "reason": "Overran morning meetings"},
    ]


def full_complete_day(user_id: int, day: date):
    """A fully-completed (DCP 1.0) day of 3 tasks."""
    _clear_day(user_id, day)
    subs = seed_library(user_id)
    timetable = TimetableManager.get_or_create_timetable(user_id, day)
    for name, start, end in [
        ("Morning Run", time(7, 0), time(7, 40)),
        ("Read Book", time(12, 0), time(13, 0)),
        ("Build Project", time(17, 0), time(18, 30)),
    ]:
        entry = TimetableEntry(
            timetable_id=timetable.id,
            sub_activity_id=subs[name].id,
            start_time=start,
            end_time=end,
            cyclic=False,
        )
        db.session.add(entry)
        db.session.flush()
        _log(user_id, entry, "completed")
    db.session.commit()


def run_scenario(username: str = "kim", scenario: str = "mission-day", day: date = None) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from {SCENARIOS}")

    ensure_levels()
    user = seed_user(username=username)
    stats = {"user": user.username, "activities": 0, "timetables": 0, "entries": 0, "logs": 0}

    user_now = now_for(user)
    day = day or user_now.date()

    subs = seed_library(user.id)
    stats["activities"] = len(LIBRARY)

    if scenario == "mission-day":
        seed_day(user.id, day, mission_day_plan(now=user_now))
    else:  # full-week
        for i in range(6, 0, -1):
            full_complete_day(user.id, day - timedelta(days=i))
        seed_day(user.id, day, mission_day_plan(now=user_now))

    stats["timetables"] = Timetable.query.filter_by(user_id=user.id).count()
    stats["entries"] = TimetableEntry.query.join(Timetable).filter(
        Timetable.user_id == user.id).count()
    stats["logs"] = CompletionLog.query.filter_by(user_id=user.id).count()
    return stats


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"Invalid date '{value}' — expected YYYY-MM-DD")


if __name__ == "__main__":
    import argparse
    from app.init import create_app

    parser = argparse.ArgumentParser(description="Seed e2e/demo data.")
    parser.add_argument("--user", default="kim")
    parser.add_argument("--scenario", default="mission-day", choices=SCENARIOS)
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    with create_app().app_context():
        result = run_scenario(username=args.user, scenario=args.scenario,
                              day=_parse_date(args.date) if args.date else None)
        print("SEEDED", result)