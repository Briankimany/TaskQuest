"""
Authentication blueprint for the Real-Life RPG System
Handles user registration, login, and logout
"""
from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
       
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Invalid username.', 'danger')
            return render_template('auth/login.html')
        
        # In a real app, we would check password here
        # For this demo, just log the user in
        session['user_id'] = user.id
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('views.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html')
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
