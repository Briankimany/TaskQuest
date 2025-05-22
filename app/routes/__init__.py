"""
Routes package for the Real-Life RPG System.

This package contains all the route blueprints used in the application,
including API endpoints, authentication routes, and template rendering.
"""

from .auth import auth_bp
from .views import views_bp
from .completion_api import api_bp
from .assistant import assistant