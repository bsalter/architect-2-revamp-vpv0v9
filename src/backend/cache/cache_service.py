"""
Cache service module for the Interaction Management System.

This module provides a high-level caching service that abstracts over Redis
for storing and retrieving application data with proper TTL management.
It implements a multi-tier caching strategy for authentication, site access,
interactions, and search results to improve application performance.
"""

import json
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Generic

from .redis_client import RedisClient, get_redis_client
from .cache_keys import (
    TOKEN_TTL, USER_TTL, SITE_TTL, INTERACTION_TTL, SEARCH_TTL,
    get_token_key, get_user_key, get_user_sites_key, get_interaction_key,
    get_interaction_list_key, get_search_results_key
)
from .invalidation import (
    UserCacheInvalidator, SiteCacheInvalidator,
    InteractionCacheInvalidator, SearchCacheInvalidator
)
from ..logging.structured_logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Singleton instance
_cache_service_instance = None


class CacheService:
    """
    Service class providing high-level caching functionality with specialized
    methods for different entity types.
    
    This service implements a multi-tier caching strategy with appropriate TTL
    values for different data types, improving application performance while
    ensuring data consistency through targeted invalidation.
    """
    
    def __init__(self):
        """
        Initialize the cache service with a Redis client and invalidators.
        """
        self._redis_client = get_redis_client()
        
        # Initialize invalidator classes for different entity types
        self._user_invalidator = UserCacheInvalidator(self._redis_client)
        self._site_invalidator = SiteCacheInvalidator(self._redis_client)
        self._interaction_invalidator = InteractionCacheInvalidator(self._redis_client)
        self._search_invalidator = SearchCacheInvalidator(self._redis_client)
        
        logger.info("Cache service initialized")
    
    def get(self, key: str, default: Any = None, data_type: str = 'json') -> Any:
        """
        Retrieve a value from cache.
        
        Args:
            key: Cache key to retrieve
            default: Default value to return if key not found
            data_type: Data type for deserialization ('json', 'str', 'int', 'float', 'bool', 'pickle')
            
        Returns:
            Cached value or default if not found
        """
        try:
            logger.debug(f"Getting value for key: {key}")
            return self._redis_client.get(key, data_type) or default
        except Exception as e:
            logger.error(f"Error retrieving value for key {key}: {str(e)}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in cache with TTL.
        
        Args:
            key: Cache key to set
            value: Value to store
            ttl: Time-to-live in seconds (None for no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Setting value for key: {key} with TTL: {ttl}")
            return self._redis_client.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Error setting value for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Remove a value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Deleting key: {key}")
            return self._redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return self._redis_client.exists(key)
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {str(e)}")
            return False
    
    def get_or_set(self, key: str, callback: Callable[[], Any], ttl: Optional[int] = None, data_type: str = 'json') -> Any:
        """
        Get value from cache or compute and store if not present.
        
        Args:
            key: Cache key to retrieve
            callback: Function to call to compute value if not in cache
            ttl: Time-to-live in seconds for stored value
            data_type: Data type for deserialization
            
        Returns:
            Cached or computed value
        """
        try:
            # Check if key exists in cache
            if self.exists(key):
                # Return cached value if found
                return self.get(key, data_type=data_type)
            
            # Compute value if not in cache
            value = callback()
            
            # Store computed value in cache
            if value is not None:
                self.set(key, value, ttl)
            
            return value
        except Exception as e:
            logger.error(f"Error in get_or_set for key {key}: {str(e)}")
            # Call the callback as fallback
            return callback()
    
    def store_auth_token(self, user_id: str, token: str, ttl: Optional[int] = None) -> bool:
        """
        Store authentication token in cache.
        
        Args:
            user_id: User identifier
            token: JWT token string
            ttl: Time-to-live in seconds (defaults to TOKEN_TTL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate token cache key
            key = get_token_key(user_id)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = TOKEN_TTL
            
            # Store token in cache
            logger.info(f"Storing auth token for user: {user_id}")
            return self.set(key, token, ttl)
        except Exception as e:
            logger.error(f"Error storing auth token for user {user_id}: {str(e)}")
            return False
    
    def get_auth_token(self, user_id: str) -> Optional[str]:
        """
        Retrieve authentication token from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cached token or None if not found
        """
        try:
            # Generate token cache key
            key = get_token_key(user_id)
            
            # Get token from cache
            logger.debug(f"Getting auth token for user: {user_id}")
            return self.get(key, data_type='str')
        except Exception as e:
            logger.error(f"Error retrieving auth token for user {user_id}: {str(e)}")
            return None
    
    def invalidate_auth_token(self, user_id: str) -> bool:
        """
        Invalidate authentication token.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use user invalidator to invalidate token
            logger.info(f"Invalidating auth token for user: {user_id}")
            count = self._user_invalidator.invalidate_token(user_id)
            return count > 0
        except Exception as e:
            logger.error(f"Error invalidating auth token for user {user_id}: {str(e)}")
            return False
    
    def store_user_site_access(self, user_id: str, site_ids: List[int], ttl: Optional[int] = None) -> bool:
        """
        Store user's site access list in cache.
        
        Args:
            user_id: User identifier
            site_ids: List of site IDs the user has access to
            ttl: Time-to-live in seconds (defaults to USER_TTL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate user sites cache key
            key = get_user_sites_key(user_id)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = USER_TTL
            
            # Store site IDs in cache
            logger.info(f"Storing site access for user: {user_id}, sites: {site_ids}")
            return self.set(key, site_ids, ttl)
        except Exception as e:
            logger.error(f"Error storing site access for user {user_id}: {str(e)}")
            return False
    
    def get_user_site_access(self, user_id: str) -> Optional[List[int]]:
        """
        Retrieve user's site access list from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of site IDs or None if not found
        """
        try:
            # Generate user sites cache key
            key = get_user_sites_key(user_id)
            
            # Get site IDs from cache
            logger.debug(f"Getting site access for user: {user_id}")
            return self.get(key, data_type='json')
        except Exception as e:
            logger.error(f"Error retrieving site access for user {user_id}: {str(e)}")
            return None
    
    def invalidate_user_site_access(self, user_id: str) -> int:
        """
        Invalidate user's site access cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of invalidated cache entries
        """
        try:
            # Use user invalidator to invalidate site access
            logger.info(f"Invalidating site access for user: {user_id}")
            return self._user_invalidator.invalidate_site_access(user_id)
        except Exception as e:
            logger.error(f"Error invalidating site access for user {user_id}: {str(e)}")
            return 0
    
    def store_interaction(self, interaction_id: int, interaction_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store interaction data in cache.
        
        Args:
            interaction_id: Interaction identifier
            interaction_data: Interaction data dictionary
            ttl: Time-to-live in seconds (defaults to INTERACTION_TTL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate interaction cache key
            key = get_interaction_key(interaction_id)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = INTERACTION_TTL
            
            # Store interaction data in cache
            logger.info(f"Storing interaction: {interaction_id}")
            return self.set(key, interaction_data, ttl)
        except Exception as e:
            logger.error(f"Error storing interaction {interaction_id}: {str(e)}")
            return False
    
    def get_interaction(self, interaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve interaction data from cache.
        
        Args:
            interaction_id: Interaction identifier
            
        Returns:
            Interaction data or None if not found
        """
        try:
            # Generate interaction cache key
            key = get_interaction_key(interaction_id)
            
            # Get interaction data from cache
            logger.debug(f"Getting interaction: {interaction_id}")
            return self.get(key, data_type='json')
        except Exception as e:
            logger.error(f"Error retrieving interaction {interaction_id}: {str(e)}")
            return None
    
    def invalidate_interaction(self, interaction_id: int, site_id: int) -> int:
        """
        Invalidate interaction cache and related lists/search results.
        
        Args:
            interaction_id: Interaction identifier
            site_id: Site identifier for the interaction
            
        Returns:
            Number of invalidated cache entries
        """
        try:
            # Use interaction invalidator to invalidate interaction and related caches
            logger.info(f"Invalidating interaction: {interaction_id} in site: {site_id}")
            return self._interaction_invalidator.invalidate_with_related(interaction_id, site_id)
        except Exception as e:
            logger.error(f"Error invalidating interaction {interaction_id}: {str(e)}")
            return 0
    
    def store_interaction_list(self, site_id: int, page: int, size: int, list_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store paginated list of interactions in cache.
        
        Args:
            site_id: Site identifier
            page: Page number
            size: Page size
            list_data: List data to cache
            ttl: Time-to-live in seconds (defaults to INTERACTION_TTL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate interaction list cache key
            key = get_interaction_list_key(site_id, page, size)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = INTERACTION_TTL
            
            # Store list data in cache
            logger.info(f"Storing interaction list for site: {site_id}, page: {page}, size: {size}")
            return self.set(key, list_data, ttl)
        except Exception as e:
            logger.error(f"Error storing interaction list for site {site_id}: {str(e)}")
            return False
    
    def get_interaction_list(self, site_id: int, page: int, size: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve paginated list of interactions from cache.
        
        Args:
            site_id: Site identifier
            page: Page number
            size: Page size
            
        Returns:
            List data or None if not found
        """
        try:
            # Generate interaction list cache key
            key = get_interaction_list_key(site_id, page, size)
            
            # Get list data from cache
            logger.debug(f"Getting interaction list for site: {site_id}, page: {page}, size: {size}")
            return self.get(key, data_type='json')
        except Exception as e:
            logger.error(f"Error retrieving interaction list for site {site_id}: {str(e)}")
            return None
    
    def invalidate_interaction_lists(self, site_id: int) -> int:
        """
        Invalidate all interaction list cache entries for a site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Number of invalidated cache entries
        """
        try:
            # Use interaction invalidator to invalidate interaction lists
            logger.info(f"Invalidating interaction lists for site: {site_id}")
            return self._interaction_invalidator.invalidate_lists(site_id)
        except Exception as e:
            logger.error(f"Error invalidating interaction lists for site {site_id}: {str(e)}")
            return 0
    
    def store_search_results(self, site_id: int, query: str, filters: Dict[str, Any], page: int, size: int, results: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store search results in cache.
        
        Args:
            site_id: Site identifier
            query: Search query string
            filters: Search filters dictionary
            page: Page number
            size: Page size
            results: Search results to cache
            ttl: Time-to-live in seconds (defaults to SEARCH_TTL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate query hash from query string and filters
            query_hash = self.generate_query_hash(query, filters)
            
            # Generate search results cache key
            key = get_search_results_key(site_id, query_hash, page, size)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = SEARCH_TTL
            
            # Store search results in cache
            logger.info(f"Storing search results for site: {site_id}, query: {query}, page: {page}, size: {size}")
            return self.set(key, results, ttl)
        except Exception as e:
            logger.error(f"Error storing search results for site {site_id}, query {query}: {str(e)}")
            return False
    
    def get_search_results(self, site_id: int, query: str, filters: Dict[str, Any], page: int, size: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve search results from cache.
        
        Args:
            site_id: Site identifier
            query: Search query string
            filters: Search filters dictionary
            page: Page number
            size: Page size
            
        Returns:
            Search results or None if not found
        """
        try:
            # Generate query hash from query string and filters
            query_hash = self.generate_query_hash(query, filters)
            
            # Generate search results cache key
            key = get_search_results_key(site_id, query_hash, page, size)
            
            # Get search results from cache
            logger.debug(f"Getting search results for site: {site_id}, query: {query}, page: {page}, size: {size}")
            return self.get(key, data_type='json')
        except Exception as e:
            logger.error(f"Error retrieving search results for site {site_id}, query {query}: {str(e)}")
            return None
    
    def invalidate_search_results(self, site_id: int) -> int:
        """
        Invalidate all search result cache entries for a site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Number of invalidated cache entries
        """
        try:
            # Use search invalidator to invalidate search results
            logger.info(f"Invalidating search results for site: {site_id}")
            return self._search_invalidator.invalidate(site_id)
        except Exception as e:
            logger.error(f"Error invalidating search results for site {site_id}: {str(e)}")
            return 0
    
    def invalidate_user_cache(self, user_id: str) -> int:
        """
        Invalidate all user-related cache entries.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of invalidated cache entries
        """
        try:
            # Use user invalidator to invalidate all user cache entries
            logger.info(f"Invalidating all cache entries for user: {user_id}")
            return self._user_invalidator.invalidate(user_id)
        except Exception as e:
            logger.error(f"Error invalidating cache for user {user_id}: {str(e)}")
            return 0
    
    def invalidate_site_cache(self, site_id: int) -> int:
        """
        Invalidate all site-related cache entries.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Number of invalidated cache entries
        """
        try:
            # Use site invalidator to invalidate all site cache entries
            logger.info(f"Invalidating all cache entries for site: {site_id}")
            return self._site_invalidator.invalidate(site_id)
        except Exception as e:
            logger.error(f"Error invalidating cache for site {site_id}: {str(e)}")
            return 0
    
    def health_check(self) -> bool:
        """
        Check if the cache service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check Redis connection health
            return self._redis_client.health_check()
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all cache entries (use with caution).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log warning before clearing all cache
            logger.warning("Clearing ALL cache entries - this should only be used in development/testing")
            
            # Connect to Redis and flush all keys
            self._redis_client.connect()
            if self._redis_client._redis_client:
                self._redis_client._redis_client.flushdb()
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def generate_query_hash(self, query: str, filters: Dict[str, Any]) -> str:
        """
        Generate a deterministic hash for a search query and filters.
        
        Args:
            query: Search query string
            filters: Dictionary of filter criteria
            
        Returns:
            Hash string representing the query and filters
        """
        try:
            # Create a normalized string representation of filters
            # Sort the keys to ensure deterministic ordering
            filter_str = json.dumps(filters, sort_keys=True)
            
            # Combine query and filters
            combined = f"{query}:{filter_str}"
            
            # Generate MD5 hash
            return hashlib.md5(combined.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error generating query hash: {str(e)}")
            # Return fallback hash based on query alone
            return hashlib.md5(query.encode('utf-8')).hexdigest()


def get_cache_service() -> CacheService:
    """
    Singleton factory function to get or create the cache service instance.
    
    Returns:
        Singleton instance of the cache service
    """
    global _cache_service_instance
    
    # Create instance if it doesn't exist
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
        logger.info("Created new cache service instance")
    
    return _cache_service_instance