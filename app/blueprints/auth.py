"""
Authentication Blueprint
Handles user login, registration, and logout
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import limiter
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        # Use User model for validation and creation
        success, result = User.create(name, email, password, phone)

        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'error')

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Use User model for authentication
        user = User.authenticate(email, password)

        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['is_admin'] = user.get('is_admin', False)
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('main.menu'))

        flash('Invalid email or password', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}!', 'info')
    return redirect(url_for('main.index'))
