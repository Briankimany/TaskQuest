"""
Routes package for the Real-Life RPG System.

This package contains all the route blueprints used in the application,
including API endpoints, authentication routes, and template rendering.
"""

from .api import api_bp
from .auth import auth_bp
from .views import views_bp