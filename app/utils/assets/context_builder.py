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
from app.utils.assets.dashboard_payloads import (
    build_missions, build_activity, build_judge_reviews,
)


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
    player = {
        "title": current_title,
        "next_title": next_title,
        "garden_name": f"{user.username}'s Garden",
        "day": (today - user.created_at.date()).days + 1 if user.created_at else 1,
        "time_of_day": _get_time_of_day(now),
    }

    # ── Hero background (single default world art) ──
    hero_bg_data = hero_bg()

    # ── Missions (from scheduled tasks) ──
    missions = build_missions(scheduled_tasks, date_logs, today)

    # ── Seeds (placeholder — no seed model yet) ──
    seeds = [
        {"id": "seed-1", "label": "Morning Routine", "state": "DORMANT",
         "potential_xp": 80, "potential_attr": "dsc"},
        {"id": "seed-2", "label": "Weekly Review", "state": "DORMANT",
         "potential_xp": 60, "potential_attr": "fcs"},
    ]

    # ── Judge reviews (persisted, one per penalized log, generated via LLM) ──
    judge_reviews = build_judge_reviews(date_logs, dcp)

    # ── Activity (all of today's completion logs — completed, late, skipped) ──
    activity = build_activity(date_logs)

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
        "missed_count": missed_count,
        "activity": activity,
        "world_events": world_events,
        "xp_week": xp_week,
        "current_time": current_time_str,
    }
