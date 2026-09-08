"""
Seed today's schedule + completion logs so the Garden RPG dashboard has
reference-style data: a MISSED main mission (red status override), an
in-progress purple special task, and mixed DAILY/SIDE color variety.

Idempotent: if a Timetable already exists for today it refuses to touch data.
Run with:

    venv\\Scripts\\python.exe -m app.seed.seed_today
"""
from datetime import datetime, date, time

from app.models import db, Activity, SubActivity, Timetable, TimetableEntry, CompletionLog
from app.config import seed_data_folder  # noqa: F401  (import matches app/seed conventions)
from app.init import create_app

USER_ID = 1  # "kim"


def _get_or_create_sub(activity_name, sub_name, scheduled_time, multiplier, weights):
    """Find an existing SubActivity by name within user's activity, else create it."""
    activity = Activity.query.filter_by(user_id=USER_ID, name=activity_name).first()
    if not activity:
        activity = Activity(name=activity_name, user_id=USER_ID, is_active=True)
        db.session.add(activity)
        db.session.flush()

    sub = SubActivity.query.filter_by(activity_id=activity.id, name=sub_name).first()
    if sub:
        return sub
    sub = SubActivity(
        name=sub_name,
        activity_id=activity.id,
        difficulty_multiplier=multiplier,
        base_exp=70,
        attribute_weights=weights,
        active=True,
        scheduled_time=scheduled_time,
    )
    db.session.add(sub)
    return sub


def seed_today(day=None):
    day = day or datetime.now().date()

    existing = Timetable.query.filter_by(user_id=USER_ID, date=day).first()
    if existing:
        print(f"Timetable already exists for {day} — skipping (idempotent).")
        return False

    subs = {
        "morning_run": SubActivity.query.get(5),              # Fitness.Morning Run
        "exercise_hiit": _get_or_create_sub(
            "Fitness", "Exercise (HIIT)", 45, 1.2,
            {"INT": 0.1, "STA": 0.6, "FCS": 0.1, "CHA": 0.1, "DSC": 0.1}),
        "read_book": SubActivity.query.get(3),                # Learning.Read Book
        "build_project": _get_or_create_sub(
            "Projects", "Build Project", 60, 1.15,
            {"INT": 0.1, "STA": 0.1, "FCS": 0.6, "CHA": 0.1, "DSC": 0.1}),
        "meditation": SubActivity.query.get(9),               # Discipline.Meditation
    }
    db.session.flush()

    timetable = Timetable(user_id=USER_ID, date=day, finalized=True)
    db.session.add(timetable)
    db.session.flush()

    def entry(sub_key, start, end):
        e = TimetableEntry(
            timetable_id=timetable.id,
            sub_activity_id=subs[sub_key].id,
            start_time=time.fromisoformat(start),
            end_time=time.fromisoformat(end),
            cyclic=False,
            weekday=None,
        )
        db.session.add(e)
        return e

    entries = {
        "morning_run": entry("morning_run", "07:00", "07:40"),
        "exercise_hiit": entry("exercise_hiit", "09:00", "09:45"),
        "read_book": entry("read_book", "12:00", "12:45"),
        "build_project": entry("build_project", "15:00", "16:00"),
        "meditation": entry("meditation", "19:00", "19:25"),
    }
    db.session.flush()

    db.session.add(CompletionLog(
        user_id=USER_ID,
        sub_activity_id=subs["morning_run"].id,
        timetable_entry_id=entries["morning_run"].id,
        completed_on=day,
        actual_time_taken=0,
        status="skipped",
        reason="Morning run superseded by urgent family call",
        exp_impact=-38,
        comment="MISSED",
    ))
    db.session.add(CompletionLog(
        user_id=USER_ID,
        sub_activity_id=subs["meditation"].id,
        timetable_entry_id=entries["meditation"].id,
        completed_on=day,
        actual_time_taken=20,
        status="completed",
        reason=None,
        exp_impact=-12,
        comment="COMPLETED_LATE",
    ))

    db.session.commit()
    print(f"Seeded {day} ({len(entries)} missions, 2 completion logs) for user {USER_ID}.")
    return True


if __name__ == "__main__":
    with create_app().app_context():
        seed_today()