"""
Authentication blueprint for the Real-Life RPG System
Handles user registration, login, and logout
"""
from flask import Blueprint, request, render_template, redirect, url_for, flash, session ,jsonify
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

def is_api_request():
    """
    Check if the request is for an API endpoint.
    """
    return request.path.startswith('/api')

@auth_bp.route('/api/login', methods=['POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        if is_api_request():
          
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
          
            username = request.form.get('username')
            password = request.form.get('password')

        assert password is not None 

        user = User.query.filter_by(username=username).first()
        if not user:
            if is_api_request():
                return jsonify({'error': 'Invalid username'}), 400
            flash('Invalid username.', 'danger')
            return render_template('auth/login.html')
        
        if not user.check_password(password):
            if is_api_request():
                return jsonify({'error': 'Invalid password.'}), 400
            flash('Invalid password.', 'danger')
            return render_template('auth/login.html')

        session['user_id'] = user.id
        if is_api_request():
            return jsonify({'message': f'Welcome back, {user.username}!'}), 200
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('views.dashboard'))
    
    if is_api_request():
        return jsonify({'error': 'Method not allowed.'}), 405
    return render_template('auth/login.html')

@auth_bp.route('/api/register', methods=['POST'])
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        if is_api_request():
           
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        else:
          
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
        
    
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if is_api_request():
                return jsonify({'error': 'Username already exists.'}), 400
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html')
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            if is_api_request():
                return jsonify({'error': 'Email already registered.'}), 400
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        if is_api_request():
            return jsonify({'message': 'Registration successful! Please log in.'}), 201
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    if is_api_request():
        return jsonify({'error': 'Method not allowed.'}), 405
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
