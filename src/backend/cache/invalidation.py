"""
Cache invalidation module for the Interaction Management System.

This module provides specialized invalidators for different entity types in the application.
Each invalidator implements a strategy for efficiently removing specific cache entries
when the underlying data changes, ensuring cache consistency with the database.

The module follows a strategy pattern with a base abstract invalidator class and
concrete implementations for users, sites, interactions, and search results.
"""

import logging
from typing import List, Set, Dict, Any, Optional, Union, Type
from abc import ABC, abstractmethod

from ..logging.structured_logger import get_logger
from .cache_keys import (
    get_key_pattern_for_invalidation,
    USER_PREFIX,
    SITE_PREFIX,
    TOKEN_PREFIX,
    INTERACTION_PREFIX,
    INTERACTION_LIST_PREFIX,
    SEARCH_PREFIX
)
from .redis_client import RedisClient

# Initialize logger
logger = get_logger(__name__)


def invalidate_keys_by_pattern(redis_client: RedisClient, pattern: str) -> int:
    """
    Invalidates (deletes) multiple cache keys matching a given pattern.
    
    Args:
        redis_client: Redis client instance
        pattern: Pattern to match keys for deletion (e.g., "user:123*")
        
    Returns:
        Number of invalidated keys
    """
    logger.info(f"Attempting to invalidate keys matching pattern: {pattern}")
    
    try:
        # Use redis connection directly to perform SCAN operation
        redis_client.connect()
        _redis = redis_client._redis_client
        
        # Use SCAN to find all keys matching the pattern
        keys_to_delete = set()
        cursor = 0
        while True:
            cursor, keys = _redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                keys_to_delete.update([key.decode('utf-8') if isinstance(key, bytes) else key for key in keys])
            if cursor == 0:
                break
        
        # Delete all found keys
        deleted_count = 0
        if keys_to_delete:
            # Delete keys in batches to avoid blocking Redis
            for key in keys_to_delete:
                if redis_client.delete(key):
                    deleted_count += 1
        
        logger.info(f"Successfully invalidated {deleted_count} keys matching pattern: {pattern}")
        return deleted_count
    except Exception as e:
        logger.error(f"Error invalidating keys with pattern {pattern}: {str(e)}")
        return 0


class CacheInvalidator(ABC):
    """
    Abstract base class for cache invalidation strategies.
    
    This class defines the interface for all invalidators and provides
    common functionality for performing redis key invalidation operations.
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Initialize the invalidator with a Redis client.
        
        Args:
            redis_client: Redis client for cache operations
        """
        self._redis_client = redis_client
        self._prefix = ""  # To be set by subclasses
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def invalidate(self, entity_id: Union[str, int]) -> int:
        """
        Abstract method to invalidate cache entries for an entity.
        
        Args:
            entity_id: Identifier of the entity to invalidate
            
        Returns:
            Number of invalidated cache entries
        """
        pass
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidates cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match keys for deletion
            
        Returns:
            Number of invalidated cache entries
        """
        return invalidate_keys_by_pattern(self._redis_client, pattern)


class UserCacheInvalidator(CacheInvalidator):
    """
    Invalidator for user-related cache entries.
    
    Handles invalidation of user data, site access permissions, and tokens
    when user information changes.
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Initialize the user cache invalidator.
        
        Args:
            redis_client: Redis client for cache operations
        """
        super().__init__(redis_client)
        self._prefix = USER_PREFIX
        logger.debug("Initialized UserCacheInvalidator")
    
    def invalidate(self, user_id: Union[str, int]) -> int:
        """
        Invalidate user-related cache entries.
        
        This method invalidates all cache entries related to a specific user,
        including their profile data, site access, and authentication tokens.
        
        Args:
            user_id: User ID to invalidate
            
        Returns:
            Number of invalidated cache entries
        """
        logger.info(f"Invalidating cache for user {user_id}")
        
        # Generate pattern for user data keys
        pattern = get_key_pattern_for_invalidation(self._prefix, user_id)
        
        # Invalidate user data
        user_count = self.invalidate_by_pattern(pattern)
        
        # Invalidate user site access
        site_count = self.invalidate_site_access(user_id)
        
        # Invalidate user tokens
        token_count = self.invalidate_token(user_id)
        
        total_count = user_count + site_count + token_count
        logger.info(f"Invalidated {total_count} cache entries for user {user_id}")
        
        return total_count
    
    def invalidate_token(self, user_id: Union[str, int]) -> int:
        """
        Invalidate only user token cache.
        
        Args:
            user_id: User ID to invalidate tokens for
            
        Returns:
            Number of invalidated cache entries
        """
        pattern = get_key_pattern_for_invalidation(TOKEN_PREFIX, user_id)
        count = self.invalidate_by_pattern(pattern)
        logger.info(f"Invalidated {count} token cache entries for user {user_id}")
        return count
    
    def invalidate_site_access(self, user_id: Union[str, int]) -> int:
        """
        Invalidate only user site access cache.
        
        Args:
            user_id: User ID to invalidate site access for
            
        Returns:
            Number of invalidated cache entries
        """
        pattern = get_key_pattern_for_invalidation(f"{USER_PREFIX}:{user_id}", "sites")
        count = self.invalidate_by_pattern(pattern)
        logger.info(f"Invalidated {count} site access cache entries for user {user_id}")
        return count


class SiteCacheInvalidator(CacheInvalidator):
    """
    Invalidator for site-related cache entries.
    
    Handles invalidation of site data when site information changes.
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Initialize the site cache invalidator.
        
        Args:
            redis_client: Redis client for cache operations
        """
        super().__init__(redis_client)
        self._prefix = SITE_PREFIX
        logger.debug("Initialized SiteCacheInvalidator")
    
    def invalidate(self, site_id: Union[str, int]) -> int:
        """
        Invalidate site-related cache entries.
        
        This method invalidates all cache entries related to a specific site.
        
        Args:
            site_id: Site ID to invalidate
            
        Returns:
            Number of invalidated cache entries
        """
        logger.info(f"Invalidating cache for site {site_id}")
        
        # Generate pattern for site keys
        pattern = get_key_pattern_for_invalidation(self._prefix, site_id)
        
        # Invalidate site data
        count = self.invalidate_by_pattern(pattern)
        
        logger.info(f"Invalidated {count} cache entries for site {site_id}")
        return count


class InteractionCacheInvalidator(CacheInvalidator):
    """
    Invalidator for interaction-related cache entries.
    
    Handles invalidation of interaction data, lists, and related search results
    when interaction data changes.
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Initialize the interaction cache invalidator.
        
        Args:
            redis_client: Redis client for cache operations
        """
        super().__init__(redis_client)
        self._prefix = INTERACTION_PREFIX
        logger.debug("Initialized InteractionCacheInvalidator")
    
    def invalidate(self, interaction_id: Union[str, int]) -> int:
        """
        Invalidate interaction-related cache entries.
        
        This method invalidates all cache entries for a specific interaction.
        
        Args:
            interaction_id: Interaction ID to invalidate
            
        Returns:
            Number of invalidated cache entries
        """
        logger.info(f"Invalidating cache for interaction {interaction_id}")
        
        # Generate pattern for interaction keys
        pattern = get_key_pattern_for_invalidation(self._prefix, interaction_id)
        
        # Invalidate interaction data
        count = self.invalidate_by_pattern(pattern)
        
        logger.info(f"Invalidated {count} cache entries for interaction {interaction_id}")
        return count
    
    def invalidate_with_related(self, interaction_id: Union[str, int], site_id: Union[str, int]) -> int:
        """
        Invalidate interaction and related lists/search results.
        
        This method provides a more comprehensive invalidation by also clearing
        lists and search results that might contain the interaction.
        
        Args:
            interaction_id: Interaction ID to invalidate
            site_id: Site ID associated with the interaction
            
        Returns:
            Number of invalidated cache entries
        """
        logger.info(f"Performing comprehensive invalidation for interaction {interaction_id} in site {site_id}")
        
        # Invalidate specific interaction
        interaction_count = self.invalidate(interaction_id)
        
        # Invalidate interaction lists for the site
        list_count = self.invalidate_lists(site_id)
        
        # Invalidate search results for the site
        search_invalidator = SearchCacheInvalidator(self._redis_client)
        search_count = search_invalidator.invalidate(site_id)
        
        total_count = interaction_count + list_count + search_count
        
        logger.info(f"Completed comprehensive invalidation for interaction {interaction_id}: "
                   f"{total_count} total entries invalidated")
        
        return total_count
    
    def invalidate_lists(self, site_id: Union[str, int]) -> int:
        """
        Invalidate interaction list cache entries for a site.
        
        Args:
            site_id: Site ID to invalidate lists for
            
        Returns:
            Number of invalidated cache entries
        """
        pattern = get_key_pattern_for_invalidation(INTERACTION_LIST_PREFIX, site_id)
        count = self.invalidate_by_pattern(pattern)
        logger.info(f"Invalidated {count} interaction list cache entries for site {site_id}")
        return count


class SearchCacheInvalidator(CacheInvalidator):
    """
    Invalidator for search-related cache entries.
    
    Handles invalidation of search results when underlying data changes that
    might affect search results.
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Initialize the search cache invalidator.
        
        Args:
            redis_client: Redis client for cache operations
        """
        super().__init__(redis_client)
        self._prefix = SEARCH_PREFIX
        logger.debug("Initialized SearchCacheInvalidator")
    
    def invalidate(self, site_id: Union[str, int]) -> int:
        """
        Invalidate all search cache entries for a site.
        
        Args:
            site_id: Site ID to invalidate search results for
            
        Returns:
            Number of invalidated cache entries
        """
        logger.info(f"Invalidating search cache for site {site_id}")
        
        # Generate pattern for search keys
        pattern = get_key_pattern_for_invalidation(self._prefix, site_id)
        
        # Invalidate search data
        count = self.invalidate_by_pattern(pattern)
        
        logger.info(f"Invalidated {count} search cache entries for site {site_id}")
        return count