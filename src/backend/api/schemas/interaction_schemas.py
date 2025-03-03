"""
Schemas module for validating and serializing Interaction data.

This module defines Marshmallow schemas for handling Interaction data formats
in API requests and responses. The schemas enforce validation rules
specific to the Interaction entity, such as title length, required fields,
datetime formatting, and timezone validation.
"""

from marshmallow import Schema, fields, validates, validates_schema, ValidationError, EXCLUDE
from datetime import datetime
from typing import Dict, Any, Optional, List

from ...utils.enums import InteractionType, Timezone
from ...utils.datetime_util import validate_datetime_range


def validate_title_length(title: str) -> bool:
    """
    Custom validator to check title length requirements.
    
    Args:
        title: The interaction title to validate
        
    Returns:
        bool: True if valid, raises ValidationError otherwise
    """
    if not (5 <= len(title) <= 100):
        raise ValidationError("Title must be between 5 and 100 characters.")
    return True


def validate_date_range(data: Dict[str, Any]) -> bool:
    """
    Validates that end_datetime is after start_datetime.
    
    Args:
        data: Dictionary containing start_datetime and end_datetime
        
    Returns:
        bool: True if valid, raises ValidationError otherwise
    """
    start_datetime = data.get('start_datetime')
    end_datetime = data.get('end_datetime')
    
    # Only validate if both fields are present
    if start_datetime and end_datetime:
        if not validate_datetime_range(start_datetime, end_datetime):
            raise ValidationError("End date/time must be after start date/time.")
    
    return True


class InteractionPaginationSchema(Schema):
    """
    Schema for pagination metadata used in interaction list responses.
    """
    page = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    total = fields.Integer(required=True)
    pages = fields.Integer(required=True)
    
    class Meta:
        unknown = EXCLUDE


class InteractionBaseSchema(Schema):
    """
    Base schema defining common fields and validation rules for interactions.
    """
    class Meta:
        unknown = EXCLUDE
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        """
        Validates that end datetime is after start datetime.
        
        Args:
            data: Dictionary containing start_datetime and end_datetime
            
        Returns:
            dict: Validated data dictionary
        """
        validate_date_range(data)
        return data


class InteractionCreateSchema(InteractionBaseSchema):
    """
    Schema for validating interaction creation requests.
    """
    site_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate_title_length)
    type = fields.String(required=True)
    lead = fields.String(required=True)
    start_datetime = fields.DateTime(required=True)
    end_datetime = fields.DateTime(required=True)
    timezone = fields.String(required=True)
    location = fields.String(allow_none=True)
    description = fields.String(required=True)
    notes = fields.String(allow_none=True)
    
    @validates('type')
    def validate_type(self, value):
        """
        Validates that type is a valid InteractionType.
        
        Args:
            value: The interaction type to validate
            
        Returns:
            str: Validated type value
        """
        if not InteractionType.is_valid(value):
            raise ValidationError(f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}")
        return value
        
    @validates('timezone')
    def validate_timezone(self, value):
        """
        Validates that timezone is a valid IANA timezone.
        
        Args:
            value: The timezone to validate
            
        Returns:
            str: Validated timezone value
        """
        if not Timezone.is_valid(value):
            raise ValidationError("Invalid timezone. Please provide a valid IANA timezone identifier.")
        return value


class InteractionUpdateSchema(InteractionBaseSchema):
    """
    Schema for validating interaction update requests.
    """
    title = fields.String(validate=validate_title_length)
    type = fields.String()
    lead = fields.String()
    start_datetime = fields.DateTime()
    end_datetime = fields.DateTime()
    timezone = fields.String()
    location = fields.String(allow_none=True)
    description = fields.String()
    notes = fields.String(allow_none=True)
    
    @validates('type')
    def validate_type(self, value):
        """
        Validates that type is a valid InteractionType if provided.
        
        Args:
            value: The interaction type to validate
            
        Returns:
            str: Validated type value
        """
        if value is None:
            return None
            
        if not InteractionType.is_valid(value):
            raise ValidationError(f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}")
        return value
        
    @validates('timezone')
    def validate_timezone(self, value):
        """
        Validates that timezone is a valid IANA timezone if provided.
        
        Args:
            value: The timezone to validate
            
        Returns:
            str: Validated timezone value
        """
        if value is None:
            return None
            
        if not Timezone.is_valid(value):
            raise ValidationError("Invalid timezone. Please provide a valid IANA timezone identifier.")
        return value


class InteractionResponseSchema(Schema):
    """
    Schema for serializing interaction data in API responses.
    """
    id = fields.Integer()
    site_id = fields.Integer()
    title = fields.String()
    type = fields.String()
    lead = fields.String()
    start_datetime = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    end_datetime = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    timezone = fields.String()
    location = fields.String()
    description = fields.String()
    notes = fields.String()
    created_by = fields.Integer()
    created_at = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    
    class Meta:
        unknown = EXCLUDE


class InteractionDetailSchema(Schema):
    """
    Schema for serializing detailed interaction data with additional computed fields.
    """
    id = fields.Integer()
    site_id = fields.Integer()
    title = fields.String()
    type = fields.String()
    lead = fields.String()
    start_datetime = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    end_datetime = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    timezone = fields.String()
    location = fields.String()
    description = fields.String()
    notes = fields.String()
    created_by = fields.Integer()
    created_at = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = fields.DateTime(format="%Y-%m-%dT%H:%M:%SZ")
    duration_minutes = fields.Integer()
    
    class Meta:
        unknown = EXCLUDE
    
    def get_duration_minutes(self, obj):
        """
        Calculates interaction duration in minutes.
        
        Args:
            obj: Interaction object with start_datetime and end_datetime
            
        Returns:
            int: Duration in minutes
        """
        # Handle both object and dictionary access patterns
        if isinstance(obj, dict):
            start = obj.get('start_datetime')
            end = obj.get('end_datetime')
        else:
            start = getattr(obj, 'start_datetime', None)
            end = getattr(obj, 'end_datetime', None)
        
        if start and end:
            delta = end - start
            return int(delta.total_seconds() / 60)
        return 0


class InteractionListSchema(Schema):
    """
    Schema for serializing paginated lists of interactions.
    """
    interactions = fields.List(fields.Nested(InteractionResponseSchema))
    pagination = fields.Nested(InteractionPaginationSchema)
    
    class Meta:
        unknown = EXCLUDE