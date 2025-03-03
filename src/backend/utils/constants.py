"""
Constants module for the Interaction Management System.

This module defines application-wide constants used throughout the backend services.
These constants provide standardized values for configuration, validation rules, error
messages, API paths, cache settings, and other parameters to maintain consistency
across the application.

All constants should be UPPERCASE as per Python conventions for constants.
"""

import re

# API Configuration
# -----------------
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Pagination and Sorting
# ----------------------
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
DEFAULT_SORT_FIELD = "start_datetime"
DEFAULT_SORT_DIRECTION = "DESC"

# Search Configuration
# -------------------
# Fields that can be included in search and filtering operations
ALLOWED_SEARCH_FIELDS = [
    "title",
    "type",
    "lead",
    "start_datetime",
    "end_datetime",
    "timezone",
    "location",
    "description",
    "notes"
]

# Fields that support full-text search
SEARCHABLE_TEXT_FIELDS = [
    "title",
    "lead",
    "location",
    "description",
    "notes"
]

# Interaction Field Validation
# ---------------------------
# These constants define the validation rules for interaction fields
INTERACTION_TITLE_MIN_LENGTH = 5
INTERACTION_TITLE_MAX_LENGTH = 100
INTERACTION_DESCRIPTION_MIN_LENGTH = 10
INTERACTION_DESCRIPTION_MAX_LENGTH = 5000
INTERACTION_LOCATION_MAX_LENGTH = 200
INTERACTION_NOTES_MAX_LENGTH = 5000
INTERACTION_LEAD_MAX_LENGTH = 100

# Authentication and JWT Settings
# ------------------------------
JWT_ISSUER = "interaction-manager"
JWT_AUDIENCE = "interaction-manager-api"
# Access token expiration: 30 minutes in seconds
JWT_ACCESS_TOKEN_EXPIRES = 30 * 60
# Refresh token expiration: 7 days in seconds
JWT_REFRESH_TOKEN_EXPIRES = 7 * 24 * 60 * 60
# Authorization header prefix
AUTH_HEADER_PREFIX = "Bearer"
# TTL for blacklisted tokens in Redis cache (seconds)
TOKEN_BLACKLIST_TTL = 30 * 60

# Cache Configuration
# ------------------
# Short-lived cache (1 minute)
CACHE_TTL_SHORT = 60
# Medium-lived cache (5 minutes)
CACHE_TTL_MEDIUM = 5 * 60
# Long-lived cache (30 minutes)
CACHE_TTL_LONG = 30 * 60
# Prefix for all cache keys to avoid collisions with other services
CACHE_KEY_PREFIX = "interaction-manager:"

# Rate Limiting
# ------------
# Default rate limit for authenticated API requests per minute
RATE_LIMIT_DEFAULT = 300
# Rate limit for authentication operations per minute
RATE_LIMIT_AUTH = 10
# Rate limit for search operations per minute
RATE_LIMIT_SEARCH = 60
# Time window in seconds for rate limiting (1 minute)
RATE_LIMIT_WINDOW = 60
# Rate limit for anonymous requests per minute
RATE_LIMIT_ANON = 30

# Date and Time Formats
# --------------------
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # ISO 8601 format without timezone
DATETIME_FORMAT_WITH_TZ = "%Y-%m-%dT%H:%M:%S%z"  # ISO 8601 format with timezone
DEFAULT_TIMEZONE = "UTC"

# Error Messages
# -------------
# Standardized error messages for different types of errors
ERROR_MESSAGES = {
    "validation": {
        "required_field": "This field is required.",
        "invalid_type": "Invalid data type for this field.",
        "invalid_length": "Length must be between {min} and {max} characters.",
        "invalid_format": "Invalid format for this field.",
        "invalid_range": "The range is invalid. End date must be after start date.",
        "invalid_timezone": "Invalid timezone identifier.",
        "invalid_interaction_type": "Invalid interaction type. Must be one of: Meeting, Call, Email, or Other."
    },
    "authentication": {
        "invalid_credentials": "Invalid username or password.",
        "token_expired": "Authentication token has expired.",
        "token_invalid": "Invalid authentication token.",
        "token_missing": "Authentication token is missing.",
        "token_blacklisted": "Token has been revoked.",
        "session_expired": "Your session has expired. Please log in again."
    },
    "authorization": {
        "permission_denied": "You do not have permission to access this resource.",
        "site_access_denied": "You do not have access to this site.",
        "insufficient_privileges": "You do not have sufficient privileges to perform this action."
    },
    "server": {
        "internal_error": "An internal server error occurred.",
        "service_unavailable": "Service temporarily unavailable.",
        "database_error": "A database error occurred."
    }
}

# Security
# -------
# Regular expression pattern for basic input sanitization
SANITIZE_PATTERN = r"[<>\"\'&]"