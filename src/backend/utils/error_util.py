"""
Error Utilities Module

This module defines custom exception classes and error handling utilities 
for standardized error handling across the application.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from .enums import ErrorType

# Configure logger
logger = logging.getLogger('interaction_app')


class BaseAppException(Exception):
    """
    Base exception class for all application-specific exceptions.
    
    This class provides a standardized structure for all application exceptions
    with consistent attributes and serialization methods.
    """
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.SERVER,
                 details: Dict[str, Any] = None, error_code: str = None):
        """
        Initialize the base application exception.
        
        Args:
            message: Human-readable error message
            error_type: Classification of the error type
            details: Additional contextual information about the error
            error_code: Optional error code for more specific categorization
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.error_code = error_code
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary representation.
        
        Returns:
            Dict containing the exception attributes
        """
        return {
            'message': self.message,
            'error_type': self.error_type.value,
            'details': self.details,
            'error_code': self.error_code
        }
    
    def __str__(self) -> str:
        """
        String representation of the exception.
        
        Returns:
            Formatted string with message, error type, and code
        """
        base = f"{self.error_type.value.upper()} ERROR: {self.message}"
        if self.error_code:
            base += f" (Code: {self.error_code})"
        return base


class ValidationError(BaseAppException):
    """
    Exception raised for data validation errors.
    
    Used when input data fails validation rules or constraints.
    """
    
    def __init__(self, message: str, details: Dict[str, Any] = None, error_code: str = None):
        """
        Initialize a validation error.
        
        Args:
            message: Human-readable error message
            details: Field-specific validation errors
            error_code: Optional error code for more specific categorization
        """
        super().__init__(message, ErrorType.VALIDATION, details, error_code)


class AuthenticationError(BaseAppException):
    """
    Exception raised for authentication failures.
    
    Used when user authentication fails or tokens are invalid.
    """
    
    def __init__(self, message: str, details: Dict[str, Any] = None, error_code: str = None):
        """
        Initialize an authentication error.
        
        Args:
            message: Human-readable error message
            details: Additional context about the authentication failure
            error_code: Optional error code for more specific categorization
        """
        super().__init__(message, ErrorType.AUTHENTICATION, details, error_code)


class AuthorizationError(BaseAppException):
    """
    Exception raised for authorization failures.
    
    Used when an authenticated user attempts an action they don't have permission for.
    """
    
    def __init__(self, message: str, details: Dict[str, Any] = None, error_code: str = None):
        """
        Initialize an authorization error.
        
        Args:
            message: Human-readable error message
            details: Additional context about the authorization failure
            error_code: Optional error code for more specific categorization
        """
        super().__init__(message, ErrorType.AUTHORIZATION, details, error_code)


class NotFoundError(BaseAppException):
    """
    Exception raised when a requested resource is not found.
    
    Used when attempting to access or manipulate a non-existent resource.
    """
    
    def __init__(self, message: str, resource_type: str = None, 
                 resource_id: Union[str, int] = None, error_code: str = None):
        """
        Initialize a not found error.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource that was not found (e.g., 'interaction')
            resource_id: Identifier of the resource that was not found
            error_code: Optional error code for more specific categorization
        """
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
            
        super().__init__(message, ErrorType.NOT_FOUND, details, error_code)


class DatabaseError(BaseAppException):
    """
    Exception raised for database-related errors.
    
    Used when database operations fail or encounter unexpected conditions.
    """
    
    def __init__(self, message: str, details: Dict[str, Any] = None, 
                 error_code: str = None, original_exception: Exception = None):
        """
        Initialize a database error.
        
        Args:
            message: Human-readable error message
            details: Additional context about the database error
            error_code: Optional error code for more specific categorization
            original_exception: The original exception that triggered this error
        """
        super().__init__(message, ErrorType.SERVER, details, error_code)
        self.original_exception = original_exception


class SiteContextError(BaseAppException):
    """
    Exception raised for site context violations like cross-site access attempts.
    
    Used when a user attempts to access or modify data from an unauthorized site.
    """
    
    def __init__(self, message: str, user_sites: List[int] = None, 
                 requested_site: int = None, error_code: str = None):
        """
        Initialize a site context error.
        
        Args:
            message: Human-readable error message
            user_sites: List of site IDs the user has access to
            requested_site: Site ID the user attempted to access
            error_code: Optional error code for more specific categorization
        """
        details = {}
        if user_sites is not None:
            details['user_sites'] = user_sites
        if requested_site is not None:
            details['requested_site'] = requested_site
            
        super().__init__(
            message, 
            ErrorType.AUTHORIZATION, 
            details, 
            error_code="SITE_CONTEXT_ERROR" if error_code is None else error_code
        )


class ConflictError(BaseAppException):
    """
    Exception raised for resource conflicts like duplicate entries.
    
    Used when an operation would violate unique constraints or other conflict conditions.
    """
    
    def __init__(self, message: str, details: Dict[str, Any] = None, error_code: str = None):
        """
        Initialize a conflict error.
        
        Args:
            message: Human-readable error message
            details: Additional context about the conflict
            error_code: Optional error code for more specific categorization
        """
        super().__init__(message, ErrorType.CONFLICT, details, error_code)


def format_error_response(message: str, error_type: ErrorType, 
                          details: Dict[str, Any] = None, error_code: str = None) -> Dict[str, Any]:
    """
    Formats an error message into a standardized error response structure.
    
    Args:
        message: Human-readable error message
        error_type: Classification of the error type
        details: Additional contextual information about the error
        error_code: Optional error code for more specific categorization
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        'success': False,
        'message': message,
        'error_type': error_type.value
    }
    
    if error_code:
        response['error_code'] = error_code
        
    if details:
        response['details'] = details
        
    return response


def http_error_response(message: str, error_type: ErrorType = ErrorType.SERVER,
                        details: Dict[str, Any] = None, error_code: str = None) -> Dict[str, Any]:
    """
    Creates a properly formatted error response for HTTP responses.
    
    This is a convenience wrapper around format_error_response for HTTP API responses.
    
    Args:
        message: Human-readable error message
        error_type: Classification of the error type
        details: Additional contextual information about the error
        error_code: Optional error code for more specific categorization
        
    Returns:
        HTTP error response dictionary
    """
    return format_error_response(message, error_type, details, error_code)


def log_error(exception: Exception, message: str = None, context: Dict[str, Any] = None) -> None:
    """
    Helper function to log errors with consistent formatting.
    
    Args:
        exception: The exception that occurred
        message: Optional custom message to log (uses exception message if None)
        context: Additional context information to include in the log
        
    Returns:
        None
    """
    if message is None:
        message = str(exception)
        
    log_context = {
        'exception_type': exception.__class__.__name__,
        'exception_details': str(exception)
    }
    
    if context:
        log_context.update(context)
        
    logger.error(f"{message}", extra=log_context)