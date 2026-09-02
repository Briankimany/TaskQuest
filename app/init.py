"""
Real-Life RPG System web application.

This package implements a gamified productivity system that transforms daily
activities into RPG-style quests with experience points and leveling.
"""

from flask import Flask ,render_template,request
from .models import db
from .routes import api_bp, auth_bp, views_bp ,assistant
from .utils.exceptions import make_error_response
from .utils.logger import ui_logger
import os
from .config import SUPPORT_EMAIL, APP_NAME, APP_TAGLINE

from flask_migrate import Migrate

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    app.jinja_env.globals['APP_NAME'] = APP_NAME
    app.jinja_env.globals['APP_TAGLINE'] = APP_TAGLINE

    # Only swallow exceptions into a 500 page in production. In dev mode
    # (DEBUG=True / app.debug) we let exceptions propagate so the Werkzeug
    # debugger prints the full traceback on screen for easier debugging.
    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception):
        ui_logger.error(f"{error!r} | URL: {request.url} | Method: {request.method} | DEBUG={app.debug}")
        if app.debug:
            raise error
        if 'api' not in request.path:
            return render_template('500.html',exception=error), 500
        return make_error_response(error, "Unexpected server error")

    @app.errorhandler(404)
    def page_not_found(e):
        if  "api" in request.path:
            return make_error_response(e,msg='url not found. ',code=404)
        return render_template('404.html',support_mail = SUPPORT_EMAIL), 404
    
    migrate = Migrate(app, db)

    # Read debug flag fresh at startup so toggling FLASK_DEBUG in .env works
    # even if config.py was imported earlier in the process.
    debug_mode = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'rpg_system.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=debug_mode,
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
    app.register_blueprint(assistant)

    return app