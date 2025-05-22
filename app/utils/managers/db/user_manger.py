
from app.models import User ,CompletionLog,Timetable,TimetableEntry,db 
from datetime import date
from app.utils.schedulers import TaskScheduler
from app.utils.logger import user_logger


class UserManager:
    """
    Manager class for handling user-related operations.
    """
    log = user_logger

    def __init__(self):
        """
        Initialize the UserManager.
        """
        self.user = None
    def get_user(self, user_id: int) -> User:
        """
        Get a user by their ID.
        Args:
            user_id: The ID of the user.
        Returns:
            The User object.
        """
        self.user = User.query.get(user_id) 

    def dcp(self,date_obj:date) -> float:
        """
        Get the daily completion percentage for the user.
        Args:
            date_obj: The date for which to calculate the DCP.
        Returns:
            The DCP for the user.
        """
        return self.get_dcp(self.user.id,date_obj)
    
    @classmethod
    def get_dcp(cls,user_id,date_obj:date) -> float:
        """
        Get the daily completion percentage for a user.
        Args:
            user_id: The ID of the user.
            date_obj: The date for which to calculate the DCP.
        Returns:
            The DCP for the user.
        """

        total_completions =  CompletionLog.query.filter(
            CompletionLog.user_id == user_id,
            CompletionLog.status != 'skipped',
            CompletionLog.completed_on == date_obj
        ).all()
      
        completion_count = sum([1 for i in total_completions if i.sub_activity.base_exp])

        scheduled = TaskScheduler.get_daily_schedule(user_id,date_obj)
        schdeuled_count = sum([1 for i in scheduled if i.sub_activity.base_exp])
  
        if schdeuled_count == 0:
            dcp= 1.0
        else:
            dcp=completion_count / schdeuled_count

        cls.log.debug(f"Discipline factor is {dcp} : {completion_count} / {schdeuled_count}")

        return dcp 

        
