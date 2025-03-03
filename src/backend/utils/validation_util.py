"""
Validation Utilities Module

This module provides comprehensive validation utilities for validating interaction data,
form inputs, and ensuring data integrity. It centralizes validation logic to enforce
consistent rules for all application data across the system.
"""

from typing import Any, Dict, Optional
from datetime import datetime

from ..utils.constants import (
    INTERACTION_TITLE_MIN_LENGTH,
    INTERACTION_TITLE_MAX_LENGTH,
    INTERACTION_DESCRIPTION_MIN_LENGTH,
    INTERACTION_DESCRIPTION_MAX_LENGTH,
    INTERACTION_LOCATION_MAX_LENGTH,
    INTERACTION_NOTES_MAX_LENGTH,
    INTERACTION_LEAD_MAX_LENGTH,
    ERROR_MESSAGES
)
from ..utils.enums import InteractionType, Timezone
from ..utils.error_util import ValidationError
from ..utils.string_util import is_empty, is_valid_length, validate_email
from ..utils.datetime_util import validate_datetime_range

# Define validation error types for consistent error handling
VALIDATION_ERROR_TYPES = {
    'required': 'required_field',
    'type': 'invalid_type',
    'length': 'invalid_length',
    'format': 'invalid_format',
    'range': 'invalid_range',
    'timezone': 'invalid_timezone',
    'interaction_type': 'invalid_interaction_type'
}


def validate_required(value: Any, field_name: str) -> bool:
    """
    Validates that a required field has a value.
    
    Args:
        value: The value to check
        field_name: Name of the field being validated
        
    Returns:
        True if field has value, False otherwise
    """
    # None values are considered empty
    if value is None:
        return False
    
    # For strings, check if the string is empty
    if isinstance(value, str):
        return not is_empty(value)
    
    # For other types, the presence of a value is sufficient
    return True


def validate_string_length(value: str, field_name: str, min_length: int, max_length: int) -> bool:
    """
    Validates that a string field has a length within specified bounds.
    
    Args:
        value: The string value to check
        field_name: Name of the field being validated
        min_length: Minimum allowed length (inclusive)
        max_length: Maximum allowed length (inclusive)
        
    Returns:
        True if string length is valid, False otherwise
    """
    # Skip validation for None values
    if value is None:
        return True
    
    return is_valid_length(value, min_length, max_length)


def validate_interaction_type(value: str, field_name: str) -> bool:
    """
    Validates that an interaction type is one of the allowed types.
    
    Args:
        value: The type value to check
        field_name: Name of the field being validated
        
    Returns:
        True if interaction type is valid, False otherwise
    """
    # Skip validation for None values
    if value is None:
        return True
    
    return InteractionType.is_valid(value)


def validate_timezone(value: str, field_name: str) -> bool:
    """
    Validates that a timezone is a valid IANA timezone identifier.
    
    Args:
        value: The timezone value to check
        field_name: Name of the field being validated
        
    Returns:
        True if timezone is valid, False otherwise
    """
    # Skip validation for None values
    if value is None:
        return True
    
    return Timezone.is_valid(value)


def validate_datetime_order(
    start_datetime: datetime,
    end_datetime: datetime,
    start_field_name: str,
    end_field_name: str
) -> bool:
    """
    Validates that end datetime is after start datetime.
    
    Args:
        start_datetime: The start datetime value
        end_datetime: The end datetime value
        start_field_name: Name of the start datetime field
        end_field_name: Name of the end datetime field
        
    Returns:
        True if datetime order is valid, False otherwise
    """
    # Skip validation if either datetime is None
    if start_datetime is None or end_datetime is None:
        return True
    
    return validate_datetime_range(start_datetime, end_datetime)


def validate_email_format(value: str, field_name: str) -> bool:
    """
    Validates that an email address has a valid format.
    
    Args:
        value: The email value to check
        field_name: Name of the field being validated
        
    Returns:
        True if email format is valid, False otherwise
    """
    # Skip validation for None values
    if value is None:
        return True
    
    return validate_email(value)


def validate_interaction_fields(interaction_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Validates all fields of an interaction according to business rules.
    
    Args:
        interaction_data: Dictionary containing the interaction data
        
    Returns:
        Dictionary with validation errors by field, empty if valid
    """
    errors = {}
    
    # Validate required fields
    required_fields = [
        'title', 'type', 'lead', 'start_datetime', 'end_datetime', 'timezone', 'description'
    ]
    
    for field in required_fields:
        if not validate_required(interaction_data.get(field), field):
            errors[field] = VALIDATION_ERROR_TYPES['required']
    
    # Validate string lengths
    title = interaction_data.get('title')
    if title is not None and not validate_string_length(
        title,
        'title',
        INTERACTION_TITLE_MIN_LENGTH,
        INTERACTION_TITLE_MAX_LENGTH
    ):
        errors['title'] = VALIDATION_ERROR_TYPES['length']
    
    description = interaction_data.get('description')
    if description is not None and not validate_string_length(
        description,
        'description',
        INTERACTION_DESCRIPTION_MIN_LENGTH,
        INTERACTION_DESCRIPTION_MAX_LENGTH
    ):
        errors['description'] = VALIDATION_ERROR_TYPES['length']
    
    location = interaction_data.get('location')
    if location is not None and not validate_string_length(
        location,
        'location',
        0,
        INTERACTION_LOCATION_MAX_LENGTH
    ):
        errors['location'] = VALIDATION_ERROR_TYPES['length']
    
    notes = interaction_data.get('notes')
    if notes is not None and not validate_string_length(
        notes,
        'notes',
        0,
        INTERACTION_NOTES_MAX_LENGTH
    ):
        errors['notes'] = VALIDATION_ERROR_TYPES['length']
    
    lead = interaction_data.get('lead')
    if lead is not None and not validate_string_length(
        lead,
        'lead',
        0,
        INTERACTION_LEAD_MAX_LENGTH
    ):
        errors['lead'] = VALIDATION_ERROR_TYPES['length']
    
    # Validate interaction type
    interaction_type = interaction_data.get('type')
    if interaction_type is not None and not validate_interaction_type(
        interaction_type,
        'type'
    ):
        errors['type'] = VALIDATION_ERROR_TYPES['interaction_type']
    
    # Validate timezone
    timezone = interaction_data.get('timezone')
    if timezone is not None and not validate_timezone(
        timezone,
        'timezone'
    ):
        errors['timezone'] = VALIDATION_ERROR_TYPES['timezone']
    
    # Validate datetime order (start before end)
    start_datetime = interaction_data.get('start_datetime')
    end_datetime = interaction_data.get('end_datetime')
    
    if start_datetime is not None and end_datetime is not None:
        if not validate_datetime_order(
            start_datetime,
            end_datetime,
            'start_datetime',
            'end_datetime'
        ):
            errors['end_datetime'] = VALIDATION_ERROR_TYPES['range']
    
    return errors


def get_validation_error_message(error_type: str, params: Dict[str, Any] = None) -> str:
    """
    Gets the appropriate error message for a validation error type.
    
    Args:
        error_type: Type of validation error
        params: Parameters to format in the error message
        
    Returns:
        Formatted error message
    """
    if params is None:
        params = {}
    
    # Get the error message template from ERROR_MESSAGES
    error_messages = ERROR_MESSAGES.get('validation', {})
    message_template = error_messages.get(error_type, "Validation error")
    
    # Format the template with provided parameters
    try:
        return message_template.format(**params)
    except KeyError:
        return message_template


def raise_validation_error(validation_errors: Dict[str, str]) -> None:
    """
    Raises a ValidationError with formatted error messages.
    
    Args:
        validation_errors: Dictionary with field-specific validation errors
        
    Returns:
        None, raises ValidationError
    """
    if not validation_errors:
        return
    
    # Format detailed error messages
    formatted_errors = {}
    for field, error_type in validation_errors.items():
        # Set params based on field and error type
        params = {}
        if error_type == VALIDATION_ERROR_TYPES['length']:
            if field == 'title':
                params = {'min': INTERACTION_TITLE_MIN_LENGTH, 'max': INTERACTION_TITLE_MAX_LENGTH}
            elif field == 'description':
                params = {'min': INTERACTION_DESCRIPTION_MIN_LENGTH, 'max': INTERACTION_DESCRIPTION_MAX_LENGTH}
            elif field == 'location':
                params = {'min': 0, 'max': INTERACTION_LOCATION_MAX_LENGTH}
            elif field == 'notes':
                params = {'min': 0, 'max': INTERACTION_NOTES_MAX_LENGTH}
            elif field == 'lead':
                params = {'min': 0, 'max': INTERACTION_LEAD_MAX_LENGTH}
        
        formatted_errors[field] = get_validation_error_message(error_type, params)
    
    # Create error summary
    error_fields = ", ".join(validation_errors.keys())
    summary = f"Validation failed for fields: {error_fields}"
    
    # Raise ValidationError with detailed information
    raise ValidationError(summary, formatted_errors)


class InteractionValidator:
    """
    Class for validating interaction data with comprehensive rules.
    """
    
    def __init__(self):
        """
        Initializes the validator.
        """
        self.errors = {}
    
    def validate(self, interaction_data: Dict[str, Any]) -> bool:
        """
        Validates interaction data and raises ValidationError if invalid.
        
        Args:
            interaction_data: Dictionary containing interaction data
            
        Returns:
            True if valid, raises exception otherwise
        """
        # Validate using the standalone function
        validation_errors = validate_interaction_fields(interaction_data)
        
        # Raise error if validation failed
        if validation_errors:
            raise_validation_error(validation_errors)
        
        # Return True if validation passed
        return True
    
    def validate_partial(self, partial_data: Dict[str, Any], current_data: Dict[str, Any]) -> bool:
        """
        Validates only provided fields in partial update data.
        
        Args:
            partial_data: Dictionary containing fields to update
            current_data: Dictionary containing current interaction data
            
        Returns:
            True if valid, raises exception otherwise
        """
        # Create a complete interaction data by merging partial data with current data
        complete_data = {**current_data, **partial_data}
        
        # Validate fields that are being updated
        validation_errors = {}
        
        # Validate required fields that are in partial_data
        required_fields = [
            'title', 'type', 'lead', 'start_datetime', 'end_datetime', 'timezone', 'description'
        ]
        
        for field in required_fields:
            if field in partial_data and not validate_required(partial_data.get(field), field):
                validation_errors[field] = VALIDATION_ERROR_TYPES['required']
        
        # Validate string lengths for fields in partial_data
        if 'title' in partial_data and partial_data['title'] is not None:
            if not validate_string_length(
                partial_data['title'],
                'title',
                INTERACTION_TITLE_MIN_LENGTH,
                INTERACTION_TITLE_MAX_LENGTH
            ):
                validation_errors['title'] = VALIDATION_ERROR_TYPES['length']
        
        if 'description' in partial_data and partial_data['description'] is not None:
            if not validate_string_length(
                partial_data['description'],
                'description',
                INTERACTION_DESCRIPTION_MIN_LENGTH,
                INTERACTION_DESCRIPTION_MAX_LENGTH
            ):
                validation_errors['description'] = VALIDATION_ERROR_TYPES['length']
        
        if 'location' in partial_data and partial_data['location'] is not None:
            if not validate_string_length(
                partial_data['location'],
                'location',
                0,
                INTERACTION_LOCATION_MAX_LENGTH
            ):
                validation_errors['location'] = VALIDATION_ERROR_TYPES['length']
        
        if 'notes' in partial_data and partial_data['notes'] is not None:
            if not validate_string_length(
                partial_data['notes'],
                'notes',
                0,
                INTERACTION_NOTES_MAX_LENGTH
            ):
                validation_errors['notes'] = VALIDATION_ERROR_TYPES['length']
        
        if 'lead' in partial_data and partial_data['lead'] is not None:
            if not validate_string_length(
                partial_data['lead'],
                'lead',
                0,
                INTERACTION_LEAD_MAX_LENGTH
            ):
                validation_errors['lead'] = VALIDATION_ERROR_TYPES['length']
        
        # Validate interaction type if in partial_data
        if 'type' in partial_data:
            if not validate_interaction_type(
                partial_data.get('type'),
                'type'
            ):
                validation_errors['type'] = VALIDATION_ERROR_TYPES['interaction_type']
        
        # Validate timezone if in partial_data
        if 'timezone' in partial_data:
            if not validate_timezone(
                partial_data.get('timezone'),
                'timezone'
            ):
                validation_errors['timezone'] = VALIDATION_ERROR_TYPES['timezone']
        
        # Validate datetime order if either start_datetime or end_datetime is in partial_data
        if 'start_datetime' in partial_data or 'end_datetime' in partial_data:
            start_datetime = complete_data.get('start_datetime')
            end_datetime = complete_data.get('end_datetime')
            
            if start_datetime is not None and end_datetime is not None:
                if not validate_datetime_order(
                    start_datetime,
                    end_datetime,
                    'start_datetime',
                    'end_datetime'
                ):
                    validation_errors['end_datetime'] = VALIDATION_ERROR_TYPES['range']
        
        # Raise error if validation failed
        if validation_errors:
            raise_validation_error(validation_errors)
        
        # Return True if validation passed
        return True