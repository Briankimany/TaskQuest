"""
Backup / merge-import service.

Exports a user's entire data (activities, sub-activities, timetables,
completion logs, judge reviews) into a single JSON document (schema v2),
and imports it back as a MERGE:

- Your data is never replaced or deleted.
- A matching row keeps the TARGET's copy; the imported copy is skipped.
- Every conflict / skip / near-duplicate is reported on the import page
  (report-and-continue — nothing blocks).
- Re-importing the same file is a no-op (keys are deterministic).
- After a merge, stats are recomputed from the merged union of logs:
  ``total_exp`` = sum of ``exp_impact`` (None counts as 0), ``level`` from the
  ``Level.required_exp`` curve, attribute points are kept as-is.
"""
from datetime import date, datetime

from app.models import (Activity, SubActivity, Timetable, TimetableEntry,
                        CompletionLog, Level, db)
from app.models.judge import JudgeReview
from app.models.timetable import WeekDay
from app.utils.merge_matcher import (
    normalize_name,
    sub_path_key,
    entry_key,
    log_key,
    near_duplicate,
)

FORMAT_ID = "taskquest-backup"
SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = (1, 2)


def _utc_now():
    from app.utils.timezones import utc_now_naive
    return utc_now_naive()


def _default_timezone():
    from app.utils.timezones import DEFAULT_TIMEZONE
    return DEFAULT_TIMEZONE


class BackupError(ValueError):
    """Raised when an import payload is malformed or unsupported."""


def _iso_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def _iso_dt(value):
    if value is None:
        return None
    return value.isoformat()


def export_user_data(user):
    """Return a JSON-serializable dict with all of the user's data (schema v2)."""
    user_id = user.id

    activities = []
    for activity in Activity.query.filter_by(user_id=user_id).order_by(Activity.id).all():
        activities.append({
            "name": activity.name,
            "created_at": _iso_dt(activity.created_at),
            "is_active": activity.is_active,
            "sub_activities": [{
                "name": sa.name,
                "difficulty_multiplier": sa.difficulty_multiplier,
                "base_exp": sa.base_exp,
                "attribute_weights": dict(sa.attribute_weights or {}),
                "active": sa.active,
                "scheduled_time": sa.scheduled_time,
            } for sa in activity.sub_activities],
        })

    timetables = []
    for tt in Timetable.query.filter_by(user_id=user_id).order_by(Timetable.date).all():
        timetables.append({
            "date": _iso_date(tt.date),
            "goal_text": tt.goal_text,
            "meta_data": dict(tt.meta_data or {}),
            "finalized": tt.finalized,
            "entries": [{
                "activity": entry.sub_activity.activity.name,
                "sub_activity": entry.sub_activity.name,
                "start_time": str(entry.start_time)[:5],
                "end_time": str(entry.end_time)[:5],
                "cyclic": entry.cyclic,
                "weekday": int(entry.weekday) if entry.weekday is not None else None,
                "description": entry.description,
            } for entry in tt.entries],
        })

    logs = []
    for log in CompletionLog.query.filter_by(user_id=user_id).order_by(CompletionLog.id).all():
        logs.append({
            "activity": log.sub_activity.activity.name,
            "sub_activity": log.sub_activity.name,
            "timetable_date": _iso_date(log.timetable_entry.timetable.date)
                              if log.timetable_entry else None,
            "completed_on": _iso_date(log.completed_on),
            "actual_time_taken": log.actual_time_taken,
            "status": log.status,
            "reason": log.reason,
            "exp_impact": log.exp_impact,
            "comment": log.comment,
        })

    reviews = []
    for review in JudgeReview.query.filter_by(user_id=user_id).order_by(JudgeReview.id).all():
        log = review.completion_log
        reviews.append({
            "activity": log.sub_activity.activity.name,
            "sub_activity": log.sub_activity.name,
            "completed_on": _iso_date(log.completed_on),
            "task_name": review.task_name,
            "task_status": review.task_status,
            "user_reason": review.user_reason,
            "penalty": review.penalty,
            "discipline": review.discipline,
            "validity": review.validity,
            "responsibility": review.responsibility,
            "consistency": review.consistency,
            "explanation": review.explanation,
            "review_status": review.review_status,
            "dispute_reason": review.dispute_reason,
            "created_at": _iso_dt(review.created_at),
            "updated_at": _iso_dt(review.updated_at),
        })

    return {
        "format": FORMAT_ID,
        "schema_version": SCHEMA_VERSION,
        "exported_at": _utc_now().isoformat(),
        "owner": user.username,
        "user": {
            "username": user.username,
            "email": user.email,
            "timezone": user.timezone or _default_timezone(),
            "INT": user.INT,
            "STA": user.STA,
            "FCS": user.FCS,
            "CHA": user.CHA,
            "DSC": user.DSC,
            "level": user.level,
            "total_exp": user.total_exp,
            "created_at": _iso_dt(user.created_at),
        },
        "activities": activities,
        "timetables": timetables,
        "completion_logs": logs,
        "judge_reviews": reviews,
    }


# ---------------------------------------------------------------------------
# Payload validation
# ---------------------------------------------------------------------------

def _require_type(payload, key, types, what):
    if key not in payload:
        raise BackupError(f"Missing required section: {key!r}")
    value = payload[key]
    if not isinstance(value, types):
        raise BackupError(f"{what} must be {types}")
    return value


def _validate_payload(payload):
    """Validate a raw payload; return a lightweight wrapper dict."""
    if not isinstance(payload, dict):
        raise BackupError("Backup payload must be a JSON object.")
    if payload.get("format") != FORMAT_ID:
        raise BackupError("Not a TaskQuest backup file (missing format marker).")
    schema_version = payload.get("schema_version", SCHEMA_VERSION)
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise BackupError(f"Unsupported backup schema version: {schema_version!r}")
    user_data = _require_type(payload, "user", dict, "user section")
    activities_payload = _require_type(payload, "activities", list, "activities section")
    timetables_payload = _require_type(payload, "timetables", list, "timetables section")
    logs_payload = _require_type(payload, "completion_logs", list, "completion_logs section")
    reviews_payload = _require_type(payload, "judge_reviews", list, "judge_reviews section")
    _validate_activity_items(activities_payload)
    _validate_timetable_items(timetables_payload)
    _validate_log_items(logs_payload)
    _validate_review_items(reviews_payload)
    return {
        "schema_version": schema_version,
        "user": user_data,
        "activities": activities_payload,
        "timetables": timetables_payload,
        "logs": logs_payload,
        "reviews": reviews_payload,
    }


def _validate_activity_items(items):
    for i, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("name"):
            raise BackupError(f"activities[{i}] must be an object with a name.")
        for j, sub in enumerate(item.get("sub_activities") or []):
            if not isinstance(sub, dict) or not sub.get("name"):
                raise BackupError(f"activities[{i}].sub_activities[{j}] invalid.")


def _validate_timetable_items(items):
    for i, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("date"):
            raise BackupError(f"timetables[{i}] must be an object with a date.")
        try:
            _parse_date(item["date"])
        except (TypeError, ValueError):
            raise BackupError(f"timetables[{i}] has invalid date {item['date']!r}.")
        for j, entry in enumerate(item.get("entries") or []):
            if not isinstance(entry, dict):
                raise BackupError(f"timetables[{i}].entries[{j}] invalid.")
            for field in ("start_time", "end_time"):
                if entry.get(field):
                    try:
                        _parse_time(entry[field], f"timetables[{i}].entries[{j}] {field}")
                    except BackupError as exc:
                        raise BackupError(str(exc)) from exc
            weekday = entry.get("weekday")
            if weekday is not None:
                try:
                    WeekDay(int(weekday))
                except (TypeError, ValueError):
                    raise BackupError(
                        f"timetables[{i}].entries[{j}] has invalid weekday {weekday!r}.")


def _validate_log_items(items):
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise BackupError(f"completion_logs[{i}] invalid.")
        if item.get("timetable_date"):
            try:
                _parse_date(item["timetable_date"])
            except (TypeError, ValueError):
                raise BackupError(f"completion_logs[{i}] has invalid timetable date.")
        if item.get("completed_on"):
            try:
                _parse_date(item["completed_on"])
            except (TypeError, ValueError):
                raise BackupError(f"completion_logs[{i}] has invalid completed_on.")


def _validate_review_items(items):
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise BackupError(f"judge_reviews[{i}] invalid.")
        if item.get("completed_on"):
            try:
                _parse_date(item["completed_on"])
            except (TypeError, ValueError):
                raise BackupError(f"judge_reviews[{i}] has invalid completed_on.")


# ---------------------------------------------------------------------------
# Import: merge preview (pure simulation, no writes)
# ---------------------------------------------------------------------------

def preview_merge(user, payload):
    """Simulate merging ``payload`` into ``user``'s data.

    Returns ``(report, plan)`` where ``report`` describes every outcome
    (adds/conflicts/skips/near-duplicates/recompute prediction) and ``plan``
    is a JSON-serializable instruction set for :func:`apply_merge`.
    """
    parsed = _validate_payload(payload)
    user_id = user.id

    plan = {
        "format": FORMAT_ID,
        "schema_version": parsed["schema_version"],
        "owner": payload.get("owner"),
        "imported_user": {
            "username": parsed["user"].get("username"),
            "email": parsed["user"].get("email"),
            "timezone": parsed["user"].get("timezone"),
        },
        "to_add": {
            "activities": [],            # full activity dicts (with sub_activities)
            "inline_subs": [],           # subs to add under kept activities
            "timetables": [],            # full timetable dicts (new days)
            "entries_on_existing": {},   # {date_iso: [entry dicts]}
            "logs": [],                  # full log dicts
            "reviews": [],               # review dicts + "log_index"
        },
    }
    report = {
        "imported_user": plan["imported_user"],
        "summary": {
            "activities_added": 0, "activities_conflicts": 0,
            "sub_activities_added": 0, "sub_activities_conflicts": 0,
            "timetables_added": 0, "timetables_conflicts": 0,
            "entries_added": 0, "entries_conflicts": 0,
            "logs_added": 0, "logs_conflicts": 0,
            "reviews_added": 0, "reviews_skipped": 0,
        },
        "conflicts": [],
        "near_duplicates": [],
        "recompute": None,
    }

    target_activities = {normalize_name(a.name): a
                         for a in Activity.query.filter_by(user_id=user_id).all()}
    target_subs = _target_sub_map(user_id)
    available_sub_keys = set(target_subs)
    target_timetables = {tt.date: tt
                         for tt in Timetable.query.filter_by(user_id=user_id).all()}
    target_entries = _target_entry_map(user_id)
    target_logs = _target_log_map(user_id)

    for item in parsed["activities"]:
        act_name = str(item["name"])
        act_key = normalize_name(act_name)
        if act_key in target_activities:
            target_act = target_activities[act_key]
            report["summary"]["activities_conflicts"] += 1
            report["conflicts"].append({
                "entity": "activity", "imported": act_name, "kept": target_act.name,
            })
            # Descend into the kept activity and merge its sub-activities.
            existing_subs = {sub_path_key(target_act.name, sa.name): sa
                             for sa in target_act.sub_activities}
            for sub in item.get("sub_activities") or []:
                _merge_sub(sub, target_act.name, existing_subs, available_sub_keys,
                           plan, report)
        else:
            plan["to_add"]["activities"].append(item)
            report["summary"]["activities_added"] += 1
            for sub in item.get("sub_activities") or []:
                available_sub_keys.add(sub_path_key(act_name, sub.get("name", "")))
                report["summary"]["sub_activities_added"] += 1

    _near_duplicate_scan(parsed, target_activities, report)

    for tt_item in parsed["timetables"]:
        tt_date = _parse_date(tt_item["date"])
        if tt_date in target_timetables:
            report["summary"]["timetables_conflicts"] += 1
            report["conflicts"].append({
                "entity": "timetable", "imported": tt_date.isoformat(),
                "kept": tt_date.isoformat(),
            })
            _merge_entries_into_existing(tt_date, tt_item, available_sub_keys,
                                         existing_entry_keys=_entry_keys_of(target_timetables[tt_date]),
                                         plan=plan, report=report)
        else:
            kept_entries = []
            for entry in tt_item.get("entries") or []:
                if sub_path_key(entry.get("activity"), entry.get("sub_activity")) in available_sub_keys:
                    kept_entries.append(entry)
                else:
                    report["summary"]["entries_conflicts"] += 1
                    report["conflicts"].append({
                        "entity": "entry",
                        "imported": _describe_entry(tt_date, entry),
                        "kept": "entry skipped",
                    })
            report["summary"]["timetables_added"] += 1
            report["summary"]["entries_added"] += len(kept_entries)
            plan["to_add"]["timetables"].append(dict(tt_item, entries=kept_entries))

    target_entry_times = {
        (str(tt_date), (e_key[0], e_key[1])): e_key[2]
        for (tt_date, e_key), entry in target_entries.items()
    }
    additions = _AddSets(
        target_log_keys=set(target_logs),
        target_tt_dates=set(target_timetables),
        target_entry_times=target_entry_times,
    )
    plan["log_map"] = {}
    for i, item in enumerate(parsed["logs"]):
        if _plan_log(item, additions, available_sub_keys, plan, report):
            plan["log_map"][i] = len(plan["to_add"]["logs"]) - 1

    for item in parsed["reviews"]:
        _plan_review(item, parsed["logs"], plan, report)

    report["recompute"] = _predict_recompute(user, parsed,
                                             add_logs=plan["to_add"]["logs"])
    return report, plan


def _merge_sub(sub, act_name, existing_subs, available_sub_keys, plan, report):
    sub_name = str(sub["name"])
    key = sub_path_key(act_name, sub_name)
    if key in existing_subs:
        report["summary"]["sub_activities_conflicts"] += 1
        report["conflicts"].append({
            "entity": "sub_activity", "imported": f"{act_name} > {sub_name}",
            "kept": f"{act_name} > {existing_subs[key].name}",
        })
    else:
        plan["to_add"]["inline_subs"].append({"activity": act_name, "sub": dict(sub)})
        available_sub_keys.add(key)
        report["summary"]["sub_activities_added"] += 1


def _merge_entries_into_existing(tt_date, tt_item, available_sub_keys, existing_entry_keys,
                                 plan, report):
    added = []
    for entry in tt_item.get("entries") or []:
        if sub_path_key(entry.get("activity"), entry.get("sub_activity")) in available_sub_keys:
            e_key = entry_key(entry.get("activity"), entry.get("sub_activity"),
                              entry.get("start_time"))
            if e_key in existing_entry_keys:
                report["summary"]["entries_conflicts"] += 1
                report["conflicts"].append({
                    "entity": "entry",
                    "imported": _describe_entry(tt_date, entry),
                    "kept": "existing entry on target",
                })
            else:
                added.append(entry)
        else:
            report["summary"]["entries_conflicts"] += 1
            report["conflicts"].append({
                "entity": "entry",
                "imported": _describe_entry(tt_date, entry),
                "kept": "sub-activity not importable",
            })
    if added:
        plan["to_add"]["entries_on_existing"][tt_date.isoformat()] = added
        report["summary"]["entries_added"] += len(added)


def _target_sub_map_from_objects(target_tt):
    """Tiny sub map for a single kept timetable (used for entry classification)."""
    return {sub_path_key(e.sub_activity.activity.name, e.sub_activity.name): e.sub_activity
            for e in target_tt.entries}


def _entry_keys_of(target_tt):
    return set(entry_key(e.sub_activity.activity.name, e.sub_activity.name,
                         str(e.start_time)[:5]) for e in target_tt.entries)


def _near_duplicate_scan(parsed, target_activities, report):
    all_kept = [a.name for a in target_activities.values()]
    for item in parsed["activities"]:
        name = str(item["name"])
        if normalize_name(name) in target_activities:
            continue
        hit = near_duplicate(name, all_kept)
        if hit:
            report["near_duplicates"].append({
                "entity": "activity", "imported": name,
                "similar_to": hit[0], "ratio": round(hit[1], 2),
            })
    for item in parsed["activities"]:
        act_key = normalize_name(item["name"])
        if act_key not in target_activities:
            continue
        kept_activity = target_activities[act_key]
        kept_sub_names = [sa.name for sa in kept_activity.sub_activities]
        kept_sub_keys = {sub_path_key(kept_activity.name, sa.name)
                         for sa in kept_activity.sub_activities}
        for sub in item.get("sub_activities") or []:
            sub_name = str(sub["name"])
            if (sub_path_key(kept_activity.name, sub_name)) in kept_sub_keys:
                continue
            hit = near_duplicate(sub_name, kept_sub_names)
            if hit:
                report["near_duplicates"].append({
                    "entity": "sub_activity",
                    "imported": f"{kept_activity.name} > {sub_name}",
                    "similar_to": hit[0], "ratio": round(hit[1], 2),
                })


class _AddSets:
    """Tracks keys already present (target) or already planned (payload order)."""

    def __init__(self, target_log_keys, target_tt_dates, target_entry_times=None):
        self.known_log_keys = set(target_log_keys)
        self.known_tt_dates = set(target_tt_dates)
        self.target_entry_times = target_entry_times or {}


def _plan_log(item, additions, available_sub_keys, plan, report):
    act_name = item.get("activity")
    sub_name = item.get("sub_activity")
    completed_on = item.get("completed_on")
    tt_date = item.get("timetable_date")
    sub_key = sub_path_key(act_name, sub_name)
    if sub_key not in available_sub_keys:
        report["summary"]["logs_conflicts"] += 1
        report["conflicts"].append({
            "entity": "log",
            "imported": _describe_log(item),
            "kept": "unknown sub-activity reference",
        })
        return False
    start = None
    if tt_date:
        start = _find_payload_start_time(plan, tt_date, act_name, sub_name)
        if start is None:
            start = additions.target_entry_times.get((str(tt_date), sub_key))
    # Mirror the stored-side fallback: an unlinked log key resolves its
    # timetable-date tail to the completion day.
    key_tt_date = tt_date or completed_on
    key = log_key(act_name, sub_name, completed_on, start, key_tt_date)
    if key in additions.known_log_keys:
        report["summary"]["logs_conflicts"] += 1
        report["conflicts"].append({
            "entity": "log",
            "imported": _describe_log(item),
            "kept": "existing log on target",
        })
        return False
    additions.known_log_keys.add(key)
    log_item = dict(item)
    if start is not None:
        log_item["timetable_start"] = start
    plan["to_add"]["logs"].append(log_item)
    report["summary"]["logs_added"] += 1
    return True


def _find_payload_start_time(plan, tt_date, act_name, sub_name):
    try:
        want = _parse_date(tt_date)
    except (TypeError, ValueError):
        return None
    for tt in plan["to_add"]["timetables"]:
        try:
            if _parse_date(tt["date"]) == want:
                break
        except (TypeError, ValueError):
            continue
    else:
        tt = None
    candidates = []
    if tt is not None:
        candidates = tt["entries"]
    else:
        for date_iso, entries in (plan["to_add"].get("entries_on_existing") or {}).items():
            try:
                if _parse_date(date_iso) == want:
                    candidates = entries
                    break
            except (TypeError, ValueError):
                continue
    for entry in candidates:
        if str(entry.get("activity", "")) == str(act_name) and \
           str(entry.get("sub_activity", "")) == str(sub_name):
            return str(entry.get("start_time"))[:5]
    return None


def _describe_log(item):
    return (f"{item.get('completed_on')} / {item.get('activity')} > "
            f"{item.get('sub_activity')}")


def _describe_review(item):
    return f"{item.get('completed_on')} / {item.get('activity')} > {item.get('sub_activity')}"


def _describe_entry(tt_date, entry):
    return (f"{tt_date.isoformat()} / {entry.get('activity')} > "
            f"{entry.get('sub_activity')} @ {entry.get('start_time')}")


def _plan_review(item, logs_payload, plan, report):
    idx = _match_review_to_payload_log(item, logs_payload)
    if idx is None:
        report["summary"]["reviews_skipped"] += 1
        return
    plan_pos = plan["log_map"].get(idx)
    if plan_pos is None:
        report["summary"]["reviews_skipped"] += 1
        report["conflicts"].append({
            "entity": "review",
            "imported": _describe_review(item),
            "kept": "its completion log was not newly added",
        })
        return
    plan["to_add"]["reviews"].append(dict(item, log_index=plan_pos))
    report["summary"]["reviews_added"] += 1


# NOTE: log_index must be the index of the planned log in plan["to_add"]["logs"].
# _plan_review receives the payload-log index; payload atomicity guarantees the
# two match at apply time (created_log_ids is built from those same planned logs).
def _match_review_to_payload_log(item, logs_payload):
    act = str(item.get("activity", ""))
    sub = str(item.get("sub_activity", ""))
    completed_on = str(item.get("completed_on")) if item.get("completed_on") else None
    desired = {item.get("status"), item.get("reason"), item.get("exp_impact"),
               item.get("actual_time_taken")}
    for i, log in enumerate(logs_payload):
        if str(log.get("activity", "")) != act or str(log.get("sub_activity", "")) != sub:
            continue
        if completed_on and str(log.get("completed_on", "")) != completed_on:
            continue
        log_keys = {log.get("status"), log.get("reason"), log.get("exp_impact"),
                    log.get("actual_time_taken")}
        if desired & log_keys:
            return i
    return None


def _predict_recompute(user, parsed, add_logs):
    base_sum = 0
    for log in CompletionLog.query.filter_by(user_id=user.id).all():
        base_sum += int(log.exp_impact) if log.exp_impact else 0
    add_sum = sum(int(log.get("exp_impact") or 0) for log in add_logs)
    total_after = base_sum + add_sum
    return {
        "total_exp_from": user.total_exp,
        "total_exp_to": total_after,
        "level_from": user.level,
        "level_to": _level_for_exp(total_after),
        "attrs_kept": True,
    }


def _level_for_exp(total_exp):
    level = Level.query.filter(Level.required_exp <= total_exp) \
        .order_by(Level.required_exp.desc()).first()
    return level.level_number if level else 1


def _target_sub_map(user_id):
    mapping = {}
    for sub, act_name in (db.session.query(SubActivity, Activity.name)
                          .join(Activity, Activity.id == SubActivity.activity_id)
                          .filter(Activity.user_id == user_id).all()):
        mapping[sub_path_key(act_name, sub.name)] = sub
    return mapping


def _target_entry_map(user_id):
    mapping = {}
    rows = (db.session.query(TimetableEntry, Timetable.date, Activity.name, SubActivity.name)
            .join(Timetable, Timetable.id == TimetableEntry.timetable_id)
            .join(SubActivity, SubActivity.id == TimetableEntry.sub_activity_id)
            .join(Activity, Activity.id == SubActivity.activity_id)
            .filter(Timetable.user_id == user_id).all())
    for entry, tt_date, act_name, sub_name in rows:
        mapping[(tt_date, entry_key(act_name, sub_name, str(entry.start_time)[:5]))] = entry
    return mapping


def _target_log_map(user_id):
    mapping = {}
    rows = (db.session.query(CompletionLog, Activity.name, SubActivity.name,
                             TimetableEntry.start_time, Timetable.date)
            .join(SubActivity, SubActivity.id == CompletionLog.sub_activity_id)
            .join(Activity, Activity.id == SubActivity.activity_id)
            .outerjoin(TimetableEntry, TimetableEntry.id == CompletionLog.timetable_entry_id)
            .outerjoin(Timetable, Timetable.id == TimetableEntry.timetable_id)
            .filter(CompletionLog.user_id == user_id).all())
    for log, act_name, sub_name, start_time, tt_date in rows:
        # A log without a timetable entry carries no day linkage of its own;
        # fall back to its completion day so re-imports of unlinked logs collide
        # with their own first import.
        tail = tt_date if tt_date is not None else log.completed_on
        key = log_key(act_name, sub_name, log.completed_on,
                      str(start_time)[:5] if start_time else None,
                      tail)
        mapping.setdefault(key, []).append(log)
    return mapping


# ---------------------------------------------------------------------------
# Import: apply a merge plan (single transaction)
# ---------------------------------------------------------------------------

def apply_merge(user, plan):
    """Execute a merge plan (from :func:`preview_merge`) in one transaction."""
    if not isinstance(plan, dict) or plan.get("format") != FORMAT_ID:
        raise BackupError("Merge plan is not valid.")
    user_id = user.id
    applied = {"activities": 0, "sub_activities": 0, "timetables": 0,
               "entries": 0, "logs": 0, "reviews": 0}
    try:
        _apply_activities_and_subs(user_id, plan, applied)
        _apply_timetables(user_id, plan, applied)
        created_log_ids = _apply_logs(user_id, plan, applied)
        _apply_reviews(user_id, created_log_ids, plan, applied)
        _apply_recompute(user_id, user)
        db.session.commit()
    except BackupError:
        db.session.rollback()
        raise
    except Exception as exc:  # pragma: no cover - defensive
        db.session.rollback()
        raise BackupError(f"Import failed: {exc}") from exc
    return applied


def _apply_activities_and_subs(user_id, plan, applied):
    for item in plan["to_add"]["activities"]:
        act_name = str(item["name"])
        if Activity.query.filter_by(user_id=user_id, name=act_name).first():
            continue  # idempotent re-apply
        activity = Activity(
            name=act_name[:100],
            user_id=user_id,
            created_at=_parse_dt(item.get("created_at")) or _utc_now(),
            is_active=bool(item.get("is_active", True)),
        )
        db.session.add(activity)
        db.session.flush()
        applied["activities"] += 1
        for sub in item.get("sub_activities") or []:
            db.session.add(SubActivity(activity_id=activity.id, **_sub_fields(sub)))
            applied["sub_activities"] += 1
    for inline in plan["to_add"].get("inline_subs") or []:
        activity = Activity.query.filter_by(
            user_id=user_id, name=str(inline["activity"])).first()
        if activity is None:
            continue
        if SubActivity.query.filter_by(activity_id=activity.id,
                                       name=str(inline["sub"]["name"])).first():
            continue  # idempotent re-apply
        db.session.add(SubActivity(activity_id=activity.id, **_sub_fields(inline["sub"])))
        applied["sub_activities"] += 1
    db.session.flush()


def _sub_fields(sub):
    weights = sub.get("attribute_weights") or {}
    fields = {
        "name": str(sub["name"])[:100],
        "difficulty_multiplier": float(sub.get("difficulty_multiplier", 1.0) or 1.0),
        "base_exp": int(sub.get("base_exp", 100) or 100),
        "active": bool(sub.get("active", True)),
        "scheduled_time": int(sub.get("scheduled_time", 60)),
    }
    # Preserve exactly what was exported (sparse maps round-trip cleanly);
    # leave the key unset when empty so the model's own column default applies.
    if weights:
        fields["attribute_weights"] = {
            str(k): float(v) for k, v in weights.items() if v is not None
        }
    return fields


def _apply_timetables(user_id, plan, applied):
    subs = _sub_resolver(user_id)
    for tt_item in plan["to_add"]["timetables"]:
        tt_date = _parse_date(tt_item["date"])
        if Timetable.query.filter_by(user_id=user_id, date=tt_date).first():
            continue  # date present twice in the plan or re-applied
        tt = Timetable(
            user_id=user_id,
            date=tt_date,
            goal_text=tt_item.get("goal_text"),
            meta_data=tt_item.get("meta_data")
                      if isinstance(tt_item.get("meta_data"), dict) else {},
            finalized=bool(tt_item.get("finalized", False)),
        )
        db.session.add(tt)
        db.session.flush()
        applied["timetables"] += 1
        for entry in tt_item.get("entries") or []:
            _insert_entry(tt, subs, entry, applied)
    for date_iso, entries in (plan["to_add"].get("entries_on_existing") or {}).items():
        tt = Timetable.query.filter_by(user_id=user_id, date=_parse_date(date_iso)).first()
        if tt is None:
            continue
        for entry in entries:
            _insert_entry(tt, subs, entry, applied)
    db.session.flush()


def _insert_entry(tt, subs, entry, applied):
    sub = subs.get(sub_path_key(entry.get("activity"), entry.get("sub_activity")))
    if sub is None:
        return
    if TimetableEntry.query.filter_by(timetable_id=tt.id, sub_activity_id=sub.id,
                                      start_time=_entry_time(entry, "start_time")).first():
        return  # idempotent re-apply
    db.session.add(TimetableEntry(
        timetable_id=tt.id,
        sub_activity_id=sub.id,
        start_time=_entry_time(entry, "start_time"),
        end_time=_entry_time(entry, "end_time"),
        cyclic=bool(entry.get("cyclic", False)),
        weekday=WeekDay(int(entry["weekday"])) if entry.get("weekday") is not None else None,
        description=entry.get("description"),
    ))
    applied["entries"] += 1


def _entry_time(entry, field):
    value = entry.get(field)
    if not value:
        return None
    return _parse_time(value, f"entry {field}")


def _sub_resolver(user_id):
    resolver = {}
    rows = (db.session.query(SubActivity, Activity.name)
            .join(Activity, Activity.id == SubActivity.activity_id)
            .filter(Activity.user_id == user_id).all())
    for sub, act_name in rows:
        resolver[sub_path_key(act_name, sub.name)] = sub
    return resolver


def _apply_logs(user_id, plan, applied):
    subs = _sub_resolver(user_id)
    entries = _entry_resolver(user_id)
    created_ids = []
    for item in plan["to_add"]["logs"]:
        sub = subs.get(sub_path_key(item.get("activity"), item.get("sub_activity")))
        if sub is None:
            created_ids.append(None)
            continue
        entry = None
        tt_date = item.get("timetable_date")
        if tt_date:
            entry = entries.get((_parse_date(tt_date), sub.id,
                                 str(item.get("timetable_start"))[:5]
                                 if item.get("timetable_start") else None))
        log = CompletionLog(
            user_id=user_id,
            sub_activity_id=sub.id,
            timetable_entry_id=entry.id if entry else None,
            completed_on=_require_date(item.get("completed_on")),
            actual_time_taken=item.get("actual_time_taken"),
            status=str(item.get("status", "completed")),
            reason=item.get("reason"),
            exp_impact=item.get("exp_impact"),
            comment=item.get("comment"),
        )
        db.session.add(log)
        db.session.flush()
        created_ids.append(log.id)
        applied["logs"] += 1
    return created_ids


def _entry_resolver(user_id):
    resolver = {}
    rows = (db.session.query(TimetableEntry, Timetable.date)
            .join(Timetable, Timetable.id == TimetableEntry.timetable_id)
            .filter(Timetable.user_id == user_id).all())
    for entry, tt_date in rows:
        resolver[(tt_date, entry.sub_activity_id, str(entry.start_time)[:5])] = entry
    return resolver


def _require_date(value):
    if not value:
        return None
    return _parse_date(value)


def _apply_reviews(user_id, created_log_ids, plan, applied):
    for item in plan["to_add"]["reviews"]:
        log_index = item.get("log_index")
        if log_index is None or log_index < 0 or log_index >= len(created_log_ids):
            continue
        log_id = created_log_ids[log_index] if log_index < len(created_log_ids) else None
        if log_id is None:
            continue
        db.session.add(JudgeReview(
            user_id=user_id,
            completion_log_id=log_id,
            task_name=str(item.get("task_name", "")),
            task_status=str(item.get("task_status", "MISSED")),
            user_reason=item.get("user_reason"),
            penalty=int(item.get("penalty", 0) or 0),
            discipline=int(item.get("discipline", 0) or 0),
            validity=int(item.get("validity", 0) or 0),
            responsibility=int(item.get("responsibility", 0) or 0),
            consistency=int(item.get("consistency", 0) or 0),
            explanation=item.get("explanation"),
            review_status=str(item.get("review_status", "PENDING")),
            dispute_reason=item.get("dispute_reason"),
            created_at=_parse_dt(item.get("created_at")) or _utc_now(),
            updated_at=_parse_dt(item.get("updated_at")) or _utc_now(),
        ))
        applied["reviews"] += 1
    db.session.flush()


def _apply_recompute(user_id, user):
    total = 0
    for log in CompletionLog.query.filter_by(user_id=user_id).all():
        total += int(log.exp_impact) if log.exp_impact else 0
    user.total_exp = total
    level = _level_for_exp(total)
    if level:
        user.level = level


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(value):
    return date.fromisoformat(str(value))


def _parse_time(value, where):
    if not value:
        raise BackupError(f"{where} is required.")
    text_value = str(value).strip()
    hour, minute = text_value.split(":") if ":" in text_value else (text_value, "0")
    try:
        from datetime import time
        return time(int(hour), int(minute))
    except (TypeError, ValueError):
        raise BackupError(f"{where} has invalid value {value!r}.")


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None