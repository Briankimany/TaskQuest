"""
Build the garden RPG dashboard context dict from user model data.
"""
import math
from datetime import date, timedelta, datetime
from sqlalchemy import func
from app.models import User, CompletionLog, Level
from app.models.base import db
from app.utils.schedulers import TaskScheduler
from app.utils.managers import UserManager
from app.utils.assets import region_art, hero_bg, health_overlay


def _compute_tier(value):
    """Compute region tier from attribute value (server-side only)."""
    if value >= 80:
        return 4
    elif value >= 60:
        return 3
    elif value >= 40:
        return 2
    return 1


def _compute_health_state(dcp):
    """Compute garden health state from daily completion percentage."""
    if dcp >= 0.85:
        return "FLOURISHING"
    elif dcp >= 0.5:
        return "STABLE"
    return "NEGLECTED"


def _get_season(dt):
    """Determine season from month."""
    month = dt.month
    if month in (3, 4, 5):
        return "SPRING"
    elif month in (6, 7, 8):
        return "SUMMER"
    elif month in (9, 10, 11):
        return "AUTUMN"
    return "WINTER"


def _get_time_of_day(dt):
    """Determine time of day from hour."""
    hour = dt.hour
    if 5 <= hour < 12:
        return "MORNING"
    elif 12 <= hour < 17:
        return "AFTERNOON"
    elif 17 <= hour < 21:
        return "EVENING"
    return "NIGHT"


TITLES = [
    (1, "Seedling", "Sprout"),
    (5, "Sprout", "Wayfarer"),
    (10, "Wayfarer", "Pathfinder"),
    (20, "Pathfinder", "Guardian"),
    (30, "Guardian", "Warden"),
    (40, "Warden", "Sage"),
    (50, "Sage", "Master"),
]


def _get_titles(level):
    """Get current and next title from level."""
    current_title = "Seedling"
    next_title = "Sprout"
    for req_level, title, next_t in TITLES:
        if level >= req_level:
            current_title = title
            next_title = next_t
    return current_title, next_title


MISSION_STATUSES = [
    "AVAILABLE", "ACTIVE", "COMPLETED", "COMPLETED_LATE",
    "MISSED", "ABANDONED", "RESCHEDULED", "LOCKED"
]


def build_garden_rpg_context(user, scheduled_tasks, date_logs, dcp, date_obj,
                             next_level, xp_pct, ring_offset, streak,
                             streak_best, missed_count, xp_week):
    """Build the full context dict for the garden RPG dashboard."""

    now = datetime.now()
    today = date_obj.date() if isinstance(date_obj, datetime) else date_obj

    # ── Regions ──
    regions = {
        "academy": {
            "attr": "INT", "code": "int",
            "value": user.INT, "tier": _compute_tier(user.INT),
            "name": "Academy",
        },
        "river": {
            "attr": "STA", "code": "sta",
            "value": user.STA, "tier": _compute_tier(user.STA),
            "name": "River",
        },
        "moon": {
            "attr": "FCS", "code": "fcs",
            "value": user.FCS, "tier": _compute_tier(user.FCS),
            "name": "Moon",
        },
        "village": {
            "attr": "CHA", "code": "cha",
            "value": user.CHA, "tier": _compute_tier(user.CHA),
            "name": "Village",
        },
    }

    # Attach art data to each region
    for key, region in regions.items():
        region["art"] = region_art(key, region["tier"])

    # ── Garden health (DSC drives this, not a region) ──
    health_state = _compute_health_state(dcp)
    garden_health = {
        "discipline": round(dcp * 100),
        "state": health_state,
        "overlay": health_overlay(health_state),
    }

    # ── Player ──
    current_title, next_title = _get_titles(user.level)
    season = _get_season(now)
    player = {
        "title": current_title,
        "next_title": next_title,
        "garden_name": f"{user.username}'s Garden",
        "day": (today - user.created_at.date()).days + 1 if user.created_at else 1,
        "season": season,
        "time_of_day": _get_time_of_day(now),
    }

    # ── Hero background ──
    hero_bg_data = hero_bg(season)

    # ── Missions (from scheduled tasks) ──
    attr_keys = {"int", "sta", "fcs", "cha", "dsc"}
    missions = []
    for i, task in enumerate(scheduled_tasks):
        sub = task.sub_activity
        log_for_task = None
        for log in date_logs:
            if log.timetable_entry_id == task.id:
                log_for_task = log
                break

        # Determine status from log
        if log_for_task:
            if log_for_task.status == "completed":
                if log_for_task.exp_impact is not None and log_for_task.exp_impact < 0:
                    status = "COMPLETED_LATE"
                else:
                    status = "COMPLETED"
            elif log_for_task.status == "skipped":
                status = "MISSED"
            else:
                status = "COMPLETED"
        else:
            status = "ACTIVE"

        # Build attr_deltas from attribute_weights
        weights = sub.attribute_weights or {}
        attr_deltas = {}
        for k, v in weights.items():
            if v > 0:
                attr_deltas[k.lower()] = max(1, round(v * sub.difficulty_multiplier))

        # Determine target region from highest-weight attribute
        target_region = "academy"
        if weights:
            top_attr = max(weights, key=weights.get)
            region_map = {"INT": "academy", "STA": "river", "FCS": "moon", "CHA": "village", "DSC": "academy"}
            target_region = region_map.get(top_attr, "academy")

        # Difficulty dots
        diff = min(5, max(1, int(sub.difficulty_multiplier)))

        # Countdown
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

        missions.append({
            "id": f"mission-{task.id}",
            "tag": "MAIN" if i < 2 else "DAILY",
            "title": sub.name,
            "status": status,
            "difficulty": diff,
            "attr_deltas": attr_deltas,
            "attr_delta_str": " + ".join(f"{k.upper()} {v}" for k, v in attr_deltas.items()),
            "xp": int(sub.calculate_potential_exp()),
            "deadline": task.end_time.strftime("%H:%M") if task.end_time else "",
            "countdown": remaining,
            "streak_risk": -3 if i < 2 else 0,
            "target_region": target_region,
        })

    # ── Seeds (placeholder — no seed model yet) ──
    seeds = [
        {"id": "seed-1", "label": "Morning Routine", "state": "DORMANT",
         "potential_xp": 80, "potential_attr": "dsc"},
        {"id": "seed-2", "label": "Weekly Review", "state": "DORMANT",
         "potential_xp": 60, "potential_attr": "fcs"},
    ]

    # ── Judge reviews (from today's penalized logs) ──
    judge_reviews = []
    for log in date_logs:
        if log.exp_impact is not None and log.exp_impact < 0:
            judge_reviews.append({
                "id": log.id,
                "task": log.sub_activity.name if log.sub_activity else "Unknown",
                "status": log.status.upper(),
                "user_reason": log.reason or "",
                "metrics": {"validity": round(dcp * 100), "responsibility": round(dcp * 95),
                            "consistency": min(100, round(dcp * 100 + 10))},
                "penalty": log.exp_impact,
                "discipline_delta": 0,
                "review_status": "PENDING",
            })

    # ── Activity (today's completed logs) ──
    activity = []
    for log in date_logs:
        if log.status == "completed":
            # Determine target region from sub_activity weights
            weights = log.sub_activity.attribute_weights if log.sub_activity else {}
            target = "academy"
            if weights:
                top_attr = max(weights, key=weights.get)
                region_map = {"INT": "academy", "STA": "river", "FCS": "moon", "CHA": "village", "DSC": "academy"}
                target = region_map.get(top_attr, "academy")

            # Find the attr with highest weight
            primary_attr = "int"
            if weights:
                primary_attr = max(weights, key=lambda k: weights.get(k, 0)).lower()

            activity.append({
                "name": log.sub_activity.name if log.sub_activity else "Unknown",
                "completed_at": log.completed_on.strftime("%H:%M") if log.completed_on else "",
                "xp": log.exp_impact or 0,
                "attr": primary_attr,
                "attr_delta": 1,
                "target_region": target,
            })

    # ── World events (from today's data) ──
    world_events = []
    # Check if any region crossed a tier threshold today
    for key, region in regions.items():
        if region["tier"] >= 4:
            world_events.append({
                "headline": f"{region['name'].upper()} FULLY DEVELOPED",
                "body": f"{region['attr']} reached 80. {region['name']} is at maximum growth.",
            })

    # ── XP week data ──
    current_time_str = now.strftime('%H:%M')

    return {
        "regions": regions,
        "garden_health": garden_health,
        "player": player,
        "hero_bg_data": hero_bg_data,
        "missions": missions,
        "seeds": seeds,
        "judge_reviews": judge_reviews,
        "activity": activity,
        "world_events": world_events,
        "xp_week": xp_week,
        "current_time": current_time_str,
    }
