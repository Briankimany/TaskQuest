"""Export format tests — schema v2 shape and structural round-trips."""
import copy
from datetime import date

from app.models import db, User, CompletionLog
from app.utils.backup_service import export_user_data, preview_merge, apply_merge

_VOLATILE = {"created_at", "updated_at", "exported_at"}


def _drop_volatile(node):
    if isinstance(node, dict):
        return {k: _drop_volatile(v) for k, v in node.items() if k not in _VOLATILE}
    if isinstance(node, list):
        return [_drop_volatile(v) for v in node]
    return node


def _canonical(payload):
    """Sort entity lists so two exports with different insert orders compare equal."""
    data = _drop_volatile(payload)
    data["activities"] = sorted(
        data["activities"], key=lambda a: (a["name"], [s["name"] for s in a["sub_activities"]]))
    for activity in data["activities"]:
        activity["sub_activities"] = sorted(activity["sub_activities"], key=lambda s: s["name"])
    data["timetables"] = sorted(data["timetables"], key=lambda t: t["date"])
    for tt in data["timetables"]:
        tt["entries"] = sorted(
            tt["entries"], key=lambda e: (e["activity"], e["sub_activity"], e["start_time"]))
    data["completion_logs"] = sorted(
        data["completion_logs"],
        key=lambda l: (l["activity"], l["sub_activity"], l["completed_on"], l.get("timetable_date")))
    data["judge_reviews"] = sorted(
        data["judge_reviews"],
        key=lambda r: (r["activity"], r["sub_activity"], r["completed_on"], r["task_status"]))
    return data


def test_export_v2_shape(app, kim):
    payload = export_user_data(kim)
    assert payload["format"] == "taskquest-backup"
    assert payload["schema_version"] == 2
    assert payload["owner"] == "kim"
    assert payload["user"]["timezone"] == "Africa/Nairobi"
    for key in ("activities", "timetables", "completion_logs", "judge_reviews"):
        assert isinstance(payload[key], list)


def test_export_has_all_target_data(app, kim, seed_payload):
    payload = export_user_data(kim)
    names = [a["name"] for a in payload["activities"]]
    assert "School" in names and "Context Switch" in names
    school = next(a for a in payload["activities"] if a["name"] == "School")
    assert [s["name"] for s in school["sub_activities"]] == ["Math"]
    assert payload["completion_logs"][0]["exp_impact"] == 100
    assert payload["user"]["total_exp"] == 100


def test_roundtrip_into_fresh_account_preserves_structure(app, kim):
    original = export_user_data(kim)

    copy_user = User(username="copy", email="copy@t.dev")
    copy_user.password = "TestPass123!"
    copy_user.timezone = "Africa/Nairobi"
    db.session.add(copy_user)
    db.session.commit()

    report, plan = preview_merge(copy_user, original)
    assert report["summary"]["activities_added"] == 2
    apply_merge(copy_user, plan)
    db.session.expunge_all()

    restored = export_user_data(User.query.filter_by(username="copy").first())
    # User identity/stats may legitimately differ (attrs kept = 0s; copy stats recomputed);
    # every data section must come back byte-for-byte after canonical sorting.
    assert _canonical(restored)["activities"] == _canonical(original)["activities"]
    assert _canonical(restored)["timetables"] == _canonical(original)["timetables"]
    assert _canonical(restored)["completion_logs"] == _canonical(original)["completion_logs"]
    assert _canonical(restored)["judge_reviews"] == _canonical(original)["judge_reviews"]


def test_null_exp_impact_survives_export(app, kim):
    sub = kim.activities[0].sub_activities[0]
    db.session.add(CompletionLog(
        user_id=kim.id, sub_activity_id=sub.id, completed_on=date(2026, 9, 22),
        status="completed", exp_impact=None, reason="no difficulty"))
    db.session.commit()
    payload = export_user_data(kim)
    assert any(l["exp_impact"] is None for l in payload["completion_logs"])


def test_seed_payload_validation_matches_model_order(app, kim, seed_payload):
    report, plan = preview_merge(kim, copy.deepcopy(seed_payload))
    assert report["imported_user"]["username"] == "gatu"
    assert report["imported_user"]["timezone"] == "America/New_York"