
"""
View routes for the Real-Life RPG System.

This module renders HTML templates for the dashboard, activities,
stats, and timetable pages.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session,request
from datetime import date,time
from app.models import User, Activity, CompletionLog, Level
from app.models.base import db
from app.utils.schedulers import TaskScheduler
from app.utils.managers import UserManager
from app.utils.logger import ui_logger

from datetime import datetime
from app.config import DATE_PARSING_STRING

views_bp = Blueprint('views', __name__)


@views_bp.errorhandler(Exception)
def handle_generic_error(error: Exception):
    import traceback
    from flask import current_app
    msg = (
        f"{error!r} | URL: {request.url} | Method: {request.method}\n"
        f"{''.join(traceback.format_exception(type(error), error, error.__traceback__))}"
    )
    ui_logger.error(msg)
    if current_app.debug:
        raise error
    return render_template('500.html',exception=""), 500
  
class ScheduledActivites:
    
    def __init__(self,name,sub_activities):
        self.sub_activities = sub_activities
        self.name = name 


@views_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('views.dashboard'))
    return render_template('index.html')

def _get_current_user():
    """Return the logged-in user, clearing stale sessions that no longer exist in the DB."""
    user_id = session.get('user_id')
    if user_id is None:
        return None
    user = User.query.get(user_id)
    if user is None:
        session.pop('user_id', None)
        flash('Your session has expired. Please log in again.', 'warning')
        return None
    return user


@views_bp.route('/dashboard')
def dashboard():
    """Render the main dashboard with scheduled tasks."""
    user = _get_current_user()
    if user is None:
        return redirect(url_for('auth.login'))

    user_id = user.id
    
    # Parse date parameter or use current date
    date_str = request.args.get('date')
    if not date_str:
        date_obj = datetime.now()
    else:
        date_obj = datetime.strptime(date_str, DATE_PARSING_STRING)
    
    # Get scheduled tasks for the date
    taskscheduler = TaskScheduler(user_id=user_id, date=date_obj)
    scheduled_tasks = taskscheduler.get_daily_schedule(
        user_id=user_id,
        return_suggested=False,
        date_obj=date_obj.date()
    )
    
    date_logs = CompletionLog.query.filter(
        CompletionLog.user_id == user_id,
        CompletionLog.completed_on ==date_obj.date()).all()

    # Calculate discipline factor (dcp) for the day
    dcp = UserManager.get_dcp(user_id=user_id,
                              date_obj=date_obj.date())
    
    # Find next level info
    current_level = user.level
    next_level = Level.query.filter(
        Level.level_number > current_level
    ).order_by(Level.level_number).first()
    
    exp_to_next_level = (next_level.required_exp - user.total_exp) if next_level else 0

    # Determine which template to render based on theme preference
    theme = request.cookies.get('app_theme', 'default')

    if theme == 'garden-rpg':
        # Compute garden RPG specific context
        import math
        circumference = 2 * math.pi * 20  # r=20 for level ring
        if next_level and next_level.required_exp > 0:
            xp_pct = round((user.total_exp / next_level.required_exp) * 100, 1)
            ring_offset = round(circumference * (1 - (user.total_exp / next_level.required_exp)), 1)
        else:
            xp_pct = 100
            ring_offset = 0

        # Compute XP for last 7 days
        from sqlalchemy import func
        from datetime import timedelta
        today = date_obj.date()
        xp_week = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_exp = db.session.query(func.coalesce(func.sum(CompletionLog.exp_impact), 0)).filter(
                CompletionLog.user_id == user_id,
                CompletionLog.completed_on == day
            ).scalar()
            xp_week.append(int(day_exp))

        current_time_str = datetime.now().strftime('%H:%M')

        streak = UserManager.get_streak(user_id)
        streak_best = UserManager.get_best_streak(user_id)
        missed_count = UserManager.get_missed_count(user_id, date_obj.date())

        return render_template(
            'dashboard_garden_rpg.html',
            user=user,
            scheduled_tasks=scheduled_tasks,
            today_logs=date_logs,
            dcp=dcp,
            exp_to_next_level=exp_to_next_level,
            current_date=date_obj.date(),
            level=user.level,
            xp_current=user.total_exp,
            xp_next=next_level.required_exp if next_level and next_level.required_exp > 0 else max(user.total_exp, 1),
            xp_pct=xp_pct,
            ring_offset=ring_offset,
            streak=streak,
            streak_best=streak_best,
            xp_week=xp_week,
            current_time=current_time_str,
            missed_count=missed_count
        )

    return render_template(
        'dashboard.html',
        user=user,
        scheduled_tasks=scheduled_tasks,
        today_logs=date_logs,
        dcp=dcp,
        exp_to_next_level=exp_to_next_level,
        current_date=date_obj.date()
    )


@views_bp.route('/activities')
def activities():
    """Render the activities management page."""
    user = _get_current_user()
    if user is None:
        return redirect(url_for('auth.login'))

    activities = Activity.query.filter_by(user_id=user.id, is_active=True).order_by(Activity.created_at.desc()).all()
    
    return render_template('activities.html', activities=activities)

@views_bp.route('/stats')
def stats():
    """Render the statistics page."""
    user = _get_current_user()
    if user is None:
        return redirect(url_for('auth.login'))
    
    # Get completion history for charts
    completion_history = CompletionLog.query.filter_by(user_id=user.id).order_by(CompletionLog.completed_on).all()

    return render_template('stats.html', user=user, completion_history=completion_history)

@views_bp.route('/timetable')
def timetable():
    """Render the timetable planning page."""
    user = _get_current_user()
    if user is None:
        return redirect(url_for('auth.login'))
    
    activities = Activity.query.filter_by(user_id=user.id, is_active=True).order_by(Activity.created_at.desc()).all()
    
    return render_template('timetable.html', user=user, activities=activities)

@views_bp.route('/help')
def help():
    return render_template('guide.html')
@views_bp.route("/docs")
def docs():
    return render_template('docs.html',API_URL='https://funcwithme.com',TESTING_USED='test token')