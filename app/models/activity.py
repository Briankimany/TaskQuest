"""
Activity and SubActivity models for the Real-Life RPG System.

This module defines the Activity and SubActivity classes which represent
the tasks that users can complete to earn experience points.
"""

from datetime import datetime ,timedelta
from sqlalchemy.ext.mutable import MutableDict
from .base import BASE_EXP ,db 
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select ,text 

class Activity(db.Model):
    """Activity model representing a category of sub-activities."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy=True, cascade="all, delete-orphan"))
    
    def to_dict(self,include_children=False):
        data= {
            "id":self.id,
            'name':self.name,
        }
        if include_children:
            data.update(
                {"sub_activites":[i.to_dict() for i in self.sub_activities]}
            )

        return data 
    
    def __repr__(self):
        return f'<Activity {self.name}>'

class SubActivity(db.Model):
    """SubActivity model representing specific tasks within an activity category."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    difficulty_multiplier = db.Column(db.Float, default=1.0)
    base_exp = db.Column(db.Integer, default=BASE_EXP)
    attribute_weights = db.Column(MutableDict.as_mutable(db.JSON), default=lambda: {
        "INT": 0.2,
        "STA": 0.2,
        "FCS": 0.2,
        "CHA": 0.2,
        "DSC": 0.2
    })

    active = db.Column(db.Boolean, server_default=text('TRUE'), nullable=False)
    scheduled_time = db.Column('scheduled_time', db.Integer, nullable=False)
    activity = db.relationship('Activity', backref=db.backref('sub_activities', lazy=True, cascade="all, delete-orphan"))
    
    def calculate_potential_exp(self):
        exp = self.base_exp * self.difficulty_multiplier * (self.scheduled_time/60)
        return exp 
    
    @hybrid_property
    def user_id(self):
        return self.activity.user_id
    
    @user_id.expression
    def user_id(cls):
        return (
            select(Activity.user_id)
            .where(Activity.id == cls.activity_id)
            .correlate(cls)
            .scalar_subquery()
        )
    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name,
            "activity_id":self.activity_id,
            "base_exp":self.base_exp,
            "difficulty_multiplier":self.difficulty_multiplier,
            "attribute_weights":self.attribute_weights,
            "scheduled_time":self.scheduled_time
        }

    def __repr__(self):
        return f'<SubActivity {self.name}>'
    def __str__(self):
        return self.__repr__()