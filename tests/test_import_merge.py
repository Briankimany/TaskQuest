"""Merge-import unit tests — preview, apply, conflicts, idempotency, recompute."""
import copy

from app.models import db, User, Activity, CompletionLog
from app.models.judge import JudgeReview
from app.utils.backup_service import (
    export_user_data, preview_merge, apply_merge, BackupError,
)
from conftest import add_user


def _plan_counts(plan):
    to_add = plan["to_add"]
    entries_in_new_days = sum(len(tt.get("entries") or []) for tt in to_add["timetables"])
    entries_on_existing = sum(len(v) for v in (to_add.get("entries_on_existing") or {}).values())
    subs_in_new_acts = sum(len(a.get("sub_activities") or []) for a in to_add["activities"])
    return {
        "activities": len(to_add["activities"]),
        "sub_activities": len(to_add["inline_subs"]) + subs_in_new_acts,
        "timetables": len(to_add["timetables"]),
        "entries": entries_in_new_days + entries_on_existing,
        "logs": len(to_add["logs"]),
        "reviews": len(to_add["reviews"]),
    }


def _expect(kim, seed_payload):
    report, plan = preview_merge(kim, copy.deepcopy(seed_payload))
    summary = report["summary"]
    # hard-code to make the guarantee explicit (independent of the JSON notes)
    assert summary["activities_added"] == 2
    assert summary["activities_conflicts"] == 1
    assert summary["sub_activities_added"] == 4
    assert summary["sub_activities_conflicts"] == 1
    assert summary["timetables_added"] == 1
    assert summary["timetables_conflicts"] == 1
    assert summary["entries_added"] == 3
    assert summary["entries_conflicts"] == 1
    assert summary["logs_added"] == 4
    assert summary["logs_conflicts"] == 1
    assert summary["reviews_added"] == 2
    assert summary["reviews_skipped"] == 1

    nd = report["near_duplicates"]
    assert any(d["entity"] == "activity" and d["imported"] == "Contextswitch"
               and d["ratio"] >= 0.80 for d in nd), nd

    rec = report["recompute"]
    assert rec["total_exp_from"] == 100 and rec["total_exp_to"] == 160, rec

    assert _plan_counts(plan) == {
        "activities": 2, "sub_activities": 4, "timetables": 1,
        "entries": 3, "logs": 4, "reviews": 2,
    }
    return report, plan


def test_preview_expected_counts(app, kim, seed_payload):
    _expect(kim, seed_payload)


def test_apply_merges_and_recomputes(app, kim, seed_payload):
    kim_id = kim.id
    _, plan = _expect(kim, seed_payload)
    applied = apply_merge(kim, plan)
    assert applied["activities"] == 2 and applied["sub_activities"] == 4
    assert applied["logs"] == 4 and applied["reviews"] == 2

    db.session.expunge_all()
    user = User.query.get(kim_id)
    acts = {a.name for a in Activity.query.filter_by(user_id=kim_id).all()}
    assert acts == {"School", "Context Switch", "Contextswitch", "Workout"}
    school = Activity.query.filter_by(user_id=kim_id, name="School").one()
    assert {sa.name for sa in school.sub_activities} == {"Math", "physics"}
    assert CompletionLog.query.filter_by(user_id=kim_id).count() == 5
    assert JudgeReview.query.filter_by(user_id=kim_id).count() == 2
    assert user.total_exp == 160
    assert user.level == 1


def test_reapply_is_noop(app, kim, seed_payload):
    kim_id = kim.id
    _, plan = _expect(kim, seed_payload)
    apply_merge(kim, plan)
    db.session.expunge_all()

    report2, plan2 = preview_merge(User.query.get(kim_id), copy.deepcopy(seed_payload))
    s2 = report2["summary"]
    assert s2["activities_added"] == 0 and s2["sub_activities_added"] == 0
    assert s2["timetables_added"] == 0 and s2["entries_added"] == 0
    assert s2["logs_added"] == 0 and s2["reviews_added"] == 0
    assert apply_merge(User.query.get(kim_id), plan2)["activities"] == 0

    db.session.expunge_all()
    assert CompletionLog.query.filter_by(user_id=kim_id).count() == 5
    assert User.query.get(kim_id).total_exp == 160


def test_recompute_counts_null_impact_as_zero(app, kim, seed_payload):
    kim_id = kim.id
    _, plan = _expect(kim, seed_payload)
    apply_merge(kim, plan)
    db.session.expunge_all()
    assert User.query.get(kim_id).total_exp == 160  # press log has null impact


def test_import_into_fresh_account_restores(app, seed_payload):
    presto = add_user("presto")
    presto_id = presto.id
    report, plan = preview_merge(presto, copy.deepcopy(seed_payload))
    assert report["summary"]["activities_conflicts"] == 0
    apply_merge(presto, plan)
    db.session.expunge_all()
    assert User.query.get(presto_id).total_exp == 160
    assert {a.name for a in Activity.query.filter_by(user_id=presto_id).all()} \
        == {"school", "Contextswitch", "Workout"}


def test_other_user_untouched(app, kim, seed_payload):
    other = add_user("other")
    other.total_exp = 777
    db.session.commit()
    other_id = other.id
    _, plan = preview_merge(kim, copy.deepcopy(seed_payload))
    apply_merge(kim, plan)
    db.session.expunge_all()
    assert User.query.get(other_id).total_exp == 777


def test_conflicts_keep_target_values(app, kim, seed_payload):
    kim_id = kim.id
    school = Activity.query.filter_by(user_id=kim_id, name="School").one()
    school.sub_activities[0].base_exp = 999  # make the kept copy distinctive
    db.session.commit()
    _expect(kim, seed_payload)
    math = next(s for s in Activity.query.filter_by(user_id=kim_id, name="School")
                .one().sub_activities if s.name == "Math")
    assert math.base_exp == 999


def test_import_rejects_unknown_schema_version(app, kim, seed_payload):
    bad = copy.deepcopy(seed_payload)
    bad["schema_version"] = 99
    try:
        preview_merge(kim, bad)
        raise AssertionError("expected BackupError")
    except BackupError as exc:
        assert "Unsupported backup schema version" in str(exc)


def test_import_accepts_schema_v1_payload(app, kim, seed_payload):
    # v1 files carry the same entity shape but with the older version tag.
    v1 = copy.deepcopy(seed_payload)
    v1["schema_version"] = 1
    report, plan = preview_merge(kim, v1)
    assert report["summary"]["activities_added"] == 2
    assert apply_merge(kim, plan)["activities"] == 2


def test_import_rejects_missing_format_marker(app, kim, seed_payload):
    bad = copy.deepcopy(seed_payload)
    del bad["format"]
    try:
        preview_merge(kim, bad)
        raise AssertionError("expected BackupError")
    except BackupError as exc:
        assert "format marker" in str(exc)


def test_import_rejects_item_without_name(app, kim, seed_payload):
    bad = copy.deepcopy(seed_payload)
    bad["activities"][0]["name"] = ""
    try:
        preview_merge(kim, bad)
        raise AssertionError("expected BackupError")
    except BackupError as exc:
        assert "activities[0]" in str(exc)


def test_orphan_sub_reference_is_skipped_not_crash(app, kim, seed_payload):
    bad = copy.deepcopy(seed_payload)
    bad["completion_logs"][0]["sub_activity"] = "nope"
    bad["timetables"][0]["entries"][0]["sub_activity"] = "nope"
    bad["judge_reviews"][0]["sub_activity"] = "nope"
    report, plan = preview_merge(kim, bad)
    applied = apply_merge(kim, plan)
    assert applied["logs"] == len(plan["to_add"]["logs"])  # orphans skipped, rest applied
    assert applied["entries"] == _plan_counts(plan)["entries"]
    assert applied["activities"] == 2


def test_export_import_export_identity(app, kim):
    """A CLI round-trip: kim export -> fresh account -> second export matches."""
    original = export_user_data(kim)
    copy_id = add_user("roundtrip").id
    _, plan = preview_merge(User.query.get(copy_id), original)
    apply_merge(User.query.get(copy_id), plan)
    db.session.expunge_all()
    restored = export_user_data(User.query.get(copy_id))
    assert restored["completion_logs"] == original["completion_logs"]
    assert restored["judge_reviews"] == original["judge_reviews"]