"""
Initialization file for the API middleware package that exposes the middleware components for authentication, site context management, request/response logging, rate limiting, and error handling. This file enables easy importing of all middleware components for application setup.
"""

from .error_handler import ErrorHandler  # src/backend/api/middleware/error_handler.py
from .logging_middleware import LoggingMiddleware  # src/backend/api/middleware/logging_middleware.py
from .auth_middleware import AuthMiddleware  # src/backend/api/middleware/auth_middleware.py
from .site_context_middleware import SiteContextMiddleware  # src/backend/api/middleware/site_context_middleware.py
from .rate_limiting_middleware import rate_limit_middleware  # src/backend/api/middleware/rate_limiting_middleware.py


def register_middleware(app):
    """
    Registers all middleware components with the Flask application

    Args:
        app: Flask application instance

    Returns:
        None: No return value
    """
    # Register error handlers using ErrorHandler.register_error_handlers
    ErrorHandler.register_error_handlers(app)

    # Register logging middleware using LoggingMiddleware().register_middleware
    LoggingMiddleware().register_middleware(app)

    # Register authentication middleware using app.before_request(AuthMiddleware.before_request)
    app.before_request(AuthMiddleware.before_request)

    # Register site context middleware using app.before_request(SiteContextMiddleware.before_request)
    app.before_request(SiteContextMiddleware.before_request)