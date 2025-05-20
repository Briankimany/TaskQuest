"""
Real-Life RPG System web application.

This package implements a gamified productivity system that transforms daily
activities into RPG-style quests with experience points and leveling.
"""

from flask import Flask ,render_template,request
from .models import db
from .routes import api_bp, auth_bp, views_bp
from .utils.custom_errors import make_error_response
import os


from flask_migrate import Migrate

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    def handle_generic_error(error: Exception):
        return make_error_response(error, "Unexpected server error")

    app.register_error_handler(Exception,handle_generic_error)
    @app.errorhandler(404)
    def page_not_found(e):
        if  "api" in request.path:
            return make_error_response(e,msg='url not found. ',code=404)
        return render_template('404.html'), 404
    
    migrate = Migrate(app, db)

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'rpg_system.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)


    return app