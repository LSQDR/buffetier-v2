"""
Error Handlers Blueprint
Handles 404, 500, and other HTTP errors
"""

from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 - Page Not Found"""
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 - Internal Server Error"""
    return render_template('errors/500.html'), 500


@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 - Forbidden"""
    return render_template('errors/404.html'), 403  # Reuse 404 template
