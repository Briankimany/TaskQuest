"""
Real-Life RPG System web application.

This package implements a gamified productivity system that transforms daily
activities into RPG-style quests with experience points and leveling.
"""

from flask import Flask
from .models import db
from .routes import api_bp, auth_bp, views_bp
import os

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    # Default configuration
    print('sqlite:///' + os.path.join(app.instance_path, 'rpg_system.db'))
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'rpg_system.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    
    return app