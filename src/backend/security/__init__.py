"""
Root module for the security package that centralizes all security-related functionality for the Interaction Management System.

Exposes core security components including input validation, CSRF protection, and rate limiting
for easy importing throughout the application. These components protect the application from
common web vulnerabilities such as XSS, CSRF, SQL injection, and rate-based attacks.
"""

# Import validation and sanitization functions
from .input_validation import (
    sanitize_input,
    validate_interaction_data,
    validate_user_data,
    validate_site_data,
    validate_search_params,
    validate_request_json,
    validate_id_param,
    is_safe_string,
    validate_email
)

# Import CSRF protection components
from .csrf import (
    CSRFProtection,
    generate_csrf_token,
    validate_csrf_token
)

# Import rate limiting components
from .rate_limiting import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    get_rate_limit_key
)