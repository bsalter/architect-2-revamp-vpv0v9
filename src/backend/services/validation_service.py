"""
Validation Service for the Interaction Management System.

This module provides a centralized service for validating interaction data according to
business rules and validation requirements. It handles complex validation logic including
interaction field validation, date/time validation with timezone support, and cross-field
validation rules.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from marshmallow import ValidationError as MarshmallowValidationError

from ..utils.constants import (
    INTERACTION_TITLE_MIN_LENGTH,
    INTERACTION_TITLE_MAX_LENGTH,
    INTERACTION_DESCRIPTION_MIN_LENGTH,
    INTERACTION_LEAD_MAX_LENGTH,
    INTERACTION_LOCATION_MAX_LENGTH,
    INTERACTION_NOTES_MAX_LENGTH,
    ERROR_MESSAGES
)
from ..utils.enums import InteractionType, Timezone
from ..utils.error_util import ValidationError
from ..utils.string_util import is_empty, is_valid_length
from ..utils.datetime_util import validate_datetime_range
from ..api.schemas.interaction_schemas import InteractionCreateSchema, InteractionUpdateSchema

# Configure logger
logger = logging.getLogger(__name__)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, str]:
    """
    Validates that all required interaction fields are present and not empty.
    
    Args:
        data: Dictionary containing form data
        required_fields: List of field names that are required
        
    Returns:
        Dictionary of errors by field, empty if all valid
    """
    errors = {}
    
    for field in required_fields:
        # Check if field exists and is not None
        if field not in data or data[field] is None:
            errors[field] = ERROR_MESSAGES["validation"]["required_field"]
        # For string fields, check if they're empty
        elif isinstance(data[field], str) and is_empty(data[field]):
            errors[field] = ERROR_MESSAGES["validation"]["required_field"]
    
    return errors


def validate_string_lengths(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Validates that string fields are within their allowed length constraints.
    
    Args:
        data: Dictionary containing form data
        
    Returns:
        Dictionary of errors by field, empty if all valid
    """
    errors = {}
    
    # Validate title length if present
    if 'title' in data and data['title'] is not None:
        if not is_valid_length(data['title'], INTERACTION_TITLE_MIN_LENGTH, INTERACTION_TITLE_MAX_LENGTH):
            errors['title'] = ERROR_MESSAGES["validation"]["invalid_length"].format(
                min=INTERACTION_TITLE_MIN_LENGTH, 
                max=INTERACTION_TITLE_MAX_LENGTH
            )
    
    # Validate description length if present
    if 'description' in data and data['description'] is not None:
        if not is_valid_length(data['description'], INTERACTION_DESCRIPTION_MIN_LENGTH, float('inf')):
            errors['description'] = ERROR_MESSAGES["validation"]["invalid_length"].format(
                min=INTERACTION_DESCRIPTION_MIN_LENGTH, 
                max="no maximum"
            )
    
    # Validate lead length if present
    if 'lead' in data and data['lead'] is not None:
        if not is_valid_length(data['lead'], 1, INTERACTION_LEAD_MAX_LENGTH):
            errors['lead'] = ERROR_MESSAGES["validation"]["invalid_length"].format(
                min=1, 
                max=INTERACTION_LEAD_MAX_LENGTH
            )
    
    # Validate location length if present (location is optional)
    if 'location' in data and data['location'] is not None and data['location'] != '':
        if not is_valid_length(data['location'], 0, INTERACTION_LOCATION_MAX_LENGTH):
            errors['location'] = ERROR_MESSAGES["validation"]["invalid_length"].format(
                min=0, 
                max=INTERACTION_LOCATION_MAX_LENGTH
            )
    
    # Validate notes length if present (notes are optional)
    if 'notes' in data and data['notes'] is not None and data['notes'] != '':
        if not is_valid_length(data['notes'], 0, INTERACTION_NOTES_MAX_LENGTH):
            errors['notes'] = ERROR_MESSAGES["validation"]["invalid_length"].format(
                min=0, 
                max=INTERACTION_NOTES_MAX_LENGTH
            )
    
    return errors


def validate_interaction_type(type_value: str) -> Dict[str, str]:
    """
    Validates that the interaction type is one of the allowed types.
    
    Args:
        type_value: Type value to check
        
    Returns:
        Dictionary with an error if invalid, empty if valid
    """
    if type_value is None:
        return {}
    
    if not InteractionType.is_valid(type_value):
        return {"type": ERROR_MESSAGES["validation"]["invalid_interaction_type"]}
    
    return {}


def validate_timezone(timezone_value: str) -> Dict[str, str]:
    """
    Validates that the timezone is a valid IANA timezone identifier.
    
    Args:
        timezone_value: Timezone value to check
        
    Returns:
        Dictionary with an error if invalid, empty if valid
    """
    if timezone_value is None:
        return {}
    
    if not Timezone.is_valid(timezone_value):
        return {"timezone": ERROR_MESSAGES["validation"]["invalid_timezone"]}
    
    return {}


def validate_datetime_order(start_datetime: datetime, end_datetime: datetime) -> Dict[str, str]:
    """
    Validates that end_datetime is after start_datetime.
    
    Args:
        start_datetime: Start datetime
        end_datetime: End datetime
        
    Returns:
        Dictionary with error if invalid, empty if valid
    """
    if start_datetime is None or end_datetime is None:
        return {}
    
    if not validate_datetime_range(start_datetime, end_datetime):
        return {
            "start_datetime": ERROR_MESSAGES["validation"]["invalid_range"],
            "end_datetime": ERROR_MESSAGES["validation"]["invalid_range"]
        }
    
    return {}


def format_validation_errors(errors: Dict[str, str]) -> Dict[str, str]:
    """
    Formats validation errors into a standardized structure.
    
    Args:
        errors: Dictionary of errors by field
        
    Returns:
        Formatted error dictionary with messages
    """
    formatted_errors = {}
    
    for field, message in errors.items():
        formatted_errors[field] = message
    
    return formatted_errors


def handle_schema_validation_error(error: Exception) -> Dict[str, str]:
    """
    Handles marshmallow ValidationError by formatting the error messages.
    
    Args:
        error: Marshmallow ValidationError instance
        
    Returns:
        Formatted error dictionary with messages
    """
    if isinstance(error, MarshmallowValidationError):
        return {field: "; ".join(messages) if isinstance(messages, list) else str(messages) 
                for field, messages in error.messages.items()}
    return {"general": str(error)}


class InteractionValidator:
    """
    Provides comprehensive validation for interaction data with methods
    for validating new and updated interactions.
    """
    
    def __init__(self):
        """
        Initializes a new InteractionValidator instance.
        """
        self.required_fields = ["title", "type", "lead", "start_datetime", "end_datetime", "timezone", "description"]
        logger.info("InteractionValidator initialized")
    
    def validate_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates data for creating a new interaction using both schema
        and business rule validation.
        
        Args:
            data: Dictionary containing form data
            
        Returns:
            Validated and sanitized data if valid
            
        Raises:
            ValidationError: If validation fails
        """
        errors = {}
        
        try:
            # Initial schema validation
            validated_data = InteractionCreateSchema().load(data)
            
            # Additional business rule validations
            business_errors = self.validate_business_rules(validated_data)
            
            if business_errors:
                errors.update(business_errors)
            
            if errors:
                raise ValidationError("Validation failed", details=format_validation_errors(errors))
                
            return validated_data
            
        except MarshmallowValidationError as e:
            # Handle schema validation errors
            schema_errors = handle_schema_validation_error(e)
            errors.update(schema_errors)
            
            raise ValidationError("Validation failed", details=format_validation_errors(errors))
    
    def validate_update(self, data: Dict[str, Any], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates data for updating an existing interaction, respecting partial updates.
        
        Args:
            data: Dictionary containing update data (can be partial)
            current_data: Current state of the interaction
            
        Returns:
            Validated and sanitized data if valid
            
        Raises:
            ValidationError: If validation fails
        """
        errors = {}
        
        try:
            # Schema validation for updates
            validated_data = InteractionUpdateSchema().load(data)
            
            # Merge with current data to get the full state after update
            merged_data = {**current_data, **validated_data}
            
            # Apply business rule validations to the merged data
            business_errors = self.validate_business_rules(merged_data)
            
            if business_errors:
                errors.update(business_errors)
            
            if errors:
                raise ValidationError("Validation failed", details=format_validation_errors(errors))
                
            # Return only the validated update data, not the merged data
            return validated_data
            
        except MarshmallowValidationError as e:
            # Handle schema validation errors
            schema_errors = handle_schema_validation_error(e)
            errors.update(schema_errors)
            
            raise ValidationError("Validation failed", details=format_validation_errors(errors))
    
    def validate_business_rules(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Performs business rule validations not covered by schema validation.
        
        Args:
            data: Dictionary containing interaction data
            
        Returns:
            Dictionary of validation errors by field
        """
        errors = {}
        
        # Validate string lengths
        string_errors = validate_string_lengths(data)
        if string_errors:
            errors.update(string_errors)
        
        # Validate datetime order
        if 'start_datetime' in data and 'end_datetime' in data:
            datetime_errors = validate_datetime_order(data['start_datetime'], data['end_datetime'])
            if datetime_errors:
                errors.update(datetime_errors)
        
        return errors