"""
Rate limiting module for the Interaction Management System.

This module provides rate limiting functionality to protect the API from abuse.
It implements Redis-based tracking of request counts with configurable limits for
different request types and provides appropriate HTTP headers for rate limit information.

The rate limiting system uses sliding window counters to track requests and can be
configured for different types of requests (anonymous, authenticated, search, auth)
with different limits.
"""

import time  # standard library
import math  # standard library
import functools  # standard library
from typing import Dict, Any, Optional, Callable  # standard library
from dataclasses import dataclass  # standard library

from ..cache.redis_client import RedisClient
from ..cache.cache_keys import INTERACTION_PREFIX
from ..utils.error_util import AuthenticationError
from ..logging.structured_logger import get_logger

# Initialize logger
logger = get_logger('rate_limiting')

# Rate limiting constants
RATE_LIMIT_PREFIX = 'rate_limit'
RATE_LIMIT_ANONYMOUS = 30  # Anonymous requests: 30 per minute
RATE_LIMIT_AUTHENTICATED = 300  # Authenticated API: 300 per minute
RATE_LIMIT_SEARCH = 60  # Search operations: 60 per minute
RATE_LIMIT_AUTH = 10  # Auth operations: 10 per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)


@dataclass
class RateLimitInfo:
    """
    Data class representing rate limit information and status.
    
    Provides a standardized structure for rate limit status information
    that can be used for generating response headers and making rate limit
    enforcement decisions.
    """
    
    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    key: str
    
    def __init__(self, allowed: bool, limit: int, remaining: int, reset_time: int, key: str):
        """
        Initialize a new RateLimitInfo instance.
        
        Args:
            allowed: Whether the request is allowed under rate limit
            limit: Maximum number of requests allowed in the window
            remaining: Number of requests remaining in the window
            reset_time: Seconds until the rate limit window resets
            key: Redis key used for this rate limit counter
        """
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.key = key


class RateLimiter:
    """
    Class for managing rate limiting operations using Redis for counter storage.
    
    This class provides methods for tracking and enforcing rate limits based
    on configurable identifiers (e.g., IP address, user ID) and limit types.
    It uses Redis to store and increment counters with appropriate expiration.
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Initialize a RateLimiter with a Redis client.
        
        Args:
            redis_client: Redis client instance for storage operations
        """
        self._redis_client = redis_client
    
    def get_rate_limit_key(self, identifier: str, limit_type: str) -> str:
        """
        Generate a Redis key for storing rate limit data.
        
        Args:
            identifier: Unique identifier for the client (IP, user ID)
            limit_type: Type of rate limit (anonymous, authenticated, etc.)
        
        Returns:
            Formatted Redis key for the rate limit counter
        """
        return f"{RATE_LIMIT_PREFIX}:{limit_type}:{identifier}"
    
    def check_rate_limit(self, identifier: str, limit_type: str, 
                         max_requests: int = RATE_LIMIT_AUTHENTICATED,
                         window_seconds: int = RATE_LIMIT_WINDOW) -> RateLimitInfo:
        """
        Check if a request is within the rate limit without incrementing the counter.
        
        Args:
            identifier: Unique identifier for the client (IP, user ID)
            limit_type: Type of rate limit (anonymous, authenticated, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Duration of the rate limit window in seconds
        
        Returns:
            Information about the current rate limit status
        """
        # Generate key for this rate limit
        key = self.get_rate_limit_key(identifier, limit_type)
        
        # Get current count from Redis
        count = self._redis_client.get(key, 'int')
        
        # If key doesn't exist, count is 0
        if count is None:
            count = 0
        
        # Get time until window reset
        ttl = self._redis_client.ttl(key)
        # If key doesn't exist or has no TTL, set reset_time to window_seconds
        reset_time = ttl if ttl > 0 else window_seconds
        
        # Calculate remaining requests
        remaining = max(0, max_requests - count)
        
        # Determine if the request is allowed
        allowed = count < max_requests
        
        # Return rate limit information
        return RateLimitInfo(
            allowed=allowed,
            limit=max_requests,
            remaining=remaining,
            reset_time=reset_time,
            key=key
        )
    
    def increment_counter(self, identifier: str, limit_type: str, 
                          window_seconds: int = RATE_LIMIT_WINDOW) -> int:
        """
        Increment the rate limit counter and return the new count.
        
        Args:
            identifier: Unique identifier for the client (IP, user ID)
            limit_type: Type of rate limit (anonymous, authenticated, etc.)
            window_seconds: Duration of the rate limit window in seconds
        
        Returns:
            New count after incrementing
        """
        # Generate key for this rate limit
        key = self.get_rate_limit_key(identifier, limit_type)
        
        # Check if key exists
        exists = self._redis_client.exists(key)
        
        # Increment the counter
        new_count = self._redis_client.incr(key)
        
        # If this is a new key, set expiration time
        if not exists or new_count == 1:
            self._redis_client.expire(key, window_seconds)
        
        return new_count
    
    def limit(self, identifier: str, limit_type: str, 
              max_requests: int = RATE_LIMIT_AUTHENTICATED,
              window_seconds: int = RATE_LIMIT_WINDOW) -> RateLimitInfo:
        """
        Check rate limit and increment counter in one operation.
        
        Args:
            identifier: Unique identifier for the client (IP, user ID)
            limit_type: Type of rate limit (anonymous, authenticated, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Duration of the rate limit window in seconds
        
        Returns:
            Updated rate limit information
        """
        # First check the rate limit
        rate_limit_info = self.check_rate_limit(
            identifier, 
            limit_type, 
            max_requests, 
            window_seconds
        )
        
        # If already over limit, return the info without incrementing
        if not rate_limit_info.allowed:
            return rate_limit_info
        
        # Increment the counter
        new_count = self.increment_counter(identifier, limit_type, window_seconds)
        
        # Calculate remaining requests after increment
        remaining = max(0, max_requests - new_count)
        
        # Get time until window reset
        ttl = self._redis_client.ttl(rate_limit_info.key)
        reset_time = ttl if ttl > 0 else window_seconds
        
        # Return updated rate limit information
        return RateLimitInfo(
            allowed=new_count <= max_requests,
            limit=max_requests,
            remaining=remaining,
            reset_time=reset_time,
            key=rate_limit_info.key
        )
    
    def get_headers(self, rate_limit_info: RateLimitInfo) -> Dict[str, str]:
        """
        Generate HTTP headers for rate limit information.
        
        Args:
            rate_limit_info: Rate limit information object
        
        Returns:
            Dictionary of rate limit headers
        """
        return {
            'X-RateLimit-Limit': str(rate_limit_info.limit),
            'X-RateLimit-Remaining': str(rate_limit_info.remaining),
            'X-RateLimit-Reset': str(rate_limit_info.reset_time)
        }
    
    def limit_or_error(self, identifier: str, limit_type: str,
                      max_requests: int = RATE_LIMIT_AUTHENTICATED,
                      window_seconds: int = RATE_LIMIT_WINDOW) -> RateLimitInfo:
        """
        Apply rate limiting and throw error if limit exceeded.
        
        Args:
            identifier: Unique identifier for the client (IP, user ID)
            limit_type: Type of rate limit (anonymous, authenticated, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Duration of the rate limit window in seconds
        
        Returns:
            Rate limit information if allowed
            
        Raises:
            AuthenticationError: If rate limit is exceeded
        """
        # Apply rate limit
        rate_limit_info = self.limit(identifier, limit_type, max_requests, window_seconds)
        
        # If limit exceeded, log and raise exception
        if not rate_limit_info.allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} ({limit_type})",
                extra={
                    'identifier': identifier,
                    'limit_type': limit_type,
                    'limit': max_requests,
                    'window': window_seconds
                }
            )
            
            error_message = f"Rate limit exceeded. Try again in {rate_limit_info.reset_time} seconds."
            raise AuthenticationError(
                message=error_message,
                details={
                    'limit': rate_limit_info.limit,
                    'reset_time': rate_limit_info.reset_time
                },
                error_code="RATE_LIMIT_EXCEEDED"
            )
        
        return rate_limit_info
    
    def get_anonymous_limiter(self) -> Callable:
        """
        Get a rate limiter function for anonymous requests.
        
        Returns:
            Function that applies anonymous rate limiting
        """
        return functools.partial(
            self.limit_or_error,
            limit_type='anonymous',
            max_requests=RATE_LIMIT_ANONYMOUS
        )
    
    def get_authenticated_limiter(self) -> Callable:
        """
        Get a rate limiter function for authenticated requests.
        
        Returns:
            Function that applies authenticated rate limiting
        """
        return functools.partial(
            self.limit_or_error,
            limit_type='authenticated',
            max_requests=RATE_LIMIT_AUTHENTICATED
        )
    
    def get_search_limiter(self) -> Callable:
        """
        Get a rate limiter function for search operations.
        
        Returns:
            Function that applies search rate limiting
        """
        return functools.partial(
            self.limit_or_error,
            limit_type='search',
            max_requests=RATE_LIMIT_SEARCH
        )
    
    def get_auth_limiter(self) -> Callable:
        """
        Get a rate limiter function for authentication operations.
        
        Returns:
            Function that applies auth rate limiting
        """
        return functools.partial(
            self.limit_or_error,
            limit_type='auth',
            max_requests=RATE_LIMIT_AUTH
        )