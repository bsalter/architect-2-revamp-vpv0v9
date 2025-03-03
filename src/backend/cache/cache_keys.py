"""
Cache key management module for the Interaction Management System.

This module centralizes the definition of cache keys, prefixes, and TTL values
used throughout the Redis-based caching system. It ensures consistent key formats
across the application and enables effective cache invalidation patterns by entity type.

The module provides functions for generating standardized cache keys for different
entity types, as well as helper functions for generating invalidation patterns.
"""

from typing import Union, List, Dict, Any

from ..utils.constants import JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES

# Cache key prefixes
USER_PREFIX = "user"
SITE_PREFIX = "site"
TOKEN_PREFIX = "token"
BLACKLIST_PREFIX = "blacklist"
INTERACTION_PREFIX = "interaction"
INTERACTION_LIST_PREFIX = "interaction:list"
SEARCH_PREFIX = "search"

# TTL values in seconds
TOKEN_TTL = 60 * 30  # 30 minutes
USER_TTL = 60 * 30  # 30 minutes
SITE_TTL = 60 * 30  # 30 minutes
INTERACTION_TTL = 60 * 10  # 10 minutes
SEARCH_TTL = 60 * 2  # 2 minutes
REFERENCE_TTL = 60 * 60  # 1 hour


def get_token_key(token_id: str) -> str:
    """
    Generates a cache key for authentication tokens.
    
    Args:
        token_id: Unique identifier for the token
        
    Returns:
        Formatted cache key for the token
    """
    return f"{TOKEN_PREFIX}:{token_id}"


def get_token_blacklist_key(token_id: str) -> str:
    """
    Generates a cache key for blacklisted tokens.
    
    Args:
        token_id: Unique identifier for the token
        
    Returns:
        Formatted cache key for the blacklisted token
    """
    return f"{BLACKLIST_PREFIX}:{token_id}"


def get_user_key(user_id: int) -> str:
    """
    Generates a cache key for user data.
    
    Args:
        user_id: Database ID of the user
        
    Returns:
        Formatted cache key for the user
    """
    return f"{USER_PREFIX}:{user_id}"


def get_user_sites_key(user_id: int) -> str:
    """
    Generates a cache key for user's site access list.
    
    Args:
        user_id: Database ID of the user
        
    Returns:
        Formatted cache key for user's site access
    """
    return f"{USER_PREFIX}:{user_id}:sites"


def get_site_key(site_id: int) -> str:
    """
    Generates a cache key for site data.
    
    Args:
        site_id: Database ID of the site
        
    Returns:
        Formatted cache key for the site
    """
    return f"{SITE_PREFIX}:{site_id}"


def get_interaction_key(interaction_id: int) -> str:
    """
    Generates a cache key for interaction data.
    
    Args:
        interaction_id: Database ID of the interaction
        
    Returns:
        Formatted cache key for the interaction
    """
    return f"{INTERACTION_PREFIX}:{interaction_id}"


def get_interaction_list_key(site_id: int, page: int, size: int) -> str:
    """
    Generates a cache key for a paginated list of interactions.
    
    Args:
        site_id: Database ID of the site
        page: Page number for pagination
        size: Number of items per page
        
    Returns:
        Formatted cache key for the interaction list
    """
    return f"{INTERACTION_LIST_PREFIX}:{site_id}:{page}:{size}"


def get_search_results_key(site_id: int, query_hash: str, page: int, size: int) -> str:
    """
    Generates a cache key for search results.
    
    Args:
        site_id: Database ID of the site
        query_hash: Hash of the search query parameters
        page: Page number for pagination
        size: Number of items per page
        
    Returns:
        Formatted cache key for the search results
    """
    return f"{SEARCH_PREFIX}:{site_id}:{query_hash}:{page}:{size}"


def get_key_pattern_for_invalidation(prefix: str, id_or_pattern: Union[int, str]) -> str:
    """
    Generates a pattern string for cache key invalidation.
    
    This function creates a pattern that can be used with Redis SCAN command to
    find and invalidate multiple related cache keys.
    
    Args:
        prefix: The cache key prefix
        id_or_pattern: Entity ID or custom pattern to match
        
    Returns:
        Pattern string for Redis SCAN command
    """
    return f"{prefix}:{id_or_pattern}*"