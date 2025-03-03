"""
Integration tests for the Site API endpoints, validating site management functionality
including CRUD operations, user-site associations, and site context switching.
These tests ensure site-scoped access control is properly enforced across the API layer.
"""
import http  # HTTP status codes for validating API responses
import pytest  # Testing framework and test organization/categorization
import json  # JSON parsing and serialization for API request/response handling

from ...tests.conftest import test_user, test_site, test_user_site, db_setup, app, client  # Fixtures providing test environment
from ...tests.conftest import test_token, auth_headers, authorized_client  # Fixtures providing authentication
from ..fixtures.auth_fixtures import authorized_client  # Fixture providing pre-authenticated Flask test client
from ..fixtures.site_fixtures import multiple_test_sites, sites_with_same_user  # Fixtures providing multiple test sites
from ...utils.enums import UserRole  # Enum definitions for user roles in site associations

BASE_URL = "/api/sites"


@pytest.mark.integration
def test_get_all_sites(authorized_client, sites_with_same_user):
    """
    Tests the GET /api/sites endpoint to retrieve all sites for the current user
    """
    # Send GET request to /api/sites
    response = authorized_client.get(BASE_URL)

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify response contains sites list and pagination data
    assert 'data' in data
    assert 'sites' in data['data']
    assert isinstance(data['data']['sites'], list)

    # Verify number of sites matches expected count
    assert len(data['data']['sites']) == len(sites_with_same_user)

    # Verify site IDs in response match expected site IDs
    expected_site_ids = [site.id for site in sites_with_same_user]
    actual_site_ids = [site['id'] for site in data['data']['sites']]
    assert set(actual_site_ids) == set(expected_site_ids)


@pytest.mark.integration
def test_get_site_by_id(authorized_client, test_site):
    """
    Tests the GET /api/sites/{id} endpoint to retrieve details of a specific site
    """
    # Send GET request to /api/sites/{test_site.id}
    response = authorized_client.get(f"{BASE_URL}/{test_site.id}")

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify site ID in response matches expected site ID
    assert data['data']['id'] == test_site.id

    # Verify site name in response matches expected site name
    assert data['data']['name'] == test_site.name

    # Verify site description in response matches expected site description
    assert data['data']['description'] == test_site.description

    # Verify response includes user_count and interaction_count fields
    assert 'user_count' in data['data']
    assert 'interaction_count' in data['data']


@pytest.mark.integration
def test_get_site_by_id_not_found(authorized_client):
    """
    Tests the GET /api/sites/{id} endpoint with a non-existent site ID
    """
    # Send GET request to /api/sites/9999 (non-existent ID)
    response = authorized_client.get(f"{BASE_URL}/9999")

    # Verify response status code is 404 Not Found
    assert response.status_code == http.HTTPStatus.NOT_FOUND

    # Parse JSON response body
    data = response.get_json()

    # Verify error message indicates site not found
    assert data['message'] == "Site with ID 9999 not found"


@pytest.mark.integration
def test_create_site(authorized_client, test_user):
    """
    Tests the POST /api/sites endpoint to create a new site
    """
    # Prepare site data with name and description
    site_data = {
        'name': 'New Test Site',
        'description': 'Description for new test site'
    }

    # Send POST request to /api/sites with site data
    response = authorized_client.post(BASE_URL, json=site_data)

    # Verify response status code is 201 Created
    assert response.status_code == http.HTTPStatus.CREATED

    # Parse JSON response body
    data = response.get_json()

    # Verify site name and description match submitted data
    assert data['data']['name'] == site_data['name']
    assert data['data']['description'] == site_data['description']

    # Verify site has an ID assigned
    assert 'id' in data['data']
    assert isinstance(data['data']['id'], int)

    # Verify site has created_at and updated_at timestamps
    assert 'created_at' in data['data']
    assert 'updated_at' in data['data']


@pytest.mark.integration
def test_create_site_invalid_data(authorized_client):
    """
    Tests the POST /api/sites endpoint with invalid site data
    """
    # Prepare invalid site data (empty name)
    site_data = {
        'name': '',
        'description': 'Description for new test site'
    }

    # Send POST request to /api/sites with invalid data
    response = authorized_client.post(BASE_URL, json=site_data)

    # Verify response status code is 400 Bad Request
    assert response.status_code == http.HTTPStatus.BAD_REQUEST

    # Parse JSON response body
    data = response.get_json()

    # Verify error message contains validation failure for name field
    assert 'errors' in data
    assert 'name' in data['errors']


@pytest.mark.integration
def test_update_site(authorized_client, test_site):
    """
    Tests the PUT /api/sites/{id} endpoint to update an existing site
    """
    # Prepare updated site data with new name and description
    updated_data = {
        'name': 'Updated Test Site',
        'description': 'Updated description for test site'
    }

    # Send PUT request to /api/sites/{test_site.id} with updated data
    response = authorized_client.put(f"{BASE_URL}/{test_site.id}", json=updated_data)

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify site ID remains unchanged
    assert data['data']['id'] == test_site.id

    # Verify site name and description match updated data
    assert data['data']['name'] == updated_data['name']
    assert data['data']['description'] == updated_data['description']

    # Verify updated_at timestamp is newer than created_at
    assert data['data']['updated_at'] > data['data']['created_at']


@pytest.mark.integration
def test_update_site_not_found(authorized_client):
    """
    Tests the PUT /api/sites/{id} endpoint with a non-existent site ID
    """
    # Prepare valid site update data
    updated_data = {
        'name': 'Updated Test Site',
        'description': 'Updated description for test site'
    }

    # Send PUT request to /api/sites/9999 (non-existent ID) with update data
    response = authorized_client.put(f"{BASE_URL}/9999", json=updated_data)

    # Verify response status code is 404 Not Found
    assert response.status_code == http.HTTPStatus.NOT_FOUND

    # Parse JSON response body
    data = response.get_json()

    # Verify error message indicates site not found
    assert data['message'] == "Site with ID 9999 not found"


@pytest.mark.integration
def test_delete_site(authorized_client, test_site):
    """
    Tests the DELETE /api/sites/{id} endpoint to delete an existing site
    """
    # Send DELETE request to /api/sites/{test_site.id}
    response = authorized_client.delete(f"{BASE_URL}/{test_site.id}")

    # Verify response status code is 204 No Content
    assert response.status_code == http.HTTPStatus.NO_CONTENT

    # Send GET request to /api/sites/{test_site.id} to verify deletion
    response = authorized_client.get(f"{BASE_URL}/{test_site.id}")

    # Verify GET response status code is 404 Not Found
    assert response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.integration
def test_get_site_users(authorized_client, test_site, test_user_site):
    """
    Tests the GET /api/sites/{id}/users endpoint to retrieve users associated with a site
    """
    # Send GET request to /api/sites/{test_site.id}/users
    response = authorized_client.get(f"{BASE_URL}/{test_site.id}/users")

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify response contains users list and pagination data
    assert 'data' in data
    assert 'items' in data['data']
    assert isinstance(data['data']['items'], list)

    # Verify at least one user is present in the response
    assert len(data['data']['items']) >= 1

    # Verify user ID in response matches test_user.id
    assert data['data']['items'][0]['user_id'] == test_user_site.user_id

    # Verify user role in response matches test_user_site.role
    assert data['data']['items'][0]['role'] == test_user_site.role


@pytest.mark.integration
def test_add_user_to_site(authorized_client, test_site, another_test_user):
    """
    Tests the POST /api/sites/{id}/users endpoint to add a user to a site
    """
    # Prepare user assignment data with user_id and role
    assignment_data = {
        'user_id': another_test_user.id,
        'role': 'editor'
    }

    # Send POST request to /api/sites/{test_site.id}/users with assignment data
    response = authorized_client.post(f"{BASE_URL}/{test_site.id}/users", json=assignment_data)

    # Verify response status code is 201 Created
    assert response.status_code == http.HTTPStatus.CREATED

    # Parse JSON response body
    data = response.get_json()

    # Verify user_id in response matches another_test_user.id
    assert data['data']['user_id'] == another_test_user.id

    # Verify site_id in response matches test_site.id
    assert data['data']['site_id'] == test_site.id

    # Verify role in response matches the assigned role
    assert data['data']['role'] == assignment_data['role']


@pytest.mark.integration
def test_remove_user_from_site(authorized_client, test_site, test_user, test_user_site):
    """
    Tests the DELETE /api/sites/{site_id}/users/{user_id} endpoint to remove a user from a site
    """
    # Send DELETE request to /api/sites/{test_site.id}/users/{test_user.id}
    response = authorized_client.delete(f"{BASE_URL}/{test_site.id}/users/{test_user.id}")

    # Verify response status code is 204 No Content
    assert response.status_code == http.HTTPStatus.NO_CONTENT

    # Send GET request to /api/sites/{test_site.id}/users to verify removal
    response = authorized_client.get(f"{BASE_URL}/{test_site.id}/users")
    data = response.get_json()
    users = data['data']['items']

    # Verify test_user.id is not present in the users list
    user_ids = [user['user_id'] for user in users]
    assert test_user.id not in user_ids


@pytest.mark.integration
def test_update_user_role(authorized_client, test_site, test_user, test_user_site):
    """
    Tests the PUT /api/sites/{site_id}/users/{user_id} endpoint to update a user's role for a site
    """
    # Prepare role update data with new role (change from current role)
    new_role = 'admin' if test_user_site.role != 'admin' else 'editor'
    role_data = {'role': new_role}

    # Send PUT request to /api/sites/{test_site.id}/users/{test_user.id} with role data
    response = authorized_client.put(f"{BASE_URL}/{test_site.id}/users/{test_user.id}", json=role_data)

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify user_id in response matches test_user.id
    assert data['data']['user_id'] == test_user.id

    # Verify site_id in response matches test_site.id
    assert data['data']['site_id'] == test_site.id

    # Verify role in response matches the updated role
    assert data['data']['role'] == new_role


@pytest.mark.integration
def test_get_user_sites(authorized_client, test_user, sites_with_same_user):
    """
    Tests the GET /api/sites/user/{user_id} endpoint to retrieve sites a user has access to
    """
    # Send GET request to /api/sites/user/{test_user.id}
    response = authorized_client.get(f"{BASE_URL}/user/{test_user.id}")

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify sites array contains expected number of sites
    assert len(data['data']) == len(sites_with_same_user)

    # Verify site IDs in response match expected site IDs from sites_with_same_user
    expected_site_ids = [site.id for site in sites_with_same_user]
    actual_site_ids = [site['id'] for site in data['data']]
    assert set(actual_site_ids) == set(expected_site_ids)


@pytest.mark.integration
def test_switch_site_context(authorized_client, sites_with_same_user):
    """
    Tests the POST /api/sites/{id}/context endpoint to switch the current site context
    """
    # Get a site ID from sites_with_same_user list
    site_id = sites_with_same_user[0].id

    # Send POST request to /api/sites/{site_id}/context
    response = authorized_client.post(f"{BASE_URL}/{site_id}/context")

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify site_id in response matches the requested site_id
    assert data['data']['site_id'] == site_id

    # Verify name in response matches the site name
    assert data['data']['name'] == sites_with_same_user[0].name

    # Verify role field is present and valid
    assert 'role' in data['data']


@pytest.mark.integration
def test_get_current_site_context(authorized_client, test_site, test_user_site):
    """
    Tests the GET /api/sites/context endpoint to retrieve the current site context
    """
    # Send GET request to /api/sites/context
    response = authorized_client.get(f"{BASE_URL}/context")

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify site_id in response is present
    assert 'site_id' in data['data']

    # Verify name field is present
    assert 'name' in data['data']

    # Verify role field is present
    assert 'role' in data['data']


@pytest.mark.integration
def test_search_sites(authorized_client, sites_with_same_user):
    """
    Tests the GET /api/sites/search endpoint to search sites by name or description
    """
    # Extract a search term from one of the site names
    search_term = sites_with_same_user[0].name.split()[0]

    # Send GET request to /api/sites/search?term={search_term}
    response = authorized_client.get(f"{BASE_URL}/search?term={search_term}")

    # Verify response status code is 200 OK
    assert response.status_code == http.HTTPStatus.OK

    # Parse JSON response body
    data = response.get_json()

    # Verify response contains sites list and pagination data
    assert 'data' in data
    assert 'sites' in data['data']
    assert isinstance(data['data']['sites'], list)

    # Verify at least one site is found
    assert len(data['data']['sites']) >= 1

    # Verify site name in results contains the search term
    for site in data['data']['sites']:
        assert search_term.lower() in site['name'].lower()


@pytest.mark.integration
def test_unauthorized_access(client, test_site):
    """
    Tests that unauthenticated requests to protected endpoints are rejected
    """
    # Send GET request to /api/sites without auth headers
    response = client.get(BASE_URL)
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED

    # Send GET request to /api/sites/{test_site.id} without auth headers
    response = client.get(f"{BASE_URL}/{test_site.id}")
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED

    # Send POST request to /api/sites with valid data but without auth headers
    response = client.post(BASE_URL, json={'name': 'Unauthorized Site', 'description': 'Unauthorized'})
    assert response.status_code == http.HTTPStatus.UNAUTHORIZED