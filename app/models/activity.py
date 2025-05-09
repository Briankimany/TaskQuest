"""
Activity and SubActivity models for the Real-Life RPG System.

This module defines the Activity and SubActivity classes which represent
the tasks that users can complete to earn experience points.
"""

from datetime import datetime
from sqlalchemy.ext.mutable import MutableDict
from .base import BASE_EXP ,db 

class Activity(db.Model):
    """Activity model representing a category of sub-activities."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy=True, cascade="all, delete-orphan"))
    
    def __repr__(self):
        return f'<Activity {self.name}>'

class SubActivity(db.Model):
    """SubActivity model representing specific tasks within an activity category."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    difficulty_multiplier = db.Column(db.Float, default=1.0)
    scheduled_time = db.Column(db.Integer, nullable=False)  # In minutes
    base_exp = db.Column(db.Integer, default=BASE_EXP)
    attribute_weights = db.Column(MutableDict.as_mutable(db.JSON), default=lambda: {
        "INT": 0.2,
        "STA": 0.2,
        "FCS": 0.2,
        "CHA": 0.2,
        "DSC": 0.2
    })
    
    # Relationships
    activity = db.relationship('Activity', backref=db.backref('sub_activities', lazy=True, cascade="all, delete-orphan"))
    
    def __repr__(self):
        return f'<SubActivity {self.name}>'