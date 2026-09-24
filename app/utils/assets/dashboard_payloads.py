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


def build_level_progress(user, today):
    """Level + streak + XP-to-next snapshot for the context side panel.

    Mirrors the exact math in ``app/routes/views.py`` / ``app/routes/api.py``
    (Level table + user.total_exp + streak helpers), so the chat side panel
    and the dashboard's XP card can never drift from first paint.
    """
    from app.models import Level
    from app.utils.managers import UserManager

    user_id = user.id

    current_level = Level.query.filter_by(level_number=user.level).first()
    next_level = Level.query.filter(
        Level.level_number > user.level
    ).order_by(Level.level_number).first()

    current_floor = current_level.required_exp if current_level else 0
    next_floor = next_level.required_exp if next_level else None

    streak = UserManager.get_streak(user_id, today=today)
    best_streak = UserManager.get_best_streak(user_id, today=today)

    if next_floor is not None:
        exp_to_next = max(0, next_floor - user.total_exp)
        span = max(1, next_floor - current_floor)
        progress_pct = round(
            max(0, min(100, (user.total_exp - current_floor) / span * 100)), 1,
        )
        next_level_num = next_level.level_number
    else:
        exp_to_next = 0
        progress_pct = 100
        next_level_num = None

    return {
        "level": user.level,
        "total_exp": user.total_exp,
        "streak": streak,
        "best_streak": best_streak,
        "next_level": next_level_num,
        "exp_to_next": exp_to_next,
        "xp_progress_pct": progress_pct,
    }


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


def _day_minute(hhmm):
    """'HH:MM' -> minutes since midnight, or None when unparseable."""
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def _mission_order_key(start_str, now_minute):
    """Time-of-day ordering: next upcoming first, earliest-started last.

    Missions that already started sink below the ones still ahead, and within
    the started group the longest-started sits at the very bottom, so scrolling
    down walks backwards through the day. Items without a start time go last.
    """
    start_minute = _day_minute(start_str or "")
    if start_minute is None:
        return 3 * 24 * 60
    if start_minute >= now_minute:
        return start_minute - now_minute
    return 24 * 60 + (now_minute - start_minute)


def build_missions(scheduled_tasks, date_logs, today, now=None):
    """Build the Today's Missions payload.

    Context-switch buffer entries (sub-activity base_exp == 0) are excluded —
    they carry no XP and are not real missions. Ordering is time-of-day based
    (see _mission_order_key): the next unstarted mission leads the list and the
    earliest-started one of the day is the last row.

    ``now`` is the user's current local time (defaults to server time for
    backwards compatibility); pass ``now_for(user)`` from request handlers.
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
        now = now or datetime.now()
        if now.tzinfo is not None:
            naive_now = datetime.combine(today, now.time())
        else:
            naive_now = now
        remaining = ""
        if status == "ACTIVE" and task.end_time:
            end_dt = datetime.combine(today, task.end_time)
            delta = end_dt - naive_now
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

    now_minute = (now or datetime.now()).hour * 60 + (now or datetime.now()).minute
    missions.sort(key=lambda m: _mission_order_key(m.get("start") or "", now_minute))
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
        elif log.status == "partial":
            status = "PARTIAL"
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