"""
API Response Helper Module

This module provides standardized API response formatting functions to maintain
consistent response structures across all API endpoints in the application.
"""

from http import HTTPStatus
from typing import Dict, Tuple, Any, List, Optional

from flask import jsonify

from ...utils.enums import ErrorType
from .pagination import get_pagination_metadata

# HTTP Status Codes
HTTP_OK = HTTPStatus.OK
HTTP_CREATED = HTTPStatus.CREATED
HTTP_NO_CONTENT = HTTPStatus.NO_CONTENT
HTTP_BAD_REQUEST = HTTPStatus.BAD_REQUEST
HTTP_UNAUTHORIZED = HTTPStatus.UNAUTHORIZED
HTTP_FORBIDDEN = HTTPStatus.FORBIDDEN
HTTP_NOT_FOUND = HTTPStatus.NOT_FOUND
HTTP_INTERNAL_SERVER_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR


def success_response(data: Dict[str, Any] = None, 
                    message: str = 'Operation successful',
                    status_code: int = HTTP_OK) -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized success response with optional data.
    
    Args:
        data: Optional data to include in the response
        message: Success message to include in the response
        status_code: HTTP status code for the response
        
    Returns:
        JSON response with success status and HTTP status code
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return response, status_code


def error_response(message: str,
                  error_type: ErrorType,
                  status_code: int = HTTP_BAD_REQUEST,
                  details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized error response with error type and details.
    
    Args:
        message: Error message to include in the response
        error_type: Type of error that occurred
        status_code: HTTP status code for the response
        details: Optional error details to include
        
    Returns:
        JSON response with error details and HTTP status code
    """
    response = {
        'success': False,
        'message': message,
        'error_type': error_type.value
    }
    
    if details:
        response['details'] = details
    
    return response, status_code


def validation_error_response(errors: Dict[str, List[str]],
                             message: str = 'Validation error') -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized validation error response with validation errors.
    
    Args:
        errors: Dictionary of field-specific validation errors
        message: Error message to include in the response
        
    Returns:
        JSON response with validation errors and HTTP status code
    """
    return error_response(
        message=message,
        error_type=ErrorType.VALIDATION,
        status_code=HTTP_BAD_REQUEST,
        details={'errors': errors}
    )


def not_found_response(resource_type: str,
                      resource_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized not found error response.
    
    Args:
        resource_type: Type of resource that was not found
        resource_id: ID of the resource that was not found
        
    Returns:
        JSON response with not found error and HTTP status code
    """
    message = f"{resource_type} with ID {resource_id} not found"
    return error_response(
        message=message,
        error_type=ErrorType.NOT_FOUND,
        status_code=HTTP_NOT_FOUND
    )


def server_error_response(message: str = 'An unexpected error occurred',
                         details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized server error response.
    
    Args:
        message: Error message to include in the response
        details: Optional error details to include
        
    Returns:
        JSON response with server error and HTTP status code
    """
    return error_response(
        message=message,
        error_type=ErrorType.SERVER,
        status_code=HTTP_INTERNAL_SERVER_ERROR,
        details=details
    )


def unauthorized_response(message: str = 'Authentication required') -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized unauthorized error response.
    
    Args:
        message: Error message to include in the response
        
    Returns:
        JSON response with unauthorized error and HTTP status code
    """
    return error_response(
        message=message,
        error_type=ErrorType.AUTHENTICATION,
        status_code=HTTP_UNAUTHORIZED
    )


def forbidden_response(message: str = 'Access denied',
                      details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized forbidden error response.
    
    Args:
        message: Error message to include in the response
        details: Optional error details to include
        
    Returns:
        JSON response with forbidden error and HTTP status code
    """
    return error_response(
        message=message,
        error_type=ErrorType.AUTHORIZATION,
        status_code=HTTP_FORBIDDEN,
        details=details
    )


def site_context_error_response(message: str = 'Site access denied',
                               details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized site context error response.
    
    Args:
        message: Error message to include in the response
        details: Optional error details to include
        
    Returns:
        JSON response with site context error and HTTP status code
    """
    return error_response(
        message=message,
        error_type=ErrorType.AUTHORIZATION,  # Using AUTHORIZATION for site context errors
        status_code=HTTP_FORBIDDEN,
        details=details
    )


def paginated_response(items: List[Any],
                      total: int,
                      page: int,
                      page_size: int,
                      message: str = 'Data retrieved successfully') -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized paginated response with data and pagination metadata.
    
    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number
        page_size: Number of items per page
        message: Success message to include in the response
        
    Returns:
        JSON response with paginated data and HTTP status code
    """
    pagination = get_pagination_metadata(page, page_size, total)
    
    response_data = {
        'items': items,
        'pagination': pagination
    }
    
    return success_response(
        data=response_data,
        message=message
    )


def created_response(data: Dict[str, Any],
                    message: str = 'Resource created successfully') -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized created response for resource creation.
    
    Args:
        data: Data of the created resource
        message: Success message to include in the response
        
    Returns:
        JSON response with created resource data and HTTP status code
    """
    return success_response(
        data=data,
        message=message,
        status_code=HTTP_CREATED
    )


def no_content_response() -> Tuple[Dict[str, Any], int]:
    """
    Generate a standardized no content response for successful operations without return data.
    
    Returns:
        Empty JSON response with HTTP status code
    """
    return {}, HTTP_NO_CONTENT