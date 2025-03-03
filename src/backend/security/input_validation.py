"""
Security-focused input validation module for the Interaction Management System.

This module provides comprehensive validation and sanitization functions to protect 
against common security vulnerabilities like XSS, SQL injection, and other 
malicious input. All user-provided data should be processed through these 
functions before being used in database queries, rendered in templates, or 
returned in API responses.

The module implements defense-in-depth strategies for input validation as part of
the system's overall security architecture, with specialized functions for different
types of inputs and validation requirements.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import bleach  # version 6.0.0

# Internal imports
from ..utils.string_util import (
    sanitize_html,
    escape_html,
    strip_html,
    sanitize_search_term
)
from ..utils.validation_util import (
    validate_required,
    validate_string_length,
    validate_interaction_type,
    validate_timezone,
    validate_datetime_order
)
from ..utils.error_util import ValidationError
from ..utils.constants import (
    ALLOWED_SEARCH_FIELDS,
    INTERACTION_TITLE_MIN_LENGTH,
    INTERACTION_TITLE_MAX_LENGTH,
    INTERACTION_DESCRIPTION_MIN_LENGTH,
    INTERACTION_DESCRIPTION_MAX_LENGTH,
    INTERACTION_NOTES_MAX_LENGTH,
    INTERACTION_LEAD_MAX_LENGTH,
    INTERACTION_LOCATION_MAX_LENGTH,
    SANITIZE_PATTERN
)
from ..utils.datetime_util import validate_datetime_range
from ..logging.structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)

# Global constants
HTML_ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
HTML_ALLOWED_ATTRIBUTES = {'*': ['class']}
SQL_INJECTION_PATTERNS = [r"--", r"\/\*", r";\\s*$", r";", r"UNION", r"SELECT", r"DROP", r"DELETE", r"UPDATE", r"INSERT", r"EXEC"]


def sanitize_input(value: str) -> str:
    """
    Generic function to sanitize user input by removing potentially dangerous characters.
    
    Args:
        value: The input string to sanitize
        
    Returns:
        Sanitized input string with dangerous characters removed
    """
    if value is None or value == '':
        return value
    
    # Ensure value is a string
    if not isinstance(value, str):
        value = str(value)
    
    # Remove potentially dangerous characters using the pattern from constants
    sanitized = re.sub(SANITIZE_PATTERN, '', value)
    
    return sanitized


def sanitize_html_content(html_content: str, allowed_tags: List[str] = None, 
                         allowed_attributes: Dict[str, List[str]] = None) -> str:
    """
    Sanitizes HTML content using bleach to prevent XSS attacks while preserving allowed tags.
    
    Args:
        html_content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags, defaults to HTML_ALLOWED_TAGS
        allowed_attributes: Dict of allowed HTML attributes, defaults to HTML_ALLOWED_ATTRIBUTES
        
    Returns:
        Sanitized HTML content safe for storage and display
    """
    if html_content is None or html_content == '':
        return html_content
    
    if allowed_tags is None:
        allowed_tags = HTML_ALLOWED_TAGS
    
    if allowed_attributes is None:
        allowed_attributes = HTML_ALLOWED_ATTRIBUTES
    
    sanitized = sanitize_html(
        html_content, 
        allowed_tags=allowed_tags, 
        allowed_attributes=allowed_attributes
    )
    
    # Log sanitization activity
    logger.info(
        "HTML content sanitized", 
        extra={
            "content_length": len(html_content),
            "sanitized_length": len(sanitized) if sanitized else 0,
            "allowed_tags": allowed_tags
        }
    )
    
    return sanitized


def strip_all_html(html_content: str) -> str:
    """
    Completely strips all HTML tags from content, leaving only plain text.
    
    Args:
        html_content: The HTML content to strip
        
    Returns:
        Plain text with all HTML tags removed
    """
    if html_content is None or html_content == '':
        return html_content
    
    return strip_html(html_content)


def validate_json_payload(json_str: str, required_fields: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Validates that the provided payload is valid JSON and matches expected structure.
    
    Args:
        json_str: JSON string to validate
        required_fields: Dictionary of field names and their expected types
        
    Returns:
        Parsed JSON data if valid
        
    Raises:
        ValidationError: If JSON is invalid or missing required fields
    """
    if json_str is None or json_str == '':
        raise ValidationError("Empty JSON payload provided")
    
    try:
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON format", extra={"error": str(e)})
        raise ValidationError(f"Invalid JSON format: {str(e)}")
    
    # Validate required fields if specified
    if required_fields:
        missing_fields = []
        type_errors = []
        
        for field, expected_type in required_fields.items():
            if field not in data:
                missing_fields.append(field)
            elif expected_type and not isinstance(data[field], expected_type):
                type_errors.append(f"{field} (expected {expected_type.__name__})")
        
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        if type_errors:
            raise ValidationError(f"Invalid field types: {', '.join(type_errors)}")
    
    return data


def detect_sql_injection(value: str) -> bool:
    """
    Checks input for potential SQL injection patterns.
    
    Args:
        value: Input string to check
        
    Returns:
        True if suspicious patterns are detected, False otherwise
    """
    if value is None or value == '':
        return False
    
    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value)
    
    # Convert to uppercase for case-insensitive matching
    value_upper = value.upper()
    
    # Check for common SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_upper, re.IGNORECASE):
            logger.warning(
                "Potential SQL injection attempt detected", 
                extra={
                    "pattern": pattern,
                    "input_sample": value[:50] + ('...' if len(value) > 50 else '')
                }
            )
            return True
    
    return False


def sanitize_search_query(search_term: str) -> str:
    """
    Sanitizes search query parameters to prevent injection attacks.
    
    Args:
        search_term: The search term to sanitize
        
    Returns:
        Sanitized search term safe for database queries
    """
    if search_term is None or search_term == '':
        return search_term
    
    # Use utility function to sanitize search term
    sanitized = sanitize_search_term(search_term)
    
    # Check for potential SQL injection
    if detect_sql_injection(search_term):
        logger.warning(
            "Search term contains suspicious patterns, sanitizing", 
            extra={"original": search_term, "sanitized": sanitized}
        )
    
    return sanitized


def validate_search_params(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates search parameters to ensure they match allowed fields and formats.
    
    Args:
        search_params: Dictionary of search parameters
        
    Returns:
        Dictionary of validated and sanitized search parameters
    """
    if search_params is None:
        return {}
    
    sanitized_params = {}
    
    for key, value in search_params.items():
        # Skip unknown/disallowed fields
        if key not in ALLOWED_SEARCH_FIELDS:
            logger.warning(f"Disallowed search field: {key}", extra={"field": key})
            continue
        
        # Handle different field types appropriately
        if key in ['title', 'lead', 'location', 'description', 'notes']:
            # Text fields
            sanitized_params[key] = sanitize_search_query(value)
        elif key in ['start_datetime', 'end_datetime']:
            # DateTime fields - pass through as-is, will be validated by query builder
            sanitized_params[key] = value
        elif key == 'type':
            # Validate interaction type
            if validate_interaction_type(value, key):
                sanitized_params[key] = value
            else:
                logger.warning(f"Invalid interaction type in search: {value}")
        elif key == 'timezone':
            # Validate timezone
            if validate_timezone(value, key):
                sanitized_params[key] = value
            else:
                logger.warning(f"Invalid timezone in search: {value}")
        else:
            # Pass other fields through with basic sanitization
            sanitized_params[key] = sanitize_input(value)
    
    return sanitized_params


def sanitize_file_path(file_path: str) -> str:
    """
    Sanitizes file paths to prevent path traversal attacks.
    
    Args:
        file_path: The file path to sanitize
        
    Returns:
        Sanitized file path safe for filesystem operations
    """
    if file_path is None or file_path == '':
        return file_path
    
    # Remove path traversal sequences
    sanitized = re.sub(r'\.\.[/\\]', '', file_path)
    
    # Remove leading path characters that could access root
    sanitized = re.sub(r'^[/\\]', '', sanitized)
    
    # Remove any additional special characters
    sanitized = re.sub(r'[<>:"|?*]', '', sanitized)
    
    if sanitized != file_path:
        logger.warning(
            "Potential path traversal attempt sanitized", 
            extra={"original": file_path, "sanitized": sanitized}
        )
    
    return sanitized


def validate_security_headers(headers: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validates security-related HTTP headers to prevent attacks.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if headers is None:
        return False, "No headers provided"
    
    # Check Content-Type mismatch (potential content sniffing attack)
    content_type = headers.get('Content-Type', '')
    if 'json' in content_type.lower() and 'application/json' not in content_type:
        return False, "Content-Type mismatch: JSON content with incorrect MIME type"
    
    # Validate Authorization header format if present
    auth_header = headers.get('Authorization', '')
    if auth_header and not auth_header.startswith(('Bearer ', 'Basic ')):
        return False, "Invalid Authorization header format"
    
    # Check for suspiciously long headers (potential buffer overflow attack)
    for header, value in headers.items():
        if len(value) > 4096:  # Arbitrary length limit
            return False, f"Header {header} exceeds maximum length"
    
    return True, None


class SecurityValidator:
    """
    Class for handling security validation of user inputs with comprehensive security checks.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initializes the security validator with default settings.
        
        Args:
            strict_mode: If True, applies stricter validation rules
        """
        self.strict_mode = strict_mode
        self.logger = StructuredLogger(__name__)
    
    def validate_request_data(self, request_data: Dict[str, Any], 
                             required_fields: List[str] = None) -> Dict[str, Any]:
        """
        Validates and sanitizes all data from an HTTP request.
        
        Args:
            request_data: Dictionary containing request data
            required_fields: List of field names that must be present
            
        Returns:
            Validated and sanitized request data
            
        Raises:
            ValidationError: If validation fails
        """
        if request_data is None:
            raise ValidationError("No request data provided")
        
        sanitized_data = {}
        
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in request_data]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Process each field with appropriate sanitization
        for field, value in request_data.items():
            if value is None:
                sanitized_data[field] = None
                continue
                
            if isinstance(value, str):
                # Check for SQL injection in all string fields
                if detect_sql_injection(value):
                    self.logger.warning(
                        f"Potential SQL injection in field: {field}", 
                        extra={"field": field, "value_sample": value[:50]}
                    )
                    if self.strict_mode:
                        raise ValidationError(f"Suspicious input pattern detected in field: {field}")
                
                # Apply type-specific sanitization
                if field in ['description', 'notes']:
                    # Rich text fields - sanitize HTML
                    sanitized_data[field] = sanitize_html_content(value)
                elif field in ['title', 'lead', 'location']:
                    # Plain text fields - strip HTML and sanitize
                    sanitized_data[field] = sanitize_input(strip_all_html(value))
                else:
                    # Default string sanitization
                    sanitized_data[field] = sanitize_input(value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized_data[field] = self.validate_request_data(value)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized_list = []
                for item in value:
                    if isinstance(item, str):
                        sanitized_list.append(sanitize_input(item))
                    elif isinstance(item, dict):
                        sanitized_list.append(self.validate_request_data(item))
                    else:
                        sanitized_list.append(item)
                sanitized_data[field] = sanitized_list
            else:
                # Pass through non-string values unchanged
                sanitized_data[field] = value
        
        return sanitized_data
    
    def validate_interaction_data(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs security validation on interaction data.
        
        Args:
            interaction_data: Dictionary containing interaction data
            
        Returns:
            Validated and sanitized interaction data
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        required_fields = ['title', 'type', 'lead', 'start_datetime', 'end_datetime', 
                          'timezone', 'description']
        
        for field in required_fields:
            if not validate_required(interaction_data.get(field), field):
                raise ValidationError(f"Required field missing: {field}")
        
        # Sanitize and validate text fields
        sanitized_data = {}
        
        # Title validation
        title = interaction_data.get('title')
        if title:
            sanitized_title = sanitize_input(strip_all_html(title))
            if not validate_string_length(
                sanitized_title, 'title', 
                INTERACTION_TITLE_MIN_LENGTH, 
                INTERACTION_TITLE_MAX_LENGTH
            ):
                raise ValidationError(
                    f"Title must be between {INTERACTION_TITLE_MIN_LENGTH} and "
                    f"{INTERACTION_TITLE_MAX_LENGTH} characters"
                )
            sanitized_data['title'] = sanitized_title
        
        # Description validation
        description = interaction_data.get('description')
        if description:
            sanitized_description = sanitize_html_content(description)
            plain_text = strip_all_html(sanitized_description)
            if not validate_string_length(
                plain_text, 'description',
                INTERACTION_DESCRIPTION_MIN_LENGTH,
                INTERACTION_DESCRIPTION_MAX_LENGTH
            ):
                raise ValidationError(
                    f"Description must be between {INTERACTION_DESCRIPTION_MIN_LENGTH} and "
                    f"{INTERACTION_DESCRIPTION_MAX_LENGTH} characters"
                )
            sanitized_data['description'] = sanitized_description
        
        # Lead validation
        lead = interaction_data.get('lead')
        if lead:
            sanitized_lead = sanitize_input(strip_all_html(lead))
            if not validate_string_length(
                sanitized_lead, 'lead', 0, INTERACTION_LEAD_MAX_LENGTH
            ):
                raise ValidationError(f"Lead must be at most {INTERACTION_LEAD_MAX_LENGTH} characters")
            sanitized_data['lead'] = sanitized_lead
        
        # Notes validation (optional field)
        notes = interaction_data.get('notes')
        if notes:
            sanitized_notes = sanitize_html_content(notes)
            if notes and not validate_string_length(
                strip_all_html(notes), 'notes', 0, INTERACTION_NOTES_MAX_LENGTH
            ):
                raise ValidationError(f"Notes must be at most {INTERACTION_NOTES_MAX_LENGTH} characters")
            sanitized_data['notes'] = sanitized_notes
        
        # Location validation (optional field)
        location = interaction_data.get('location')
        if location:
            sanitized_location = sanitize_input(strip_all_html(location))
            if not validate_string_length(
                sanitized_location, 'location', 0, INTERACTION_LOCATION_MAX_LENGTH
            ):
                raise ValidationError(f"Location must be at most {INTERACTION_LOCATION_MAX_LENGTH} characters")
            sanitized_data['location'] = sanitized_location
        
        # Interaction type validation
        interaction_type = interaction_data.get('type')
        if interaction_type:
            if not validate_interaction_type(interaction_type, 'type'):
                raise ValidationError("Invalid interaction type")
            sanitized_data['type'] = interaction_type
        
        # Timezone validation
        timezone = interaction_data.get('timezone')
        if timezone:
            if not validate_timezone(timezone, 'timezone'):
                raise ValidationError("Invalid timezone identifier")
            sanitized_data['timezone'] = timezone
        
        # Datetime validation
        start_datetime = interaction_data.get('start_datetime')
        end_datetime = interaction_data.get('end_datetime')
        if start_datetime and end_datetime:
            if not validate_datetime_range(start_datetime, end_datetime):
                raise ValidationError("End date must be after start date")
            sanitized_data['start_datetime'] = start_datetime
            sanitized_data['end_datetime'] = end_datetime
        
        # Add other fields from the original data that don't need special validation
        for key, value in interaction_data.items():
            if key not in sanitized_data and key not in [
                'title', 'type', 'lead', 'start_datetime', 'end_datetime',
                'timezone', 'description', 'notes', 'location'
            ]:
                sanitized_data[key] = value
        
        return sanitized_data
    
    def validate_file_upload(self, file_object: Any, allowed_extensions: List[str],
                           max_size_bytes: int = 10485760) -> Tuple[bool, Optional[str]]:
        """
        Validates file uploads for security concerns.
        
        Args:
            file_object: File object from request
            allowed_extensions: List of allowed file extensions
            max_size_bytes: Maximum allowed file size in bytes (default 10MB)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_object is None:
            return False, "No file provided"
        
        # Extract filename and check extension
        filename = getattr(file_object, 'filename', '')
        if not filename:
            return False, "Invalid file or missing filename"
        
        # Check file extension
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if not file_ext or file_ext not in allowed_extensions:
            return False, f"File extension not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        # Check file size
        file_size = 0
        try:
            # Different file objects may have different ways to get size
            if hasattr(file_object, 'content_length'):
                file_size = file_object.content_length
            elif hasattr(file_object, 'size'):
                file_size = file_object.size
            elif hasattr(file_object, 'tell') and hasattr(file_object, 'seek'):
                # Try to determine size by seeking
                current_pos = file_object.tell()
                file_object.seek(0, 2)  # Seek to end
                file_size = file_object.tell()
                file_object.seek(current_pos)  # Restore position
        except Exception as e:
            self.logger.error(f"Error checking file size: {str(e)}")
            return False, "Unable to determine file size"
        
        if file_size > max_size_bytes:
            return False, f"File too large. Maximum size is {max_size_bytes / 1024 / 1024:.1f}MB"
        
        # Check for potentially malicious content based on file type
        if file_ext in ['exe', 'dll', 'bat', 'cmd', 'sh', 'js']:
            return False, f"File type {file_ext} is not allowed for security reasons"
        
        return True, None
    
    def log_validation_event(self, event_type: str, details: Dict[str, Any], is_violation: bool = False) -> None:
        """
        Logs validation events for security auditing.
        
        Args:
            event_type: Type of validation event
            details: Details about the validation event
            is_violation: Whether this event represents a security violation
        """
        log_data = {
            "event_type": event_type,
            "timestamp": details.get("timestamp", ""),
            "details": details
        }
        
        if is_violation:
            if details.get("severity") == "high":
                self.logger.error("Security validation violation", extra=log_data)
            else:
                self.logger.warning("Security validation issue", extra=log_data)
        else:
            self.logger.info("Security validation passed", extra=log_data)


class InputSanitizer:
    """
    Class for sanitizing different types of user inputs.
    """
    
    def __init__(self):
        """
        Initializes the input sanitizer.
        """
        # Set up default sanitization rules
        pass
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitizes plain text input by removing dangerous characters.
        
        Args:
            text: Plain text to sanitize
            
        Returns:
            Sanitized text
        """
        return sanitize_input(text)
    
    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitizes HTML content to prevent XSS attacks.
        
        Args:
            html_content: HTML content to sanitize
            
        Returns:
            Sanitized HTML
        """
        return sanitize_html_content(html_content)
    
    def sanitize_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes JSON data by validating and cleaning field values.
        
        Args:
            json_data: JSON data to sanitize
            
        Returns:
            Sanitized JSON data
            
        Raises:
            ValidationError: If JSON data is invalid
        """
        if not isinstance(json_data, dict):
            raise ValidationError("JSON data must be a dictionary")
        
        sanitized_data = {}
        
        for key, value in json_data.items():
            if isinstance(value, str):
                sanitized_data[key] = sanitize_input(value)
            elif isinstance(value, dict):
                sanitized_data[key] = self.sanitize_json(value)
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if isinstance(item, str):
                        sanitized_list.append(sanitize_input(item))
                    elif isinstance(item, dict):
                        sanitized_list.append(self.sanitize_json(item))
                    else:
                        sanitized_list.append(item)
                sanitized_data[key] = sanitized_list
            else:
                sanitized_data[key] = value
        
        return sanitized_data
    
    def sanitize_query_params(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes query parameters for database searches.
        
        Args:
            query_params: Dictionary of query parameters
            
        Returns:
            Sanitized query parameters
        """
        return validate_search_params(query_params)