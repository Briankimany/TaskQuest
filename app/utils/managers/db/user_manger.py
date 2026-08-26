
from app.models import User ,CompletionLog,Timetable,TimetableEntry,db 
from datetime import date, timedelta
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

    @classmethod
    def get_streak(cls, user_id: int) -> int:
        """
        Count consecutive completed days going backward from today.
        A day counts as completed if DCP >= 1.0 (all scheduled tasks done).
        Stops at the first incomplete day or when no tasks were scheduled.
        """
        streak = 0
        today = date.today()

        # Check today first — only count if the day is fully done
        today_dcp = cls.get_dcp(user_id, today)
        if today_dcp >= 1.0:
            streak = 1
            check_date = today - timedelta(days=1)
        else:
            check_date = today - timedelta(days=1)

        # Walk backward
        for _ in range(365):
            scheduled = TaskScheduler.get_daily_schedule(user_id, check_date)
            if not scheduled:
                break
            day_dcp = cls.get_dcp(user_id, check_date)
            if day_dcp >= 1.0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return streak

    @classmethod
    def get_best_streak(cls, user_id: int) -> int:
        """
        Scan the last 365 days for the longest run of consecutive fully-completed days.
        """
        today = date.today()
        best = 0
        current = 0

        for i in range(365, -1, -1):
            check_date = today - timedelta(days=i)
            scheduled = TaskScheduler.get_daily_schedule(user_id, check_date)
            if not scheduled:
                current = 0
                continue
            day_dcp = cls.get_dcp(user_id, check_date)
            if day_dcp >= 1.0:
                current += 1
                best = max(best, current)
            else:
                current = 0

        return best

    @classmethod
    def get_missed_count(cls, user_id: int, date_obj: date) -> int:
        """
        Count tasks scheduled for a date that have no CompletionLog entry at all.
        Skipped/partial tasks are NOT counted as missed — they were at least logged.
        """
        scheduled = TaskScheduler.get_daily_schedule(user_id, date_obj)
        logged_entry_ids = {
            log.timetable_entry_id for log in CompletionLog.query.filter(
                CompletionLog.user_id == user_id,
                CompletionLog.completed_on == date_obj
            ).all()
        }
        missed = sum(1 for task in scheduled if task.id not in logged_entry_ids)
        return missed
