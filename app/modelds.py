"""
Real-Life RPG System - Database Models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model representing player in the RPG system."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    INT = db.Column(db.Integer, default=0)  # Intelligence
    STA = db.Column(db.Integer, default=0)  # Stamina
    FCS = db.Column(db.Integer, default=0)  # Focus
    CHA = db.Column(db.Integer, default=0)  # Charisma
    DSC = db.Column(db.Integer, default=0)  # Discipline
    level = db.Column(db.Integer, default=1)
    total_exp = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='user', lazy=True)
    timetables = db.relationship('Timetable', backref='user', lazy=True)
    completion_logs = db.relationship('CompletionLog', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Activity(db.Model):
    """Model for activity categories."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sub_activities = db.relationship('SubActivity', backref='activity', lazy=True)
    
    def __repr__(self):
        return f'<Activity {self.name}>'


class SubActivity(db.Model):
    """Model for specific sub-activities within activity categories."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    difficulty_multiplier = db.Column(db.Float, default=1.0)
    scheduled_time = db.Column(db.Integer, nullable=False)  # In minutes
    base_exp = db.Column(db.Integer, default=100)
    
    # Attribute weights (as JSON string)
    _attribute_weights = db.Column('attribute_weights', db.String(255), default='{"INT": 0, "STA": 0, "FCS": 0, "CHA": 0, "DSC": 0}')
    
    # Relationships
    completion_logs = db.relationship('CompletionLog', backref='sub_activity', lazy=True)
    
    @property
    def attribute_weights(self):
        return json.loads(self._attribute_weights)
    
    @attribute_weights.setter
    def attribute_weights(self, value):
        self._attribute_weights = json.dumps(value)
    
    def __repr__(self):
        return f'<SubActivity {self.name}>'


class Timetable(db.Model):
    """Model for user's timetable."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    _json_blob = db.Column('json_blob', db.Text, nullable=False)
    
    @property
    def json_blob(self):
        return json.loads(self._json_blob)
    
    @json_blob.setter
    def json_blob(self, value):
        self._json_blob = json.dumps(value)
    
    def __repr__(self):
        return f'<Timetable {self.date}>'


class CompletionLog(db.Model):
    """Model for tracking activity completion."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activity.id'), nullable=False)
    completed_on = db.Column(db.DateTime, default=datetime.utcnow)
    actual_time_taken = db.Column(db.Integer)  # In minutes
    status = db.Column(db.String(20), nullable=False)  # 'completed', 'skipped', 'late'
    reason = db.Column(db.Text)  # For skipped activities
    
    def __repr__(self):
        return f'<CompletionLog {self.status} {self.completed_on}>'


class Level(db.Model):
    """Model for defining level requirements and rewards."""
    id = db.Column(db.Integer, primary_key=True)
    level_number = db.Column(db.Integer, nullable=False, unique=True)
    required_exp = db.Column(db.Integer, nullable=False)
    reward_description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Level {self.level_number}>'