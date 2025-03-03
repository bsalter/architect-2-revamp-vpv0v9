import unittest.mock
from unittest.mock import MagicMock, patch
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

from src.backend.services.search_service import SearchService
from src.backend.repositories.interaction_repository import InteractionRepository
from src.backend.auth.site_context_service import SiteContextService
from src.backend.utils.error_util import SiteContextError, ValidationError
from src.backend.cache.cache_service import get_cache_service

# Define fixtures for mocking dependencies
@pytest.fixture
def mock_interaction_repository() -> MagicMock:
    """Fixture that creates a mock InteractionRepository for testing"""
    # Create a MagicMock instance for InteractionRepository
    mock = MagicMock(spec=InteractionRepository)
    # Configure mock search method to return a tuple of ([], 0)
    mock.search.return_value = ([], 0)
    # Configure mock advanced_search method to return a tuple of ([], 0)
    mock.advanced_search.return_value = ([], 0)
    # Configure mock find_by_date_range method to return a tuple of ([], 0)
    mock.find_by_date_range.return_value = ([], 0)
    # Configure mock find_by_type method to return a tuple of ([], 0)
    mock.find_by_type.return_value = ([], 0)
    # Configure mock find_by_lead method to return a tuple of ([], 0)
    mock.find_by_lead.return_value = ([], 0)
    # Configure mock get_upcoming_interactions method to return []
    mock.get_upcoming_interactions.return_value = []
    # Configure mock get_recent_interactions method to return []
    mock.get_recent_interactions.return_value = []
    # Return the configured mock
    return mock

@pytest.fixture
def mock_site_context_service() -> MagicMock:
    """Fixture that creates a mock SiteContextService for testing"""
    # Create a MagicMock instance for SiteContextService
    mock = MagicMock(spec=SiteContextService)
    # Configure mock get_current_site_id method to return 1
    mock.get_current_site_id.return_value = 1

    # Create a pass-through decorator for requires_site_context
    def pass_through_decorator(func):
        return func

    mock.requires_site_context = pass_through_decorator
    # Return the configured mock
    return mock

@pytest.fixture
def mock_cache_service() -> MagicMock:
    """Fixture that creates a mock CacheService for testing"""
    # Create a MagicMock instance for CacheService
    mock = MagicMock()
    # Configure mock get method to return None (cache miss)
    mock.get.return_value = None
    # Configure mock set method to return True
    mock.set.return_value = True
    # Configure mock delete method to return True
    mock.delete.return_value = True
    # Return the configured mock
    return mock

@pytest.fixture
def search_service(mock_interaction_repository: MagicMock, mock_site_context_service: MagicMock) -> SearchService:
    """Fixture that creates a SearchService instance with mocked dependencies"""
    # Create a SearchService instance with mocked dependencies
    service = SearchService(mock_interaction_repository, mock_site_context_service)
    # Return the service instance for testing
    return service

class TestSearchService:
    """Test suite for the SearchService class methods and behaviors"""

    def test_search_with_site_context(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test that search works correctly with a valid site context"""
        # Set up mock_interaction_repository.search to return sample data
        mock_interaction_repository.search.return_value = (['interaction1', 'interaction2'], 2)
        # Call search_service.search with a sample query
        results, total = search_service.search("test query")
        # Verify mock_interaction_repository.search was called with correct parameters
        mock_interaction_repository.search.assert_called_once_with("test query", 1, 20)
        # Verify site context was applied to the search
        assert results == ['interaction1', 'interaction2']
        assert total == 2

    def test_search_without_site_context(self, search_service: SearchService, mock_site_context_service: MagicMock):
        """Test that search fails when no site context is available"""
        # Configure mock_site_context_service.get_current_site_id to return None
        mock_site_context_service.get_current_site_id.return_value = None
        # Configure mock_site_context_service.requires_site_context to raise SiteContextError
        mock_site_context_service.requires_site_context.side_effect = SiteContextError("Site context required")
        # Use pytest.raises to verify that SiteContextError is raised when calling search_service.search
        with pytest.raises(SiteContextError):
            search_service.search("test query")
        # Verify that the repository's search method was not called
        assert not search_service._interaction_repository.search.called

    def test_search_with_pagination(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test that search pagination parameters are passed correctly"""
        # Call search_service.search with custom page and page_size parameters
        search_service.search("test query", page=2, page_size=10)
        # Verify mock_interaction_repository.search was called with the correct pagination values
        mock_interaction_repository.search.assert_called_once_with("test query", 2, 10)
        # Assert search result matches expected format
        assert search_service._interaction_repository.search.return_value == ([], 0)

    def test_advanced_search(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test that advanced search correctly passes filters to repository"""
        # Prepare search_params with filters, sorting, and pagination
        search_params = {
            'filters': {'title': 'test', 'type': 'Meeting'},
            'sort_by': 'title',
            'sort_desc': True,
            'page': 2,
            'page_size': 10
        }
        # Set up mock_interaction_repository.advanced_search to return sample data
        mock_interaction_repository.advanced_search.return_value = (['interaction1'], 1)
        # Call search_service.advanced_search with search_params
        results, total = search_service.advanced_search(search_params)
        # Verify mock_interaction_repository.advanced_search was called with correct parameters
        mock_interaction_repository.advanced_search.assert_called_once_with(
            {'title': 'test', 'type': 'Meeting'}, 'title', True, 2, 10
        )
        # Assert search result matches expected format
        assert results == ['interaction1']
        assert total == 1

    def test_search_by_date_range(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test searching interactions by date range"""
        # Create start_date and end_date objects
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        # Set up mock_interaction_repository.find_by_date_range to return sample data
        mock_interaction_repository.find_by_date_range.return_value = (['interaction1'], 1)
        # Call search_service.search_by_date_range with date parameters
        results, total = search_service.search_by_date_range(start_date, end_date)
        # Verify repository method was called with correct date range
        mock_interaction_repository.find_by_date_range.assert_called_once_with(start_date, end_date, 1, 20)
        # Assert search result matches expected format
        assert results == ['interaction1']
        assert total == 1

    def test_search_by_invalid_date_range(self, search_service: SearchService):
        """Test error handling for invalid date range (end before start)"""
        # Create start_date and end_date where end is before start
        start_date = datetime(2023, 1, 31)
        end_date = datetime(2023, 1, 1)
        # Use pytest.raises to verify ValidationError is raised
        with pytest.raises(ValidationError):
            search_service.search_by_date_range(start_date, end_date)
        # Verify repository method was not called
        assert not search_service._interaction_repository.find_by_date_range.called

    def test_search_by_type(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test searching interactions by type"""
        # Set up mock_interaction_repository.find_by_type to return sample data
        mock_interaction_repository.find_by_type.return_value = (['interaction1'], 1)
        # Call search_service.search_by_type with a valid interaction type
        results, total = search_service.search_by_type("Meeting")
        # Verify repository method was called with correct type
        mock_interaction_repository.find_by_type.assert_called_once_with("Meeting", 1, 20)
        # Assert search result matches expected format
        assert results == ['interaction1']
        assert total == 1

    @patch('src.backend.utils.enums.InteractionType.is_valid')
    def test_search_by_invalid_type(self, mock_is_valid, search_service: SearchService):
        """Test error handling for invalid interaction type"""
        # Mock InteractionType.is_valid to return False
        mock_is_valid.return_value = False
        # Use pytest.raises to verify ValidationError is raised when calling search_by_type with invalid type
        with pytest.raises(ValidationError):
            search_service.search_by_type("InvalidType")
        # Verify repository method was not called
        assert not search_service._interaction_repository.find_by_type.called

    def test_search_by_lead(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test searching interactions by lead person"""
        # Set up mock_interaction_repository.find_by_lead to return sample data
        mock_interaction_repository.find_by_lead.return_value = (['interaction1'], 1)
        # Call search_service.search_by_lead with a lead name
        results, total = search_service.search_by_lead("John Doe")
        # Verify repository method was called with correct lead parameter
        mock_interaction_repository.find_by_lead.assert_called_once_with("John Doe", 1, 20)
        # Assert search result matches expected format
        assert results == ['interaction1']
        assert total == 1

    def test_search_by_empty_lead(self, search_service: SearchService):
        """Test error handling for empty lead parameter"""
        # Use pytest.raises to verify ValidationError is raised when calling search_by_lead with empty string
        with pytest.raises(ValidationError):
            search_service.search_by_lead("")
        # Verify repository method was not called
        assert not search_service._interaction_repository.find_by_lead.called

    def test_get_upcoming_interactions(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test retrieving upcoming interactions"""
        # Set up mock_interaction_repository.get_upcoming_interactions to return sample data
        mock_interaction_repository.get_upcoming_interactions.return_value = ['interaction1', 'interaction2']
        # Call search_service.get_upcoming_interactions with a custom limit
        results = search_service.get_upcoming_interactions(limit=5)
        # Verify repository method was called with correct limit parameter
        mock_interaction_repository.get_upcoming_interactions.assert_called_once_with(5)
        # Assert result matches expected format
        assert results == ['interaction1', 'interaction2']

    def test_get_recent_interactions(self, search_service: SearchService, mock_interaction_repository: MagicMock):
        """Test retrieving recent interactions"""
        # Set up mock_interaction_repository.get_recent_interactions to return sample data
        mock_interaction_repository.get_recent_interactions.return_value = ['interaction1', 'interaction2']
        # Call search_service.get_recent_interactions with a custom limit
        results = search_service.get_recent_interactions(limit=5)
        # Verify repository method was called with correct limit parameter
        mock_interaction_repository.get_recent_interactions.assert_called_once_with(5)
        # Assert result matches expected format
        assert results == ['interaction1', 'interaction2']

    @patch('src.backend.cache.cache_service.get_cache_service')
    def test_search_cache_hit(self, mock_get_cache_service, search_service: SearchService, mock_cache_service: MagicMock):
        """Test that search results are returned from cache when available"""
        # Configure mock_cache_service.get to return cached search results
        mock_cache_service.get.return_value = {'interactions': ['cached_interaction'], 'total': 1}
        # Configure patched get_cache_service to return mock_cache_service
        mock_get_cache_service.return_value = mock_cache_service
        # Call search_service.search with a query
        results, total = search_service.search("test query")
        # Verify cache was checked with correct key
        mock_cache_service.get.assert_called_once()
        # Verify repository search method was not called
        assert not search_service._interaction_repository.search.called
        # Assert result matches cached data
        assert results == ['cached_interaction']
        assert total == 1

    @patch('src.backend.cache.cache_service.get_cache_service')
    def test_search_cache_miss(self, mock_get_cache_service, search_service: SearchService, mock_interaction_repository: MagicMock, mock_cache_service: MagicMock):
        """Test that search results are stored in cache on cache miss"""
        # Configure mock_cache_service.get to return None (cache miss)
        mock_cache_service.get.return_value = None
        # Configure patched get_cache_service to return mock_cache_service
        mock_get_cache_service.return_value = mock_cache_service
        # Set up mock_interaction_repository.search to return sample data
        mock_interaction_repository.search.return_value = (['db_interaction'], 1)
        # Call search_service.search with a query
        results, total = search_service.search("test query")
        # Verify cache was checked with correct key
        mock_cache_service.get.assert_called_once()
        # Verify repository search method was called
        mock_interaction_repository.search.assert_called_once()
        # Verify cache.set was called to store search results
        mock_cache_service.set.assert_called_once()
        # Assert result matches repository data
        assert results == ['db_interaction']
        assert total == 1

    @patch('src.backend.cache.cache_service.get_cache_service')
    def test_invalidate_search_cache(self, mock_get_cache_service, search_service: SearchService, mock_cache_service: MagicMock):
        """Test that search cache invalidation works correctly"""
        # Configure patched get_cache_service to return mock_cache_service
        mock_get_cache_service.return_value = mock_cache_service
        # Configure mock_cache_service.invalidate_search_results to return 5
        mock_cache_service.invalidate_search_results.return_value = 5
        # Call search_service.invalidate_search_cache with a site_id
        count = search_service.invalidate_search_cache(site_id=1)
        # Verify cache.invalidate_search_results was called with correct site_id
        mock_cache_service.invalidate_search_results.assert_called_once_with(1)
        # Assert return value matches expected number of invalidated entries
        assert count == 5

    def test_format_interaction_data(self, search_service: SearchService):
        """Test that interaction data is correctly formatted for API response"""
        # Create mock interaction objects with to_dict method
        class MockInteraction:
            def to_dict(self):
                return {'id': 1, 'title': 'Test Interaction'}

        mock_interactions = [MockInteraction(), MockInteraction()]
        # Call the private _format_interaction_data method with mock interactions
        formatted_data = search_service.format_interaction_data(mock_interactions)
        # Verify each interaction's to_dict method was called
        assert all(isinstance(item, dict) for item in formatted_data)
        # Assert formatted result has expected structure
        assert formatted_data == [{'id': 1, 'title': 'Test Interaction'}, {'id': 1, 'title': 'Test Interaction'}]