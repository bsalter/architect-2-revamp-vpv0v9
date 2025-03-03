"""
Utility module providing string manipulation and validation functions.

This module contains various utility functions for handling text data, sanitization,
format validation, and string operations used throughout the application. These
functions are designed to be used across different components of the backend to
ensure consistent handling of string data.

Functions provide capabilities for:
- Input validation and sanitization to prevent XSS and injection attacks
- Form field validation for fields like title, description, and notes
- Search term processing and text normalization for consistent search
- HTML content handling with proper sanitization
- String formatting and manipulation for display and storage
"""

import re
import html
import bleach  # version 6.0.0
import unicodedata
from typing import Optional, List, Dict, Any

from .constants import (
    SANITIZE_PATTERN,
    INTERACTION_TITLE_MIN_LENGTH,
    INTERACTION_TITLE_MAX_LENGTH,
    INTERACTION_LEAD_MAX_LENGTH,
    INTERACTION_DESCRIPTION_MIN_LENGTH,
    INTERACTION_DESCRIPTION_MAX_LENGTH,
    INTERACTION_LOCATION_MAX_LENGTH,
    INTERACTION_NOTES_MAX_LENGTH
)

# List of HTML tags allowed in rich text fields
ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']

# Dictionary of allowed HTML attributes for specific tags
ALLOWED_HTML_ATTRIBUTES = {'*': ['class']}

# Regular expression pattern for email validation
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


def is_empty(value: Optional[str]) -> bool:
    """
    Checks if a string is None, empty, or contains only whitespace.
    
    Args:
        value: The string to check
        
    Returns:
        True if string is empty or None, False otherwise
    """
    if value is None:
        return True
    
    if not isinstance(value, str):
        return False
    
    return len(value.strip()) == 0


def is_valid_length(value: Optional[str], min_length: int, max_length: int) -> bool:
    """
    Checks if a string's length falls within specified min and max bounds.
    
    Args:
        value: The string to check
        min_length: Minimum allowed length (inclusive)
        max_length: Maximum allowed length (inclusive)
        
    Returns:
        True if string length is within bounds, False otherwise
    """
    if value is None:
        return False
    
    length = len(value.strip())
    return min_length <= length <= max_length


def truncate(text: Optional[str], max_length: int, suffix: str = "...") -> Optional[str]:
    """
    Truncates a string to a specified maximum length with an optional suffix.
    
    Args:
        text: The string to truncate
        max_length: Maximum allowed length
        suffix: String to append if truncation occurs, defaults to "..."
        
    Returns:
        Truncated string with suffix if truncation occurred, or original string if no truncation needed
    """
    if text is None or is_empty(text):
        return text
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_html(
    html_content: Optional[str], 
    allowed_tags: Optional[List[str]] = None, 
    allowed_attributes: Optional[Dict[str, List[str]]] = None
) -> Optional[str]:
    """
    Sanitizes HTML content to prevent XSS attacks while preserving allowed tags.
    
    Args:
        html_content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags, defaults to ALLOWED_HTML_TAGS
        allowed_attributes: Dictionary of allowed HTML attributes, defaults to ALLOWED_HTML_ATTRIBUTES
        
    Returns:
        Sanitized HTML content, or None if input was None
    """
    if html_content is None:
        return None
    
    if allowed_tags is None:
        allowed_tags = ALLOWED_HTML_TAGS
    
    if allowed_attributes is None:
        allowed_attributes = ALLOWED_HTML_ATTRIBUTES
    
    return bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )


def escape_html(content: Optional[str]) -> Optional[str]:
    """
    Escapes HTML special characters to their entity equivalents.
    
    Args:
        content: The content to escape
        
    Returns:
        HTML-escaped content, or None if input was None
    """
    if content is None:
        return None
    
    return html.escape(content)


def strip_html(html_content: Optional[str]) -> Optional[str]:
    """
    Strips all HTML tags from a string, leaving only plain text.
    
    Args:
        html_content: The HTML content to strip
        
    Returns:
        Plain text with HTML tags removed, or None if input was None
    """
    if html_content is None:
        return None
    
    return bleach.clean(html_content, tags=[], strip=True)


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """
    Normalizes whitespace in a string by replacing consecutive whitespace with a single space.
    
    Args:
        text: The text to normalize
        
    Returns:
        String with normalized whitespace, or None if input was None
    """
    if text is None:
        return None
    
    return re.sub(r'\s+', ' ', text).strip()


def normalize_text(text: Optional[str]) -> Optional[str]:
    """
    Normalizes text for consistent comparison by removing diacritics, 
    converting to lowercase, and normalizing whitespace.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text for consistent comparison, or None if input was None
    """
    if text is None:
        return None
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove diacritics (accents)
    text = ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )
    
    # Normalize whitespace
    return normalize_whitespace(text)


def validate_email(email: Optional[str]) -> bool:
    """
    Validates if a string is a properly formatted email address.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if email is None or is_empty(email):
        return False
    
    return bool(re.match(EMAIL_PATTERN, email))


def generate_slug(text: Optional[str]) -> str:
    """
    Generates a URL-friendly slug from a string by removing special characters 
    and replacing spaces with hyphens.
    
    Args:
        text: The text to convert to a slug
        
    Returns:
        URL-friendly slug, or empty string if input was None or empty
    """
    if text is None or is_empty(text):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove diacritics (accents)
    text = ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )
    
    # Replace spaces with hyphens
    text = text.replace(' ', '-')
    
    # Remove characters that are not alphanumeric or hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)
    
    # Replace multiple consecutive hyphens with a single hyphen
    text = re.sub(r'-+', '-', text)
    
    # Remove leading and trailing hyphens
    return text.strip('-')


def sanitize_search_term(search_term: Optional[str]) -> Optional[str]:
    """
    Sanitizes a search term to prevent injection attacks while preserving search functionality.
    
    Args:
        search_term: The search term to sanitize
        
    Returns:
        Sanitized search term, or original input if it was None or empty
    """
    if search_term is None or is_empty(search_term):
        return search_term
    
    # Remove potentially dangerous characters using the pattern from constants
    sanitized = re.sub(SANITIZE_PATTERN, '', search_term)
    
    # Normalize whitespace
    sanitized = normalize_whitespace(sanitized)
    
    # Limit search term length to a reasonable maximum (e.g., 100 characters)
    return truncate(sanitized, 100, '')


def format_name(name: Optional[str]) -> Optional[str]:
    """
    Formats a name properly by capitalizing first letters of words and handling special cases.
    
    Args:
        name: The name to format
        
    Returns:
        Properly formatted name, or original input if it was None or empty
    """
    if name is None or is_empty(name):
        return name
    
    # Split the name into words
    words = name.lower().split()
    
    # Process each word
    for i, word in enumerate(words):
        # Special case for names like "McDonald"
        if "mc" in word.lower() and len(word) > 2:
            words[i] = "Mc" + word[2].upper() + word[3:]
        # Special case for names with apostrophes like "O'Brien"
        elif "'" in word and len(word) > 2:
            parts = word.split("'")
            words[i] = parts[0].capitalize() + "'" + parts[1].capitalize()
        else:
            words[i] = word.capitalize()
    
    # Join the words back together with spaces
    return ' '.join(words)