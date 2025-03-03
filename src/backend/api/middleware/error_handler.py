"""
Flask middleware that provides centralized error handling for the API, catching
exceptions and converting them to standardized API responses with appropriate
HTTP status codes. Implements comprehensive logging and error tracking for all API errors.
"""

from flask import Flask, current_app, request  # version 2.3.2
from flask import has_request_context  # version 2.3.2
import werkzeug.exceptions  # version 2.3.2
import http  # standard library
import traceback  # standard library
import typing  # standard library
import marshmallow  # version 3.20.1

from ...utils.error_util import (
    ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, DatabaseError, SiteContextError, ConflictError, 
    BaseAppException, log_error
)
from ..helpers.response import (
    validation_error_response, server_error_response, not_found_response,
    unauthorized_response, forbidden_response, site_context_error_response,
    error_response
)
from ...logging.structured_logger import StructuredLogger
from ...logging.error_tracker import ErrorTracker
from ...utils.enums import ErrorType

# Initialize logger and error tracker
logger = StructuredLogger(__name__)
error_tracker = ErrorTracker({})


def handle_validation_error(error: ValidationError) -> typing.Tuple:
    """
    Handle validation errors from request data validation.
    
    Args:
        error: The validation error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the validation error with structured logger
    logger.error(f"Validation error: {str(error)}", 
                 extra={"details": error.details})
    
    # Extract validation errors from exception details
    validation_errors = error.details if error.details else {"general": ["Invalid input data"]}
    
    # Track the validation error via error tracker
    error_tracker.track_exception(
        error, 
        {"validation_errors": validation_errors},
        ErrorType.VALIDATION.value
    )
    
    # Return formatted validation error response with 400 status
    return validation_error_response(validation_errors, error.message)


def handle_authentication_error(error: AuthenticationError) -> typing.Tuple:
    """
    Handle authentication errors from JWT validation.
    
    Args:
        error: The authentication error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the authentication error with structured logger
    logger.error(f"Authentication error: {str(error)}", 
                extra={"details": error.details})
    
    # Track the authentication error via error tracker
    error_tracker.track_exception(
        error, 
        error.details,
        ErrorType.AUTHENTICATION.value
    )
    
    # Return formatted unauthorized response with 401 status
    return unauthorized_response(error.message)


def handle_authorization_error(error: AuthorizationError) -> typing.Tuple:
    """
    Handle authorization errors from permission checks.
    
    Args:
        error: The authorization error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the authorization error with structured logger
    logger.error(f"Authorization error: {str(error)}", 
                extra={"details": error.details})
    
    # Track the authorization error via error tracker
    error_tracker.track_exception(
        error, 
        error.details,
        ErrorType.AUTHORIZATION.value
    )
    
    # Return formatted forbidden response with 403 status
    return forbidden_response(error.message, error.details)


def handle_site_context_error(error: SiteContextError) -> typing.Tuple:
    """
    Handle site context errors from site-scoping violations.
    
    Args:
        error: The site context error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the site context error with structured logger
    logger.error(f"Site context error: {str(error)}", 
                extra={"details": error.details})
    
    # Track the site context error via error tracker
    error_tracker.track_exception(
        error, 
        error.details,
        ErrorType.AUTHORIZATION.value
    )
    
    # Return formatted site context error response with 403 status
    return site_context_error_response(error.message, error.details)


def handle_not_found_error(error: NotFoundError) -> typing.Tuple:
    """
    Handle not found errors for missing resources.
    
    Args:
        error: The not found error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the not found error with structured logger
    logger.error(f"Resource not found: {str(error)}", 
                extra={"details": error.details})
    
    # Extract resource type and ID from exception details
    resource_type = error.details.get("resource_type", "Resource") if error.details else "Resource"
    resource_id = error.details.get("resource_id", "unknown") if error.details else "unknown"
    
    # Track the not found error via error tracker
    error_tracker.track_exception(
        error, 
        error.details,
        ErrorType.NOT_FOUND.value
    )
    
    # Return formatted not found response with 404 status
    return not_found_response(resource_type, str(resource_id))


def handle_conflict_error(error: ConflictError) -> typing.Tuple:
    """
    Handle conflict errors like duplicate entries.
    
    Args:
        error: The conflict error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the conflict error with structured logger
    logger.error(f"Resource conflict: {str(error)}", 
                extra={"details": error.details})
    
    # Track the conflict error via error tracker
    error_tracker.track_exception(
        error, 
        error.details,
        ErrorType.CONFLICT.value
    )
    
    # Return formatted error response with 409 status
    return error_response(error.message, ErrorType.CONFLICT, http.HTTPStatus.CONFLICT, error.details)


def handle_database_error(error: DatabaseError) -> typing.Tuple:
    """
    Handle database errors with proper abstraction for client.
    
    Args:
        error: The database error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the database error with structured logger and original exception
    logger.exception(f"Database error: {str(error)}", 
                extra={"details": error.details, "original_exception": str(getattr(error, 'original_exception', 'None'))})
    
    # Track the database error via error tracker with full context
    error_tracker.track_exception(
        error, 
        {"details": error.details, "original_exception": str(getattr(error, 'original_exception', 'None'))},
        ErrorType.SERVER.value
    )
    
    # Return formatted server error response with 500 status and generic message
    return server_error_response("A database error occurred. Please try again later.")


def handle_marshmallow_validation_error(error: marshmallow.ValidationError) -> typing.Tuple:
    """
    Handle validation errors from marshmallow schema validation.
    
    Args:
        error: The marshmallow validation error exception
        
    Returns:
        JSON error response and status code
    """
    # Log the validation error with structured logger
    logger.error(f"Schema validation error: {str(error)}", 
                extra={"errors": error.messages})
    
    # Convert marshmallow validation errors to application format
    validation_errors = {}
    for field, field_errors in error.messages.items():
        if isinstance(field_errors, list):
            validation_errors[field] = field_errors
        else:
            validation_errors[field] = [str(field_errors)]
    
    # Track the validation error via error tracker
    error_tracker.track_exception(
        error, 
        {"validation_errors": validation_errors},
        ErrorType.VALIDATION.value
    )
    
    # Return formatted validation error response with 400 status
    return validation_error_response(validation_errors, "Validation error")


def handle_werkzeug_not_found(error: werkzeug.exceptions.NotFound) -> typing.Tuple:
    """
    Handle 404 errors from undefined routes.
    
    Args:
        error: The werkzeug NotFound exception
        
    Returns:
        JSON error response and status code
    """
    # Log the not found error with structured logger
    requested_path = request.path if has_request_context() else "unknown"
    logger.error(f"Endpoint not found: {requested_path}", 
                extra={"method": request.method if has_request_context() else "unknown", 
                       "path": requested_path})
    
    # Track the not found error via error tracker
    error_tracker.track_exception(
        error, 
        {"method": request.method if has_request_context() else "unknown", 
         "path": requested_path},
        ErrorType.NOT_FOUND.value
    )
    
    # Return formatted not found response with 404 status
    return not_found_response("Endpoint", requested_path)


def handle_werkzeug_method_not_allowed(error: werkzeug.exceptions.MethodNotAllowed) -> typing.Tuple:
    """
    Handle 405 errors from method not allowed on routes.
    
    Args:
        error: The werkzeug MethodNotAllowed exception
        
    Returns:
        JSON error response and status code
    """
    # Extract method and path from request
    method = request.method if has_request_context() else "unknown"
    path = request.path if has_request_context() else "unknown"
    
    # Log the method not allowed error with structured logger
    logger.error(f"Method not allowed: {method} {path}", 
                extra={"method": method, "path": path, "allowed_methods": error.valid_methods})
    
    # Track the method not allowed error via error tracker
    error_tracker.track_exception(
        error, 
        {"method": method, "path": path, "allowed_methods": error.valid_methods},
        ErrorType.SERVER.value
    )
    
    # Return formatted error response with 405 status
    valid_methods = ", ".join(error.valid_methods)
    return error_response(
        f"Method {method} not allowed for this endpoint. Valid methods: {valid_methods}",
        ErrorType.SERVER,
        http.HTTPStatus.METHOD_NOT_ALLOWED
    )


def handle_base_app_exception(error: BaseAppException) -> typing.Tuple:
    """
    Handle any other application exceptions not specifically handled.
    
    Args:
        error: The base application exception
        
    Returns:
        JSON error response and status code
    """
    # Log the application exception with structured logger
    logger.error(f"Application exception: {str(error)}", 
                extra={"error_type": error.error_type.value, "details": error.details})
    
    # Extract error type and details from exception
    error_type = error.error_type
    details = error.details
    
    # Track the exception via error tracker
    error_tracker.track_exception(
        error, 
        details,
        error_type.value
    )
    
    # Return formatted error response with appropriate status code based on error type
    if error_type == ErrorType.VALIDATION:
        status_code = http.HTTPStatus.BAD_REQUEST
    elif error_type == ErrorType.AUTHENTICATION:
        status_code = http.HTTPStatus.UNAUTHORIZED
    elif error_type == ErrorType.AUTHORIZATION:
        status_code = http.HTTPStatus.FORBIDDEN
    elif error_type == ErrorType.NOT_FOUND:
        status_code = http.HTTPStatus.NOT_FOUND
    elif error_type == ErrorType.CONFLICT:
        status_code = http.HTTPStatus.CONFLICT
    else:
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    
    return error_response(error.message, error_type, status_code, details)


def handle_unhandled_exception(error: Exception) -> typing.Tuple:
    """
    Catch-all handler for any unhandled exceptions.
    
    Args:
        error: The unhandled exception
        
    Returns:
        JSON error response and status code
    """
    # Log the unhandled exception with structured logger at critical level
    logger.exception(f"Unhandled exception: {str(error)}")
    
    # Generate full traceback for debugging
    tb = traceback.format_exc()
    
    # Track the exception via error tracker with full context and traceback
    error_tracker.track_exception(
        error, 
        {"traceback": tb, **get_error_context()},
        ErrorType.SERVER.value,
        notify=True  # Send to external error tracking service
    )
    
    # Return formatted server error response with 500 status and generic message
    return server_error_response()


def get_error_context() -> dict:
    """
    Extract context information from request for error logging.
    
    Returns:
        Context dictionary with request information
    """
    context = {}
    
    # Check if in request context
    try:
        if has_request_context():
            # If in request context, add endpoint, method, path, and URL
            context.update({
                "endpoint": request.endpoint,
                "method": request.method,
                "path": request.path,
                "url": request.url
            })
            
            # Add user ID and site ID if available in session
            if hasattr(request, "user_id"):
                context["user_id"] = request.user_id
            
            if hasattr(request, "site_id"):
                context["site_id"] = request.site_id
    except Exception:
        # If there's any error getting context, return what we have so far
        pass
        
    return context


def configure_error_handlers(app: Flask) -> None:
    """
    Register all error handlers with Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register ValidationError handler
    app.register_error_handler(ValidationError, handle_validation_error)
    
    # Register AuthenticationError handler
    app.register_error_handler(AuthenticationError, handle_authentication_error)
    
    # Register AuthorizationError handler
    app.register_error_handler(AuthorizationError, handle_authorization_error)
    
    # Register SiteContextError handler
    app.register_error_handler(SiteContextError, handle_site_context_error)
    
    # Register NotFoundError handler
    app.register_error_handler(NotFoundError, handle_not_found_error)
    
    # Register ConflictError handler
    app.register_error_handler(ConflictError, handle_conflict_error)
    
    # Register DatabaseError handler
    app.register_error_handler(DatabaseError, handle_database_error)
    
    # Register Marshmallow ValidationError handler
    app.register_error_handler(marshmallow.ValidationError, handle_marshmallow_validation_error)
    
    # Register Werkzeug NotFound handler
    app.register_error_handler(werkzeug.exceptions.NotFound, handle_werkzeug_not_found)
    
    # Register Werkzeug MethodNotAllowed handler
    app.register_error_handler(werkzeug.exceptions.MethodNotAllowed, handle_werkzeug_method_not_allowed)
    
    # Register BaseAppException handler
    app.register_error_handler(BaseAppException, handle_base_app_exception)
    
    # Register catch-all Exception handler
    app.register_error_handler(Exception, handle_unhandled_exception)
    
    # Log successful registration of error handlers
    logger.info("Error handlers registered successfully")