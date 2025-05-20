from flask import jsonify
from app.models import db
from app.models import Activity, SubActivity
from app.utils.custom_errors import (
    InvalidRequestData,
    RecordNotFoundError,
    AuthorizationError,
    RecordDuplicationError
)

from app.utils.logger import api_logger
from app.config import ATTRIBUTES_LIST 

class ActivityManager:
    """Handles all CRUD operations for Activities and SubActivities"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    # Activity Operations

    def  get_activity(self, name,dict_format = True):
        activity=  Activity.query.filter_by(name=name, user_id=self.user_id).first()
        if not dict_format:
            return activity
        
        return {
            'id': activity.id,
            'name': activity.name,
            'created_at': activity.created_at.isoformat()
        }
    
    def get_all_activities(self) -> list:
        """Retrieve all activities with their sub-activities for the user"""
        activities = Activity.query.filter_by(user_id=self.user_id).all()
        return [self._serialize_activity(act) for act in activities]
    
    def create_activity(self, name: str) -> dict:
        """Create a new activity"""

        if self.get_activity(name,False) :
            raise RecordDuplicationError(f"Activity already exists: {name}", 201)
            
        new_activity = Activity(name=name, user_id=self.user_id)
        db.session.add(new_activity)
        db.session.commit()
        
        return {
            'id': new_activity.id,
            'name': new_activity.name,
            'created_at': new_activity.created_at.isoformat()
        }
    
    def update_activity(self, activity_id: int, new_name: str) -> dict:
        """Update an existing activity"""
        activity = self._get_user_activity(activity_id)
        activity.name = new_name
        db.session.commit()
        
        return {
            'id': activity.id,
            'name': activity.name,
            'created_at': activity.created_at.isoformat()
        }
    
    def delete_activity(self, activity_id: int) -> None:
        """Delete an activity"""
        activity = self._get_user_activity(activity_id)
        db.session.delete(activity)
        db.session.commit()
    
    # SubActivity Operations
    def create_subactivity(self, activity_id: int, subactivity_data: dict ,skip_validation=False) -> dict:
        """Create a new sub-activity"""
        self._validate_activity_ownership(activity_id)
        if  skip_validation:
            self._validate_subactivity_data(subactivity_data)
            
        if SubActivity.query.filter_by(name=subactivity_data['name'], user_id=self.user_id).first():
            raise RecordDuplicationError(f"Sub-activity exists: {subactivity_data['name']}")
        
        new_sub = SubActivity(
            name=subactivity_data['name'],
            activity_id=activity_id,
            difficulty_multiplier=subactivity_data['difficulty_multiplier'],
            base_exp=subactivity_data['base_exp'],
            scheduled_time=subactivity_data['scheduled_time'],
            attribute_weights=subactivity_data['attribute_weights']
        )
        db.session.add(new_sub)
        db.session.commit()
        
        return self._serialize_subactivity(new_sub)
    
    def update_subactivity(self, subactivity_id: int, update_data: dict) -> dict:
        """Update existing sub-activity"""
        sub = self._get_user_subactivity(subactivity_id)
        
        for attr, value in update_data.items():
            if hasattr(sub, attr):
                validator = self._get_validator(attr)
                setattr(sub, attr, validator(value) if validator else value)
        
        db.session.commit()
        return self._serialize_subactivity(sub)
    
    def deactivate_subactivity(self, subactivity_id: int) -> None:
        """Deactivate (soft delete) a sub-activity"""
        sub = self._get_user_subactivity(subactivity_id)
        sub.active = False
        db.session.commit()
    
    # Helper Methods
    def _get_user_activity(self, activity_id: int) -> Activity:
        """Verify and return activity belonging to user"""
        activity = Activity.query.filter_by(id=activity_id, user_id=self.user_id).first()
        if not activity:
            raise RecordNotFoundError(f'No activity with id {activity_id}', 404)
        return activity
    
    def _get_user_subactivity(self, subactivity_id: int) -> SubActivity:
        """Verify and return sub-activity belonging to user"""
        sub = SubActivity.query.filter_by(id=subactivity_id, user_id=self.user_id).first()
        if not sub:
            raise AuthorizationError("Can only edit owned sub-activities")
        return sub
    
    def _validate_activity_ownership(self, activity_id: int) -> None:
        """Verify activity belongs to user"""
        if not Activity.query.filter_by(id=activity_id, user_id=self.user_id).first():
            raise AuthorizationError("Can only modify owned activities", 400)
    
    def _validate_subactivity_data(self, data: dict) -> None:
        """Validate required sub-activity fields"""
        required = ['name', 'difficulty_multiplier', 'scheduled_time', 'base_exp', 'attribute_weights']
        missing = [field for field in required if field not in data or not data[field]]
        
        if missing:
            raise InvalidRequestData(f"Missing required fields: {missing}")
        
        self._validate_attributes(data['attribute_weights'])
    

    def _validate_attributes(self,data):
        sent_data = [data.get(key ,0 ) for key in ATTRIBUTES_LIST]
       
        if round(sum(sent_data),ndigits=3) !=1:
            raise InvalidRequestData(f"All attributes weights must add up to 1 {data}")
        return data
    
    
    def _get_validator(self, attribute: str):
        """Get validator for sub-activity attributes"""
        validators = {
            'difficulty_multiplier': lambda x: float(x),
            'base_exp': lambda x: int(x),
            'scheduled_time': lambda x: int(x)
        }
        return validators.get(attribute)
    
    def _serialize_activity(self, activity: Activity) -> dict:
        """Serialize activity with sub-activities"""
        return {
            'id': activity.id,
            'name': activity.name,
            'created_at': activity.created_at.isoformat(),
            'sub_activities': [
                self._serialize_subactivity(sub) 
                for sub in activity.sub_activities 
                if sub.active
            ]
        }
    
    def _serialize_subactivity(self, sub: SubActivity) -> dict:
        """Serialize sub-activity data"""
        return {
            'id': sub.id,
            'name': sub.name,
            'activity_id': sub.activity_id,
            'difficulty_multiplier': sub.difficulty_multiplier,
            'scheduled_time': sub.scheduled_time,
            'base_exp': sub.base_exp,
            'attribute_weights': sub.attribute_weights
        }