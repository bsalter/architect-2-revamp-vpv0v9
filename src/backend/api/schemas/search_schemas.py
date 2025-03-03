"""
Search schema module for the Interaction Management System.

This module defines Marshmallow schemas for validating and serializing search-related
requests and responses. It provides structured validation for search criteria, filters,
sorting, and pagination parameters while ensuring proper formatting of search results.
"""

from marshmallow import Schema, fields, validates, validates_schema, ValidationError, EXCLUDE
from datetime import datetime
from typing import Dict, Any, List, Optional

from .interaction_schemas import InteractionResponseSchema, InteractionPaginationSchema
from ...utils.enums import InteractionType, SortDirection
from ...utils.datetime_util import validate_datetime_range

# Constants for pagination defaults and limits
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Valid filter operators for search operations
FILTER_OPERATORS = ['eq', 'neq', 'gt', 'lt', 'gte', 'lte', 'contains', 'in']

def validate_filter_operator(operator: str) -> bool:
    """
    Validates that the filter operator is in the allowed operators list.
    
    Args:
        operator: The operator to validate
        
    Returns:
        bool: Returns True if valid, raises ValidationError otherwise
    """
    if operator not in FILTER_OPERATORS:
        raise ValidationError(f"Invalid filter operator. Must be one of: {', '.join(FILTER_OPERATORS)}")
    return True

def validate_sort_fields(data: Dict) -> Dict:
    """
    Validates that sort fields exist in the interaction model.
    
    Args:
        data: Dictionary containing sort field
        
    Returns:
        dict: Returns validated data if valid
    """
    field = data.get('field')
    # Using fields that match the Interaction model structure
    allowed_fields = [
        'title', 'type', 'lead', 'start_datetime', 'end_datetime', 
        'timezone', 'location', 'description', 'notes', 
        'created_at', 'updated_at'
    ]
    
    if field and field not in allowed_fields:
        raise ValidationError(f"Invalid sort field. Must be one of: {', '.join(allowed_fields)}")
    return data

class FilterSchema(Schema):
    """
    Schema for validating search filter criteria.
    """
    field = fields.String(required=True)
    operator = fields.String(required=True)
    value = fields.Raw(required=True)
    
    class Meta:
        unknown = EXCLUDE
    
    @validates('operator')
    def validate_operator(self, value: str) -> str:
        """
        Validates that the operator is allowed.
        
        Args:
            value: The operator to validate
            
        Returns:
            str: Returns validated operator
        """
        validate_filter_operator(value)
        return value

class SortSchema(Schema):
    """
    Schema for validating sort criteria in search requests.
    """
    field = fields.String(required=True)
    direction = fields.String(default=SortDirection.ASC.value)
    
    class Meta:
        unknown = EXCLUDE
    
    @validates('direction')
    def validate_direction(self, value: str) -> str:
        """
        Validates sort direction is either ASC or DESC.
        
        Args:
            value: The sort direction to validate
            
        Returns:
            str: Returns validated direction
        """
        if value is None:
            return SortDirection.ASC.value
            
        value = value.upper()
        if not SortDirection.is_valid(value):
            raise ValidationError(f"Invalid sort direction. Must be one of: {', '.join(SortDirection.get_values())}")
        return value
    
    @validates('field')
    def validate_field(self, value: str) -> str:
        """
        Validates that the sort field exists in the interaction model.
        
        Args:
            value: The field to validate
            
        Returns:
            str: Returns validated field
        """
        validate_sort_fields({'field': value})
        return value

class PaginationSchema(Schema):
    """
    Schema for validating pagination parameters.
    """
    page = fields.Integer(default=1, validate=lambda n: n >= 1)
    page_size = fields.Integer(default=DEFAULT_PAGE_SIZE)
    
    class Meta:
        unknown = EXCLUDE
    
    @validates('page_size')
    def validate_page_size(self, value: int) -> int:
        """
        Validates page size is within allowed limits.
        
        Args:
            value: The page size to validate
            
        Returns:
            int: Returns validated page size
        """
        if value is None:
            return DEFAULT_PAGE_SIZE
            
        if value < 1:
            return DEFAULT_PAGE_SIZE
            
        if value > MAX_PAGE_SIZE:
            return MAX_PAGE_SIZE
            
        return value

class DateRangeSchema(Schema):
    """
    Schema for validating date range parameters in search.
    """
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    
    class Meta:
        unknown = EXCLUDE
    
    @validates_schema
    def validate_date_range(self, data: Dict, **kwargs) -> Dict:
        """
        Validates that end_date is after start_date.
        
        Args:
            data: Dictionary containing start_date and end_date
            
        Returns:
            dict: Returns validated data
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if not validate_datetime_range(start_date, end_date):
                raise ValidationError("End date must be after start date.")
        
        return data

class SearchSchema(Schema):
    """
    Schema for validating basic search requests.
    """
    query = fields.String(required=False)
    pagination = fields.Nested(PaginationSchema, missing=lambda: {})
    filters = fields.List(fields.Nested(FilterSchema), required=False)
    
    class Meta:
        unknown = EXCLUDE

class AdvancedSearchSchema(Schema):
    """
    Schema for validating advanced search requests with complex criteria.
    """
    filters = fields.List(fields.Nested(FilterSchema), required=False)
    sort = fields.Nested(SortSchema, required=False)
    pagination = fields.Nested(PaginationSchema, missing=lambda: {})
    
    class Meta:
        unknown = EXCLUDE

class SearchResultsSchema(Schema):
    """
    Schema for serializing search results with interactions and pagination.
    """
    results = fields.List(fields.Nested(InteractionResponseSchema))
    pagination = fields.Nested(InteractionPaginationSchema)
    
    class Meta:
        unknown = EXCLUDE