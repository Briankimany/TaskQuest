from flask import request, jsonify
from app.routes.timetable_api import api_bp ,session ,log_app_errors,parse_time_date
from app.utils.managers.completion_manager import CompletionLogManager
from app.utils.custom_errors import InvalidRequestData
from app.config import TIME_PARSING_STRING ,TIME_DATE_SEPARATOR,DATE_PARSING_STRING


@api_bp.route('/complete/complete_activity', methods=['POST'])
@log_app_errors
def complete_activity():
    """
    Mark a timetable entry as completed.
    
    Request Body:
        timetable_entry_id (int): ID of the timetable entry to complete
        status (str): Completion status ('completed', 'skipped', 'partial')
        actual_time_taken (int, optional): Actual time spent in minutes
        reason (str, optional): Reason for skipped/partial completion
        
    Returns:
        JSON object containing the created completion log details
    """
    data = request.json
    user_id = session['user_id']
    
    required_fields = ['timetable_entry_id', 'status','completed_on']
    if any(field not in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        raise InvalidRequestData(f"Missing required fields: {missing_fields}")
    
    parsing_string = DATE_PARSING_STRING+TIME_DATE_SEPARATOR+TIME_PARSING_STRING

    completed_on = parse_time_date(parsing_string,data['completed_on'])

    valid_statuses = ['completed', 'skipped', 'partial']
    if data['status'] not in valid_statuses:
        raise InvalidRequestData(f"Invalid status. Must be one of: {valid_statuses}")
        
    try:
        log = CompletionLogManager.create_completion_log(
            user_id=user_id,
            timetable_entry_id=data['timetable_entry_id'],
            status=data['status'],
            completion_time = completed_on,
            actual_time_taken=data.get('actual_time_taken'),
            reason=data.get('reason'),
            comment=data.get('comment')
        )
        
        user_response = CompletionLogManager.exp_manager.distribute_user_exp(
            user_id, log.exp_impact,log.sub_activity_id)
    except ValueError as e:
        raise InvalidRequestData(e)    
    
    return jsonify({
        'completion_id': log.id,
        'status': log.status,
        'exp_change': log.exp_impact,
        **user_response
    }), 201

@api_bp.route('/complete/finalize_day', methods=['POST'])
@log_app_errors
def finalize_day():
    """
    Finalize the day's events and calculate the overall day's gained EXP.
    
    Returns:
        JSON object containing the total EXP gained for the day and updated user attributes
    """
    data = request.json 
    if 'date' not in data:
        raise InvalidRequestData("date is a required in the json body. ")
    
    date_obj = parse_time_date(DATE_PARSING_STRING,data['date'])
    user_id = session['user_id']
    
    try:
        response = CompletionLogManager.finalize_day(user_id,date_obj.date())
    except ValueError as e:
        raise InvalidRequestData(e)
    
    return jsonify(response), 200