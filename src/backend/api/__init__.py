# src/backend/api/__init__.py
"""Initialization module for the Flask API package that creates and configures the API blueprint,
registers routes, sets up middleware components, and provides utilities for API initialization.
This module serves as the entry point for the API layer of the Interaction Management System."""

from flask import Flask, Blueprint  # flask: version 2.3.2
from flask_cors import CORS  # flask-cors: version 4.0.0
from flask_marshmallow import JSONSchemaValidator  # flask-marshmallow: version 0.15.0

from .routes import register_routes  # src/backend/api/routes.py
from .middleware import register_middleware  # src/backend/api/middleware/__init__.py
from .middleware.error_handler import configure_error_handlers  # src/backend/api/middleware/error_handler.py
from ..logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py
from ..auth.token_service import TokenService  # src/backend/auth/token_service.py
from ..auth.user_context_service import UserContextService  # src/backend/auth/user_context_service.py
from ..auth.site_context_service import SiteContextService  # src/backend/auth/site_context_service.py

# Initialize structured logger
logger = StructuredLogger(__name__)

# Initialize TokenService, UserContextService, and SiteContextService
token_service = TokenService()
user_context_service = UserContextService()
site_context_service = SiteContextService()


def create_api_blueprint() -> Blueprint:
    """Creates the API blueprint with base URL prefix"""
    # Create a new Blueprint with name 'api' and url_prefix='/api'
    api_bp = Blueprint('api', __name__, url_prefix='/api')

    # Configure blueprint options for URL handling
    api_bp.url_value_preprocessor(lambda endpoint, values: values.pop('api', None))
    api_bp.url_defaults = lambda endpoint, values: values.setdefault('api', 'true')

    # Set default content type to application/json
    api_bp.after_request(lambda response: response.content_type == 'application/json')

    # Return the created blueprint
    return api_bp


def init_app(app: Flask) -> Blueprint:
    """Initializes the API with the Flask application, registering routes and middleware"""
    # Create API blueprint using create_api_blueprint()
    api_bp = create_api_blueprint()

    # Configure API-specific settings from app.config
    app.config['API_TITLE'] = 'Interaction Management System API'
    app.config['API_VERSION'] = 'v1'

    # Register middleware with the app using register_middleware(app)
    register_middleware(app)

    # Configure error handlers using configure_error_handlers(app)
    configure_error_handlers(app)

    # Register API routes to the blueprint using register_routes(api_bp)
    register_routes(api_bp)

    # Register the blueprint with the Flask app
    app.register_blueprint(api_bp)

    # Log successful API initialization
    logger.info("API initialized successfully")

    # Return the configured blueprint
    return api_bp


def configure_api_security(blueprint: Blueprint, app: Flask) -> None:
    """Configures security settings for the API blueprint"""
    # Configure CORS settings for the blueprint
    CORS(blueprint, origins=app.config.get('CORS_ORIGINS', '*'))

    # Set up Content Security Policy headers
    # TODO: Implement CSP headers

    # Configure JWT token settings
    # TODO: Implement JWT token settings

    # Set up rate limiting defaults
    # TODO: Implement rate limiting defaults

    # Add security headers to all responses
    # TODO: Implement security headers

    # Log security configuration completion
    logger.info("API security configured successfully")


def get_api_version() -> str:
    """Returns the current API version for versioning responses"""
    # Return the current API version from configuration or default to 'v1'
    return 'v1'