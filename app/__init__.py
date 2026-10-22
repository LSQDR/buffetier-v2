"""
Application factory pattern.
Creates and configures the Flask application.
"""

from flask import Flask

from app.extensions import csrf, limiter
from config import config

# Bootstrap comes from jsDelivr and the location page loads Google Maps.
# Scripts still allow 'unsafe-inline' because the templates use inline onclick handlers.
CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://maps.googleapis.com https://maps.gstatic.com",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
    "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self' https://maps.googleapis.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
])


def create_app(config_name='development'):
    """
    Application factory function.

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Make sessions permanent (with timeout)
    @app.before_request
    def make_session_permanent():
        from flask import session
        session.permanent = True

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault('Content-Security-Policy', CONTENT_SECURITY_POLICY)
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        return response

    # Register blueprints
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.errors import errors_bp
    from app.blueprints.main import main_bp
    from app.blueprints.orders import orders_bp
    from app.blueprints.reviews import reviews_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(errors_bp)

    return app
