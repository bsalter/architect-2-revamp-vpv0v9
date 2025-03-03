"""
Pagination utility module for the Interaction Management System.

This module provides standardized pagination functionality for API endpoints,
supporting the Interaction Finder interface with consistent pagination controls.
It includes functions for parameter validation, metadata generation, and
result formatting to ensure consistent paginated responses across the application.
"""

import math
from typing import Dict, List, Tuple, Any, Optional, Union

from flask import request, current_app

from ...utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ...utils.validation_util import validate_required
from ...config import get_env_var

# Default page number if not specified
DEFAULT_PAGE = 1

# Helper function to get integer environment variables
def get_int_env_var(name: str, default: int) -> int:
    """
    Get an environment variable as an integer with a default value.
    
    Args:
        name: Name of the environment variable
        default: Default value if environment variable is not set or not an integer
        
    Returns:
        Integer value of environment variable or default
    """
    value = get_env_var(name, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

# Get page size defaults from environment or fall back to constants
DEFAULT_PAGE_SIZE = get_int_env_var('DEFAULT_PAGE_SIZE', DEFAULT_PAGE_SIZE)
MAX_PAGE_SIZE = get_int_env_var('MAX_PAGE_SIZE', MAX_PAGE_SIZE)


def validate_pagination_params(page: int, page_size: int) -> Tuple[int, int]:
    """
    Validates and normalizes pagination parameters, ensuring they are within acceptable ranges.
    
    Args:
        page: The page number to validate
        page_size: The page size to validate
        
    Returns:
        Tuple of normalized (page, page_size)
    """
    # Ensure page is an integer greater than or equal to 1
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = DEFAULT_PAGE
    
    if page < 1:
        page = DEFAULT_PAGE
    
    # Ensure page_size is an integer greater than 0
    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    
    # Limit page_size to maximum allowed
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    
    return page, page_size


def get_pagination_metadata(page: int, page_size: int, total_items: int) -> Dict[str, Any]:
    """
    Calculates pagination metadata including total pages, has_next, has_prev flags.
    
    Args:
        page: Current page number
        page_size: Number of items per page
        total_items: Total number of items across all pages
        
    Returns:
        Dictionary with pagination metadata
    """
    # Calculate total pages
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    
    # Determine if there is a next page
    has_next = page < total_pages
    
    # Determine if there is a previous page
    has_prev = page > 1
    
    return {
        'page': page,
        'page_size': page_size,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev
    }


def get_pagination_info() -> Tuple[int, int]:
    """
    Extracts and normalizes pagination parameters from request data (query params or JSON body).
    
    Returns:
        Tuple of (page, page_size)
    """
    # Try to get pagination parameters from query string
    page = request.args.get('page', DEFAULT_PAGE)
    page_size = request.args.get('page_size', DEFAULT_PAGE_SIZE)
    
    # If not found in query string, try to get from JSON body
    if request.is_json and (page == DEFAULT_PAGE or page_size == DEFAULT_PAGE_SIZE):
        json_data = request.get_json(silent=True) or {}
        if page == DEFAULT_PAGE and 'page' in json_data:
            page = json_data.get('page')
        if page_size == DEFAULT_PAGE_SIZE and 'page_size' in json_data:
            page_size = json_data.get('page_size')
    
    # Validate and normalize the parameters
    return validate_pagination_params(page, page_size)


def get_slice_params(page: int, page_size: int) -> Tuple[int, int]:
    """
    Calculates database query slice parameters (offset and limit) from page and page_size.
    
    Args:
        page: The page number
        page_size: The number of items per page
        
    Returns:
        Tuple of (offset, limit) for database queries
    """
    offset = (page - 1) * page_size
    return offset, page_size


def paginate_results(items: List[Any], total_items: int, page: int, page_size: int) -> Dict[str, Any]:
    """
    Creates a complete paginated response object with data and metadata.
    
    Args:
        items: The list of items for the current page
        total_items: Total number of items across all pages
        page: Current page number
        page_size: Number of items per page
        
    Returns:
        Dictionary with items and pagination metadata
    """
    # Validate pagination parameters
    page, page_size = validate_pagination_params(page, page_size)
    
    # Get pagination metadata
    pagination = get_pagination_metadata(page, page_size, total_items)
    
    # Return combined result
    return {
        'items': items,
        'pagination': pagination
    }


class Paginator:
    """
    Class-based pagination handler for more complex pagination requirements.
    
    This class provides an object-oriented interface to pagination functionality,
    allowing for more complex pagination scenarios and stateful pagination handling.
    """
    
    def __init__(self, page: int = DEFAULT_PAGE, page_size: int = DEFAULT_PAGE_SIZE, total_items: int = 0):
        """
        Initializes a paginator with default or provided values.
        
        Args:
            page: The page number (defaults to DEFAULT_PAGE)
            page_size: The number of items per page (defaults to DEFAULT_PAGE_SIZE)
            total_items: The total number of items (defaults to 0)
        """
        self.page = page
        self.page_size = page_size
        self.total_items = total_items
        
        # Validate parameters
        self.validate_params()
    
    def validate_params(self):
        """
        Validates and normalizes pagination parameters.
        
        Updates instance attributes with normalized values.
        """
        self.page, self.page_size = validate_pagination_params(self.page, self.page_size)
    
    def get_slice_params(self) -> Tuple[int, int]:
        """
        Gets database query slice parameters.
        
        Returns:
            Tuple of (offset, limit) for database queries
        """
        return get_slice_params(self.page, self.page_size)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Gets pagination metadata for the current state.
        
        Returns:
            Dictionary with pagination metadata
        """
        return get_pagination_metadata(self.page, self.page_size, self.total_items)
    
    def paginate(self, items: List[Any]) -> Dict[str, Any]:
        """
        Creates a paginated response with items and metadata.
        
        Args:
            items: The list of items for the current page
            
        Returns:
            Dictionary with items and pagination metadata
        """
        # Update total_items if not already set
        if self.total_items == 0 and items is not None:
            self.total_items = len(items)
        
        # Get pagination metadata
        pagination = self.get_metadata()
        
        # Return combined result
        return {
            'items': items,
            'pagination': pagination
        }
    
    @classmethod
    def from_request(cls) -> 'Paginator':
        """
        Factory method to create a Paginator from the current request.
        
        Returns:
            New Paginator instance with request parameters
        """
        page, page_size = get_pagination_info()
        return cls(page=page, page_size=page_size)