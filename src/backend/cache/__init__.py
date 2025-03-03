"""
Cache package initialization module for the Interaction Management System.

This module serves as the main entry point for accessing Redis caching functionality,
providing a clean interface for cache operations, key management, and invalidation 
strategies throughout the application.

The cache package implements a multi-level caching strategy for authentication tokens,
user site access, interaction data, and search results to optimize application 
performance while ensuring data consistency.
"""

# Redis client imports
from .redis_client import (
    RedisClient,
    get_redis_client,
    serialize_data,
    deserialize_data
)

# Cache service imports
from .cache_service import (
    CacheService,
    get_cache_service
)

# Create an alias for backward compatibility or as specified in requirements
create_cache_service = get_cache_service

# Cache key imports
from .cache_keys import *

# Cache invalidation imports
from .invalidation import (
    CacheInvalidator,
    UserCacheInvalidator,
    SiteCacheInvalidator,
    InteractionCacheInvalidator,
    SearchCacheInvalidator,
    invalidate_keys_by_pattern
)

# Initialize the global cache service instance
cache_service = create_cache_service()