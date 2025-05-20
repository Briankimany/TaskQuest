"""
Run script for the Real-Life RPG System web application.

This script creates and runs the Flask application with the development server.
"""

from app import app 

if __name__ == '__main__':
    app.run(debug=True)