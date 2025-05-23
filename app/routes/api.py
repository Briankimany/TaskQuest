"""
API routes for the Real-Life RPG System.

This module provides JSON API endpoints for activities, sub-activities,
timetables, completion tracking, and stats retrieval.
"""

from app.utils import login_required


from flask import Blueprint, request, jsonify ,session
from datetime import datetime, date, timedelta
from sqlalchemy import func

from app.models import db, User, Activity, SubActivity, CompletionLog, Level, Timetable
from app.models import BASE_EXP, STANDARD_TIME_UNIT, GRACE_PERIOD
from app.config import ATTRIBUTES_LIST  ,TIME_PARSING_STRING

from app.utils.exceptions import *
from app.utils.logger import api_logger 
from app.utils.routes_api_utils import general_decorator as log_app_errors
from werkzeug.exceptions import BadRequest ,HTTPException


api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.errorhandler(HTTPException)
def handle_http_errors(e):
   return jsonify({'type': 'HTTPException', 'msg': str(e)}), e.code

@api_bp.errorhandler(BadRequest)
def server_bad_request(error):
    return jsonify(
        {
            'description': str(error),
            'msg': "Could not process request"
        }
    ) , 400

@api_bp.errorhandler(AppError)
def handle_app_error(error: AppError):
    response, code = error.to_response()
    return jsonify(response), code



def serialize_sub_activity(sa):
    return {
        'id': sa.id,
        'name': sa.name,
        'difficulty_multiplier': sa.difficulty_multiplier,
        'scheduled_time': str(sa.scheduled_time),
        'base_exp': sa.base_exp,
        'attribute_weights': sa.attribute_weights
    }

def serialize_activity(act):
    return {
        'id': act.id,
        'name': act.name,
        'created_at': act.created_at.isoformat(),
        'sub_activities': [
            sa.to_dict() for sa in act.sub_activities if sa.active
        ]
    }
    
def validate_sub_activity_attributes(data):
    sent_data = [data['attribute_weights'].get(key ,0 ) for key in ATTRIBUTES_LIST]
    if sum(sent_data) !=1:
        raise InvalidRequestData(f"All attributes weights must add up to 1 {data['attribute_weights']}")
    return data['attribute_weights']


sub_activity_validator_map ={
    "attribute_weights":validate_sub_activity_attributes
}

def verify_id(id_:str):
    try:
        if not id_:
            return None 
        
        id_= int(id_)
        if id_ < 1:
            raise InvalidRequestData("Requst id must be greater than 1")
        return id_
    except ValueError as e:
        raise InvalidRequestData("Invalid request id ")


@api_bp.route('/activities', methods=['GET', 'POST'])
@log_app_errors
def activities():
    """Handle CRUD operations for activities.
    API endpoint for managing activities.

    GET: Retrieves all activities for the authenticated user with their sub-activities.
    POST: Creates a new activity for the authenticated user.

    Returns:
        GET: JSON with list of activities and their sub-activities
        POST: JSON with the newly created activity details and 201 status code
        
    Requires user authentication via session.
    """

    user_id = session['user_id']
   
    if request.method == 'GET':
        
        activity_id = verify_id(request.args.get("id",None))
        activities = Activity.query.filter_by(user_id=user_id)
        if activity_id:
            activities=activities.filter_by(id=activity_id)
       
        return jsonify({
            'activities': [serialize_activity(act) for act in activities.all()]
        })

        
    elif request.method == 'POST':
        data = request.json
        activity =  Activity.query.filter_by(name=data['name'],user_id=session['user_id']).first()
        if  activity:
            raise RecordDuplicationError(f"Acivity already exist. {data['name']}",201)
        
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
@login_required
def activity_detail(activity_id):
    """
    Handle updating and deleting activities.

    Endpoint for modifying or removing an activity. Requires user authentication.
    PUT: Updates activity name
    DELETE: Removes the activity

    Returns:
        PUT: JSON with updated activity details
        DELETE: Empty response with 204 status
        401: If user is not authenticated
        404: If activity not found
    """
    
    user_id = session['user_id']
    activity = Activity.query.filter_by(id=activity_id, user_id=user_id).first()
    
    if not activity:
      raise RecordNotFoundError(f'No activity with id {activity_id}',
                                404)

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
@log_app_errors
def create_subactivity():
    """
    Create a new sub-activity for an existing activity.

    API endpoint for creating sub-activities. Requires user authentication.
    Validates that the activity belongs to the authenticated user.

    Returns:
        JSON with the newly created sub-activity details and 201 status code
        401: If user is not authenticated
        404: If activity not found or doesn't belong to user
    """
  
    data = request.json

    activity_id = data.get('activity_id')
    if not activity_id:
        api_logger.error(f'invalid request data: {data}')
        raise InvalidRequestData("Key error 'activity_id not in request's json' ")
   

    activity = Activity.query.filter_by(
        id=activity_id, 
        user_id=session['user_id']
    ).first()
    
    if not activity:
        api_logger.error(f"Cant modify other users activities data: {data}")
        raise AuthorizationError("Can only modify activites you created ",400)

    activity_data_keys = ['name','difficulty_multiplier',
                          'scheduled_time','base_exp'
                          ,'attribute_weights']
    
    activity_data = [data.get(key) for key in activity_data_keys]
    if not all(activity_data):
        missing_values = [i for i in activity_data_keys if i not in data]
        raise InvalidRequestData(f"Mising activity keys :{missing_values}")
    
    validate_sub_activity_attributes(data)

    if SubActivity.query.filter_by(name=data['name'],user_id=session['user_id']).first():
        raise RecordDuplicationError(f"Sub activity duplication detected {data['name']}")
    
    new_subactivity = SubActivity(
        name=data['name'],
        activity_id=activity_id,
        difficulty_multiplier=data['difficulty_multiplier'],
        base_exp=data['base_exp']
    )
    new_subactivity.scheduled_time = data['scheduled_time']
    
    new_subactivity.attribute_weights = data['attribute_weights']
    db.session.add(new_subactivity)
    db.session.commit()
    
    return jsonify({
        'id': new_subactivity.id,
        'name': new_subactivity.name,
        'activity_id': new_subactivity.activity_id,
        'difficulty_multiplier': new_subactivity.difficulty_multiplier,
        'scheduled_time': str(new_subactivity.scheduled_time),
        'base_exp': new_subactivity.base_exp,
        'attribute_weights': new_subactivity.attribute_weights
    }), 201


@api_bp.route('/subactivity/<int:subactivity_id>', methods=['PUT', 'DELETE'])
@login_required
def subactivity_detail(subactivity_id):
    """Handle updating and deleting sub-activities."""
    user_id = session['user_id']
    
    # Verify sub-activity belongs to user
    subactivity = SubActivity.query.filter(
        SubActivity.id == subactivity_id,
        SubActivity.user_id == user_id
    ).first()
    
    if not subactivity:
        raise AuthorizationError("Can only edit sub activites user own")
    
    if request.method == 'PUT':
        data = request.json

        for sub_activity_attribute ,value in data.items():
            if not hasattr(subactivity,sub_activity_attribute):
                continue
    
            validator = sub_activity_validator_map.get(sub_activity_attribute)
            value = validator(data) if validator else value

            setattr(subactivity,sub_activity_attribute,value)
       
        db.session.commit()
        
        return jsonify({
            'id': subactivity.id,
            'name': subactivity.name,
            'activity_id': subactivity.activity_id,
            'difficulty_multiplier': subactivity.difficulty_multiplier,
            'base_exp': subactivity.base_exp,
            'attribute_weights': subactivity.attribute_weights
        })
    
    elif request.method == 'DELETE':
        subactivity.active=False 
        db.session.commit()
        return '', 204


@api_bp.route('/stats', methods=['GET'])
@log_app_errors
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
            