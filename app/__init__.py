"""
Application factory pattern.
Creates and configures the Flask application.
"""

from flask import Flask

from app.extensions import csrf, limiter
from config import config


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
