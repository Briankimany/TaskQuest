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
            "tag": "MAIN" if index == 0 else ("DAILY" if index == 1 else "SIDE"),
            "title": sub.name,
            "status": status,
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


def build_activity(date_logs):
    """Build the Recent Activity feed for today.

    Includes every status — completed, late, and skipped/missed — each with
    its scheduled time and signed XP impact (penalties render negative).
    """
    activity = []
    for log in date_logs:
        sub = log.sub_activity
        weights = sub.attribute_weights if sub else {}
        xp = log.exp_impact if log.exp_impact is not None else 0

        if log.status == "completed":
            status = "LATE" if xp < 0 else "DONE"
        else:
            status = "MISSED"

        activity.append({
            "name": sub.name if sub else "Unknown",
            "time": log.timetable_entry.start_time.strftime("%H:%M")
                    if log.timetable_entry and log.timetable_entry.start_time else "",
            "xp": xp,
            "attr": (_top_weight(weights) or "int").lower(),
            "attr_delta": 1,
            "target_region": _target_region(weights),
            "status": status,
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