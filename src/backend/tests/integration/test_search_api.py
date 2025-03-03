"""
Integration tests for the Search API endpoints in the Interaction Management System.
Tests verify search functionality across interaction records with various filtering capabilities while ensuring proper site-scoping and authentication.
"""
import json  # standard library
from datetime import datetime  # standard library
from unittest import mock  # standard library

import flask  # flask==2.3.2
import pytest  # pytest==7.3.1

from src.backend.auth.jwt_service import jwt_service  # src/backend/auth/jwt_service.py
from src.backend.utils.enums import InteractionType  # src/backend/utils/enums.py
from ..conftest import app, client, db_setup, test_user, test_site, test_user_site  # src/backend/tests/conftest.py
from ..fixtures.interaction_fixtures import call_interaction, future_interaction, interaction, meeting_interaction, multiple_interactions, past_interaction  # src/backend/tests/fixtures/interaction_fixtures.py

SEARCH_API_BASE_URL = '/api/search'


def get_auth_headers(user: dict) -> dict:
    """Helper function to create authentication headers with JWT token

    Args:
        user (dict): User data

    Returns:
        dict: Headers with Authorization bearer token
    """
    token = jwt_service.generate_token(user)  # Generate JWT token for user with site claims
    headers = {'Authorization': f'Bearer {token}'}  # Create Authorization header with bearer token
    return headers  # Return headers dictionary


def test_search_interactions_authenticated(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, multiple_interactions: list):
    """Test that authenticated users can search interactions

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        multiple_interactions (fixture): Multiple interactions fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.get(f'{SEARCH_API_BASE_URL}/interactions?query=Test', headers=headers)  # Make GET request to search endpoint with query parameter
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert 'results' in data  # Verify response contains results and pagination
    assert 'pagination' in data
    assert len(data['results']) > 0  # Verify results list contains interactions matching query


def test_search_interactions_unauthenticated(client: flask.testing.FlaskClient, multiple_interactions: list):
    """Test that unauthenticated requests are rejected

    Args:
        client (fixture): Flask test client
        multiple_interactions (fixture): Multiple interactions fixture
    """
    response = client.get(f'{SEARCH_API_BASE_URL}/interactions')  # Make GET request to search endpoint without auth headers
    assert response.status_code == 401  # Verify 401 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert 'message' in data  # Verify response contains error message about authentication


def test_search_interactions_site_scoping(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, multiple_interactions: list):
    """Test that search results are correctly site-scoped

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        multiple_interactions (fixture): Multiple interactions fixture
    """
    # Create second site with interactions
    second_site = test_site(name='Second Site')
    InteractionFactory.create_batch_for_site(size=5, site=second_site, user=test_user)

    headers = get_auth_headers(test_user)  # Get authentication headers for test user with only first site access
    response = client.get(f'{SEARCH_API_BASE_URL}/interactions', headers=headers)  # Make GET request to search endpoint
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert all(item['site_id'] == test_site.id for item in data['results'])  # Verify results only contain interactions from authorized site
    assert not any(item['site_id'] == second_site.id for item in data['results'])  # Verify no interactions from unauthorized site are included in results


def test_advanced_search(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, multiple_interactions: list, meeting_interaction: dict, call_interaction: dict):
    """Test advanced search with multiple filters

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        multiple_interactions (fixture): Multiple interactions fixture
        meeting_interaction (fixture): Meeting type interaction fixture
        call_interaction (fixture): Call type interaction fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    search_data = {'filters': [{'field': 'type', 'operator': 'eq', 'value': InteractionType.MEETING.value}]}  # Create advanced search request with filters for meeting type
    response = client.post(f'{SEARCH_API_BASE_URL}/advanced', headers=headers, json=search_data)  # Make POST request to advanced search endpoint with filters
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert all(item['type'] == InteractionType.MEETING.value for item in data['results'])  # Verify results only contain meeting interactions
    assert not any(item['type'] == InteractionType.CALL.value for item in data['results'])  # Verify no call interactions are included in results


def test_search_by_date_range(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, past_interaction: dict, future_interaction: dict):
    """Test search by date range functionality

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        past_interaction (fixture): Past interaction fixture
        future_interaction (fixture): Future interaction fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    past_week = datetime.now() - datetime.timedelta(days=7)  # Create date range for past week
    response = client.get(f'{SEARCH_API_BASE_URL}/interactions/dates?start_date={past_week.isoformat()}&end_date={datetime.now().isoformat()}', headers=headers)  # Make GET request to date range search endpoint with date parameters
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert any(item['title'] == past_interaction.title for item in data['results'])  # Verify results contain past interactions
    assert not any(item['title'] == future_interaction.title for item in data['results'])  # Verify future interactions are not included in results


def test_search_by_type(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, meeting_interaction: dict, call_interaction: dict):
    """Test search by interaction type functionality

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        meeting_interaction (fixture): Meeting type interaction fixture
        call_interaction (fixture): Call type interaction fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.get(f'{SEARCH_API_BASE_URL}/type/{InteractionType.MEETING.value}', headers=headers)  # Make GET request to type search endpoint with MEETING type
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert all(item['type'] == InteractionType.MEETING.value for item in data['results'])  # Verify results only contain meeting type interactions

    response = client.get(f'{SEARCH_API_BASE_URL}/type/{InteractionType.CALL.value}', headers=headers)  # Make second request for CALL type
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert all(item['type'] == InteractionType.CALL.value for item in data['results'])  # Verify second results only contain call type interactions


def test_search_by_lead(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, multiple_interactions: list):
    """Test search by lead person functionality

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        multiple_interactions (fixture): Multiple interactions fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    lead_name = multiple_interactions[0].lead  # Get lead name from first interaction
    response = client.get(f'{SEARCH_API_BASE_URL}/lead/{lead_name}', headers=headers)  # Make GET request to lead search endpoint with specific lead name
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert all(item['lead'] == lead_name for item in data['results'])  # Verify results only contain interactions with matching lead name


def test_get_upcoming_interactions(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, future_interaction: dict, past_interaction: dict):
    """Test retrieving upcoming interactions

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        future_interaction (fixture): Future interaction fixture
        past_interaction (fixture): Past interaction fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.get(f'{SEARCH_API_BASE_URL}/upcoming', headers=headers)  # Make GET request to upcoming interactions endpoint
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert any(item['title'] == future_interaction.title for item in data['data'])  # Verify results only contain future interactions
    assert not any(item['title'] == past_interaction.title for item in data['data'])  # Verify past interactions are not included in results


def test_get_recent_interactions(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, future_interaction: dict, past_interaction: dict):
    """Test retrieving recent interactions

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        future_interaction (fixture): Future interaction fixture
        past_interaction (fixture): Past interaction fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.get(f'{SEARCH_API_BASE_URL}/recent', headers=headers)  # Make GET request to recent interactions endpoint
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert any(item['title'] == past_interaction.title for item in data['data'])  # Verify results only contain past interactions
    assert not any(item['title'] == future_interaction.title for item in data['data'])  # Verify future interactions are not included in results


def test_pagination(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict, multiple_interactions: list):
    """Test pagination functionality in search results

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
        multiple_interactions (fixture): Multiple interactions fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.get(f'{SEARCH_API_BASE_URL}/interactions?page=1&page_size=5', headers=headers)  # Make GET request to search endpoint with page=1 and page_size=5
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert len(data['results']) == 5  # Verify results contains exactly 5 items
    assert data['pagination']['page'] == 1  # Verify pagination info shows correct page and total
    assert data['pagination']['total'] == len(multiple_interactions)

    response = client.get(f'{SEARCH_API_BASE_URL}/interactions?page=2&page_size=5', headers=headers)  # Make second request with page=2
    assert response.status_code == 200  # Verify 200 status code
    data = json.loads(response.get_data(as_text=True))  # Parse response JSON
    assert len(data['results']) == 5  # Verify results contains exactly 5 items
    assert data['pagination']['page'] == 2  # Verify pagination info shows correct page and total
    assert data['pagination']['total'] == len(multiple_interactions)


def test_invalid_search_parameters(client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict):
    """Test handling of invalid search parameters

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.get(f'{SEARCH_API_BASE_URL}/interactions?page=-1', headers=headers)  # Make GET request with invalid page parameter (negative value)
    assert response.status_code == 400  # Verify 400 status code with validation error
    data = json.loads(response.get_data(as_text=True))
    assert 'errors' in data

    search_data = {'filters': [{'field': 'type', 'operator': 'invalid', 'value': 'Meeting'}]}  # Make advanced search request with invalid filter operator
    response = client.post(f'{SEARCH_API_BASE_URL}/advanced', headers=headers, json=search_data)
    assert response.status_code == 400  # Verify 400 status code with validation error message
    data = json.loads(response.get_data(as_text=True))
    assert 'errors' in data

    response = client.get(f'{SEARCH_API_BASE_URL}/interactions/dates?start_date=2024-01-02&end_date=2024-01-01', headers=headers)  # Make date range search with end date before start date
    assert response.status_code == 400  # Verify 400 status code with appropriate validation error
    data = json.loads(response.get_data(as_text=True))
    assert 'errors' in data


@mock.patch('src.backend.services.search_service.SearchService.invalidate_search_cache')
def test_invalidate_search_cache(mock_invalidate_cache, client: flask.testing.FlaskClient, test_user: dict, test_site: dict, test_user_site: dict):
    """Test cache invalidation functionality

    Args:
        client (fixture): Flask test client
        test_user (fixture): Test user fixture
        test_site (fixture): Test site fixture
        test_user_site (fixture): User-site association fixture
    """
    headers = get_auth_headers(test_user)  # Get authentication headers for test user
    response = client.post(f'{SEARCH_API_BASE_URL}/cache/invalidate', headers=headers)  # Make POST request to invalidate cache endpoint
    assert response.status_code == 200  # Verify 200 status code
    assert mock_invalidate_cache.called  # Verify cache service invalidate method was called with correct site ID
    mock_invalidate_cache.assert_called_with(test_site.id)