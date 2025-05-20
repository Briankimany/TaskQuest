from datetime import datetime, time, timedelta
from typing import Optional
from app.utils.logger import api_logger
from app.models import SubActivity ,User ,db

class ExpManager:
    """
    Handles all EXP-related calculations with strict input validation and error handling.
    Implements the EXP calculation rules from the project documentation.
    """
    
    STANDARD_UNIT_TIME = timedelta(hours=1)
    GRACE_PERIOD = timedelta(minutes=15)
    
    def __init__(self):
        self.logger = api_logger
        
    def calculate_exp_impact(
        self,
        sub_activity: SubActivity,
        status: str,
        actual_time_taken: Optional[int] = None,
        scheduled_time: Optional[int] = None,
        end_time: Optional[time] = None,
        start_time: Optional[time] = None,
        completion_time: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> int:
        """
        Calculate EXP impact with comprehensive validation.
        
        Args:
            sub_activity: The subactivity being completed (required)
            status: Completion status ('completed', 'partial', 'skipped') (required)
            actual_time_taken: Actual time spent in seconds (required for 'partial')
            scheduled_time: Scheduled duration in seconds (required for 'completed'/'partial')
            end_time: Scheduled end time (required for 'completed'/'partial')
            start_time: Scheduled start time (required for 'completed'/'partial')
            completion_time: Actual completion timestamp (required for 'completed'/'partial')
            reason: Explanation for status (required for 'partial'/'skipped')
            
        Returns:
            Calculated EXP impact (positive or negative)
            
        Raises:
            ValueError: For invalid inputs or logical inconsistencies
        """
        self.logger.debug(
            "Starting EXP calculation for sub_activity_id=%s with status=%s",
            sub_activity.id if sub_activity else None,
            status
        )
        
        try:
            # Validate core required inputs
            if not sub_activity:
                error_msg = "SubActivity is required"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
            if status not in ('completed', 'partial', 'skipped'):
                error_msg = f"Invalid status: {status}. Must be 'completed', 'partial', or 'skipped'"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Status-specific validation
            if status == 'completed':
                self._validate_completed_activity(scheduled_time, end_time, start_time, completion_time)
            elif status == 'partial':
                self._validate_partial_activity(actual_time_taken, scheduled_time, end_time, start_time, completion_time, reason)
            elif status == 'skipped':
                self._validate_skipped_activity(reason)
            
            # Log input parameters
            self.logger.debug(
                "Validated inputs - base_exp=%s, difficulty_multiplier=%s, scheduled_time=%s",
                sub_activity.base_exp,
                sub_activity.difficulty_multiplier,
                scheduled_time
            )
            
            if status == 'skipped':
                penalty = self._calculate_skipped_penalty(reason, sub_activity.base_exp, sub_activity.difficulty_multiplier)
                self.logger.debug("Calculated skipped penalty: %s", penalty)
                return penalty
                
            # Calculate for completed/partial status
            scheduled_time_hours = scheduled_time /3600   * (1/(self.STANDARD_UNIT_TIME.total_seconds()/3600))
            exp_per_task = sub_activity.base_exp * scheduled_time_hours * sub_activity.difficulty_multiplier
            self.logger.debug("Base EXP calculation: %s * %s * %s = %s", 
                            sub_activity.base_exp, scheduled_time_hours, sub_activity.difficulty_multiplier, exp_per_task)
            
            if status == 'completed':
                if self._completed_within_grace_period(end_time, completion_time):
                    self.logger.debug("Task completed within grace period, awarding full EXP: %s", exp_per_task)

                    return int(exp_per_task)
                
                exp_lost = self._calculate_late_penalty(start_time, completion_time, scheduled_time, exp_per_task)
                exp_penalties = self._calculate_reason_penalty(reason, exp_per_task) if reason else 0
                final_exp = int(exp_per_task - exp_lost - exp_penalties)
                self.logger.debug(
                    "Completed task with penalties - exp_per_task=%s, exp_lost=%s, exp_penalties=%s, final_exp=%s",
                    exp_per_task, exp_lost, exp_penalties, final_exp
                )
                return final_exp if final_exp > 0 else 0
            
            elif status == 'partial':
                exp_lost = self._calculate_late_penalty(start_time, completion_time, scheduled_time, exp_per_task)
                exp_penalties = self._calculate_reason_penalty(reason, exp_per_task)
                completion_ratio = actual_time_taken / scheduled_time
                final_exp = int((exp_per_task) - exp_lost - exp_penalties)
                self.logger.debug(
                    "Partial completion - completion_ratio=%s, exp_lost=%s, exp_penalties=%s, final_exp=%s",
                    1-completion_ratio, exp_lost, exp_penalties, final_exp
                )
                return final_exp if final_exp > 0 else 0
                
        except ValueError as e:
            self.logger.error(
                "Failed to calculate EXP impact for sub_activity_id=%s: %s",
                sub_activity.id if sub_activity else None,
                str(e),
                exc_info=True
            )
            raise
    
    def _validate_completed_activity(self, scheduled_time, end_time, start_time, completion_time):
        """Validate inputs for completed activities"""
        if None in (scheduled_time, end_time, start_time, completion_time):
            error_msg = "All time parameters required for 'completed' status"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if scheduled_time <= 0:
            error_msg = "Scheduled time must be positive"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if end_time <= start_time:
            error_msg = f"End time {end_time} must be after start time {start_time}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.debug("Completed activity validation passed")
    
    def _validate_partial_activity(self, actual_time_taken, scheduled_time, end_time, start_time, completion_time, reason):
        """Validate inputs for partially completed activities"""
        if None in (actual_time_taken, scheduled_time, end_time, start_time, completion_time, reason):
  
            error_msg = "All parameters required for 'partial' status"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if actual_time_taken <= 0:
            error_msg = f"Actual time taken {actual_time_taken} must be positive"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if actual_time_taken > scheduled_time:
            error_msg = f"Actual time {actual_time_taken} cannot exceed scheduled time {scheduled_time} for partial completion"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not reason.strip():
            error_msg = "Reason required for partial completion"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.debug("Partial activity validation passed")
    
    def _validate_skipped_activity(self, reason):
        """Validate inputs for skipped activities"""
        if not reason or not reason.strip():
            error_msg = "Reason required for skipped activity"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.debug("Skipped activity validation passed with reason: %s", reason[:50])  # Log first 50 chars
    
    def _completed_within_grace_period(self, end_time: time, completion_time: datetime) -> bool:
        """Check if task was completed within grace period"""
        grace_cutoff = datetime.combine(completion_time.date(), end_time) + self.GRACE_PERIOD
        grace_limmit =  datetime.combine(completion_time.date(), end_time) - self.GRACE_PERIOD
        is_within_grace = completion_time.time() <= grace_cutoff.time() and completion_time.time() >= grace_limmit.time()
        
        self.logger.debug(
            "Grace period check - end_time=%s, completion_time=%s, grace_cutoff=%s, is_within_grace=%s",
            end_time, completion_time.time(), grace_cutoff.time(), is_within_grace
        )
        
        return is_within_grace
    
    def _calculate_late_penalty(self, start_time: time, completion_time: datetime, 
                              scheduled_time: int, exp_per_task: float) -> float:
        """Calculate penalty for late completion"""
        
        time_diff = abs((completion_time - datetime.combine(completion_time.date(), start_time)).total_seconds() -scheduled_time)
        penalty = max(0, (time_diff / scheduled_time) * exp_per_task)
        
        self.logger.debug(
            "Late penalty calculation - start_time=%s,completion_time=%s, scheduled_time=%s, time_diff=%s, penalty=%s",
            start_time, completion_time.time(), scheduled_time,time_diff, penalty
        )
        
        return penalty
    
    def _calculate_reason_penalty(self, reason: str, exp_per_task: float) -> float:
        """
        Calculate penalty based on reason (placeholder implementation).
        In production, this would integrate with your reason analysis system.
        """
        penalty = 0.0
        
        if "emergency" in reason.lower():
            penalty = exp_per_task * 0.1
            self.logger.debug("Emergency reason detected, applying 10%% penalty: %s", penalty)
        elif "lazy" in reason.lower():
            penalty = exp_per_task * 0.5
            self.logger.warning("Lazy reason detected, applying 50%% penalty: %s", penalty)
        else:
            penalty = exp_per_task * 0.3
            self.logger.debug("Default reason penalty (30%%): %s", penalty)
        
        return penalty
    
    def _calculate_skipped_penalty(self, reason: str, base_exp: int, difficulty_multiplier: float) -> int:
        """
        Calculate penalty for skipped tasks.
        Skipped tasks always result in negative EXP based on base value and reason.
        """
        penalty_multiplier = self._get_skip_penalty_multiplier(reason)
        penalty = -int(base_exp * difficulty_multiplier * penalty_multiplier)
        
        self.logger.warning(
            "Skipped task penalty - reason='%s', base_exp=%s, difficulty=%s, multiplier=%s, penalty=%s",
            reason[:100],  # Truncate long reasons
            base_exp,
            difficulty_multiplier,
            penalty_multiplier,
            penalty
        )
        
        return penalty
    
    def _get_skip_penalty_multiplier(self, reason: str) -> float:
        """
        Determine penalty severity based on skip reason.
        This should be enhanced with your actual reason analysis logic.
        """
        reason_lower = reason.lower()
        
        if "emergency" in reason_lower:
            self.logger.debug("Emergency skip reason, using 0.5 multiplier")
            return 0.5
        elif "forgot" in reason_lower:
            self.logger.warning("Forgot skip reason, using 1.0 multiplier")
            return 1.0
        
        self.logger.debug("Default skip penalty multiplier (0.8)")
        return 0.8
    
    def distribute_user_exp(self,user_id: int, gained_exp: int, sub_activity_id: int) -> dict:
        """
        Update user's EXP and check for level up.
        
        Args:
            user_id: ID of the user
            gained_exp: EXP gained or lost
            sub_activity_id: ID of the subactivity
            
        Returns:
            Dictionary with updated user attributes and level up details
        """
        user = User.query.get(user_id)
        subactivity = SubActivity.query.filter_by(id=sub_activity_id).first()
        if not subactivity:
            raise ValueError('Sub activity not found or belongs to another user.')

        if gained_exp:
            weights = subactivity.attribute_weights
            user.INT += int(gained_exp * weights.get('INT', 0))
            user.STA += int(gained_exp * weights.get('STA', 0))
            user.FCS += int(gained_exp * weights.get('FCS', 0))
            user.CHA += int(gained_exp * weights.get('CHA', 0))
            user.DSC += int(gained_exp * weights.get('DSC', 0))

        db.session.commit()

        response = {
            'attributes': {
                'INT': user.INT,
                'STA': user.STA,
                'FCS': user.FCS,
                'CHA': user.CHA,
                'DSC': user.DSC
            }
        }

        return response

    def reset_user_exp(self,user_id:int,**kwargs):
   
        user = User.query.get(user_id)
        user.total_exp = kwargs.get('total_exp',0)
        user.INT = kwargs.get('INT', 0)
        user.STA = kwargs.get('STA', 0)
        user.FCS = kwargs.get('FCS', 0)
        user.CHA = kwargs.get('CHA', 0)
        user.DSC = kwargs.get('DSC', 0)
        
        db.session.commit()