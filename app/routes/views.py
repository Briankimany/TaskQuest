
"""
View routes for the Real-Life RPG System.

This module renders HTML templates for the dashboard, activities,
stats, and timetable pages.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session
from datetime import date
from app.models import User, Activity, SubActivity, CompletionLog, Level

views_bp = Blueprint('views', __name__)



views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Render the landing page."""
    if 'user_id' in session:
        return redirect(url_for('views.dashboard'))
    return render_template('index.html')

@views_bp.route('/dashboard')
def dashboard():
    """Render the main dashboard."""
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get activities for the user
    activities = Activity.query.filter_by(user_id=user_id).all()
    
    # Get today's completion logs
    today = date.today()
    today_logs = CompletionLog.query.filter(
        CompletionLog.user_id == user_id,
        CompletionLog.completed_on >= today
    ).all()
    
    # Calculate discipline factor (dcp)
    total_scheduled = SubActivity.query.join(Activity).filter(
        Activity.user_id == user_id
    ).count()
    
    total_completed = CompletionLog.query.filter(
        CompletionLog.user_id == user_id,
        CompletionLog.status == 'completed'
    ).count()
    
    dcp = (total_completed / total_scheduled) if total_scheduled > 0 else 0
    
    # Find next level
    current_level = user.level
    next_level = Level.query.filter(Level.level_number > current_level).order_by(Level.level_number).first()
    
    exp_to_next_level = next_level.required_exp - user.total_exp if next_level else 0
    
    return render_template(
        'dashboard.html',
        user=user,
        activities=activities,
        today_logs=today_logs,
        dcp=dcp,
        exp_to_next_level=exp_to_next_level
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
    import pprint

    return render_template('stats2.html', user=user, completion_history=completion_history)

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
