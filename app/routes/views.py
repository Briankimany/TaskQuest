
"""
View routes for the Real-Life RPG System.

This module renders HTML templates for the dashboard, activities,
stats, and timetable pages.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session,request
from datetime import date,time
from app.models import User, Activity, CompletionLog, Level
from app.utils.schedulers import TaskScheduler
from app.utils.managers import UserManager

from datetime import datetime
from app.config import DATE_PARSING_STRING

views_bp = Blueprint('views', __name__)

class ScheduledActivites:
    
    def __init__(self,name,sub_activities):
        self.sub_activities = sub_activities
        self.name = name 


@views_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('views.dashboard'))
    return render_template('index.html')

@views_bp.route('/dashboard')
def dashboard():
    """Render the main dashboard with scheduled tasks."""
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
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
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    activities = Activity.query.filter_by(user_id=user_id).all()
    
    return render_template('activities.html', activities=activities)

@views_bp.route('/stats')
def stats():
    """Render the statistics page."""
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get completion history for charts
    completion_history = CompletionLog.query.filter_by(user_id=user_id).order_by(CompletionLog.completed_on).all()

    return render_template('stats.html', user=user, completion_history=completion_history)

@views_bp.route('/timetable')
def timetable():
    """Render the timetable planning page."""
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    activities = Activity.query.filter_by(user_id=user_id).all()
    
    return render_template('timetable.html', user=user, activities=activities)

@views_bp.route('/help')
def help():
    return render_template('guide.html')
@views_bp.route("/docs")
def docs():
    return render_template('docs.html',API_URL='https://funcwithme.com',TESTING_USED='test token')