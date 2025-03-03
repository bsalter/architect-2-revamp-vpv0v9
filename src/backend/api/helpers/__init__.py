"""
API Helper Package for the Interaction Management System.

This package provides standardized utilities for API response formatting
and pagination handling across the application. It ensures consistent
API contracts and simplifies pagination implementation for the Interaction
Finder and search functionality.

The helpers are designed for use in all API endpoint implementations to 
maintain consistent response structures and pagination behavior.
"""

# Import pagination utilities
from .pagination import (
    validate_pagination_params,
    get_pagination_metadata,
    get_pagination_info,
    get_slice_params,
    paginate_results,
    Paginator
)

# Import response formatting utilities
from .response import (
    success_response,
    error_response,
    validation_error_response,
    not_found_response,
    unauthorized_response,
    forbidden_response,
    site_access_error_response,
    server_error_response,
    paginated_response,
    no_content_response,
    created_response
)

# Create a class-based ResponseFormatter for more object-oriented usage
class ResponseFormatter:
    """
    Class-based API response formatting utility.
    
    This class provides an object-oriented interface to the response formatting
    functions for cases where a more stateful or context-aware approach is preferred.
    """
    
    @staticmethod
    def success(data=None, message="Operation successful", status_code=200):
        """
        Generate a standardized success response.
        
        Args:
            data: Optional data to include in the response
            message: Success message to include
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return success_response(data, message, status_code)
    
    @staticmethod
    def error(message, error_type, status_code=400, details=None):
        """
        Generate a standardized error response.
        
        Args:
            message: Error message
            error_type: Type of error that occurred
            status_code: HTTP status code
            details: Optional error details
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return error_response(message, error_type, status_code, details)
    
    @staticmethod
    def validation_error(errors, message="Validation error"):
        """
        Generate a validation error response.
        
        Args:
            errors: Dictionary of field-specific validation errors
            message: Error message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return validation_error_response(errors, message)
    
    @staticmethod
    def not_found(resource_type, resource_id):
        """
        Generate a not found error response.
        
        Args:
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return not_found_response(resource_type, resource_id)
    
    @staticmethod
    def paginated(items, total, page, page_size, message="Data retrieved successfully"):
        """
        Generate a paginated response.
        
        Args:
            items: List of items for the current page
            total: Total number of items across all pages
            page: Current page number
            page_size: Number of items per page
            message: Success message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return paginated_response(items, total, page, page_size, message)

# Export all functionality at the package level
__all__ = [
    # Pagination utilities
    'validate_pagination_params',
    'get_pagination_metadata',
    'get_pagination_info',
    'get_slice_params',
    'paginate_results',
    'Paginator',
    
    # Response formatting utilities
    'success_response',
    'error_response',
    'validation_error_response',
    'not_found_response',
    'unauthorized_response',
    'forbidden_response',
    'site_access_error_response',
    'server_error_response',
    'paginated_response',
    'no_content_response',
    'created_response',
    'ResponseFormatter'
]