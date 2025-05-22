from datetime import date, time, timedelta
from typing import List, Dict
from sqlalchemy import and_

from app.utils.logger import api_logger
from app.models import (
    Timetable, 
    TimetableEntry, 
    WeekDay ,
    SubActivity, 
    Activity,
    db)
from app.utils.exceptions import (TaskScheduleError ,
                                     AuthorizationError ,
                                     RecordDuplicationError,
                                     CustomWarnings)


class TimetableManager:
    """
    Utility class to manage timetable operations including scheduling tasks,
    deleting them, and querying them.
    """
        
    @staticmethod
    def create_buffer_activity(user_id: int ,buffer_name='Context switch') -> Activity:
        """Creates or retrieves a context-switching activity for the user.
        
        This activity serves as a container for buffer periods between tasks,
        helping users transition between different types of work.

        Args:
            user_id: The ID of the user who owns the activity

        Returns:
            Activity: The context-switching activity instance
        """
        api_logger.info(f"Attempting to retrieve buffer activity for user_id={user_id}", extra={"user": user_id})
        
        activity = Activity.query.filter_by(
            name=buffer_name,
            user_id=user_id
        ).first()
        
        if not activity:
            api_logger.info(f"No existing buffer activity found for user_id={user_id}, creating new one", extra={"user": user_id})
            activity = Activity(name='Context switch', user_id=user_id)
            db.session.add(activity)
            db.session.commit()
            api_logger.info(f"Created new buffer activity id={activity.id} for user_id={user_id}", extra={"user": user_id})
        else:
            api_logger.info(f"Retrieved existing buffer activity id={activity.id} for user_id={user_id}", extra={"user": user_id})
        
        return activity

    @staticmethod
    def create_buffer_sub_activity(
        user_id: int,
        activity_id: int,
        name: str = "Context switch break",
        schedule_time: int = 15
    ) -> SubActivity:
        """Creates or retrieves a context-switching break sub-activity.
        
        These breaks appear between scheduled tasks and:
        - Award 0 EXP by default
        - Have no attribute weights
        - Default to 15 minute duration

        Args:
            user_id: Owner user ID
            activity_id: Parent activity ID
            name: Display name (default: "Context switch break")
            schedule_time: Duration in minutes (default: 15)

        Returns:
            SubActivity: The created or existing buffer sub-activity
        """
        subactivity = SubActivity.query.filter_by(
            user_id=user_id,
            name=name,
            activity_id=activity_id
        ).first()

        if not subactivity:
            subactivity = SubActivity(
                name=name,
                activity_id=activity_id,
                base_exp=0,
                attribute_weights={},
                scheduled_time=schedule_time
            )
            db.session.add(subactivity)
            db.session.commit()
        
        return subactivity

    @staticmethod
    def create_timetable(user_id: int, date_obj: date, goal_text: str = None) -> Timetable:
        """
        Create a new timetable for a specific date.
        
        Args:
            user_id: The ID of the user
            date_obj: The date for the timetable
            goal_text: Optional goal text for the day
            
        Returns:
            The created Timetable object
        """
        if  Timetable.query.filter_by(user_id=user_id, date=date_obj).first():
            raise RecordDuplicationError("Time table duplication detected.")
        
        timetable = Timetable(
            user_id=user_id,
            date=date_obj,
            goal_text=goal_text
        )
        db.session.add(timetable)
        db.session.commit()
        return timetable
    
    @staticmethod
    def get_or_create_timetable(user_id: int, date_obj: date) -> Timetable:
        """
        Get an existing timetable for a date or create a new one if it doesn't exist.
        
        Args:
            user_id: The ID of the user
            date_obj: The date for the timetable
            
        Returns:
            The retrieved or created Timetable object
        """
        timetable = Timetable.query.filter_by(user_id=user_id, date=date_obj).first()
        if not timetable:
            timetable = TimetableManager.create_timetable(user_id, date_obj)
        return timetable
    
    @staticmethod
    def schedule_task(
        user_id: int,
        sub_activity_id: int,
        date_obj: date,
        start_time: time,
        end_time: time,
        cyclic: bool = False,
        description:str=None
    ) -> TimetableEntry:
        """
        Schedule a task in the timetable.
        
        Args:
            user_id: The ID of the user
            sub_activity_id: The ID of the sub-activity to schedule
            date_obj: The date for the task
            start_time: The start time for the task
            end_time: The end time for the task
            cyclic: Whether this is a recurring task
            
        Returns:
            The created TimetableEntry object
            
        Raises:
            ValueError: If there's a time conflict or invalid parameters
        """
 
        sub_activity = SubActivity.query.filter_by(id=sub_activity_id).first()
        if not sub_activity or sub_activity.user_id != user_id:
            raise AuthorizationError("Invalid sub-activity ID or sub-activity doesn't belong to the user")
        
        
        if start_time >= end_time:
            raise TaskScheduleError("Start time must be before end time")
        
        # Get or create timetable for the date
        timetable = TimetableManager.get_or_create_timetable(user_id, date_obj)
        if timetable.finalized:
            raise TaskScheduleError("Cannot schedule tasks to an already finalized day. ")
        # Check for time conflicts
        if TimetableManager._has_time_conflict(timetable.id, start_time, end_time):
            api_logger.error(f"Time conflict with existing task date:{date_obj} start time: {start_time}: end time: {end_time}")
            raise TaskScheduleError("Time conflict with existing task")
        
        # Create the entry
        entry = TimetableEntry(
            timetable_id=timetable.id,
            sub_activity_id=sub_activity_id,
            start_time=start_time,
            end_time=end_time,
            cyclic=cyclic,
            weekday= date_obj.isocalendar().weekday if cyclic else None,
            description=description
        )
        
        db.session.add(entry)
        db.session.commit()
        return entry
    
    @staticmethod
    def _has_time_conflict(timetable_id: int, start_time: time, end_time: time) -> bool:
        """
        Check if there's a time conflict with existing entries.
        
        Args:
            timetable_id: The ID of the timetable
            start_time: The start time to check
            end_time: The end time to check
            
        Returns:
            True if there's a conflict, False otherwise
        """
        conflicts = TimetableEntry.query.filter(
            TimetableEntry.timetable_id == timetable_id,
                and_(
                    TimetableEntry.start_time < end_time,
                    TimetableEntry.end_time > start_time
                )
        )
    
        return conflicts.count() > 0
    
    @staticmethod
    def delete_task(entry_id: int, user_id: int) -> bool:
        """
        Delete a scheduled task.
        
        Args:
            entry_id: The ID of the entry to delete
            user_id: The ID of the user (for security check)
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            ValueError: If the entry doesn't exist or doesn't belong to the user
        """
        entry = TimetableEntry.query.join(Timetable).filter(
            TimetableEntry.id == entry_id,
            Timetable.user_id == user_id
        ).first()
        
        if not entry:
            raise AuthorizationError("Entry not found or doesn't belong to the user")
        
        db.session.delete(entry)
        db.session.commit()
        return True
    
    @staticmethod
    def update_task(
        entry_id: int,
        user_id: int,
        start_time: time = None,
        end_time: time = None,
        sub_activity_id: int = None,
        cyclic: bool = None,
        weekday: WeekDay = None,
        description:str=None
    ) -> TimetableEntry:
        """Update a scheduled task while maintaining RPG system integrity.
        
        Handles:
        - Time validation
        - Allows shrinking buffer periods freely
        - Prevents overlapping non-buffer activities
        - Smart adjacent activity detection
            
        Args:
            entry_id: ID of entry to update
            user_id: Owner verification
            start_time: New start time (optional)
            end_time: New end time (optional)
            sub_activity_id: New activity ID (optional)
            cyclic: Recurring flag (optional)
            weekday: For cyclic tasks (optional)
            
        Returns:
            Updated TimetableEntry
            
        Raises:
            AuthorizationError: Invalid ownership
            ValueError: Invalid time logic
            TaskScheduleError: RPG rule violations
        """
        api_logger.info(f"Updating task entry_id={entry_id} for user_id={user_id}", extra={"user": user_id})
        
        entry = TimetableEntry.query.join(Timetable).filter(
            TimetableEntry.id == entry_id,
            Timetable.user_id == user_id
        ).first()
        if not entry:
            api_logger.warning(f"Authorization error: Entry {entry_id} not found or doesn't belong to user {user_id}", extra={"user": user_id})
            raise AuthorizationError("Entry not found")
        
        if entry.timetable.finalized:
            raise TaskScheduleError("Cannot modify  tasks for an already finalized day. ")
        
        api_logger.info(f"Found entry {entry_id} for timetable_id={entry.timetable_id}", extra={"user": user_id})
   
        new_start = start_time or entry.start_time
        new_end = end_time or entry.end_time
        if new_start >= new_end:
            api_logger.warning(f"Invalid time range for entry {entry_id}: start={new_start}, end={new_end}", extra={"user": user_id})
            raise ValueError("Invalid time range")

        api_logger.info(f"Checking for adjacent activities for entry {entry_id}", extra={"user": user_id})

        prev_activity = TimetableEntry.query.filter(
            TimetableEntry.timetable_id == entry.timetable_id,
            TimetableEntry.end_time <= entry.start_time, 
            TimetableEntry.id != entry_id 
        ).order_by(TimetableEntry.end_time.desc()).first()

        next_activity = TimetableEntry.query.filter(
            TimetableEntry.timetable_id == entry.timetable_id,
            TimetableEntry.start_time >= entry.end_time, 
            TimetableEntry.id != entry_id 
        ).order_by(TimetableEntry.start_time.asc()).first()

        if prev_activity and prev_activity.sub_activity.base_exp > 0:  
            api_logger.info(f"Previous activity {prev_activity.id} is non-buffer (base_exp > 0)", extra={"user": user_id})
            if new_start < prev_activity.end_time:
                api_logger.warning(f"Task overlap error: new_start={new_start} would overlap previous task end_time={prev_activity.end_time}", extra={"user": user_id})
                raise TaskScheduleError("Would overlap previous task")

        
        if next_activity and next_activity.sub_activity.base_exp > 0:  
            api_logger.info(f"Next activity {next_activity.id} is non-buffer (base_exp > 0)", extra={"user": user_id})
            if new_end > next_activity.start_time:
                api_logger.warning(f"Task overlap error: new_end={new_end} would overlap next task start_time={next_activity.start_time}", extra={"user": user_id})
                raise TaskScheduleError("Would overlap next task")

        # Handle buffer adjustments
        if prev_activity and prev_activity.sub_activity.base_exp == 0: 
            api_logger.info(f"Adjusting previous buffer activity {prev_activity.id} end_time from {prev_activity.end_time} to {new_start}", extra={"user": user_id})
            prev_activity.end_time = new_start  

        if next_activity and next_activity.sub_activity.base_exp == 0: 
            api_logger.info(f"Adjusting next buffer activity {next_activity.id} start_time from {next_activity.start_time} to {new_end}", extra={"user": user_id})
            next_activity.start_time = new_end 

        # Validate buffer adjustments
        if next_activity:
            if next_activity.start_time >= next_activity.end_time:
                api_logger.error(f"Invalid buffer adjustment: next activity {next_activity.id} would have invalid duration", extra={"user": user_id})
                raise TaskScheduleError(
                    "Invalid buffer adjustment: the start time of the next buffer activity is greater than or equal to its end time. "
                    "This results in a zero or negative duration, which is not allowed."
                )
        if prev_activity:
            if prev_activity.start_time >= prev_activity.end_time:
                api_logger.error(f"Invalid buffer adjustment: previous activity {prev_activity.id} would have invalid duration", extra={"user": user_id})
                raise TaskScheduleError(
                    "Invalid buffer adjustment: the end time of the previous buffer activity is earlier than or equal to its start time. "
                    "This would result in an invalid duration for the buffer period."
                )

        api_logger.info(f"Updating entry {entry_id} times: start_time={new_start}, end_time={new_end}", extra={"user": user_id})
        entry.start_time = new_start
        entry.end_time = new_end
        entry.description = description if (description and description.strip()) else entry.description

        if sub_activity_id:
            api_logger.info(f"Updating entry {entry_id} sub_activity_id to {sub_activity_id}", extra={"user": user_id})
            sub_activity = SubActivity.query.filter_by(id=sub_activity_id).first()
            if not sub_activity or sub_activity.user_id != user_id:
                api_logger.warning(f"Authorization error: Invalid sub-activity ID {sub_activity_id} for user {user_id}", extra={"user": user_id})
                raise AuthorizationError("Invalid sub-activity ID or sub-activity doesn't belong to the user")
            entry.sub_activity_id = sub_activity_id


        
        api_logger.info(f"Updating entry {entry_id} cyclic status to {cyclic}", extra={"user": user_id})
        if not cyclic and entry.cyclic != cyclic:
            api_logger.info("Removing cyclic and week day attributes. ")
            entry.weekday=None
        entry.cyclic = cyclic
        
        
        if weekday is not None:
            if (cyclic or entry.cyclic) is False and weekday is not None:
                api_logger.warning(f"Cannot set weekday for non-cyclic task: entry_id={entry_id}", extra={"user": user_id})
                raise TaskScheduleError("Cannot set weekday for non-cyclic tasks")
            api_logger.info(f"Updating entry {entry_id} weekday to {weekday}", extra={"user": user_id})
            entry.weekday = weekday
        
        if cyclic and not weekday :
            weekday = entry.timetable.date.isocalendar().weekday 
            entry.weekday = weekday
            db.session.commit()

            api_logger.warning("Entry cyclic modified but no weekday was provided. ")
            raise CustomWarnings(
                "Week day was not provided. Defaulting to week day from {}".format(entry.timetable.date),
                extra_data=entry.to_dict())
            
        db.session.commit()
        api_logger.info(f"Successfully updated task entry_id={entry_id}", extra={"user": user_id})
        return entry
    
    @staticmethod
    def get_daily_schedule(user_id: int, date_obj: date ,return_suggested=False) -> List[TimetableEntry]:
        """
        Get all scheduled tasks for a specific date.
        
        Args:
            user_id: The ID of the user
            date_obj: The date to get the schedule for
            return_suggested: Whether to look for cyclic results
            
        Returns:
            List of TimetableEntry objects for the day (may include cyclic events)
        """
        timetable = Timetable.query.filter_by(user_id=user_id, date=date_obj).first()
        
        if not timetable and not return_suggested:
            return []
        
        if timetable:
           entries = TimetableEntry.query.filter_by(timetable_id=timetable.id).all()
           if not return_suggested:
               return entries
        else:
            entries = []

        all_timetables = Timetable.query.filter_by(user_id=user_id).all()
        timetable_ids = [t.id for t in all_timetables]
        scheduled_entries = [i.id for i in entries]

        # Get cyclic entries that match the weekday
        cyclic_entries = TimetableEntry.query.filter(
            TimetableEntry.timetable_id.in_(timetable_ids),
            ~TimetableEntry.id.in_(scheduled_entries),
            TimetableEntry.cyclic == True,
            TimetableEntry.weekday == WeekDay(date_obj.isocalendar().weekday)
        ).all()
        
        # Combine and sort by start time
        all_entries = entries + cyclic_entries
        all_entries.sort(key=lambda x: x.start_time)
        
        return all_entries
    
    @staticmethod
    def get_weekly_schedule(user_id: int, 
                            start_date: date ,
                            days:int=7,
                            return_suggested:bool=False) -> Dict[date, List[TimetableEntry]]:
        """
        Get scheduled tasks for a week starting from the given date.
        
        Args:
            user_id: The ID of the user
            start_date: The starting date of the week
            days: Number of days to look ahead
            return_suggested : includes cyclic days
            
        Returns:
            Dictionary mapping dates to lists of TimetableEntry objects
        """
        result = {}
        
        # Get schedules for 7 days
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            result[current_date] = TimetableManager.get_daily_schedule(
                user_id, current_date,return_suggested=return_suggested)
            
        return result
    
    @staticmethod
    def get_tasks_by_activity(user_id: int, 
                              activity_id: int, 
                              start_date: date = None,
                                end_date: date = None) -> List[TimetableEntry]:
        """
        Get all scheduled tasks for a specific activity within a date range.
        
        Args:
            user_id: The ID of the user
            activity_id: The ID of the activity
            start_date: The start date of the range (optional)
            end_date: The end date of the range (optional)
            
        Returns:
            List of TimetableEntry objects for the activity
        """
        # Get all sub-activities for this activity
        sub_activities = SubActivity.query.filter_by(activity_id=activity_id).all()
        if not sub_activities:
            return []
            
        sub_activity_ids = [sa.id for sa in sub_activities]
        
        # Build the query
        query = TimetableEntry.query.join(Timetable).filter(
            Timetable.user_id == user_id,
            TimetableEntry.sub_activity_id.in_(sub_activity_ids)
        )
        
        # Add date filters if provided
        if start_date:
            query = query.filter(Timetable.date >= start_date)
        if end_date:
            query = query.filter(Timetable.date <= end_date)
            
        # Execute and return
        return query.all()
    
    @staticmethod
    def get_task_stats(user_id: int,today:date, days: int = 30) -> Dict:
        """
        Get statistics about scheduled tasks for a user.
        
        Args:
            user_id: The ID of the user
            days: Number of past days to include in stats,
            todat: starting date
            
        Returns:
            Dictionary with statistics
        
        """
        start_date = today - timedelta(days=days)
        
        # Get all timetables in the date range
        timetables = Timetable.query.filter(
            Timetable.user_id == user_id,
            Timetable.date >= start_date,
            Timetable.date <= today
        ).all()
        
        if not timetables:
            return {
                "total_tasks": 0,
                "total_hours": 0,
                "activities": {}
            }
            
        timetable_ids = [t.id for t in timetables]
        
        # Get all entries for these timetables
        entries = TimetableEntry.query.filter(
            TimetableEntry.timetable_id.in_(timetable_ids)
        ).all()
        
        # Calculate statistics
        total_tasks = len(entries)
        total_minutes = sum(
            (entry.end_time.hour * 60 + entry.end_time.minute) - 
            (entry.start_time.hour * 60 + entry.start_time.minute)
            for entry in entries
        )
        total_hours = total_minutes / 60
        
        # Group by activity
        activity_stats = {}
        for entry in entries:
            activity_name = entry.sub_activity.activity.name
            if activity_name not in activity_stats:
                activity_stats[activity_name] = {
                    "count": 0,
                    "hours": 0
                }
            
            activity_stats[activity_name]["count"] += 1
            minutes = (entry.end_time.hour * 60 + entry.end_time.minute) - (entry.start_time.hour * 60 + entry.start_time.minute)
            activity_stats[activity_name]["hours"] += minutes / 60
            
        return {
            "total_tasks": total_tasks,
            "total_hours": total_hours,
            "activities": activity_stats
        }

    @staticmethod
    def delete_user_entry(user_id: int, entry_id: int) -> bool:
        """
        Delete a timetable entry if it belongs to the specified user.
        
        Performs an ownership check before deletion to ensure users can only delete
        their own entries. Uses database transaction for atomic operation.

        Args:
            user_id: ID of the user attempting the deletion
            entry_id: ID of the timetable entry to delete

        Returns:
            bool: True if deletion was successful, False if entry wasn't found

        """

        entry = (
            db.session.query(TimetableEntry)
            .join(Timetable)
            .filter(
                TimetableEntry.id == entry_id,
                Timetable.user_id == user_id
            )
            .first()
        )
        if entry.timetable.finalized:
            raise TaskScheduleError("Cannot delete  tasks in a  finalized day. ")
        
        if not entry:
            api_logger.info(
                f"Entry not found for deletion",
                extra={'user_id': user_id, 'entry_id': entry_id}
            )
            return False 
        
        # Perform deletion
        db.session.delete(entry)
        db.session.commit()
        
        api_logger.info(
            f"Successfully deleted timetable entry",
            extra={
                'user_id': user_id,
                'entry_id': entry_id,
            }
        )
        return True

