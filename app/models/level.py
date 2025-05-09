"""
Level model for the Real-Life RPG System.

This module defines the Level class which stores experience thresholds
and rewards for different levels.
"""

from .base import db

class Level(db.Model):
    """Level model for defining experience thresholds and rewards."""
    id = db.Column(db.Integer, primary_key=True)
    level_number = db.Column(db.Integer, unique=True, nullable=False)
    required_exp = db.Column(db.Integer, nullable=False)
    reward_description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Level {self.level_number}>'