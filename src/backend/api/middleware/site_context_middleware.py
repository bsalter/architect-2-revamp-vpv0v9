"""
Site Context Middleware

This module provides middleware for managing site context in Flask API requests.
It ensures that all requests are properly associated with a site and that users
only access data from sites they have permission to access.
"""

from flask import request, g, current_app, make_response, jsonify
import functools
import re
from typing import Optional, Union, Dict, Any, List, Callable

from ...auth.site_context_service import SiteContextService
from ...utils.error_util import SiteContextError, http_error_response
from ...utils.enums import ErrorType
from ...logging.structured_logger import StructuredLogger
from ...utils.constants import SITE_EXEMPT_ENDPOINTS

# Initialize structured logger
logger = StructuredLogger(__name__)


def extract_site_id_from_request() -> Optional[int]:
    """
    Extracts site ID from request parameters, headers, or JSON body.
    
    Returns:
        int or None: Site ID if found in request, None otherwise
    """
    site_id = None
    
    # Check URL parameters
    if 'site_id' in request.args:
        site_id = request.args.get('site_id')
        logger.debug(f"Found site_id in URL parameters: {site_id}")
    
    # Check headers
    elif 'X-Site-ID' in request.headers:
        site_id = request.headers.get('X-Site-ID')
        logger.debug(f"Found site_id in headers: {site_id}")
    
    # Check JSON body for POST/PUT requests
    elif request.is_json and request.method in ['POST', 'PUT']:
        json_data = request.get_json(silent=True)
        if json_data and 'site_id' in json_data:
            site_id = json_data.get('site_id')
            logger.debug(f"Found site_id in JSON body: {site_id}")
    
    # Convert to int if possible
    if site_id is not None:
        try:
            return int(site_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid site_id format: {site_id}")
            return None
    
    logger.debug("No site_id found in request")
    return None


def is_site_exempt_endpoint() -> bool:
    """
    Checks if the current request endpoint is exempt from site context requirements.
    
    Returns:
        bool: True if endpoint is exempt, False otherwise
    """
    # Get current endpoint path and method
    path = request.path
    method = request.method
    
    # Check against list of exempt endpoints
    for exempt_pattern in SITE_EXEMPT_ENDPOINTS:
        # If pattern is a string, check for exact match
        if isinstance(exempt_pattern, str) and path == exempt_pattern:
            logger.debug(f"Endpoint {path} is exempt from site context (exact match)")
            return True
        
        # If pattern is a tuple with method and path
        elif isinstance(exempt_pattern, tuple) and len(exempt_pattern) == 2:
            exempt_method, exempt_path = exempt_pattern
            if method == exempt_method and path == exempt_path:
                logger.debug(f"Endpoint {method} {path} is exempt from site context (method+path match)")
                return True
        
        # If pattern is a regex pattern
        elif isinstance(exempt_pattern, str) and exempt_pattern.startswith('^'):
            if re.match(exempt_pattern, path):
                logger.debug(f"Endpoint {path} is exempt from site context (regex match)")
                return True
    
    logger.debug(f"Endpoint {method} {path} requires site context")
    return False


def site_context_middleware() -> Optional[Dict[str, Any]]:
    """
    Main middleware function for establishing and validating site context.
    
    Returns:
        flask.Response: Error response if site context validation fails, None if successful
    """
    # Skip site context for exempt endpoints
    if is_site_exempt_endpoint():
        logger.debug("Skipping site context for exempt endpoint")
        return None
    
    # Extract site_id from request
    site_id = extract_site_id_from_request()
    
    # Get site context service from app context
    site_context_service = current_app.extensions.get('site_context_service')
    if not site_context_service:
        logger.error("Site context service not found in Flask app extensions")
        return make_response(jsonify(http_error_response(
            "Site context service not configured",
            error_type=ErrorType.SERVER,
            error_code="SITE_SERVICE_MISSING"
        )), 500)
    
    try:
        if site_id:
            # Set specific site context
            logger.debug(f"Setting site context for site ID: {site_id}")
            site_context_service.set_site_context(site_id)
        else:
            # Set default site context
            logger.debug("Setting default site context")
            site_context = site_context_service.set_default_site_context()
            if not site_context:
                logger.warning("Failed to set default site context, user has no site access")
                return make_response(jsonify(http_error_response(
                    "No site access available",
                    error_type=ErrorType.AUTHORIZATION,
                    error_code="NO_SITE_ACCESS"
                )), 403)
    except SiteContextError as e:
        logger.error(f"Site context error: {str(e)}")
        return make_response(jsonify(http_error_response(
            str(e),
            error_type=ErrorType.AUTHORIZATION,
            details=getattr(e, 'details', None),
            error_code="SITE_ACCESS_DENIED"
        )), 403)
    
    logger.info("Site context established successfully")
    return None


def site_context_cleanup(exception=None) -> None:
    """
    Cleanup function to clear site context after request processing.
    
    Args:
        exception: Exception that was raised during request handling, if any
    """
    # Get site context service from app context
    site_context_service = current_app.extensions.get('site_context_service')
    if site_context_service:
        site_context_service.clear_site_context()
        logger.debug("Site context cleared")


def requires_site_context(func):
    """
    Decorator for routes that require site context.
    
    Args:
        func: Flask route function to decorate
        
    Returns:
        Wrapped function with site context check
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if site context is established
        if not hasattr(g, 'site_id') or g.site_id is None:
            logger.warning("Route requires site context but none is set")
            return make_response(jsonify(http_error_response(
                "Site context required for this operation",
                error_type=ErrorType.AUTHORIZATION,
                error_code="SITE_CONTEXT_REQUIRED"
            )), 403)
        
        # Call the original function
        return func(*args, **kwargs)
    
    return wrapper


class SiteContextMiddleware:
    """
    Class that provides site context middleware for Flask application.
    """
    
    def __init__(self, site_context_service: SiteContextService):
        """
        Initialize the site context middleware with required services.
        
        Args:
            site_context_service: Service for managing site context
        """
        self._site_context_service = site_context_service
        logger.info("SiteContextMiddleware initialized")
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask application.
        
        Args:
            app: Flask application instance
        """
        # Store site context service in app extensions
        app.extensions['site_context_service'] = self._site_context_service
        
        # Register before_request handler
        app.before_request(self.establish_site_context)
        
        # Register teardown_request handler
        app.teardown_request(self.cleanup)
        
        logger.info("SiteContextMiddleware registered with Flask app")
    
    def establish_site_context(self):
        """
        Middleware handler to establish site context for request.
        
        Returns:
            flask.Response: Error response if site context establishment fails, None if successful
        """
        # Skip site context for exempt endpoints
        if is_site_exempt_endpoint():
            logger.debug("Skipping site context for exempt endpoint")
            return None
        
        # Extract site_id from request
        site_id = extract_site_id_from_request()
        
        try:
            if site_id:
                # Verify the user has access to this site
                self._site_context_service.verify_site_access(site_id)
                
                # Set specific site context
                logger.debug(f"Setting site context for site ID: {site_id}")
                self._site_context_service.set_site_context(site_id)
            else:
                # Set default site context
                logger.debug("Setting default site context")
                site_context = self._site_context_service.set_default_site_context()
                if not site_context:
                    logger.warning("Failed to set default site context, user has no site access")
                    return make_response(jsonify(http_error_response(
                        "No site access available",
                        error_type=ErrorType.AUTHORIZATION,
                        error_code="NO_SITE_ACCESS"
                    )), 403)
        except SiteContextError as e:
            logger.error(f"Site context error: {str(e)}")
            return make_response(jsonify(http_error_response(
                str(e),
                error_type=ErrorType.AUTHORIZATION,
                details=getattr(e, 'details', None),
                error_code="SITE_ACCESS_DENIED"
            )), 403)
        
        logger.info("Site context established successfully")
        return None
    
    def cleanup(self, exception=None):
        """
        Cleanup handler to clear site context after request.
        
        Args:
            exception: Exception that was raised during request handling, if any
        """
        self._site_context_service.clear_site_context()
        logger.debug("Site context cleared")