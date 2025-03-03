"""
Cross-Site Request Forgery (CSRF) protection implementation for the Flask backend.

Provides token generation, validation, and middleware for protecting state-changing 
requests in the Interaction Management System.
"""

import base64
import hashlib
import hmac
import secrets
import time
from functools import wraps
from typing import Callable, Dict, Optional, Union, Any

from flask import current_app, request, session
from urllib.parse import urlparse

from ..logging.structured_logger import StructuredLogger, info, warning, error
from ..utils.error_util import BaseAppException
from ..utils.enums import ErrorType

# Create module logger
logger = StructuredLogger(__name__)

# Constants
CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
CSRF_FORM_FIELD = 'csrf_token'
CSRF_SESSION_KEY = 'csrf_token'
CSRF_DEFAULT_TOKEN_EXPIRY = 3600  # 1 hour in seconds
CSRF_SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


class CSRFError(BaseAppException):
    """Exception raised when CSRF validation fails"""
    
    def __init__(self, message: str = 'CSRF token validation failed'):
        """
        Initialize a CSRF error.
        
        Args:
            message: Error message
        """
        super().__init__(message, ErrorType.AUTHORIZATION)
        self.error_code = 'CSRF_ERROR'


def generate_csrf_token() -> str:
    """
    Generates a new CSRF token and stores it in the session.
    
    Returns:
        str: The generated CSRF token string
    """
    # Generate random token
    token = secrets.token_hex(32)
    
    # Get current timestamp for expiration
    timestamp = int(time.time())
    
    # Combine token and timestamp
    combined = f"{token}:{timestamp}"
    
    # Create signature with app secret key
    secret_key = current_app.config.get('SECRET_KEY', '').encode('utf-8')
    signature = hmac.new(
        secret_key, 
        combined.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    
    # Combine token, timestamp, and signature
    final_token = f"{combined}:{signature}"
    
    # Encode in base64 for easier transport
    encoded_token = base64.urlsafe_b64encode(final_token.encode('utf-8')).decode('utf-8')
    
    # Store in session
    session[CSRF_SESSION_KEY] = encoded_token
    
    logger.info("Generated new CSRF token", extra={"action": "csrf_token_generated"})
    
    return encoded_token


def validate_csrf_token(token: str) -> bool:
    """
    Validates the provided CSRF token against the one stored in the session.
    
    Args:
        token: CSRF token to validate
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    if not token:
        logger.warning("CSRF validation failed: No token provided", 
                      extra={"action": "csrf_validation_failed", "reason": "token_missing"})
        return False
    
    # Get token from session
    session_token = session.get(CSRF_SESSION_KEY)
    if not session_token:
        logger.warning("CSRF validation failed: No token in session", 
                      extra={"action": "csrf_validation_failed", "reason": "session_token_missing"})
        return False
    
    # If tokens match exactly, it's valid
    if token == session_token:
        return True
    
    try:
        # Decode token from base64
        decoded_token = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
        
        # Split into parts
        token_parts = decoded_token.split(':')
        
        if len(token_parts) != 3:
            logger.warning("CSRF validation failed: Invalid token format", 
                          extra={"action": "csrf_validation_failed", "reason": "token_format"})
            return False
        
        # Extract parts
        token_value, token_timestamp, token_signature = token_parts
        
        # Verify signature
        token_combined = f"{token_value}:{token_timestamp}"
        secret_key = current_app.config.get('SECRET_KEY', '').encode('utf-8')
        computed_signature = hmac.new(
            secret_key, 
            token_combined.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # Check if signatures match
        if token_signature != computed_signature:
            logger.warning("CSRF validation failed: Invalid signature", 
                          extra={"action": "csrf_validation_failed", "reason": "invalid_signature"})
            return False
        
        # Check token expiration
        expiry_seconds = current_app.config.get('CSRF_TOKEN_EXPIRY', CSRF_DEFAULT_TOKEN_EXPIRY)
        current_time = int(time.time())
        
        try:
            token_time = int(token_timestamp)
        except ValueError:
            logger.warning("CSRF validation failed: Invalid timestamp", 
                          extra={"action": "csrf_validation_failed", "reason": "invalid_timestamp"})
            return False
        
        if (current_time - token_time) > expiry_seconds:
            logger.warning("CSRF validation failed: Token expired", 
                          extra={"action": "csrf_validation_failed", "reason": "token_expired"})
            return False
        
        # Token is valid
        return True
        
    except (ValueError, TypeError, IndexError, base64.binascii.Error) as e:
        logger.error(f"CSRF validation error: {str(e)}", 
                    extra={"action": "csrf_validation_failed", "reason": "token_processing_error"})
        return False


def get_csrf_token_from_request() -> Optional[str]:
    """
    Extracts CSRF token from the current request (headers or form data).
    
    Returns:
        str or None: CSRF token if found, None otherwise
    """
    # Check headers
    token = request.headers.get(CSRF_HEADER_NAME)
    if not token:
        # Some frameworks use X-XSRF-TOKEN instead
        token = request.headers.get('X-XSRF-TOKEN')
    
    # Check form data
    if not token and request.form:
        token = request.form.get(CSRF_FORM_FIELD)
    
    # Check JSON data
    if not token and request.is_json:
        json_data = request.get_json(silent=True) or {}
        token = json_data.get(CSRF_FORM_FIELD)
    
    return token


def csrf_required(f: Callable) -> Callable:
    """
    Decorator for Flask routes that require CSRF protection.
    
    Args:
        f: The view function to protect
        
    Returns:
        function: Decorated function with CSRF protection
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip check for safe methods
        if request.method in CSRF_SAFE_METHODS:
            return f(*args, **kwargs)
        
        # Skip for CSRF exempt views
        if getattr(f, '_csrf_exempt', False):
            return f(*args, **kwargs)
        
        # Get token from request
        token = get_csrf_token_from_request()
        
        # Validate token
        if not token or not validate_csrf_token(token):
            logger.warning(f"CSRF validation failed for {request.endpoint}", 
                          extra={"action": "csrf_validation_failed", 
                                "endpoint": request.endpoint,
                                "method": request.method})
            raise CSRFError()
        
        return f(*args, **kwargs)
    
    return decorated_function


def csrf_exempt(f: Callable) -> Callable:
    """
    Decorator to mark a view function as exempt from CSRF protection.
    
    Args:
        f: The view function to exempt
        
    Returns:
        function: The function marked as CSRF exempt
    """
    f._csrf_exempt = True
    return f


class CSRFProtection:
    """CSRF protection middleware for Flask applications."""
    
    def __init__(self, app=None):
        """
        Initialize the CSRF protection middleware.
        
        Args:
            app: Flask application instance
        """
        self._app = None
        self._config = {
            'CSRF_ENABLED': True,
            'CSRF_TOKEN_EXPIRY': CSRF_DEFAULT_TOKEN_EXPIRY,
            'CSRF_HEADER_NAME': CSRF_HEADER_NAME,
            'CSRF_FORM_FIELD': CSRF_FORM_FIELD,
            'CSRF_SESSION_KEY': CSRF_SESSION_KEY,
            'CSRF_SAFE_METHODS': CSRF_SAFE_METHODS
        }
        self._enabled = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app, config=None):
        """
        Configure CSRF protection for a Flask application.
        
        Args:
            app: Flask application instance
            config: Optional configuration dictionary
        """
        self._app = app
        
        # Update config with app config and provided config
        app_config = app.config.get('CSRF_PROTECTION', {})
        self._config.update(app_config)
        
        if config:
            self._config.update(config)
        
        # Register handlers if CSRF is enabled
        if self._config['CSRF_ENABLED']:
            app.before_request(self._before_request)
            app.after_request(self._after_request)
            
            # Add template context processor to make CSRF token available in templates
            app.context_processor(self._context_processor)
            
            logger.info("CSRF protection initialized", 
                       extra={"action": "csrf_protection_initialized", 
                             "config": self._config})
            
            self._enabled = True
    
    def exempt(self, view_function):
        """
        Mark a view function as exempt from CSRF protection.
        
        Args:
            view_function: The function to exempt
            
        Returns:
            function: The function marked as CSRF exempt
        """
        return csrf_exempt(view_function)
    
    def _before_request(self):
        """
        Flask before_request handler to check CSRF token.
        
        Returns:
            Response or None: Error response if CSRF validation fails, None otherwise
        """
        # Skip if not enabled
        if not self._enabled:
            return
        
        # Skip for safe methods
        if request.method in self._config['CSRF_SAFE_METHODS']:
            return
        
        # Skip for exempt views
        if self._is_exempt():
            return
        
        # Get token from request
        token = get_csrf_token_from_request()
        
        # Validate token
        if not token or not validate_csrf_token(token):
            logger.warning(f"CSRF validation failed in before_request", 
                          extra={"action": "csrf_validation_failed", 
                                "endpoint": request.endpoint,
                                "method": request.method})
            raise CSRFError()
    
    def _after_request(self, response):
        """
        Flask after_request handler to inject CSRF token in responses.
        
        Args:
            response: Flask response object
            
        Returns:
            Response: Modified response with CSRF token
        """
        # Skip if not enabled
        if not self._enabled:
            return response
        
        # Only inject token for HTML responses
        if not response.mimetype.startswith('text/html'):
            return response
        
        # Generate token if not in session
        if CSRF_SESSION_KEY not in session:
            generate_csrf_token()
        
        # Add token as a cookie for JavaScript frameworks
        response.set_cookie(
            'XSRF-TOKEN',
            session[CSRF_SESSION_KEY],
            httponly=False,
            secure=request.is_secure,
            samesite='Lax'
        )
        
        return response
    
    def _context_processor(self):
        """
        Flask context processor to make CSRF token available in templates.
        
        Returns:
            dict: Dictionary with CSRF token variable for templates
        """
        # Generate token if not in session
        if CSRF_SESSION_KEY not in session:
            token = generate_csrf_token()
        else:
            token = session[CSRF_SESSION_KEY]
        
        return {
            'csrf_token': token,
            'csrf_field_name': self._config['CSRF_FORM_FIELD']
        }
    
    def _is_exempt(self):
        """
        Check if a view function is exempt from CSRF protection.
        
        Returns:
            bool: True if current view is exempt, False otherwise
        """
        view = current_app.view_functions.get(request.endpoint)
        return view and getattr(view, '_csrf_exempt', False)