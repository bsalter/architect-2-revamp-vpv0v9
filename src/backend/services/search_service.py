"""
Service that implements business logic for searching and filtering Interaction records with site-scoping,
caching, and optimized query execution. Provides various search methods to power the Interaction Finder interface.
"""

import typing
from typing import Dict, List, Optional, Union, Any, Tuple
import datetime
from datetime import datetime
import hashlib
import json

from ..repositories.interaction_repository import InteractionRepository
from ..auth.site_context_service import SiteContextService
from ..cache.cache_service import get_cache_service
from ..cache.cache_keys import get_search_results_key, SEARCH_TTL
from ..api.helpers.pagination import validate_pagination_params
from ..utils.error_util import SiteContextError, ValidationError
from ..logging.structured_logger import StructuredLogger
from ..utils.enums import InteractionType

# Initialize logger
logger = StructuredLogger(__name__)

# Global constants for pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def generate_query_hash(query: str, filters: Dict[str, Any]) -> str:
    """
    Generates a deterministic hash for a search query and filters for caching.

    Args:
        query: Search query string
        filters: Dictionary of filter criteria

    Returns:
        MD5 hash string representing the query parameters
    """
    try:
        # Sort filter keys to ensure consistent order
        sorted_filter_keys = sorted(filters.keys())
        sorted_filters = {key: filters[key] for key in sorted_filter_keys}

        # Serialize filters to JSON string
        filter_str = json.dumps(sorted_filters, sort_keys=True)

        # Combine query string and serialized filters
        combined = f"{query}:{filter_str}"

        # Generate MD5 hash of the combined string
        hash_object = hashlib.md5(combined.encode('utf-8'))
        hash_str = hash_object.hexdigest()

        # Return hexadecimal digest of the hash
        return hash_str
    except Exception as e:
        logger.error(f"Error generating query hash: {str(e)}")
        return ""


class SearchService:
    """
    Service for handling interaction search operations with caching and site-scoping.
    """

    def __init__(self, interaction_repository: InteractionRepository, site_context_service: SiteContextService):
        """
        Initialize the search service with required dependencies.

        Args:
            interaction_repository: Data access for interaction records with search capabilities
            site_context_service: Ensure site-scoped data access for search operations
        """
        self._interaction_repository = interaction_repository
        self._site_context_service = site_context_service
        self._cache_service = get_cache_service()
        logger.info("SearchService initialized")

    @SiteContextService.requires_site_context
    def search(self, query: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search interactions by text query across all fields.

        Args:
            query: Search query string
            page: Page number for pagination (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (interactions list, total count)
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Validate pagination parameters
            page, page_size = validate_pagination_params(page, page_size)

            # Generate cache key for search query
            cache_key = get_search_results_key(site_id, generate_query_hash(query, {}), page, page_size)

            # Try to get cached search results
            cached_results = self._cache_service.get(cache_key, data_type='json')
            if cached_results:
                logger.debug(f"Cache hit for search query: {query}, returning cached results")
                return cached_results['interactions'], cached_results['total']

            # If no cache hit, search using interaction_repository
            interactions, total_count = self._interaction_repository.search(query, page, page_size)

            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Cache results with SEARCH_TTL
            results = {'interactions': formatted_interactions, 'total': total_count}
            self._cache_service.set(cache_key, results, SEARCH_TTL)

            # Log search operation with metrics
            logger.info(f"Search query: {query}, results: {total_count}, cached: True")

            # Return tuple of (interactions list, total count)
            return formatted_interactions, total_count

        except Exception as e:
            logger.error(f"Error during search operation: {str(e)}")
            return [], 0

    @SiteContextService.requires_site_context
    def advanced_search(self, search_params: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Perform advanced search with multiple filters and sorting.

        Args:
            search_params: Dictionary containing search parameters

        Returns:
            Tuple of (interactions list, total count)
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Extract filters, sorting, and pagination from search_params
            filters = search_params.get('filters', {})
            sort_by = search_params.get('sort_by')
            sort_desc = search_params.get('sort_desc', False)
            page = search_params.get('page', 1)
            page_size = search_params.get('page_size', DEFAULT_PAGE_SIZE)

            # Validate all search parameters
            page, page_size = validate_pagination_params(page, page_size)

            # Generate cache key for advanced search
            cache_key = get_search_results_key(site_id, generate_query_hash("", filters), page, page_size)

            # Try to get cached search results
            cached_results = self._cache_service.get(cache_key, data_type='json')
            if cached_results:
                logger.debug(f"Cache hit for advanced search, returning cached results")
                return cached_results['interactions'], cached_results['total']

            # If no cache hit, perform advanced search using interaction_repository
            interactions, total_count = self._interaction_repository.advanced_search(
                filters, sort_by, sort_desc, page, page_size
            )

            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Cache results with SEARCH_TTL
            results = {'interactions': formatted_interactions, 'total': total_count}
            self._cache_service.set(cache_key, results, SEARCH_TTL)

            # Log advanced search operation with metrics
            logger.info(f"Advanced search, results: {total_count}, cached: True")

            # Return tuple of (interactions list, total count)
            return formatted_interactions, total_count

        except Exception as e:
            logger.error(f"Error during advanced search operation: {str(e)}")
            return [], 0

    @SiteContextService.requires_site_context
    def search_by_date_range(self, start_date: datetime, end_date: datetime, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search interactions within a specific date range.

        Args:
            start_date: Start date for range
            end_date: End date for range
            page: Page number for pagination (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (interactions list, total count)
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Validate date range (end_date >= start_date)
            if end_date < start_date:
                raise ValidationError("End date must be after start date")

            # Validate pagination parameters
            page, page_size = validate_pagination_params(page, page_size)

            # Generate cache key for date range search
            filters = {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
            cache_key = get_search_results_key(site_id, generate_query_hash("", filters), page, page_size)

            # Try to get cached search results
            cached_results = self._cache_service.get(cache_key, data_type='json')
            if cached_results:
                logger.debug(f"Cache hit for date range search, returning cached results")
                return cached_results['interactions'], cached_results['total']

            # If no cache hit, search using interaction_repository.find_by_date_range
            interactions, total_count = self._interaction_repository.find_by_date_range(start_date, end_date, page, page_size)

            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Cache results with SEARCH_TTL
            results = {'interactions': formatted_interactions, 'total': total_count}
            self._cache_service.set(cache_key, results, SEARCH_TTL)

            # Log date range search operation with metrics
            logger.info(f"Date range search, results: {total_count}, cached: True")

            # Return tuple of (interactions list, total count)
            return formatted_interactions, total_count

        except Exception as e:
            logger.error(f"Error during date range search operation: {str(e)}")
            return [], 0

    @SiteContextService.requires_site_context
    def search_by_type(self, interaction_type: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search interactions by interaction type.

        Args:
            interaction_type: Type of interaction to search for
            page: Page number for pagination (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (interactions list, total count)
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Validate interaction_type using InteractionType.is_valid
            if not InteractionType.is_valid(interaction_type):
                raise ValidationError("Invalid interaction type")

            # Validate pagination parameters
            page, page_size = validate_pagination_params(page, page_size)

            # Generate cache key for type search
            filters = {'type': interaction_type}
            cache_key = get_search_results_key(site_id, generate_query_hash("", filters), page, page_size)

            # Try to get cached search results
            cached_results = self._cache_service.get(cache_key, data_type='json')
            if cached_results:
                logger.debug(f"Cache hit for type search, returning cached results")
                return cached_results['interactions'], cached_results['total']

            # If no cache hit, search using interaction_repository.find_by_type
            interactions, total_count = self._interaction_repository.find_by_type(interaction_type, page, page_size)

            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Cache results with SEARCH_TTL
            results = {'interactions': formatted_interactions, 'total': total_count}
            self._cache_service.set(cache_key, results, SEARCH_TTL)

            # Log type search operation with metrics
            logger.info(f"Type search, results: {total_count}, cached: True")

            # Return tuple of (interactions list, total count)
            return formatted_interactions, total_count

        except Exception as e:
            logger.error(f"Error during type search operation: {str(e)}")
            return [], 0

    @SiteContextService.requires_site_context
    def search_by_lead(self, lead: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search interactions by lead person.

        Args:
            lead: Lead person to search for
            page: Page number for pagination (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (interactions list, total count)
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Validate lead parameter is not empty
            if not lead:
                raise ValidationError("Lead parameter cannot be empty")

            # Validate pagination parameters
            page, page_size = validate_pagination_params(page, page_size)

            # Generate cache key for lead search
            filters = {'lead': lead}
            cache_key = get_search_results_key(site_id, generate_query_hash("", filters), page, page_size)

            # Try to get cached search results
            cached_results = self._cache_service.get(cache_key, data_type='json')
            if cached_results:
                logger.debug(f"Cache hit for lead search, returning cached results")
                return cached_results['interactions'], cached_results['total']

            # If no cache hit, search using interaction_repository.find_by_lead
            interactions, total_count = self._interaction_repository.find_by_lead(lead, page, page_size)

            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Cache results with SEARCH_TTL
            results = {'interactions': formatted_interactions, 'total': total_count}
            self._cache_service.set(cache_key, results, SEARCH_TTL)

            # Log lead search operation with metrics
            logger.info(f"Lead search, results: {total_count}, cached: True")

            # Return tuple of (interactions list, total count)
            return formatted_interactions, total_count

        except Exception as e:
            logger.error(f"Error during lead search operation: {str(e)}")
            return [], 0

    @SiteContextService.requires_site_context
    def get_upcoming_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get interactions scheduled in the future.

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of upcoming interaction records
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Get current datetime
            now = datetime.utcnow()

            # Get upcoming interactions from repository with site scope
            interactions = self._interaction_repository.get_upcoming_interactions(limit)

            # Cache results with SEARCH_TTL
            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Log upcoming interactions retrieval
            logger.info(f"Retrieved {len(interactions)} upcoming interactions")

            # Format and return interaction list
            return formatted_interactions

        except Exception as e:
            logger.error(f"Error retrieving upcoming interactions: {str(e)}")
            return []

    @SiteContextService.requires_site_context
    def get_recent_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recently completed interactions.

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of recent interaction records
        """
        try:
            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()

            # Get current datetime
            now = datetime.utcnow()

            # Get recent interactions from repository with site scope
            interactions = self._interaction_repository.get_recent_interactions(limit)

            # Process and format search results
            formatted_interactions = self.format_interaction_data(interactions)

            # Log recent interactions retrieval
            logger.info(f"Retrieved {len(interactions)} recent interactions")

            # Format and return interaction list
            return formatted_interactions

        except Exception as e:
            logger.error(f"Error retrieving recent interactions: {str(e)}")
            return []

    def invalidate_search_cache(self, site_id: int = None) -> int:
        """
        Invalidate search cache entries for a site.

        Args:
            site_id: ID of the site to invalidate cache for. If None, get current site ID from site_context_service

        Returns:
            Number of invalidated cache entries
        """
        try:
            # If site_id is None, get current site ID from site_context_service
            if site_id is None:
                site_id = self._site_context_service.get_current_site_id()

            # Use cache service to invalidate search results for the site
            count = self._cache_service.invalidate_search_results(site_id)

            # Log cache invalidation operation
            logger.info(f"Invalidated search cache for site: {site_id}, entries: {count}")

            # Return number of invalidated cache entries
            return count

        except Exception as e:
            logger.error(f"Error invalidating search cache: {str(e)}")
            return 0

    def format_interaction_data(self, interactions: List[object]) -> List[Dict[str, Any]]:
        """
        Format interaction data for API response.

        Args:
            interactions: List of interaction objects

        Returns:
            List of formatted interaction dictionaries
        """
        try:
            # Initialize empty result list
            formatted_list = []

            # Iterate through interaction objects
            for interaction in interactions:
                # Convert each interaction to dictionary representation
                interaction_dict = interaction.to_dict()

                # Add any computed properties needed for the response
                formatted_list.append(interaction_dict)

            # Return the formatted list
            return formatted_list

        except Exception as e:
            logger.error(f"Error formatting interaction data: {str(e)}")
            return []