"""
Rate Limiting Middleware for Flask API

This module provides middleware for limiting the rate of requests to the API to protect
against abuse, brute force attacks, and excessive traffic. It implements different
rate limits for anonymous vs. authenticated users, and special limits for search
and authentication operations.

The middleware can be applied as a decorator to Flask route handlers:

    @rate_limit_middleware(endpoint_type='search')
    def search_endpoint():
        # Your code here

Rate limits are based on IP address for anonymous users and user ID for authenticated users.
"""

import functools  # standard library
import logging  # standard library
from flask import request, g  # version 2.3.2
from typing import Callable, Dict, Any, Optional  # standard library

from ...security.rate_limiting import RateLimiter
from ...cache.redis_client import RedisClient
from ..helpers.response import error_response
from ...utils.enums import ErrorType
from ...config import RATE_LIMIT_CONFIG

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Redis client and rate limiter
redis_client = RedisClient()
rate_limiter = RateLimiter(redis_client)


def get_rate_limit_identifier(request) -> str:
    """
    Determines the identifier to use for rate limiting based on authentication status.
    
    Args:
        request: Flask request object
        
    Returns:
        str: IP address for anonymous users, user ID for authenticated users
    """
    # If user is authenticated, use their user ID as the identifier
    if hasattr(g, 'user_id') and g.user_id:
        return f"user:{g.user_id}"
    
    # Otherwise, use the IP address as the identifier
    # Use X-Forwarded-For header if available (for clients behind proxy)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    return f"ip:{ip_address}"


def rate_limit_middleware(endpoint_type: str = 'api', max_requests: int = None, window_seconds: int = None):
    """
    Decorator function that applies rate limiting to Flask route handlers.
    
    Args:
        endpoint_type: Type of endpoint ('api', 'auth', 'search', 'anonymous')
        max_requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        
    Returns:
        Callable: Decorated function with rate limiting applied
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get rate limit configuration
            rate_limit = max_requests
            window = window_seconds
            
            # If rate limit not provided, get it from config based on endpoint type
            if rate_limit is None:
                # Try to get from RATE_LIMIT_CONFIG
                if isinstance(RATE_LIMIT_CONFIG, dict):
                    if endpoint_type == 'anonymous':
                        rate_limit = RATE_LIMIT_CONFIG.get('anonymous', 30)
                    elif endpoint_type == 'search':
                        rate_limit = RATE_LIMIT_CONFIG.get('search', 60)
                    elif endpoint_type == 'auth':
                        rate_limit = RATE_LIMIT_CONFIG.get('auth', 10)
                    else:
                        rate_limit = RATE_LIMIT_CONFIG.get('api', 300)
                else:
                    # Use default values
                    if endpoint_type == 'anonymous':
                        rate_limit = 30
                    elif endpoint_type == 'search':
                        rate_limit = 60
                    elif endpoint_type == 'auth':
                        rate_limit = 10
                    else:
                        rate_limit = 300
            
            # Default window to 60 seconds (1 minute) if not specified
            if window is None:
                window = 60
            
            # Get identifier for rate limiting
            identifier = get_rate_limit_identifier(request)
            
            # Check rate limit
            rate_limit_info = rate_limiter.limit(
                identifier=identifier,
                limit_type=endpoint_type,
                max_requests=rate_limit,
                window_seconds=window
            )
            
            # If rate limit exceeded
            if not rate_limit_info.allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier} ({endpoint_type})",
                    extra={
                        'identifier': identifier,
                        'endpoint_type': endpoint_type,
                        'limit': rate_limit,
                        'window': window
                    }
                )
                
                # Return 429 Too Many Requests error
                return error_response(
                    message=f"Rate limit exceeded. Try again in {rate_limit_info.reset_time} seconds.",
                    error_type=ErrorType.AUTHENTICATION,
                    status_code=429,
                    details={
                        'limit': rate_limit_info.limit,
                        'remaining': 0,
                        'reset': rate_limit_info.reset_time
                    }
                )
            
            # Execute the original function
            response = func(*args, **kwargs)
            
            # Get rate limit headers
            headers = rate_limiter.get_headers(rate_limit_info)
            
            # Add headers to the response
            if isinstance(response, tuple) and len(response) >= 2:
                response_body, status_code, *rest = response
                
                # If response_body is a Flask response object with headers attribute
                if hasattr(response_body, 'headers'):
                    for key, value in headers.items():
                        response_body.headers[key] = value
                    
                    return (response_body, status_code, *rest)
            
            # If response is a Flask response object with headers attribute
            elif hasattr(response, 'headers'):
                for key, value in headers.items():
                    response.headers[key] = value
            
            return response
            
        return wrapper
    
    return decorator