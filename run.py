"""
Run script for the Real-Life RPG System web application.

This script creates and runs the Flask application with the development server.
"""

from app import app 
from app.config import DEBUG_MODE

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, use_reloader=DEBUG_MODE)