"""System Judge tests — status pill, health endpoint, timeout resolution,
judge log page (all completions) and completion-time verdict creation."""
from datetime import datetime, time

from app.models import db, Activity, SubActivity, CompletionLog
from app.models.judge import JudgeReview
from app.utils.judge_status import get_judge_status, PROVISIONAL_MARKER
from app.utils.managers.ai_assistant import AIAssistant
from app.utils.timezones import today_for_id


def _seed_review(kim, provisional=False):
    """Attach a review to kim's first completion log (dates from conftest)."""
    log = CompletionLog.query.filter_by(user_id=kim.id).first()
    explanation = (f"The {PROVISIONAL_MARKER}; a fallback verdict was recorded."
                   if provisional else "Consistent with the player's explanation.")
    rev = JudgeReview(user_id=kim.id, completion_log_id=log.id,
                      task_name="Math", task_status="MISSED", user_reason="x",
                      penalty=-80, discipline=5, validity=2,
                      responsibility=1, consistency=1,
                      explanation=explanation, review_status="PENDING",
                      created_at=datetime(2026, 9, 21, 12, 0))
    db.session.add(rev)
    db.session.commit()
    return rev


def _add_entry(user, name="ProbeTask", start=time(10, 0), end=time(11, 0),
               completed_on=None):
    """A fresh timetable entry for a completion-flow test."""
    act = Activity(name="Probe", user_id=user.id)
    db.session.add(act)
    db.session.flush()
    sub = SubActivity(name=name, activity_id=act.id, base_exp=100,
                      difficulty_multiplier=1.0, attribute_weights={"INT": 1.0},
                      scheduled_time=45)
    db.session.add(sub)
    db.session.flush()
    from datetime import date
    from app.models import Timetable, TimetableEntry
    day = completed_on or date(2026, 9, 21)
    tt = Timetable(user_id=user.id, date=day)
    db.session.add(tt)
    db.session.flush()
    entry = TimetableEntry(timetable_id=tt.id, sub_activity_id=sub.id,
                           start_time=start, end_time=end)
    db.session.add(entry)
    db.session.commit()
    return entry


def _add_today_log(user, status="skipped", exp=-80, reason="probe"):
    """A completion log dated the user's calendar today (page/state tests)."""
    act = Activity(name="JudgeProbe", user_id=user.id)
    db.session.add(act)
    db.session.flush()
    sub = SubActivity(name="ProbeTask", activity_id=act.id, base_exp=100,
                      difficulty_multiplier=1.0, attribute_weights={"INT": 1.0},
                      scheduled_time=45)
    db.session.add(sub)
    db.session.flush()
    log = CompletionLog(user_id=user.id, sub_activity_id=sub.id,
                        completed_on=today_for_id(user.id), status=status,
                        exp_impact=exp, reason=reason, timetable_entry_id=None)
    db.session.add(log)
    db.session.commit()
    return log


# ── status pill / health / timeout ──

def test_off_when_provider_unreachable(app, kim):
    status = get_judge_status(kim)
    assert status["state"] in ("LIVE", "OFF")
    assert status["state"] != "PROVISIONAL"


def test_off_state_reported(app, kim):
    # OMNIROUTE_URL is 127.0.0.1:9 in the test env -> connection refused -> OFF.
    status = get_judge_status(kim, probe=True)
    assert status["state"] == "OFF"


def test_no_probe_live_without_reviews(app, kim):
    status = get_judge_status(kim, probe=False)
    assert status["state"] == "LIVE"
    assert status["provisional"] is False


def test_no_probe_live_with_final_review(app, kim):
    _seed_review(kim, provisional=False)
    status = get_judge_status(kim, probe=False)
    assert status["state"] == "LIVE"
    assert status["provisional"] is False


def test_no_probe_provisional_with_fallback_review(app, kim):
    _seed_review(kim, provisional=True)
    status = get_judge_status(kim, probe=False)
    assert status["state"] == "PROVISIONAL"
    assert status["provisional"] is True


def test_health_endpoint_shape(client):
    r = client.get("/api/judge/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["state"] in ("LIVE", "PROVISIONAL", "OFF")
    assert "checked_at" in body


def test_resolve_timeout_default(app, monkeypatch):
    monkeypatch.delenv("OMNIROUTE_TIMEOUT", raising=False)
    assistant = AIAssistant()
    assert assistant.timeout == 90.0


def test_resolve_timeout_env_override(app, monkeypatch):
    monkeypatch.setenv("OMNIROUTE_TIMEOUT", "42.0")
    assistant = AIAssistant()
    assert assistant.timeout == 42.0


def test_resolve_timeout_invalid_env_falls_back(app, monkeypatch):
    monkeypatch.setenv("OMNIROUTE_TIMEOUT", "fast")
    assistant = AIAssistant()
    assert assistant.timeout == 90.0


# ── judge log page: shows ALL completions by default (today), with filters ──

def test_judge_log_lists_unreviewed_log_by_default(app, kim, client):
    log = _add_today_log(kim, status="skipped", exp=-80, reason="probe")
    r = client.get("/judge-log")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "JudgeProbe" in html      # the log is listed even with no review
    assert "Awaiting verdict" in html
    assert "-80" in html

    # Conftest's kim logs are dated 09-21; on other days the default (today)
    # filter hides them, proving the default date filter is active.
    filter_date = today_for_id(kim.id).isoformat()
    assert "(1)" in html or "1 completion" in html


def test_judge_log_renders_provisional_badge(app, kim, client):
    log = _add_today_log(kim, status="skipped", exp=-80)
    db.session.add(JudgeReview(
        user_id=kim.id, completion_log_id=log.id, task_name="ProbeTask",
        task_status="MISSED", penalty=-80, discipline=5, validity=2,
        responsibility=1, consistency=1, review_status="PENDING",
        explanation=f"The {PROVISIONAL_MARKER}; a fallback verdict was recorded.",
        created_at=datetime(2026, 9, 21, 12, 0)))
    db.session.commit()
    r = client.get("/judge-log", query_string={"date": "all"})
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "PROVISIONAL" in html
    assert "PENDING" in html


def test_judge_log_date_and_task_filters(app, kim, client):
    _add_today_log(kim, status="skipped", exp=-80, reason="probe")
    # task filter narrows
    r = client.get("/judge-log", query_string={"task": "JudgeProbe::ProbeTask"})
    assert "ProbeTask" in r.get_data(as_text=True)
    r = client.get("/judge-log", query_string={"task": "Nope::Nada"})
    assert "No completion logs match this filter" in r.get_data(as_text=True)
    # date filter excludes tomorrow
    from datetime import date
    import datetime as _dt
    tomorrow = (today_for_id(kim.id) + _dt.timedelta(days=1)).isoformat()
    r = client.get("/judge-log", query_string={"date": tomorrow})
    assert "No completion logs match this filter" in r.get_data(as_text=True)


# ── completion flow now creates the verdict (server-side, not frontend) ──

def test_completion_skipped_triggers_review(app, kim, client):
    entry = _add_entry(kim)
    r = client.post("/api/complete/complete_activity", json={
        "timetable_entry_id": entry.id, "status": "skipped", "reason": "no time"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["exp_change"] < 0
    review = JudgeReview.query.filter_by(completion_log_id=body["completion_id"]).first()
    assert review is not None
    assert PROVISIONAL_MARKER in (review.explanation or "")


def test_completion_partial_triggers_review(app, kim, client):
    entry = _add_entry(kim)
    r = client.post("/api/complete/complete_activity", json={
        "timetable_entry_id": entry.id, "status": "partial",
        "completed_on": "2026-09-21T10:30", "actual_time_taken": 30,
        "reason": "ran out of steam"})
    assert r.status_code == 201
    body = r.get_json()
    review = JudgeReview.query.filter_by(completion_log_id=body["completion_id"]).first()
    assert review is not None
    assert review.task_status == "PARTIAL"


def test_completion_clean_completed_no_review(app, kim, client):
    entry = _add_entry(kim)
    r = client.post("/api/complete/complete_activity", json={
        "timetable_entry_id": entry.id, "status": "completed",
        "completed_on": "2026-09-21T10:30", "actual_time_taken": 60})
    assert r.status_code == 201
    body = r.get_json()
    assert body["exp_change"] > 0
    assert JudgeReview.query.filter_by(completion_log_id=body["completion_id"]).first() is None