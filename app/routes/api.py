"""
API routes for the Real-Life RPG System.

This module provides JSON API endpoints for activities, sub-activities,
timetables, completion tracking, and stats retrieval.
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime, date, timedelta
from sqlalchemy import func

from app.models import db, User, Activity, SubActivity, CompletionLog, Level, Timetable
from app.models import BASE_EXP, STANDARD_TIME_UNIT, GRACE_PERIOD
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Constants
BASE_EXP = 100  # Default base experience
STANDARD_TIME_UNIT = 60  # 1 hour in minutes
GRACE_PERIOD = 15  # 15 minutes grace period

@api_bp.route('/activities', methods=['GET', 'POST'])
def activities():
    """Handle CRUD operations for activities."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        activities = Activity.query.filter_by(user_id=user_id).all()
        return jsonify({
            'activities': [
                {
                    'id': act.id,
                    'name': act.name,
                    'created_at': act.created_at.isoformat(),
                    'sub_activities': [
                        {
                            'id': sub_act.id,
                            'name': sub_act.name,
                            'difficulty_multiplier': sub_act.difficulty_multiplier,
                            'scheduled_time': sub_act.scheduled_time,
                            'base_exp': sub_act.base_exp,
                            'attribute_weights': sub_act.attribute_weights
                        } for sub_act in act.sub_activities
                    ]
                } for act in activities
            ]
        })
    
    elif request.method == 'POST':
        data = request.json
        new_activity = Activity(
            name=data['name'],
            user_id=user_id
        )
        db.session.add(new_activity)
        db.session.commit()
        
        return jsonify({
            'id': new_activity.id,
            'name': new_activity.name,
            'created_at': new_activity.created_at.isoformat()
        }), 201

@api_bp.route('/activity/<int:activity_id>', methods=['PUT', 'DELETE'])
def activity_detail(activity_id):
    """Handle updating and deleting activities."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    activity = Activity.query.filter_by(id=activity_id, user_id=user_id).first()
    
    if not activity:
        return jsonify({'error': 'Activity not found'}), 404
    
    if request.method == 'PUT':
        data = request.json
        activity.name = data.get('name', activity.name)
        db.session.commit()
        
        return jsonify({
            'id': activity.id,
            'name': activity.name,
            'created_at': activity.created_at.isoformat()
        })
    
    elif request.method == 'DELETE':
        db.session.delete(activity)
        db.session.commit()
        return '', 204

@api_bp.route("/subactivity",methods=['POST'])
@api_bp.route('/subactivities', methods=['POST'])
def create_subactivity():
    """Create a sub-activity."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    activity_id = data['activity_id']
    # Verify activity belongs to user
    activity = Activity.query.filter_by(
        id=activity_id, 
        user_id=session['user_id']
    ).first()
    
    if not activity:
        return jsonify({'error': 'Activity not found'}), 404
    
    new_subactivity = SubActivity(
        name=data['name'],
        activity_id=activity_id,
        difficulty_multiplier=data.get('difficulty_multiplier', 1.0),
        scheduled_time=data['scheduled_time'],
        base_exp=data.get('base_exp', BASE_EXP)
    )
    
    if 'attribute_weights' in data:
        new_subactivity.attribute_weights = data['attribute_weights']
    
    db.session.add(new_subactivity)
    db.session.commit()
    
    return jsonify({
        'id': new_subactivity.id,
        'name': new_subactivity.name,
        'activity_id': new_subactivity.activity_id,
        'difficulty_multiplier': new_subactivity.difficulty_multiplier,
        'scheduled_time': new_subactivity.scheduled_time,
        'base_exp': new_subactivity.base_exp,
        'attribute_weights': new_subactivity.attribute_weights
    }), 201


@api_bp.route('/subactivity/<int:subactivity_id>', methods=['PUT', 'DELETE'])
def subactivity_detail(subactivity_id):
    """Handle updating and deleting sub-activities."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    # Verify sub-activity belongs to user
    subactivity = SubActivity.query.join(Activity).filter(
        SubActivity.id == subactivity_id,
        Activity.user_id == user_id
    ).first()
    
    if not subactivity:
        return jsonify({'error': 'Sub-activity not found'}), 404
    
    if request.method == 'PUT':
        data = request.json
        
        if 'name' in data:
            subactivity.name = data['name']
        if 'difficulty_multiplier' in data:
            subactivity.difficulty_multiplier = data['difficulty_multiplier']
        if 'scheduled_time' in data:
            subactivity.scheduled_time = data['scheduled_time']
        if 'base_exp' in data:
            subactivity.base_exp = data['base_exp']
        if 'attribute_weights' in data:
            subactivity.attribute_weights = data['attribute_weights']
        
        db.session.commit()
        
        return jsonify({
            'id': subactivity.id,
            'name': subactivity.name,
            'activity_id': subactivity.activity_id,
            'difficulty_multiplier': subactivity.difficulty_multiplier,
            'scheduled_time': subactivity.scheduled_time,
            'base_exp': subactivity.base_exp,
            'attribute_weights': subactivity.attribute_weights
        })
    
    elif request.method == 'DELETE':
        db.session.delete(subactivity)
        db.session.commit()
        return '', 204

@api_bp.route('/complete_activity', methods=['POST'])
def complete_activity():
    """_summary_
    
    Returns:
        _type_: _description_
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    data = request.json
    
    subactivity_id = data.get('subactivity_id')
    status = data.get('status', 'completed')  # completed, skipped, partial
    actual_time = data.get('actual_time')  # In minutes
    reason = data.get('reason')  # Optional reason for skipping/partial
    # Verify sub-activity belongs to user
    subactivity = SubActivity.query.join(Activity).filter(
        SubActivity.id == subactivity_id,
        Activity.user_id == user_id
    ).first()

    if status == 'completed':
        actual_time = subactivity.scheduled_time

    if not subactivity:
        return jsonify({'error': 'Sub-activity not found'}), 404
    
    user = User.query.get(user_id)
    # Calculate discipline factor (dcp)
    total_scheduled = SubActivity.query.join(Activity).filter(
        Activity.user_id == user_id
    ).count()
    
    total_completed = CompletionLog.query.filter(
        CompletionLog.user_id == user_id,
        CompletionLog.status == 'completed'
    ).count()
    
    dcp = (total_completed / total_scheduled) if total_scheduled > 0 else 0
    
    # Create completion log
    completion = CompletionLog(
        user_id=user_id,
        sub_activity_id=subactivity_id,
        actual_time_taken=actual_time,
        status=status,
        reason=reason
    )
    
    db.session.add(completion)
    
    # Calculate EXP based on status
    gained_exp = 0
    lost_exp = 0

    if status == 'completed':
        # Apply grace period
        time_factor = subactivity.scheduled_time / STANDARD_TIME_UNIT
        if actual_time and actual_time > subactivity.scheduled_time:
            # If over scheduled time but within grace period
            if actual_time <= (subactivity.scheduled_time + GRACE_PERIOD):
                # Still award full EXP
                time_factor = subactivity.scheduled_time / STANDARD_TIME_UNIT
            else:
                # Adjust for overtime
                time_factor = actual_time / STANDARD_TIME_UNIT

        # Calculate EXP gain
        gained_exp = subactivity.base_exp * time_factor * subactivity.difficulty_multiplier * dcp

        # Update user's attributes based on attribute weights
        weights = subactivity.attribute_weights
        user.INT += int(gained_exp * weights.get('INT', 0.2) / 100)
        user.STA += int(gained_exp * weights.get('STA', 0.2) / 100)
        user.FCS += int(gained_exp * weights.get('FCS', 0.2) / 100)
        user.CHA += int(gained_exp * weights.get('CHA', 0.2) / 100)
        user.DSC += int(gained_exp * weights.get('DSC', 0.2) / 100)

    elif status == 'skipped':
        # Calculate penalty for skipped activity
        # P penalty factor (default to 0.5)
        P = 0.5
        lost_exp = subactivity.base_exp * (subactivity.scheduled_time / STANDARD_TIME_UNIT) * subactivity.difficulty_multiplier * P
        gained_exp = -lost_exp  # Negative exp for skipping

    elif status == 'partial':
        # For partial completion, award EXP proportional to time spent
        if actual_time:
            completion_ratio = min(1.0, actual_time / subactivity.scheduled_time)
            gained_exp = subactivity.base_exp * (subactivity.scheduled_time / STANDARD_TIME_UNIT) * subactivity.difficulty_multiplier * dcp * completion_ratio

            # Update attributes with partial EXP
            weights = subactivity.attribute_weights
            user.INT += int(gained_exp * weights.get('INT', 0.2) / 100)
            user.STA += int(gained_exp * weights.get('STA', 0.2) / 100)
            user.FCS += int(gained_exp * weights.get('FCS', 0.2) / 100)
            user.CHA += int(gained_exp * weights.get('CHA', 0.2) / 100)
            user.DSC += int(gained_exp * weights.get('DSC', 0.2) / 100)

    # Update user's total EXP
    user.total_exp += int(gained_exp)
    if user.total_exp < 0:  # Prevent negative EXP
        user.total_exp = 0

    # Check if user should level up
    next_level = Level.query.filter(Level.level_number > user.level).order_by(Level.level_number).first()
    level_up = False

    if next_level and user.total_exp >= next_level.required_exp:
        user.level = next_level.level_number
        level_up = True

    db.session.commit()

    response = {
        'completion_id': completion.id,
        'status': status,
        'exp_change': int(gained_exp),
        'new_total_exp': user.total_exp,
            'level': user.level,
        'level_up': level_up,
            'attributes': {
                'INT': user.INT,
                'STA': user.STA,
                'FCS': user.FCS,
                'CHA': user.CHA,
                'DSC': user.DSC
            }
    }

    if level_up and next_level:
        response['level_up_details'] = {
            'new_level': next_level.level_number,
            'reward': next_level.reward_description
        }

    return jsonify(response), 200

@api_bp.route('/timetable', methods=['GET', 'POST', 'PUT'])
def timetable():
    """Handle timetable operations."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        # Get date from query params, default to today
        req_date = request.args.get('date', date.today().isoformat())
        date_obj = date.fromisoformat(req_date)

        # Find timetable for the requested date
        timetable = Timetable.query.filter_by(
            user_id=user_id,
            date=date_obj
        ).first()
        
        if not timetable:
            return jsonify({'date': req_date, 'schedule': {}}), 200

        return jsonify({
            'date': req_date,
            'schedule': timetable.json_blob
        }), 200

    elif request.method == 'POST':
        # Create new timetable
        data = request.json
        date_obj = date.fromisoformat(data['date'])

        # Check if timetable already exists
        existing = Timetable.query.filter_by(
            user_id=user_id,
            date=date_obj
        ).first()

        if existing:
            return jsonify({'error': 'Timetable for this date already exists'}), 400

        new_timetable = Timetable(
            user_id=user_id,
            date=date_obj,
            json_blob=data['schedule']
        )

        db.session.add(new_timetable)
        db.session.commit()

        return jsonify({
            'id': new_timetable.id,
            'date': data['date'],
            'schedule': new_timetable.json_blob
        }), 201

    elif request.method == 'PUT':
        # Update existing timetable
        data = request.json
        date_obj = date.fromisoformat(data['date'])

        timetable = Timetable.query.filter_by(
            user_id=user_id,
            date=date_obj
        ).first()

        if not timetable:
            return jsonify({'error': 'Timetable not found'}), 404

        timetable.json_blob = data['schedule']
        db.session.commit()

        return jsonify({
            'id': timetable.id,
            'date': data['date'],
            'schedule': timetable.json_blob
        }), 200

@api_bp.route('/stats', methods=['GET'])
def stats():
    """Get user statistics."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    # Calculate discipline factor (dcp)
    total_scheduled = SubActivity.query.join(Activity).filter(
        Activity.user_id == user_id
    ).count()
    
    total_completed = CompletionLog.query.filter(
        CompletionLog.user_id == user_id,
        CompletionLog.status == 'completed'
    ).count()
    
    dcp = (total_completed / total_scheduled) if total_scheduled > 0 else 0

    # Get next level
    next_level = Level.query.filter(Level.level_number > user.level).order_by(Level.level_number).first()
    current_level = Level.query.filter_by(level_number=user.level).first()

    # Calculate progress to next level
    if next_level:
        level_progress = {
            'current_level': user.level,
            'current_exp': user.total_exp,
            'next_level': next_level.level_number,
            'exp_required': next_level.required_exp,
            'exp_to_next_level': next_level.required_exp - user.total_exp,
            'progress_percentage': min(100, ((user.total_exp - current_level.required_exp) /
                                        (next_level.required_exp - current_level.required_exp)) * 100)
        }
    else:
        level_progress = {
            'current_level': user.level,
            'current_exp': user.total_exp,
            'max_level': True
        }

    # Get completion history
    last_30_days = date.today() - timedelta(days=30)
    completion_history = db.session.query(
        func.date(CompletionLog.completed_on).label('date'),
        func.count().label('count')
    ).filter(
        CompletionLog.user_id == user_id,
        CompletionLog.completed_on >= last_30_days
    ).group_by(
        func.date(CompletionLog.completed_on)
    ).all()
    
    history_data = {str(entry.date): entry.count for entry in completion_history}

    data= {
        'user': {
            'id': user.id,
            'username': user.username,
            'level': user.level,
            'total_exp': user.total_exp,
            'attributes': {
                'INT': user.INT,
                'STA': user.STA,
                'FCS': user.FCS,
                'CHA': user.CHA,
                'DSC': user.DSC
            }
        },
        'discipline_factor': dcp,
        'level_progress': level_progress,
        'completion_history': history_data
    }

    return jsonify(data)  ,200
            