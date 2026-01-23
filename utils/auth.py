from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        if not session.get('is_admin', False):
            flash('Admin access required', 'danger')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function
