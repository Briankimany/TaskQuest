from datetime import datetime, timedelta ,time ,date
from app.models import CompletionLog, SubActivity, TimetableEntry, User, Level, db,Timetable
from app.utils.logger import api_logger
from .exp_manager import ExpManager
from app.utils.exceptions import RecordDuplicationError ,InvalidRequestData,IncompleteTasks,RecordNotFoundError
from .timetable_manager import TimetableManager

class CompletionLogManager:
    """Utility class to manage completion log operations."""
    
    GRACE_PERIOD = timedelta(minutes=15)  
    STANDARD_UNIT_TIME =timedelta(hours=1) 
    log = api_logger
    exp_manager = ExpManager()

    @classmethod
    def create_completion_log(cls,user_id: int, timetable_entry_id: int, status: str, completion_time:datetime,
                            actual_time_taken: int = None, reason: str = None,comment:str=None) -> CompletionLog:
        """_summary_

        Args:
            user_id (int): user id
            timetable_entry_id (int): timetable entry id
            status (str): status of completion
            completion_time (datetime): actual completion time
            actual_time_taken (int, optional): time spent on task. Defaults to None.
            reason (str, optional): Reason for. Defaults to None.

        Raises:
            ValueError: if timetable entry is not found.

        Returns:
            CompletionLog: a record from the table completion logs.
        """
        cls.log.debug("-"*40)
        cls.log.info(f"Creating completion log for timetable_entry_id={timetable_entry_id}", 
                       extra={"user": user_id})
        
        # Get the subactivity from timetable entry
        entry = db.session.query(TimetableEntry).join(SubActivity).filter(
            TimetableEntry.id==timetable_entry_id,SubActivity.user_id==user_id).first()
        
        if not entry.timetable.date == completion_time.date():
            raise InvalidRequestData("Completion time does not match the date of the timetable entry")
        
        if not entry:
            raise InvalidRequestData("Invalid timetable entry ID or Provided user does not have the rights")
        
        task_is_logged = CompletionLog.query.filter_by(
            user_id=user_id,
            timetable_entry_id=timetable_entry_id,
            completed_on=completion_time.date()
        )

        if task_is_logged.first():
            cls.log.warning("Task already logged. ")
            raise RecordDuplicationError("Task already logged for this day")
        
        sub_activity = entry.sub_activity
     
        exp_impact = None
        if sub_activity.base_exp > 0:
            exp_impact =cls.exp_manager.calculate_exp_impact(
                sub_activity=sub_activity,
                status=status,
                actual_time_taken=actual_time_taken,
                scheduled_time=cls._subtract_time_obj(
                        entry.end_time,entry.start_time).total_seconds(),
                end_time=entry.end_time,
                start_time=entry.start_time,
                completion_time=completion_time,
                reason=reason
            )
            
        log = CompletionLog(
            user_id=user_id,
            timetable_entry_id=timetable_entry_id,
            sub_activity_id=sub_activity.id,
            status=status,
            actual_time_taken=actual_time_taken,
            reason=reason,
            exp_impact=exp_impact,
            completed_on=completion_time.date(),
            comment=comment
        )
        
        db.session.add(log)
        db.session.commit()
        api_logger.info(f"Successfully created completion log id={log.id}", 
                       extra={"user": user_id})
        return log
    
    @classmethod
    def _wrapp_time_to_datetime(cls,time_obj:time):
        assert type(time_obj) == time 
        return datetime.combine(datetime.now(),time_obj)
    @classmethod
    def _subtract_time_obj(cls,t1:time ,t2:time):
        """_summary_
        Args:
            t1 (time):  time to subtract t2 from
            t2 (time): time to subtract from t1
        Returns:
            time object: returns t1 -t2
        """
        return cls._wrapp_time_to_datetime(t1) - cls._wrapp_time_to_datetime(t2)
    
    @classmethod
    def _get_scheduled_tasks(cls,user_id ,today:date):
        scheduled_tasks = TimetableManager.get_daily_schedule(
            user_id,
            today,
            return_suggested=False
        )
        return scheduled_tasks
    
    @classmethod 
    def _get_completed_logs(cls,user_id,today:date):
        completed_logs = CompletionLog.query.filter_by(
            user_id = user_id,
            completed_on=today
        ).all()
        return completed_logs
    
    @classmethod
    def finalize_day(cls,user_id: int ,today:date) -> dict:
        """
        Finalize the day's events and calculate the overall day's gained EXP.
        
        Args:
            user_id: ID of the user
            today: Date to finalize tasks on
            
        Returns:
            Dictionary with the total EXP gained for the day and updated user attributes
        """
        timetable = Timetable.query.filter_by(date=today).first()
        if not timetable:
            cls.log.warning(f"No timetable found for date {today}")
            raise RecordNotFoundError("No timetable found for the given date.")
        if timetable.finalized:
            cls.log.warning(f"Timetable for date {today} is already finalized.")
            # raise RecordDuplicationError("Timetable for the given date is already finalized.")
        
        timetable.finalized = True  

        cls.log.info(f"Finalizing day for user_id={user_id} on date={today}")
        scheduled_tasks = cls._get_scheduled_tasks(user_id,today)
        
        if not scheduled_tasks:
            cls.log.warning("No scheduled tasks werer found. ")
            raise RecordNotFoundError("No scheduled tasks found for the given date.")

        completed_logs = cls._get_completed_logs(user_id,today)
        cls.log.debug(f"Found {len(completed_logs)} entry logs. ")

        completed_tasks = [i.timetable_entry.id for i in completed_logs]
        in_complete_tasks = [i for i in scheduled_tasks if i.id not in completed_tasks]
       
        if in_complete_tasks:
            names ={"names":[i.sub_activity.name for i in in_complete_tasks]}
            cls.log.warning(f"Incomplete tasks detected: {names}")

            raise IncompleteTasks(message="Cannot finalize day. Incomplete tasks still exist.",
                                  extra_data=names)
        
        total_exp = cls._calculate_total_exp(user_id=user_id,today=today)
        

        # Update user's EXP and attributes
        user = User.query.get(user_id)
        user.total_exp += total_exp
        
        # Check for level up
        next_level = Level.query.filter(Level.level_number > user.level).order_by(Level.level_number).first()
        level_up = False

        if next_level and user.total_exp >= next_level.required_exp:
            user.level = next_level.level_number
            level_up = True
        
        db.session.commit()

        response = {
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

        return response

    @classmethod
    def _calculate_total_exp(cls,today:date ,user_id: int) -> int:
        
        cls.log.info(f"Calculating total EXP for user_id={user_id} on date={today}")
        logs = cls._get_completed_logs(user_id,today)

        total_exp = sum(log.exp_impact for log in logs if log.exp_impact is not None )
        
        cls.log.debug(f"Total Exp is {total_exp}")
        # Calculate discipline factor
        total_scheduled = len(cls._get_scheduled_tasks(user_id,today))
        total_followed = CompletionLog.query.filter(
            CompletionLog.user_id == user_id,
            CompletionLog.status != 'skipped',
            CompletionLog.completed_on == today
        ).count()
        
        dcp = total_followed / total_scheduled
        if dcp > 1:
            raise Exception("SERVER ERROR. dcp cannot be greater than 1")
        cls.log.debug(f"Discipline factor is {dcp} : {total_followed} / {total_scheduled}")

        final_exp= int(total_exp * dcp)
        cls.log.debug(f"Final exp is {final_exp}")
        return final_exp
    