"""
CompletionLog model for the Real-Life RPG System.

This module defines the CompletionLog class which tracks completed sub-activities,
including their status and time taken.
"""

from datetime import datetime
from .base import db

class CompletionLog(db.Model):
    """CompletionLog model for tracking completed scheduled sub-activities."""
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activity.id'), nullable=False)
    timetable_entry_id = db.Column(db.Integer, db.ForeignKey('timetable_entry.id'), nullable=True)

    completed_on = db.Column(db.Date)
    actual_time_taken = db.Column(db.Integer)  # In minutes

    status = db.Column(db.String(20), default='completed')  # completed, skipped, partial
    reason = db.Column(db.Text, nullable=True)  # Reason for skipped or partial completion

    exp_impact = db.Column(db.Integer, nullable=True)  # EXP earned or lost
    comment = db.Column(db.String)

    # Relationships
    user = db.relationship('User', backref=db.backref('completion_logs', lazy=True))
    sub_activity = db.relationship('SubActivity', backref=db.backref('completion_logs', lazy=True))
    timetable_entry  = db.relationship('TimetableEntry', backref=db.backref('completion_log', uselist=False))

    def __repr__(self):
        return f'<CompletionLog {self.id} | {self.status} | {self.exp_impact}>'
