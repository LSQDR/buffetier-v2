"""
Authentication and authorization decorators with audit logging.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging
from datetime import datetime


# Setup logging for security events
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)


def log_security_event(event_type, user_id=None, message="", ip_address=None):
    """Log security-related events for audit trail."""
    timestamp = datetime.now().isoformat()
    log_message = f"[{timestamp}] {event_type} | User: {user_id or 'Anonymous'} | IP: {ip_address or 'Unknown'} | {message}"
    security_logger.info(log_message)
    print(f"🔒 SECURITY: {log_message}")


def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            log_security_event(
                'UNAUTHORIZED_ACCESS',
                message=f"Attempted to access {request.path} without login",
                ip_address=request.remote_addr
            )
            
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))  
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            log_security_event(
                'ADMIN_ACCESS_DENIED',
                message=f"Attempted to access admin route {request.path} without login",
                ip_address=request.remote_addr
            )
            
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))  
        if not session.get('is_admin', False):
            log_security_event(
                'PRIVILEGE_ESCALATION_ATTEMPT',
                user_id=session.get('user_id'),
                message=f"Non-admin user attempted to access {request.path}",
                ip_address=request.remote_addr
            )
            
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))  
        log_security_event(
            'ADMIN_ACCESS',
            user_id=session.get('user_id'),
            message=f"Admin accessed {request.path}",
            ip_address=request.remote_addr
        )
        
        return f(*args, **kwargs)
    return decorated_function
