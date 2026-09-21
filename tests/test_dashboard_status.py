"""Mission/activity status payloads — logged tasks surface as done on the
dashboard (completed=green check, partial=amber check, skipped=MISSED)."""
from datetime import time

from app.models import db, Activity, SubActivity, Timetable, TimetableEntry, CompletionLog
from app.utils.assets.dashboard_payloads import (
    build_missions, build_activity,
)
from app.utils.timezones import today_for_id


def _seed(user, rows):
    """One activity + one timetable for the user's today; one entry per row.

    ``rows`` is an iterable of (name, status, exp, start_time).
    """
    act = Activity(name="StatusProbe", user_id=user.id)
    db.session.add(act)
    db.session.flush()
    day = today_for_id(user.id)
    tt = Timetable.query.filter_by(user_id=user.id, date=day).first() \
        or Timetable(user_id=user.id, date=day)
    if not tt.id:
        db.session.add(tt)
        db.session.flush()
    created = []
    for name, status, exp, start in rows:
        sub = SubActivity(name=name, activity_id=act.id, base_exp=100,
                          difficulty_multiplier=1.0,
                          attribute_weights={"INT": 1.0}, scheduled_time=45)
        db.session.add(sub)
        db.session.flush()
        entry = TimetableEntry(timetable_id=tt.id, sub_activity_id=sub.id,
                               start_time=start, end_time=time(10, 0))
        db.session.add(entry)
        db.session.flush()
        db.session.add(CompletionLog(user_id=user.id, sub_activity_id=sub.id,
                                     timetable_entry_id=entry.id,
                                     completed_on=today_for_id(user.id),
                                     status=status, exp_impact=exp))
        created.append(entry)
    db.session.commit()
    return created


def test_missions_status_for_each_log_state(app, kim):
    e_done, e_partial, e_skip = _seed(kim, [
        ("DoneTask", "completed", 100, time(8, 0)),
        ("PartTask", "partial", 40, time(9, 0)),
        ("SkipTask", "skipped", -80, time(10, 0)),
    ])

    from app.utils.schedulers import TaskScheduler
    from app.utils.timezones import now_for
    now = now_for(kim)
    scheduled = TaskScheduler(user_id=kim.id, date=now).get_daily_schedule(
        user_id=kim.id, date_obj=today_for_id(kim.id))
    logs = CompletionLog.query.filter(
        CompletionLog.user_id == kim.id,
        CompletionLog.completed_on == today_for_id(kim.id)).all()
    missions = build_missions(scheduled, logs, today_for_id(kim.id), now=now)

    by_id = {m["id"]: m for m in missions}
    assert by_id[f"mission-{e_done.id}"]["status"] == "COMPLETED"
    assert by_id[f"mission-{e_partial.id}"]["status"] == "PARTIAL"
    assert by_id[f"mission-{e_skip.id}"]["status"] == "MISSED"


def test_activity_partial_label_for_partial_log(app, kim):
    _seed(kim, [("PartTask2", "partial", 40, time(9, 0))])
    logs = CompletionLog.query.filter_by(user_id=kim.id).all()
    activity = build_activity(logs)
    partial_rows = [a for a in activity if a["name"] == "PartTask2"]
    assert partial_rows and partial_rows[0]["status"] == "PARTIAL"
    assert partial_rows[0]["status_override"] is None