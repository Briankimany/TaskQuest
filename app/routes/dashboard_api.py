"""
JSON endpoints for the Garden RPG dashboard cards.

Responses mirror the Jinja context produced by ``context_builder`` exactly,
so the client-side JS can reconcile data without visual drift.
"""
from flask import jsonify, session
from datetime import datetime

from app.routes.api import api_bp, log_app_errors
from app.models import User, CompletionLog
from app.utils.schedulers import TaskScheduler
from app.utils.managers import UserManager
from app.utils.assets.dashboard_payloads import (
    build_missions, build_activity, build_judge_reviews,
)


def _current_user():
    uid = session.get("user_id")
    if uid is None:
        return None
    user = User.query.get(uid)
    if user is None:
        session.pop("user_id", None)
        return None
    return user


def _today_ctx():
    """Return (user, scheduled, logs, dcp) or (None, …) if not logged in."""
    user = _current_user()
    if user is None:
        return None, None, None, None
    now = datetime.now()
    today = now.date()
    scheduled = TaskScheduler(user_id=user.id, date=now).get_daily_schedule(
        user_id=user.id, date_obj=today,
    )
    logs = CompletionLog.query.filter(
        CompletionLog.user_id == user.id,
        CompletionLog.completed_on == today,
    ).all()
    dcp = UserManager.get_dcp(user_id=user.id, date_obj=today)
    return user, scheduled, logs, dcp


@api_bp.route("/missions/today")
@log_app_errors
def missions_today():
    user, scheduled, logs, dcp = _today_ctx()
    if user is None:
        return jsonify({"msg": "Unauthorized"}), 401
    missions = build_missions(scheduled, logs, datetime.now().date())
    return jsonify({
        "missions": missions,
        "total": len(missions),
        "user_xp": user.total_exp,
    }), 200


@api_bp.route("/activity/recent")
@log_app_errors
def activity_recent():
    user, scheduled, logs, _dcp = _today_ctx()
    if user is None:
        return jsonify({"msg": "Unauthorized"}), 401
    return jsonify({"activity": build_activity(logs, scheduled)}), 200


@api_bp.route("/system-judge/latest")
@log_app_errors
def system_judge_latest():
    user, _scheduled, logs, dcp = _today_ctx()
    if user is None:
        return jsonify({"msg": "Unauthorized"}), 401
    reviews = build_judge_reviews(logs, dcp)
    missed = UserManager.get_missed_count(user.id, datetime.now().date())
    return jsonify({
        "review": reviews[0] if reviews else None,
        "missed_count": missed,
        "reviews_count": len(reviews),
    }), 200