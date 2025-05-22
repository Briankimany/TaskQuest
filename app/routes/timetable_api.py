from datetime import datetime, date, time ,timedelta
from flask import request, jsonify 

from app.routes.api import api_bp ,log_app_errors ,session ,verify_id
from app.utils.routes_api_utils import general_decorator as log_app_errors
from app.utils import  login_required 
from app.utils.logger import api_logger

from app.models.timetable import WeekDay
from app.utils.routes_api_utils import is_valid_timezone ,to_utc_from_user_input 
from app.config import TIME_PARSING_STRING ,DATE_PARSING_STRING ,TIME_DATE_SEPARATOR

from app.models.timetable import WeekDay
from app.utils.exceptions.custom_errors import (InvalidRequestData, 
                                     RecordNotFoundError
                                         )

from app.utils.schedulers import TaskScheduler


def parse_time_date(parsing_string :str,date_string:str):
    try:
        if not date_string or not date_string.strip():
            raise InvalidRequestData("Time string can't be empty. ")
        time_obj= datetime.strptime(date_string ,parsing_string)
        return time_obj
    except ValueError as e:
        raise InvalidRequestData(f"Time string needs to be informat {parsing_string}")
    

def validate_timezone(time_zone)  :
    if not is_valid_timezone(time_zone):
        raise InvalidRequestData(f"Incorrect time zone info.")
    return time_zone

def validate_starting_time(time_string:str,time_zone:str,parsing_string):

    starting_time = to_utc_from_user_input(
        user_datetime_str=time_string,
        parsing_string=parsing_string,
        user_timezone_str=validate_timezone(time_zone)
    )
    if not starting_time:
        raise InvalidRequestData(f"Invalid time stamp {time_string} expected {parsing_string}")
    return starting_time



@api_bp.route('/timetable/create', methods=['POST'])
@log_app_errors
def create_timetable():
    """
    Create a new timetable entry for the specified date.
    
    This endpoint handles the creation of a new timetable for the authenticated user.
    It expects a date in YYYY-MM-DD format and optionally accepts a goal text.
    
    Request Body:
        date (str): The date for the timetable in YYYY-MM-DD format
        goal_text (str, optional): Descriptive goal for the day
    
    Returns:
        JSON object containing the created timetable details with HTTP 201 status
    
    Raises:
        InvalidRequestData: If date is missing or improperly formatted
        AuthorizationError: If user authentication fails
    """
        
    user_id = session['user_id']
    data = request.json
    
    if not data.get('date'):
        raise InvalidRequestData("Date is required")
    
    try:
        date_obj = date.fromisoformat(data['date'])
    except ValueError:
        raise InvalidRequestData(f"Invalid date format. Expected {DATE_PARSING_STRING}")
    
    scheduler = TaskScheduler(user_id, datetime.combine(date_obj, time.min))
    timetable = scheduler.create_timetable(
        user_id=user_id,
        date_obj=date_obj,
        goal_text=data.get('goal_text'))
    
    return jsonify({
        'id': timetable.id,
        'date': timetable.date.isoformat(),
        'goal_text': timetable.goal_text
    }), 201


@api_bp.route('/timetable/task', methods=['POST'])
@log_app_errors
def schedule_task():
    """
    Create a new scheduled task in the timetable.
    
    Handles the creation of both regular and cyclic tasks. Requires
    complete scheduling information including sub-activity ID, date,
    start and end times.
    
    Request Body:
        sub_activity_id (int): ID of the activity to schedule
        date (str): Scheduled date in YYYY-MM-DD format
        start_time (str): Start time in HH:MM format
        end_time (str): End time in HH:MM format
        cyclic (bool, optional): Whether task repeats weekly
        weekday (int, optional): Weekday for cyclic tasks (1=Monday)
        create_buffer (bool,optional): whether to schedule a buffer activity.
    
    Returns:
        JSON object containing the created task details with HTTP 201 status
    
    Raises:
        InvalidRequestData: If required fields are missing or invalid
        AuthorizationError: If user authentication fails
        TaskScheduleError: If scheduling constraints are violated
    """

    data = request.json
    required_fields = ['sub_activity_id', 'date', 'start_time', 'time_zone']

    api_logger.info(f"Incoming scheduling request data: {data}")

    if any(field not in data for field in required_fields):
        missing_fields = [i for i in required_fields if i not in data]
        api_logger.error(
            "Missing required fields in scheduling request",
            extra={
                'user_id': session.get('user_id'),
                'missing_fields': missing_fields,
                'received_data': list(data.keys())
            }
        )                       
        raise InvalidRequestData(f"Missing required fields: {missing_fields}")


    api_logger.info(
        "Processing schedule request",
        extra={
            'user_id': session['user_id'],
            'date': data['date'],
            'time_zone': data['time_zone']
        }
    )

    try:
        date_obj = date.fromisoformat(data['date'])
        validate_timezone(data['time_zone'])
        
        start_time = to_utc_from_user_input(
            user_datetime_str=data['start_time'],
            user_timezone_str=data['time_zone'],
            parsing_string=TIME_PARSING_STRING
        ).time()

    except ValueError as e:
        raise InvalidRequestData(str(e))

    api_logger.debug(
        "Attempting to schedule task",
        extra={
            'user_id': session['user_id'],
            'date': date_obj.isoformat(),
            'start_time': start_time.isoformat(),
            'sub_activity_id': data['sub_activity_id'],
            'duration': data.get('task_duration'),
            'cyclic': data.get('cyclic', False)
        }
    )

    scheduler = TaskScheduler(session['user_id'], datetime.combine(date_obj, start_time))
    task_duration = data.get('task_duration', None)
    if task_duration:
        try:
            try:
                task_duration = int(task_duration) / 60
            except Exception as e:
                raise InvalidRequestData("Task duraion must be positive integers in terms of minutes ")
            if task_duration <= 0:
                raise InvalidRequestData("Task duration cannot be less than 1")
        except ValueError as e:
            raise InvalidRequestData(f"Invalid value for duraion {e}")
    
    entry = scheduler.schedule_with_buffer(
        sub_activity_id=data['sub_activity_id'],
        start_time=start_time,
        task_duration_hours=task_duration,
        cyclic=data.get('cyclic', False),
        buffer_name=data.get("buffer_name") or 'Context Switch',
        specific_buffer_name=data.get("specific_buffer_name") or 'Short Break',
        create_buffer_activity=data.get("create_buffer",True),
        description = data.get('description')
    )

 
    api_logger.info(
        "Successfully scheduled task",
        extra={
            'user_id': session['user_id'],
            'entry': entry
        }
    )
    
    return jsonify(entry), 201

@api_bp.route('/timetable/task/<int:entry_id>', methods=['PUT', 'DELETE','GET'])
@log_app_errors
def manage_task(entry_id):

    scheduler = TaskScheduler(session['user_id'], datetime.now())
    if request.method =='GET':
    
        entry = scheduler.update_task(
            user_id=scheduler.user_id,
            entry_id=entry_id

        )
        return jsonify(entry.to_dict()) , 200
    
    if request.method == 'PUT':
        data = request.json

        def validate_timezone_info():
            if not data.get('time_zone'):
                raise InvalidRequestData("Time zone info is required. ")
            validate_timezone(data['time_zone'])
        
        if data.get('start_time'):
            validate_timezone_info()

            try:
                start_time = to_utc_from_user_input(
                    user_datetime_str=data['start_time'],
                    user_timezone_str=data['time_zone'],
                    parsing_string=TIME_PARSING_STRING
                ).time()
            except ValueError as e:
               
                raise InvalidRequestData(f"Inalid time format {e}. expected {TIME_PARSING_STRING}")
        else:
            start_time = None 

        if data.get('end_time'):
            validate_timezone_info()

            try:
                end_time = to_utc_from_user_input(
                    user_datetime_str=data['end_time'],
                    user_timezone_str=data['time_zone'],
                    parsing_string=TIME_PARSING_STRING
                ).time()
            except ValueError as e:
                raise InvalidRequestData(e)
            
        else:
            if start_time:
                duration = data.get("task_duration" ,0)
                
                duration = timedelta(minutes=duration)
                end_time = (datetime.combine(
                    datetime.now(),start_time) +duration).time()
            else:
                end_time = None 

        if data.get('weekday',None):
            try:
                week_day = int(data['weekday'])
                if week_day < 1:
                    raise ValueError
                week_day = WeekDay(week_day)
            except ValueError as e:
                raise InvalidRequestData("Week day must be a positive integer. ")
        else:
            week_day = None 
            
        
        entry = scheduler.update_task(
            user_id=scheduler.user_id,
            entry_id=entry_id,
            start_time=start_time ,
            end_time=end_time,
            sub_activity_id= verify_id(data.get('sub_activity_id',None)) ,
            cyclic=data.get('cyclic'),
            weekday=week_day,
            description = data.get('description')
        )
        return jsonify(entry.to_dict())
            
    elif request.method == 'DELETE':
        if not scheduler.delete_task(entry_id):
             raise RecordNotFoundError("Record not found.")
        return '', 204


@api_bp.route('/timetable/info/<start_date_str>', methods=['GET'])
@api_bp.route('/timetable/weekly/<start_date_str>', methods=['GET'])
@log_app_errors
def get_weekly_timetable(start_date_str):
    """Fetch sheduled tasks from a date string

    Args:
        start_date_str (str): the date to fetch entries.

    Raises:
        InvalidRequestData: If number of days set is lest than 1
        InvalidRequestData: If the date string does not match {}

    Returns:
        json: json list of entries recorded on that day.
    """
    try:
        start_date_obj = datetime.strptime(start_date_str,DATE_PARSING_STRING)
    except ValueError:
        raise InvalidRequestData("Invalid date format. Use YYYY-MM-DD")
    
    days = request.args.get('days',1)
    try:
        days = int(days)
        if days < 1:
            raise InvalidRequestData("Day's range must be greater than zero")
    except ValueError:
        raise InvalidRequestData(f"Day's range must be an integer :{days}")


    scheduler = TaskScheduler(session['user_id'],start_date_obj)
    weekly_schedule = scheduler.weekly_schedule(days=days,return_suggested=True)
    
    return jsonify({
        'start_date': start_date_str,
        'schedule': {d.isoformat(): [e.to_dict() for e in entries] 
                     for d, entries in weekly_schedule.items()}
    })




@api_bp.route('/timetable/stats', methods=['GET'])
@login_required
def get_timetable_stats():
    """Get statistics about scheduled tasks."""
    try:
        days = int(request.args.get('days', 30))
        if days <1:
            raise ValueError("Days must be greater than 1")
    except ValueError as e:
            raise InvalidRequestData(e)
    
    date = request.args.get('date')
    
    if not date:
        date = datetime.now()
    else:
        try:
            date = datetime.strptime(date ,DATE_PARSING_STRING)
        except ValueError as e:
            raise InvalidRequestData(f"Invalid date format {DATE_PARSING_STRING}")
        
    scheduler = TaskScheduler(session['user_id'], date)
    data = scheduler.get_task_stats(
        user_id=scheduler.user_id,
        days=days,
        today=scheduler.current_date)
    
    return jsonify(data)


@api_bp.route('/timetable/activity/<int:activity_id>', methods=['GET'])
@log_app_errors
def get_tasks_by_activity(activity_id):
    """Get all scheduled tasks for a specific activity."""
    scheduler = TaskScheduler(session['user_id'], datetime.now())
    
    try:
        start_date =datetime.strptime(request.args['start_date'] ,DATE_PARSING_STRING) if 'start_date' in request.args else None
        end_date = datetime.strptime(request.args['end_date'],DATE_PARSING_STRING) if 'end_date' in request.args else None
    except ValueError:
        raise InvalidRequestData("Invalid date format. Use YYYY-MM-DD")
    
    entries = scheduler.get_tasks_by_activity(
        user_id=scheduler.user_id,
        activity_id=activity_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'activity_id': activity_id,
        'entries': [entry.to_dict() for entry in entries]
    })

@api_bp.route("/timetable/scheduling/tasks")
@log_app_errors
def get_tasks_to_schedule():


    current_date = request.args.get('date',None)
    if current_date:
        try:
            current_date = datetime.strptime(
                current_date ,DATE_PARSING_STRING)
        except ValueError as e:
            raise InvalidRequestData(
                f"Date string must mactch {DATE_PARSING_STRING}")
    else:
        current_date = datetime.now()

    tasks =  TaskScheduler(
        session['user_id'],current_date).get_tasks_to_schedule(
            return_dict=True 
        )
    
    return jsonify(tasks)


