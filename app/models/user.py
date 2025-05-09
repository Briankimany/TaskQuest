"""
User model for the Real-Life RPG System.

This module defines the User class representing players in the system,
including their attributes, level, and experience points.
"""

from datetime import datetime
from .base import db

class User(db.Model):
    """User model representing a player in the RPG system."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Core attributes
    INT = db.Column(db.Integer, default=0)  # Intelligence
    STA = db.Column(db.Integer, default=0)  # Stamina
    FCS = db.Column(db.Integer, default=0)  # Focus
    CHA = db.Column(db.Integer, default=0)  # Charisma
    DSC = db.Column(db.Integer, default=0)  # Discipline
    
    # Level and experience
    level = db.Column(db.Integer, default=1)
    total_exp = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'