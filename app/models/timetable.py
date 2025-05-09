"""
Timetable model for the Real-Life RPG System.

This module defines the Timetable class which stores scheduled activities
for specific dates using a JSON blob.
"""

from sqlalchemy.ext.mutable import MutableDict
from .base import db

class Timetable(db.Model):
    """Timetable model for scheduling activities."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    json_blob = db.Column(MutableDict.as_mutable(db.JSON), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('timetables', lazy=True))
    
    def __repr__(self):
        return f'<Timetable {self.date}>'