"""
Main application factory for creating and configuring the Flask application instance.
This file initializes the Flask app, registers extensions, applies middleware, connects routes, and handles configuration loading
to create a fully configured backend API server for the Interaction Management System.
"""

import os  # standard library

from flask import Flask, Blueprint  # flask: version 2.3.2
from flask_cors import CORS  # flask_cors: version 4.0.0

from .config import CONFIG  # src/backend/config.py
from .extensions import db, jwt, cors, migrate, ma, redis_client  # src/backend/extensions.py
from .api.routes import register_routes  # src/backend/api/routes.py
from .api.middleware.auth_middleware import AuthMiddleware  # src/backend/api/middleware/auth_middleware.py
from .api.middleware.site_context_middleware import SiteContextMiddleware  # src/backend/api/middleware/site_context_middleware.py
from .api.middleware.error_handler import configure_error_handlers  # src/backend/api/middleware/error_handler.py
from .auth.auth0 import Auth0Client  # src/backend/auth/auth0.py
from .auth.token_service import TokenService  # src/backend/auth/token_service.py
from .auth.user_context_service import UserContextService  # src/backend/auth/user_context_service.py
from .auth.site_context_service import SiteContextService  # src/backend/auth/site_context_service.py
from .cache.cache_service import get_cache_service  # src/backend/cache/cache_service.py
from .logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py

# Initialize structured logger
logger = StructuredLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """
    Application factory function that creates and configures a Flask application instance

    Args:
        config_name: Configuration key to load from the CONFIG dictionary

    Returns:
        Configured Flask application instance
    """
    # Create Flask application instance with appropriate settings
    app = Flask(__name__)

    # Load configuration from CONFIG dictionary based on config_name
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')  # Default to 'development' if not set
    app.config.from_object(CONFIG[config_name])
    logger.info(f"Loaded configuration: {config_name}")

    # Initialize logger with application configuration
    configure_logging(app)

    # Initialize database with app (db.init_app(app))
    db.init_app(app)
    logger.info("Initialized SQLAlchemy")

    # Initialize JWT manager with app (jwt.init_app(app))
    jwt.init_app(app)
    logger.info("Initialized Flask-JWT-Extended")

    # Initialize Redis client with app configuration
    init_redis(app)

    # Initialize authentication services (Auth0Client, TokenService)
    auth0_client, token_service, user_context_service, site_context_service = init_auth_services(app)

    # Initialize API Blueprint for route organization
    api_blueprint = init_api_blueprint(app)

    # Register API routes with the API blueprint
    register_routes(api_blueprint)

    # Register API blueprint with main Flask app
    app.register_blueprint(api_blueprint)
    logger.info("Registered API blueprint")

    # Apply middleware (AuthMiddleware, SiteContextMiddleware)
    auth_middleware = AuthMiddleware(token_service, user_context_service, site_context_service)
    auth_middleware.init_app(app)
    logger.info("Applied AuthMiddleware")

    site_context_middleware = SiteContextMiddleware(site_context_service)
    site_context_middleware.init_app(app)
    logger.info("Applied SiteContextMiddleware")

    # Configure error handlers
    configure_error_handlers(app)
    logger.info("Configured error handlers")

    # Configure CORS settings
    cors.init_app(app, resources={r"/api/*": {"origins": app.config['CORS_CONFIG']['origins']}})
    logger.info("Configured CORS")

    # Configure migration extension
    migrate.init_app(app, db)
    logger.info("Initialized Flask-Migrate")

    # Configure Marshmallow extension
    ma.init_app(app)
    logger.info("Initialized Flask-Marshmallow")

    # Log successful application creation
    logger.info("Flask application created successfully")

    # Return the fully configured Flask application
    return app


def configure_logging(app: Flask) -> None:
    """
    Configure application logging based on configuration settings

    Args:
        app: Flask application instance

    Returns:
        None: No return value
    """
    # Extract log level from app configuration
    log_level = app.config['LOG_LEVEL']

    # Configure structured logger with appropriate level
    logger.set_level(log_level)

    # Configure Flask's built-in logger
    app.logger.setLevel(log_level)
    logger.info(f"Configured logging with level: {log_level}")


def init_redis(app: Flask) -> None:
    """
    Initialize Redis client with configuration from app

    Args:
        app: Flask application instance

    Returns:
        None: No return value
    """
    # Extract Redis configuration from app config
    redis_config = app.config.get('REDIS_CONFIG')

    # Configure redis_client with host, port, db, password
    redis_client.init_app(redis_config)
    logger.info("Initialized Redis client")


def init_auth_services(app: Flask) -> tuple:
    """
    Initialize authentication-related services

    Args:
        app: Flask application instance

    Returns:
        tuple: Tuple of initialized auth service instances
    """
    # Initialize Auth0Client instance
    auth0_client = Auth0Client()

    # Initialize TokenService with auth0_client and cache_service
    cache_service = get_cache_service()
    token_service = TokenService(auth0_client=auth0_client)

    # Initialize UserContextService with token_service
    user_context_service = UserContextService(token_service=token_service)

    # Initialize SiteContextService with token_service
    site_context_service = SiteContextService(user_context_service=user_context_service)

    # Register JWTManager callbacks for token handling
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return identity

    logger.info("Initialized authentication services")

    # Return tuple of initialized services
    return auth0_client, token_service, user_context_service, site_context_service


def init_api_blueprint(app: Flask) -> Blueprint:
    """
    Initialize and configure the main API blueprint

    Args:
        app: Flask application instance

    Returns:
        Blueprint: Configured API blueprint
    """
    # Create Blueprint instance for API routes
    api_blueprint = Blueprint('api', __name__, url_prefix='/api')

    # Apply middleware to blueprint if applicable
    # (No blueprint-specific middleware at this time)

    logger.info("Initialized API blueprint")

    # Return configured blueprint
    return api_blueprint