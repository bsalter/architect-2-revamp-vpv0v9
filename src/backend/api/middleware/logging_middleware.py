"""Flask middleware that handles request and response logging, enriching logs with request context information, user context, site context, and performance metrics. Implements structured logging for all API requests and responses."""
import time  # standard library
import json  # standard library
from typing import Dict, Any  # standard library

from flask import Flask, Request, Response, request  # flask 2.3.2
from flask import g, has_request_context
from flask_cors import CORS  # flask-cors 4.0.0

from marshmallow import ValidationError  # marshmallow 3.20.1

from ...logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py
from ...logging.performance_monitor import PerformanceMonitor  # src/backend/logging/performance_monitor.py
from ...logging.audit_logger import AuditLogger  # src/backend/logging/audit_logger.py
from ...auth.user_context_service import UserContextService  # src/backend/auth/user_context_service.py
from ...auth.site_context_service import SiteContextService  # src/backend/auth/site_context_service.py
from ...config import LOGGING_CONFIG  # src/backend/config.py

# Initialize logger, performance monitor, and audit logger
logger = StructuredLogger(__name__)
performance_monitor = PerformanceMonitor('api')
audit_logger = AuditLogger()
API_RESPONSE_TIME_THRESHOLD_MS = LOGGING_CONFIG.get('API_RESPONSE_TIME_THRESHOLD_MS', 500)


def get_request_data_for_logging(request: Request) -> Dict[str, Any]:
    """Extracts and formats request data for logging purposes, with sensitive data redaction

    Args:
        request (flask.Request): Flask request object

    Returns:
        dict: Formatted request data suitable for logging
    """
    # Extract HTTP method, path, and query parameters from request
    request_data = {
        'method': request.method,
        'path': request.path,
        'query_params': request.args.to_dict()
    }

    # Get request headers (redacting authorization and sensitive headers)
    headers = {}
    for key, value in request.headers.items():
        if key.lower() in ['authorization', 'cookie']:
            headers[key] = '[REDACTED]'
        else:
            headers[key] = value
    request_data['headers'] = headers

    # Parse request body if present and content type is JSON
    if request.content_type == 'application/json':
        try:
            request_data['body'] = request.get_json()
        except Exception as e:
            request_data['body'] = f"Error parsing JSON body: {str(e)}"
    else:
        request_data['body'] = "Non-JSON content"

    # Redact sensitive fields like passwords and tokens from the body
    sensitive_fields = ['password', 'token', 'secret', 'key', 'auth', 'jwt', 'credential']
    if 'body' in request_data and isinstance(request_data['body'], dict):
        request_data['body'] = redact_sensitive_data(request_data['body'], sensitive_fields)

    # Return dictionary with method, path, headers, and body
    return request_data


def get_response_data_for_logging(response: Response) -> Dict[str, Any]:
    """Extracts and formats response data for logging purposes

    Args:
        response (flask.Response): Flask response object

    Returns:
        dict: Formatted response data suitable for logging
    """
    # Extract HTTP status code from response
    response_data = {
        'status_code': response.status_code
    }

    # Get response headers
    response_data['headers'] = dict(response.headers)

    # Parse response body if content type is JSON and not too large
    if response.content_type == 'application/json' and len(response.data) < 4096:
        try:
            response_data['body'] = json.loads(response.data.decode('utf-8'))
        except Exception as e:
            response_data['body'] = f"Error parsing JSON body: {str(e)}"
    else:
        response_data['body'] = "Non-JSON content or body too large"

    # Return dictionary with status code, headers, and body (if applicable)
    return response_data


def redact_sensitive_data(data: Dict, sensitive_fields: list) -> Dict:
    """Redacts sensitive information from request or response data

    Args:
        data (dict): Data to redact
        sensitive_fields (list): List of sensitive field names

    Returns:
        dict: Data with sensitive fields redacted
    """
    # Create a copy of the input data to avoid modifying the original
    redacted_data = data.copy()

    # For each sensitive field, replace its value with '[REDACTED]' if present
    for key in list(redacted_data.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            redacted_data[key] = '[REDACTED]'
        elif isinstance(redacted_data[key], dict):
            redacted_data[key] = redact_sensitive_data(redacted_data[key], sensitive_fields)

    # Return the redacted data dictionary
    return redacted_data


class LoggingMiddleware:
    """Flask middleware that logs all requests and responses with structured context"""

    def __init__(self, app: Flask, user_context_service: UserContextService, site_context_service: SiteContextService):
        """Initialize the logging middleware with required services

        Args:
            app (flask.Flask): Flask app instance
            user_context_service (UserContextService): User context service
            site_context_service (SiteContextService): Site context service
        """
        # Store reference to Flask app
        self.app = app
        # Store reference to user context service
        self.user_context_service = user_context_service
        # Store reference to site context service
        self.site_context_service = site_context_service
        # Initialize logger, performance monitor, and audit logger
        self.logger = logger
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        # Register before_request and after_request handlers on the app
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)

    def before_request(self):
        """Handler that runs before each request to set up logging context and start performance timer"""
        # Generate or get request ID via structured_logger
        request_id = logger.get_request_id()

        # Set up request context with method, path, and client info
        context = {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }

        # Capture user context info if authenticated
        if self.user_context_service.is_authenticated():
            user_context = self.user_context_service.get_current_user_context()
            if user_context:
                context['user_id'] = user_context.user_id
                context['username'] = user_context.username
                context['email'] = user_context.email

        # Capture site context info if available
        if self.site_context_service.get_current_site_id():
            site_context = self.site_context_service.get_current_site_context()
            if site_context:
                context['site_id'] = site_context.site_id
                context['site_name'] = site_context.site_name

        logger.set_request_context(context)

        # Start performance timer for request
        g.start_time = time.perf_counter()

        # Log the incoming request with detailed request data
        self.log_request(request, context)

        # Record API access in audit log if appropriate (non-health check paths)
        if request.path != '/health':
            self.audit_logger.log_data_access(
                action='access',
                resource_type='api',
                resource_id=request.path,
                details=context
            )

    def after_request(self, response: Response) -> Response:
        """Handler that runs after each request to log response and performance metrics

        Args:
            response (flask.Response): Flask response

        Returns:
            flask.Response: Original or modified response
        """
        # Stop performance timer and calculate request duration
        duration = time.perf_counter() - g.start_time
        duration_ms = duration * 1000

        # Format response data for logging
        context = logger.get_context_data()
        self.log_response(response, duration_ms, context)

        # Check duration against threshold and log warning if exceeded
        if duration_ms > API_RESPONSE_TIME_THRESHOLD_MS:
            logger.warning(
                f"API endpoint {request.path} took {duration_ms:.2f}ms, exceeding threshold of {API_RESPONSE_TIME_THRESHOLD_MS}ms"
            )

        # Add performance tracking headers to response if configured
        response.headers['X-Process-Time'] = str(duration_ms)

        # Clear request context from structured logger
        logger.clear_request_context()

        # Return the response object
        return response

    def log_request(self, request: Request, context: Dict[str, Any]):
        """Logs detailed information about the incoming request

        Args:
            request (flask.Request): Flask request object
            context (dict): Request context
        """
        # Format request data using get_request_data_for_logging
        request_data = get_request_data_for_logging(request)

        # Combine with existing context
        log_data = context.copy()
        log_data.update(request_data)

        # Log request at INFO level with complete context
        logger.info(f"Incoming request: {request.method} {request.path}", log_data)

    def log_response(self, response: Response, duration_ms: float, context: Dict[str, Any]):
        """Logs detailed information about the outgoing response

        Args:
            response (flask.Response): Flask response object
            duration_ms (float): Request duration in milliseconds
            context (dict): Request context
        """
        # Format response data using get_response_data_for_logging
        response_data = get_response_data_for_logging(response)

        # Add duration information to context
        log_data = context.copy()
        log_data.update(response_data)
        log_data['duration_ms'] = duration_ms

        # Determine log level based on status code (ERROR for 4xx/5xx, INFO otherwise)
        log_level = logger.error if response.status_code >= 400 else logger.info

        # Log response with complete context
        log_level(f"Outgoing response: {response.status_code}", log_data)