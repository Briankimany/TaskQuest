

from datetime import datetime, time, timedelta
from typing import Optional
from app.utils.managers import TimetableManager
from app.models import SubActivity  ,db,Activity 
from app.utils.custom_errors import TaskScheduleError ,AuthorizationError
from app.utils.logger import api_logger

class TaskScheduler(TimetableManager):
    """Handles RPG system task scheduling with buffer periods between activities."""
    
    def __init__(self, user_id: int,date:datetime):
        self.user_id = user_id
  
        self.current_date = date.date()

    def schedule_with_buffer(self, 
                          sub_activity_id: int,
                          start_time: time,
                          task_duration_hours: int = None,
                          buffer_duration:int=None,
                          specific_buffer_name:str="Short Break",
                          buffer_name:str='Context Switch',
                          cyclic= False,
                          create_buffer_activity=True,
                          description:str=None) -> Optional[dict]:
        """Schedules a task with automatic context-switching buffer.
        
        Args:
            sub_activity_id: ID of the activity to schedule
            start_time: When the task should begin
            task_duration_hours: Length of main task (default: sub_activity.scheduled_time)
            
        Returns:
            Dictionary with scheduled items or None if failed
        """
        try:
            
            if not task_duration_hours:
                sub_activity = SubActivity.query.filter_by(id=sub_activity_id).first()
                if not sub_activity:
                    raise AuthorizationError("Invalid activity or subactivty does not belong to user")
                task_duration_hours = sub_activity.scheduled_time /60

            task_start = self._combine_date_time(start_time)
            task_end = task_start + timedelta(hours=task_duration_hours)
            
 
            timetable = self.get_or_create_timetable(
                user_id=self.user_id,
                date_obj=self.current_date
            )
            
            main_task = self.schedule_task(
                user_id=self.user_id,
                sub_activity_id=sub_activity_id,
                date_obj=self.current_date,
                start_time=start_time,
                end_time=task_end.time().replace(microsecond=0),
                cyclic=cyclic,
                description=description
            )
            
            if not create_buffer_activity:
                return {
                    "main_task":main_task.to_dict(),
                    "buffer_task":None
                }
            
            buffer_activity = self._get_or_create_buffer(name=buffer_name,specific_name=specific_buffer_name)
            
            buffer_end = task_end + timedelta(minutes= buffer_duration or buffer_activity.scheduled_time)
            
            buffer_task = self.schedule_task(
                user_id=self.user_id,
                sub_activity_id=buffer_activity.id,
                date_obj=self.current_date,
                start_time=task_end.time(),
                end_time=buffer_end.time().replace(microsecond=0)
            )
            
            return {
                'main_task': main_task.to_dict(),
                'buffer_task': buffer_task.to_dict()
            }
            
        except TaskScheduleError as e:
            api_logger.warning(f"Scheduling conflict: {e}")
            db.session.rollback()
            raise e 
        
        except Exception as e:
            api_logger.critical(f"Unexpected error: {e}")
            db.session.rollback()
            raise e 
    
    def weekly_schedule(self,days:int=7 ,return_suggested=False):
        """Retrive scheduled tasks for a spand of seven days.

        Args:
            days (int, optional): Number of days to look ahead. Defaults to 7.
            return_suggested (bool, optional): Whether to retireve cylcic activites . Defaults to False.

        Returns:
            list:  of TimetableEntry instances
        """
        return self.get_weekly_schedule(
            user_id=self.user_id,
            start_date=self.current_date,
            days=days,
            return_suggested=return_suggested,

        )
    def delete_task(self,entry_id):
        return self.delete_user_entry(self.user_id,entry_id)
    
    def get_tasks_to_schedule(self ,return_dict=False):

        suggested_entries = self.get_daily_schedule(
            user_id=self.user_id,
            return_suggested=True,
            date_obj=self.current_date
        )
        suggested_activites = set([i.sub_activity.activity.name for i in suggested_entries])
        new_activites = self._get_users_activities()

        activities_data = {}
        
        for activity in new_activites:
            if activity.name in suggested_activites:
                key = 'suggested_activities'
            else:
                key = 'new_activities'

            if key not in activities_data:
                activities_data[key]=[]
            
            if return_dict:
                activity = activity.to_dict()
            activities_data[key].append(activity)

        
        for key in ['suggested_activities', 'new_activities']:
            if key not in activities_data:
                activities_data[key] = []

        if return_dict:
            suggested_entries = [i.sub_activity.to_dict() for i in suggested_entries]

        activities_data['suggested_sub_activities'] = suggested_entries 

        return activities_data
             

    def _get_users_activities(self):
        return Activity.query.filter_by(user_id=self.user_id).all()
    
    def _get_or_create_buffer(self,name='Context Switch',specific_name:str='Short Break') -> SubActivity:
        """Ensures buffer activity exists for the user."""
        buffer_activity = self.create_buffer_activity(self.user_id ,name)
        return self.create_buffer_sub_activity(
            user_id=self.user_id,
            activity_id=buffer_activity.id,
            name=specific_name
        )
    
    def _combine_date_time(self, time_obj: time) -> datetime:
        """Combines current date with time object."""
        return datetime.combine(self.current_date, time_obj)
    
