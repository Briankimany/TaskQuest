"""
Shared payload builders for the Garden RPG dashboard cards.

Mission rows, the recent-activity feed, and system-judge reviews are built
here once and consumed by both the Jinja first paint (context_builder) and
the JSON API endpoints used by the client-side refresh layer, so the two
sides can never drift apart.
"""
from datetime import datetime

REGION_MAP = {
    "INT": "academy",
    "STA": "river",
    "FCS": "moon",
    "CHA": "village",
    "DSC": "academy",
}

# Mission-type accent colors — single source of truth, shared by the
# Today's Missions card and Recent Activity so the same task always renders
# with the same color regardless of which card shows it.
TYPE_COLORS = {
    "MAIN": "cyan",
    "DAILY": "green",
    "SIDE": "amber",
}

# Per-task overrides on top of the type default. Purple is not a second SIDE
# color — it's a deliberate opt-out for specific tasks (e.g. Build Project).
COLOR_OVERRIDES = {
    "build project": "purple",
    "finish portfolio": "purple",
    "side project code": "purple",
}

# Failed states force a red status ring/label regardless of the task's type
# color (the reference's red is a status override, not a fifth category).
STATUS_OVERRIDE_RED = {"MISSED", "ABANDONED", "COMPLETED_LATE"}


def mission_color(title, tag):
    """Resolve the stored/canonical accent color for a task.

    Per-task override wins; otherwise the mission-type default applies. Both
    build_missions and build_activity call this so cards never drift.
    """
    override = COLOR_OVERRIDES.get((title or "").strip().lower())
    if override:
        return override
    return TYPE_COLORS.get(tag, "amber")


def _tag_for_index(index):
    """Missions are tagged by schedule position: 1st=MAIN, 2nd=DAILY, else SIDE."""
    return "MAIN" if index == 0 else ("DAILY" if index == 1 else "SIDE")

# Urgent/in-progress first, resolved last. "Overdue" is an ACTIVE mission whose
# window has already passed, so ACTIVE already includes it.
STATUS_PRIORITY = {
    "ACTIVE": 0,
    "AVAILABLE": 0,
    "RESCHEDULED": 1,
    "LOCKED": 2,
    "COMPLETED": 3,
    "COMPLETED_LATE": 3,
    "MISSED": 3,
    "ABANDONED": 3,
}


def _top_weight(weights):
    return max(weights, key=weights.get) if weights else None


def _target_region(weights):
    top = _top_weight(weights)
    return REGION_MAP.get(top, "academy") if top else "academy"


def _task_status(log):
    """Mirror the mission-list status labels for a completion log."""
    if log.status == "completed":
        if log.exp_impact is not None and log.exp_impact < 0:
            return "COMPLETED_LATE"
        return "COMPLETED"
    if log.status == "skipped":
        return "MISSED"
    return log.status.upper()


def build_missions(scheduled_tasks, date_logs, today):
    """Build the Today's Missions payload.

    Context-switch buffer entries (sub-activity base_exp == 0) are excluded —
    they carry no XP and are not real missions. Ordering keeps ACTIVE/AVAILABLE
    first (stable by scheduled start time) and resolved missions at the bottom.
    """
    missions = []
    index = 0
    for task in scheduled_tasks:
        sub = task.sub_activity
        if not sub or sub.base_exp == 0:
            continue

        log_for_task = None
        for log in date_logs:
            if log.timetable_entry_id == task.id:
                log_for_task = log
                break

        status = _task_status(log_for_task) if log_for_task else "ACTIVE"

        # Build attr_deltas from attribute_weights
        weights = sub.attribute_weights or {}
        attr_deltas = {}
        for k, v in weights.items():
            if v > 0:
                attr_deltas[k.lower()] = max(1, round(v * sub.difficulty_multiplier))

        target_region = _target_region(weights)

        # Difficulty dots
        diff = min(5, max(1, int(sub.difficulty_multiplier)))

        # Countdown
        now = datetime.now()
        remaining = ""
        if status == "ACTIVE" and task.end_time:
            end_dt = datetime.combine(today, task.end_time)
            delta = end_dt - now
            if delta.total_seconds() > 0:
                hours = int(delta.total_seconds() // 3600)
                mins = int((delta.total_seconds() % 3600) // 60)
                remaining = f"{hours}h {mins}m left"
            else:
                remaining = "Overdue"

        # Duration (minutes) so the client can preserve it on reschedule
        duration_minutes = 0
        if task.start_time and task.end_time:
            start_dt = datetime.combine(today, task.start_time)
            end_dt = datetime.combine(today, task.end_time)
            duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
            if duration_minutes <= 0:
                duration_minutes = 0

        missions.append({
            "id": f"mission-{task.id}",
            "tag": _tag_for_index(index),
            "title": sub.name,
            "color": mission_color(sub.name, _tag_for_index(index)),
            "status": status,
            "status_override": "red" if status in STATUS_OVERRIDE_RED else None,
            "difficulty": diff,
            "attr_deltas": attr_deltas,
            "attr_delta_str": " + ".join(f"{k.upper()} {v}" for k, v in attr_deltas.items()),
            "xp": int(sub.calculate_potential_exp()) if hasattr(sub, "calculate_potential_exp") else int(sub.base_exp or 0),
            "duration": duration_minutes,
            "deadline": task.end_time.strftime("%H:%M") if task.end_time else "",
            "start": task.start_time.strftime("%H:%M") if task.start_time else "",
            "countdown": remaining,
            "streak_risk": -3 if index < 2 else 0,
            "target_region": target_region,
        })
        index += 1

    missions.sort(key=lambda m: (STATUS_PRIORITY.get(m["status"], 9), m.get("start") or ""))
    return missions


def build_activity(date_logs, scheduled_tasks=None):
    """Build the Recent Activity feed for today.

    Shows resolved items first (completed/late/missed) with signed XP impact,
    then any still-in-progress missions as a grayed next-up row.

    Colors match the missions card: every item resolves to the same stored
    per-task color (by schedule position + override, identical logic), so a
    purple Build Project is purple here too.
    """
    # Map timetable_entry -> mission tag, mirroring build_missions's ordering
    # (skip buffer entries whose base_exp == 0). When the schedule is provided
    # use it directly so in-progress items tag identically to the missions card.
    entry_index = {}
    index = 0

    def assign_tags(iterable, key_fn):
        nonlocal index
        for item in iterable:
            sub = item.sub_activity
            if not sub or sub.base_exp == 0:
                continue
            entry_index[key_fn(item)] = _tag_for_index(index)
            index += 1

    if scheduled_tasks is not None:
        assign_tags(scheduled_tasks, lambda t: t.id)
    else:
        assign_tags(date_logs, lambda lg: lg.timetable_entry_id)

    activity = []
    for log in date_logs:
        sub = log.sub_activity
        weights = sub.attribute_weights if sub else {}
        xp = log.exp_impact if log.exp_impact is not None else 0

        if log.status == "completed":
            status = "LATE" if xp < 0 else "DONE"
        else:
            status = "MISSED"

        entry = log.timetable_entry
        tag = entry_index.get(log.timetable_entry_id, "SIDE") if log.timetable_entry_id else "SIDE"

        activity.append({
            "name": sub.name if sub else "Unknown",
            "time": entry.start_time.strftime("%H:%M")
                    if entry and entry.start_time else "",
            "xp": xp,
            "attr": (_top_weight(weights) or "int").lower(),
            "attr_delta": 1,
            "target_region": _target_region(weights),
            "status": status,
            "color": mission_color(sub.name, tag) if sub else "amber",
            "status_override": "red" if status in ("LATE", "MISSED") else None,
        })

    if scheduled_tasks is not None:
        logged_ids = {lg.timetable_entry_id for lg in date_logs if lg.timetable_entry_id}
        for task in scheduled_tasks:
            sub = task.sub_activity
            if not sub or sub.base_exp == 0 or task.id in logged_ids:
                continue
            weights = sub.attribute_weights or {}
            tag = entry_index.get(task.id, "SIDE")
            activity.append({
                "name": sub.name,
                "time": task.start_time.strftime("%H:%M") if task.start_time else "",
                "xp": int(sub.calculate_potential_exp()) if hasattr(sub, "calculate_potential_exp") else int(sub.base_exp or 0),
                "attr": (_top_weight(weights) or "int").lower(),
                "attr_delta": 1,
                "target_region": _target_region(weights),
                "status": "IN_PROGRESS",
                "color": mission_color(sub.name, tag),
                "status_override": None,
            })
    return activity


def build_judge_reviews(date_logs, dcp):
    """Return today's judge reviews, newest first (one per penalized log).

    Reviews are created lazily (get-or-create), matching dashboard behavior;
    the LLM may run on first creation.
    """
    from app.utils.managers.judge_manager import JudgeManager

    reviews = []
    for log in date_logs:
        if log.exp_impact is not None and log.exp_impact < 0:
            review = JudgeManager.get_or_create_for_log(log, dcp)
            if review:
                reviews.append(JudgeManager.to_context_dict(review))
    reviews.sort(key=lambda r: r["id"], reverse=True)
    return reviews