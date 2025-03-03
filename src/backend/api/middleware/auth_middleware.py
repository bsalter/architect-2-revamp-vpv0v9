"""
Authentication middleware for Flask API requests in the Interaction Management System.

This module provides authentication middleware that validates JWT tokens,
extracts user information and site access claims, and sets up user context
for request processing. It rejects unauthorized requests with appropriate
error responses and provides decorators for routes requiring authentication.
"""

from flask import request, g, current_app, make_response, jsonify  # version 2.3.2
import functools  # standard library
import re  # standard library
from typing import Dict, List, Optional, Any, Union, Callable  # standard library

from ...auth.token_service import TokenService
from ...auth.user_context_service import UserContextService
from ...auth.site_context_service import SiteContextService
from ...utils.error_util import AuthenticationError, http_error_response
from ...utils.enums import ErrorType
from ...utils.constants import PUBLIC_ENDPOINTS
from ...logging.structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)


def extract_token_from_header(auth_header: str) -> Optional[str]:
    """
    Extracts JWT token from the Authorization header.
    
    Args:
        auth_header: Authorization header string
        
    Returns:
        Extracted token or None if not found/invalid format
    """
    if not auth_header:
        logger.debug("Authorization header is missing")
        return None
        
    # Check if the header has the correct format (Bearer token)
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        logger.debug("Invalid Authorization header format")
        return None
    
    return parts[1]


def is_exempt_endpoint() -> bool:
    """
    Checks if the current request endpoint is exempt from authentication.
    
    Returns:
        True if endpoint is exempt, False otherwise
    """
    # Get the current path and method
    path = request.path
    method = request.method
    
    # Check exact matches first
    for endpoint in PUBLIC_ENDPOINTS:
        # If endpoint is a string, check for exact match
        if isinstance(endpoint, str) and endpoint == path:
            logger.debug(f"Request to {path} is exempt (exact match)")
            return True
            
        # If endpoint is a tuple, check both path and method
        elif isinstance(endpoint, tuple) and len(endpoint) == 2:
            exempt_path, exempt_method = endpoint
            if exempt_path == path and (exempt_method == '*' or exempt_method == method):
                logger.debug(f"Request to {path} with method {method} is exempt (exact match)")
                return True
    
    # Check pattern matches
    for endpoint in PUBLIC_ENDPOINTS:
        # If endpoint is a regex pattern
        if isinstance(endpoint, re.Pattern) and endpoint.match(path):
            logger.debug(f"Request to {path} is exempt (pattern match)")
            return True
    
    logger.debug(f"Request to {path} with method {method} requires authentication")
    return False


def auth_middleware() -> Optional[Any]:
    """
    Main authentication middleware function for validating requests.
    
    Returns:
        Error response if authentication fails, None if successful
    """
    # Skip authentication for exempt endpoints
    if is_exempt_endpoint():
        logger.debug("Skipping authentication for exempt endpoint")
        return None
    
    # Get Authorization header from request
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        logger.warning("No Authorization header in request")
        return http_error_response(
            "Authentication required", 
            ErrorType.AUTHENTICATION, 
            error_code="MISSING_TOKEN"
        ), 401
    
    # Extract token from header
    token = extract_token_from_header(auth_header)
    if not token:
        logger.warning("Invalid Authorization header format")
        return http_error_response(
            "Invalid Authorization header format", 
            ErrorType.AUTHENTICATION, 
            error_code="INVALID_TOKEN_FORMAT"
        ), 401
    
    # Get required services from current_app
    token_service = current_app.config.get('token_service')
    user_context_service = current_app.config.get('user_context_service')
    site_context_service = current_app.config.get('site_context_service')
    
    if not token_service:
        logger.error("TokenService not configured in application")
        return http_error_response(
            "Authentication service unavailable", 
            ErrorType.SERVER, 
            error_code="SERVICE_UNAVAILABLE"
        ), 500
    
    try:
        # Validate token
        token_payload = token_service.validate_token(token)
        if not token_payload:
            logger.warning("Invalid or expired token")
            return http_error_response(
                "Invalid or expired token", 
                ErrorType.AUTHENTICATION, 
                error_code="INVALID_TOKEN"
            ), 401
        
        # Set user context if user_context_service is available
        if user_context_service:
            user_context_service.set_user_context_from_token(token_payload)
        
        # Set default site context if site_context_service is available
        if site_context_service:
            site_context_service.set_default_site_context()
        
        logger.info(f"Authenticated user {g.user_id if hasattr(g, 'user_id') else 'unknown'}")
        return None
        
    except AuthenticationError as e:
        logger.warning(f"Authentication error: {str(e)}")
        return http_error_response(
            str(e), 
            ErrorType.AUTHENTICATION, 
            error_code="AUTH_ERROR"
        ), 401
        
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        return http_error_response(
            "Authentication failed due to server error", 
            ErrorType.SERVER, 
            error_code="SERVER_ERROR"
        ), 500


def auth_cleanup(exception: Optional[Exception] = None) -> None:
    """
    Cleanup function to clear authentication context after request processing.
    
    Args:
        exception: Exception that may have occurred during request processing
    """
    # Get required services from current_app
    user_context_service = current_app.config.get('user_context_service')
    site_context_service = current_app.config.get('site_context_service')
    
    # Clear user context if available
    if user_context_service:
        user_context_service.clear_user_context()
    
    # Clear site context if available
    if site_context_service:
        site_context_service.clear_site_context()
    
    logger.debug("Authentication context cleanup completed")


def requires_auth(func: Callable) -> Callable:
    """
    Decorator for routes that require authentication.
    
    Args:
        func: The route function to decorate
        
    Returns:
        Wrapped function with authentication check
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if user is authenticated by looking at g.user_id
        if not hasattr(g, 'user_id') or not g.user_id:
            logger.warning("Authentication required for route but user not authenticated")
            response = http_error_response(
                "Authentication required", 
                ErrorType.AUTHENTICATION, 
                error_code="AUTHENTICATION_REQUIRED"
            )
            return make_response(jsonify(response), 401)
        
        # Call the original function
        return func(*args, **kwargs)
        
    return wrapper


class AuthMiddleware:
    """
    Class that provides authentication middleware for Flask application.
    """
    
    def __init__(self, token_service: TokenService, user_context_service: UserContextService, 
                 site_context_service: SiteContextService):
        """
        Initialize the authentication middleware with required services.
        
        Args:
            token_service: Service for token validation and extraction
            user_context_service: Service for managing user context
            site_context_service: Service for managing site context
        """
        self._token_service = token_service
        self._user_context_service = user_context_service
        self._site_context_service = site_context_service
        logger.info("AuthMiddleware initialized")
    
    def init_app(self, app) -> None:
        """
        Initialize the middleware with a Flask application.
        
        Args:
            app: Flask application instance
        """
        # Store services in app config for access during requests
        app.config['token_service'] = self._token_service
        app.config['user_context_service'] = self._user_context_service
        app.config['site_context_service'] = self._site_context_service
        
        # Register middleware functions with Flask
        app.before_request(self.authenticate)
        app.teardown_request(self.cleanup)
        
        logger.info("AuthMiddleware registered with Flask application")
    
    def authenticate(self) -> Optional[Any]:
        """
        Authentication handler called before each request.
        
        Returns:
            Error response if authentication fails, None if successful
        """
        # Skip authentication for exempt endpoints
        if is_exempt_endpoint():
            logger.debug("Skipping authentication for exempt endpoint")
            return None
        
        # Get Authorization header from request
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("No Authorization header in request")
            return http_error_response(
                "Authentication required", 
                ErrorType.AUTHENTICATION, 
                error_code="MISSING_TOKEN"
            ), 401
        
        # Extract token from header
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning("Invalid Authorization header format")
            return http_error_response(
                "Invalid Authorization header format", 
                ErrorType.AUTHENTICATION, 
                error_code="INVALID_TOKEN_FORMAT"
            ), 401
        
        try:
            # Validate token
            token_payload = self._token_service.validate_token(token)
            if not token_payload:
                logger.warning("Invalid or expired token")
                return http_error_response(
                    "Invalid or expired token", 
                    ErrorType.AUTHENTICATION, 
                    error_code="INVALID_TOKEN"
                ), 401
            
            # Set user context
            self._user_context_service.set_user_context_from_token(token_payload)
            
            # Set default site context
            self._site_context_service.set_default_site_context()
            
            logger.info(f"Authenticated user {g.user_id if hasattr(g, 'user_id') else 'unknown'}")
            return None
            
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            return http_error_response(
                str(e), 
                ErrorType.AUTHENTICATION, 
                error_code="AUTH_ERROR"
            ), 401
            
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return http_error_response(
                "Authentication failed due to server error", 
                ErrorType.SERVER, 
                error_code="SERVER_ERROR"
            ), 500
    
    def cleanup(self, exception: Optional[Exception] = None) -> None:
        """
        Cleanup handler called after each request.
        
        Args:
            exception: Exception that may have occurred during request processing
        """
        # Clear user context
        self._user_context_service.clear_user_context()
        
        # Clear site context
        self._site_context_service.clear_site_context()
        
        logger.debug("Authentication context cleanup completed")