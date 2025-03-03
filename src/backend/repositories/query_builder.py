"""
Query Builder Module

This module provides utilities for building complex database queries using SQLAlchemy,
with support for filtering, sorting, pagination, and full-text search. It ensures
all queries respect site-scoping security constraints to maintain data isolation.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

import sqlalchemy  # version 2.0.19
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Query

from src.backend.utils.error_util import ValidationError
from src.backend.utils.enums import FilterOperator, SortDirection
from src.backend.utils.validation_util import validate_site_context


def apply_pagination(query: Query, page: int, page_size: int) -> Query:
    """
    Applies pagination parameters to a query.
    
    Args:
        query: The SQLAlchemy query to paginate
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Query: Paginated query object
    """
    # Validate page and page_size parameters
    if page < 1:
        raise ValidationError("Page number must be greater than 0")
    
    if page_size < 1:
        raise ValidationError("Page size must be greater than 0")
    
    # Calculate offset based on page and page_size
    offset = (page - 1) * page_size
    
    # Apply limit and offset to query
    paginated_query = query.limit(page_size).offset(offset)
    
    return paginated_query


def apply_sorting(query: Query, model, sort_field: str, direction: SortDirection) -> Query:
    """
    Applies sorting criteria to a query.
    
    Args:
        query: The SQLAlchemy query to sort
        model: The SQLAlchemy model class
        sort_field: Field name to sort by
        direction: Sort direction (ascending or descending)
        
    Returns:
        Query: Sorted query object
    """
    # Get the column object from the model using the sort_field
    try:
        column = getattr(model, sort_field)
    except AttributeError:
        raise ValidationError(f"Invalid sort field: {sort_field}")
    
    # If direction is descending, apply desc() function to column
    if direction == SortDirection.DESC:
        sorted_query = query.order_by(desc(column))
    else:  # Otherwise apply asc() function to column
        sorted_query = query.order_by(asc(column))
    
    return sorted_query


def apply_filter(query: Query, model, field: str, operator: FilterOperator, value: Any) -> Query:
    """
    Applies a single filter condition to a query.
    
    Args:
        query: The SQLAlchemy query to filter
        model: The SQLAlchemy model class
        field: Field name to filter on
        operator: Filter operator (equals, contains, etc.)
        value: Value to filter by
        
    Returns:
        Query: Filtered query object
    """
    # Get the column object from the model using the field name
    try:
        column = getattr(model, field)
    except AttributeError:
        raise ValidationError(f"Invalid filter field: {field}")
    
    # Based on operator type, construct the appropriate filter expression
    if operator == FilterOperator.EQUALS:
        filter_expr = column == value
    elif operator == FilterOperator.NOT_EQUALS:
        filter_expr = column != value
    elif operator == FilterOperator.GREATER_THAN:
        filter_expr = column > value
    elif operator == FilterOperator.LESS_THAN:
        filter_expr = column < value
    elif operator == FilterOperator.CONTAINS:
        filter_expr = column.ilike(f"%{value}%")
    elif operator == FilterOperator.STARTS_WITH:
        filter_expr = column.ilike(f"{value}%")
    elif operator == FilterOperator.ENDS_WITH:
        filter_expr = column.ilike(f"%{value}")
    elif operator == FilterOperator.IN:
        if not isinstance(value, list):
            raise ValidationError(f"IN operator requires a list value, got {type(value)}")
        filter_expr = column.in_(value)
    elif operator == FilterOperator.BETWEEN:
        if not isinstance(value, list) or len(value) != 2:
            raise ValidationError("BETWEEN operator requires a list of two values")
        filter_expr = column.between(value[0], value[1])
    else:
        raise ValidationError(f"Unsupported filter operator: {operator}")
    
    # Apply the filter to the query using filter() method
    filtered_query = query.filter(filter_expr)
    
    return filtered_query


def apply_filters(query: Query, model, filters: List[Dict[str, Any]]) -> Query:
    """
    Applies multiple filter conditions to a query.
    
    Args:
        query: The SQLAlchemy query to filter
        model: The SQLAlchemy model class
        filters: List of filter dictionaries
        
    Returns:
        Query: Filtered query object
    """
    filtered_query = query
    
    # For each filter in filters list
    for filter_dict in filters:
        # Extract field, operator, and value from the filter dict
        field = filter_dict.get('field')
        operator = filter_dict.get('operator')
        value = filter_dict.get('value')
        
        # Validate filter parameters
        if not field:
            raise ValidationError("Filter missing 'field' parameter")
        if not operator:
            raise ValidationError("Filter missing 'operator' parameter")
        if value is None and operator not in (FilterOperator.EQUALS, FilterOperator.NOT_EQUALS):
            # Allow None values for equality checks but not other operators
            raise ValidationError("Filter missing 'value' parameter")
        
        # Apply individual filter using apply_filter function
        filtered_query = apply_filter(filtered_query, model, field, operator, value)
    
    return filtered_query


def apply_site_filter(query: Query, model, site_ids: List[int]) -> Query:
    """
    Applies site-scoping filter to ensure data security.
    
    Args:
        query: The SQLAlchemy query to filter
        model: The SQLAlchemy model class
        site_ids: List of site IDs the user has access to
        
    Returns:
        Query: Site-scoped query object
    """
    # Validate that site_ids is not empty using validate_site_context
    validate_site_context(site_ids)
    
    # Get the site_id column from the model
    try:
        site_id_column = getattr(model, 'site_id')
    except AttributeError:
        raise ValidationError(f"Model {model.__name__} does not have a site_id column")
    
    # Apply filter: model.site_id.in_(site_ids)
    site_scoped_query = query.filter(site_id_column.in_(site_ids))
    
    return site_scoped_query


def apply_text_search(query: Query, model, search_term: str, fields: List[str]) -> Query:
    """
    Applies full-text search across specified fields.
    
    Args:
        query: The SQLAlchemy query to search
        model: The SQLAlchemy model class
        search_term: The search term to look for
        fields: List of field names to search within
        
    Returns:
        Query: Query with search filter applied
    """
    if not search_term or not fields:
        return query
    
    # Prepare search term by stripping whitespace and adding wildcards
    search_term = search_term.strip()
    
    # Create empty list for search conditions
    search_conditions = []
    
    # For each field in fields list
    for field_name in fields:
        try:
            column = getattr(model, field_name)
            
            # If column is string type, add ilike condition to search conditions
            column_type = str(column.type).upper()
            if 'VARCHAR' in column_type or 'TEXT' in column_type or 'CHAR' in column_type:
                search_conditions.append(column.ilike(f"%{search_term}%"))
            # If column is numeric and search_term is numeric, add equality condition
            elif ('INT' in column_type or 'DECIMAL' in column_type or 'NUMERIC' in column_type) and search_term.isdigit():
                search_conditions.append(column == int(search_term))
            # If column is date and search_term is valid date format, add date search condition
            elif 'DATE' in column_type or 'TIMESTAMP' in column_type:
                try:
                    date_value = datetime.strptime(search_term, "%Y-%m-%d")
                    search_conditions.append(func.date(column) == date_value.date())
                except ValueError:
                    # Not a valid date format, skip this field
                    pass
        except AttributeError:
            # Skip fields that don't exist in the model
            continue
    
    # Combine all conditions with OR operator
    if search_conditions:
        combined_condition = or_(*search_conditions)
        # Apply combined condition to query
        return query.filter(combined_condition)
    
    # Return the original query if no search conditions were created
    return query


def build_query(
    model,
    site_ids: Optional[List[int]] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    search_term: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    sort_field: Optional[str] = None,
    sort_direction: Optional[SortDirection] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> Tuple[Query, int]:
    """
    Main function to build a complete query with all parameters.
    
    Args:
        model: The SQLAlchemy model class
        site_ids: List of site IDs for site-scoping
        filters: List of filter dictionaries
        search_term: Search term for text search
        search_fields: List of fields to search within
        sort_field: Field to sort by
        sort_direction: Sort direction
        page: Page number for pagination
        page_size: Page size for pagination
        
    Returns:
        Tuple[Query, int]: Tuple containing the final query and total count
    """
    # Initialize base query from model
    query = model.query
    
    # If site_ids provided, apply site filter using apply_site_filter
    if site_ids:
        query = apply_site_filter(query, model, site_ids)
    
    # If filters provided, apply all filters using apply_filters
    if filters:
        query = apply_filters(query, model, filters)
    
    # If search_term and search_fields provided, apply text search using apply_text_search
    if search_term and search_fields:
        query = apply_text_search(query, model, search_term, search_fields)
    
    # Create a count query before pagination to get total count
    count_query = query.with_entities(func.count())
    # Reset any ordering that might affect the count
    count_query = count_query.order_by(None)
    total_count = count_query.scalar()
    
    # If sort_field and sort_direction provided, apply sorting using apply_sorting
    if sort_field and sort_direction:
        query = apply_sorting(query, model, sort_field, sort_direction)
    
    # If page and page_size provided, apply pagination using apply_pagination
    if page is not None and page_size is not None:
        query = apply_pagination(query, page, page_size)
    
    # Return tuple of (final_query, total_count)
    return query, total_count


class QueryBuilder:
    """
    Class encapsulating query building functionality with session management.
    """
    
    def __init__(self, model, site_ids: List[int]):
        """
        Initialize a new QueryBuilder instance.
        
        Args:
            model: The SQLAlchemy model class
            site_ids: List of site IDs the user has access to
        """
        # Store model in self._model
        self._model = model
        
        # Validate and store site_ids in self._site_ids
        validate_site_context(site_ids)
        self._site_ids = site_ids
        
        # Initialize empty query from model class
        self._query = model.query
    
    def filter(self, field: str, operator: FilterOperator, value: Any) -> 'QueryBuilder':
        """
        Apply a filter to the query.
        
        Args:
            field: Field name to filter on
            operator: Filter operator (equals, contains, etc.)
            value: Value to filter by
            
        Returns:
            QueryBuilder: Self for method chaining
        """
        # Use apply_filter function to add filter to query
        self._query = apply_filter(self._query, self._model, field, operator, value)
        # Return self for method chaining
        return self
    
    def search(self, search_term: str, fields: List[str]) -> 'QueryBuilder':
        """
        Apply text search to the query.
        
        Args:
            search_term: The search term to look for
            fields: List of field names to search within
            
        Returns:
            QueryBuilder: Self for method chaining
        """
        # Use apply_text_search function to add search to query
        self._query = apply_text_search(self._query, self._model, search_term, fields)
        # Return self for method chaining
        return self
    
    def sort(self, field: str, direction: SortDirection) -> 'QueryBuilder':
        """
        Apply sorting to the query.
        
        Args:
            field: Field name to sort by
            direction: Sort direction
            
        Returns:
            QueryBuilder: Self for method chaining
        """
        # Use apply_sorting function to add sorting to query
        self._query = apply_sorting(self._query, self._model, field, direction)
        # Return self for method chaining
        return self
    
    def paginate(self, page: int, page_size: int) -> 'QueryBuilder':
        """
        Apply pagination to the query.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            QueryBuilder: Self for method chaining
        """
        # Use apply_pagination function to add pagination to query
        self._query = apply_pagination(self._query, page, page_size)
        # Return self for method chaining
        return self
    
    def apply_site_context(self) -> 'QueryBuilder':
        """
        Apply site context to the query for security.
        
        Returns:
            QueryBuilder: Self for method chaining
        """
        # Use apply_site_filter function with stored site_ids
        self._query = apply_site_filter(self._query, self._model, self._site_ids)
        # Return self for method chaining
        return self
    
    def count(self) -> int:
        """
        Execute count query to get total results.
        
        Returns:
            int: Total count of results
        """
        # Create copy of query
        count_query = self._query.with_entities(func.count())
        # Reset any grouping/having/ordering
        count_query = count_query.order_by(None)
        # Execute query and return scalar result
        return count_query.scalar()
    
    def all(self) -> List[Any]:
        """
        Execute query and return all results.
        
        Returns:
            List[Any]: List of result objects
        """
        # Execute query with all() method
        return self._query.all()
    
    def first(self) -> Optional[Any]:
        """
        Execute query and return first result.
        
        Returns:
            Optional[Any]: First result or None
        """
        # Execute query with first() method
        return self._query.first()
    
    def get_query(self) -> Query:
        """
        Get the underlying SQLAlchemy query object.
        
        Returns:
            Query: The current query object
        """
        # Return the stored _query object
        return self._query