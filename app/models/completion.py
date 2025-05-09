"""
CompletionLog model for the Real-Life RPG System.

This module defines the CompletionLog class which tracks completed sub-activities,
including their status and time taken.
"""

from datetime import datetime
from .base import db

class CompletionLog(db.Model):
    """CompletionLog model for tracking completed sub-activities."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activity.id'), nullable=False)
    completed_on = db.Column(db.DateTime, default=datetime.utcnow)
    actual_time_taken = db.Column(db.Integer)  # In minutes
    status = db.Column(db.String(20), default='completed')  # completed, skipped, partial
    reason = db.Column(db.Text, nullable=True)  # For skipped or partial completion
    exp_impact = db.Column(db.Integer, nullable=True)  # To store the EXP gained/lost
    
    # Relationships
    user = db.relationship('User', backref=db.backref('completion_logs', lazy=True))
    sub_activity = db.relationship('SubActivity', backref=db.backref('completion_logs', lazy=True))
    
    def __repr__(self):
        return f'<CompletionLog {self.id}>'