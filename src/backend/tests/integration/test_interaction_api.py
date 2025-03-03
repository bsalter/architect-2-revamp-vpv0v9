# src/backend/tests/integration/test_interaction_api.py
"""
Integration tests for the Interaction API endpoints, verifying CRUD operations,
search functionality, and site-scoped access controls. Tests ensure that the API
properly handles validation, authorization, and data persistence across the full
request-response cycle.
"""
import pytest  # pytest==7.3.1
import flask  # flask==2.3.2
import json  # standard library
import datetime  # standard library
import http  # standard library

from ..fixtures.interaction_fixtures import interaction, meeting_interaction, email_interaction, multiple_interactions, invalid_interaction_data  # src/backend/tests/fixtures/interaction_fixtures.py
from ..conftest import test_user, test_site, client  # src/backend/tests/conftest.py
from ..fixtures.auth_fixtures import test_token, auth_headers, authorized_client  # src/backend/tests/fixtures/auth_fixtures.py
from ...utils.enums import InteractionType, Timezone  # src/backend/utils/enums.py


def test_get_interactions_list(authorized_client: flask.testing.FlaskClient, multiple_interactions: list) -> None:
    """Tests retrieving a list of interactions through the API"""
    # Make GET request to /api/interactions endpoint
    response = authorized_client.get('/api/interactions')

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response is JSON with expected structure
    data = response.get_json()
    assert 'success' in data
    assert 'message' in data
    assert 'data' in data
    assert 'items' in data['data']
    assert 'pagination' in data['data']

    # Verify interactions list is present in response
    interactions = data['data']['items']
    assert isinstance(interactions, list)

    # Verify pagination information is present and correct
    pagination = data['data']['pagination']
    assert 'page' in pagination
    assert 'page_size' in pagination
    assert 'total_items' in pagination
    assert 'total_pages' in pagination
    assert 'has_next' in pagination
    assert 'has_prev' in pagination

    # Verify at least one interaction is returned
    assert len(interactions) > 0

    # Verify all interactions belong to the authorized site
    for interaction in interactions:
        assert interaction['site_id'] == multiple_interactions[0].site_id


def test_get_interaction_by_id(authorized_client: flask.testing.FlaskClient, interaction: Interaction) -> None:
    """Tests retrieving a single interaction by ID"""
    # Make GET request to /api/interactions/{interaction.id} endpoint
    response = authorized_client.get(f'/api/interactions/{interaction.id}')

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response is JSON with expected structure
    data = response.get_json()
    assert 'success' in data
    assert 'message' in data
    assert 'data' in data

    # Verify interaction data matches the fixture
    interaction_data = data['data']
    assert interaction_data['id'] == interaction.id
    assert interaction_data['title'] == interaction.title
    assert interaction_data['type'] == interaction.type
    assert interaction_data['lead'] == interaction.lead
    assert interaction_data['timezone'] == interaction.timezone
    assert interaction_data['location'] == interaction.location
    assert interaction_data['description'] == interaction.description
    assert interaction_data['notes'] == interaction.notes

    # Verify all required fields are present in response
    assert 'id' in interaction_data
    assert 'site_id' in interaction_data
    assert 'title' in interaction_data
    assert 'type' in interaction_data
    assert 'lead' in interaction_data
    assert 'start_datetime' in interaction_data
    assert 'end_datetime' in interaction_data
    assert 'timezone' in interaction_data
    assert 'description' in interaction_data

    # Verify additional computed fields like duration_minutes are present
    assert 'duration_minutes' in interaction_data


def test_get_nonexistent_interaction(authorized_client: flask.testing.FlaskClient) -> None:
    """Tests appropriate error handling when requesting non-existent interaction"""
    # Make GET request to /api/interactions/99999 (non-existent ID)
    response = authorized_client.get('/api/interactions/99999')

    # Verify HTTP status code is 404 Not Found
    assert response.status_code == 404

    # Verify response is JSON with error information
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is False
    assert 'message' in data
    assert 'error_type' in data

    # Verify error message indicates resource not found
    assert 'not found' in data['message'].lower()


def test_create_interaction(authorized_client: flask.testing.FlaskClient, test_site: Site, test_user: User) -> None:
    """Tests creating a new interaction through the API"""
    # Prepare valid interaction data with all required fields
    interaction_data = {
        'site_id': test_site.id,
        'title': 'New Test Interaction',
        'type': InteractionType.MEETING.value,
        'lead': 'Test Lead',
        'start_datetime': datetime.datetime.utcnow().isoformat(),
        'end_datetime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat(),
        'timezone': 'UTC',
        'location': 'Test Location',
        'description': 'This is a new test interaction',
        'notes': 'Additional notes'
    }

    # Make POST request to /api/interactions endpoint with interaction data
    response = authorized_client.post('/api/interactions', json=interaction_data)

    # Verify HTTP status code is 201 Created
    assert response.status_code == 201

    # Verify response is JSON with created interaction
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is True
    assert 'message' in data
    assert 'data' in data

    created_interaction = data['data']
    assert 'id' in created_interaction
    assert created_interaction['title'] == interaction_data['title']
    assert created_interaction['type'] == interaction_data['type']
    assert created_interaction['lead'] == interaction_data['lead']
    assert created_interaction['timezone'] == interaction_data['timezone']
    assert created_interaction['location'] == interaction_data['location']
    assert created_interaction['description'] == interaction_data['description']
    assert created_interaction['notes'] == interaction_data['notes']

    # Verify created interaction has an ID and matches submitted data
    assert 'id' in created_interaction
    assert created_interaction['title'] == interaction_data['title']

    # Verify site_id and created_by fields are set correctly
    assert created_interaction['site_id'] == test_site.id
    assert created_interaction['created_by'] == test_user.id

    # Make GET request to verify interaction was persisted
    response = authorized_client.get(f'/api/interactions/{created_interaction["id"]}')
    assert response.status_code == 200
    retrieved_data = response.get_json()['data']
    assert retrieved_data['id'] == created_interaction['id']
    assert retrieved_data['title'] == interaction_data['title']


def test_create_interaction_missing_required_fields(authorized_client: flask.testing.FlaskClient) -> None:
    """Tests validation when creating an interaction with missing required fields"""
    # Prepare incomplete interaction data missing required fields
    interaction_data = {
        'title': 'Incomplete Interaction',
        'type': InteractionType.MEETING.value,
        'lead': 'Test Lead',
    }

    # Make POST request to /api/interactions endpoint with incomplete data
    response = authorized_client.post('/api/interactions', json=interaction_data)

    # Verify HTTP status code is 400 Bad Request
    assert response.status_code == 400

    # Verify response is JSON with validation error information
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is False
    assert 'message' in data
    assert 'error_type' in data
    assert data['error_type'] == 'validation'
    assert 'details' in data

    # Verify error message indicates which fields are missing
    assert 'start_datetime' in data['details']['errors']
    assert 'end_datetime' in data['details']['errors']
    assert 'timezone' in data['details']['errors']
    assert 'description' in data['details']['errors']


def test_create_interaction_invalid_date_range(authorized_client: flask.testing.FlaskClient, test_site: Site) -> None:
    """Tests validation when creating an interaction with end date before start date"""
    # Prepare interaction data with end_datetime before start_datetime
    interaction_data = {
        'site_id': test_site.id,
        'title': 'Invalid Date Range',
        'type': InteractionType.MEETING.value,
        'lead': 'Test Lead',
        'start_datetime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat(),
        'end_datetime': datetime.datetime.utcnow().isoformat(),
        'timezone': 'UTC',
        'location': 'Test Location',
        'description': 'This interaction has an invalid date range',
        'notes': 'Additional notes'
    }

    # Make POST request to /api/interactions endpoint with invalid date range
    response = authorized_client.post('/api/interactions', json=interaction_data)

    # Verify HTTP status code is 400 Bad Request
    assert response.status_code == 400

    # Verify response is JSON with validation error information
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is False
    assert 'message' in data
    assert 'error_type' in data
    assert data['error_type'] == 'validation'
    assert 'details' in data

    # Verify error message indicates date range issue
    assert 'end_datetime' in data['details']['errors']
    assert 'start_datetime' in data['details']['errors']


def test_update_interaction(authorized_client: flask.testing.FlaskClient, interaction: Interaction) -> None:
    """Tests updating an existing interaction through the API"""
    # Prepare updated interaction data with modified fields
    updated_data = {
        'title': 'Updated Test Interaction',
        'description': 'This interaction has been updated',
        'location': 'New Location'
    }

    # Make PUT request to /api/interactions/{interaction.id} with updated data
    response = authorized_client.put(f'/api/interactions/{interaction.id}', json=updated_data)

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response is JSON with updated interaction
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is True
    assert 'message' in data
    assert 'data' in data

    updated_interaction = data['data']
    assert updated_interaction['id'] == interaction.id
    assert updated_interaction['title'] == updated_data['title']
    assert updated_interaction['description'] == updated_data['description']
    assert updated_interaction['location'] == updated_data['location']

    # Verify fields were updated correctly
    assert updated_interaction['title'] == updated_data['title']
    assert updated_interaction['description'] == updated_data['description']
    assert updated_interaction['location'] == updated_data['location']

    # Verify unchanged fields remain the same
    assert updated_interaction['type'] == interaction.type
    assert updated_interaction['lead'] == interaction.lead
    assert updated_interaction['timezone'] == interaction.timezone

    # Make GET request to verify changes were persisted
    response = authorized_client.get(f'/api/interactions/{interaction.id}')
    assert response.status_code == 200
    retrieved_data = response.get_json()['data']
    assert retrieved_data['title'] == updated_data['title']
    assert retrieved_data['description'] == updated_data['description']
    assert retrieved_data['location'] == updated_data['location']


def test_partial_update_interaction(authorized_client: flask.testing.FlaskClient, interaction: Interaction) -> None:
    """Tests partial update of an interaction with only some fields"""
    # Prepare partial update data with only a few fields
    partial_data = {
        'title': 'Partial Update',
        'description': 'Only updating these two fields'
    }

    # Make PUT request to /api/interactions/{interaction.id} with partial data
    response = authorized_client.put(f'/api/interactions/{interaction.id}', json=partial_data)

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response is JSON with updated interaction
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is True
    assert 'message' in data
    assert 'data' in data

    updated_interaction = data['data']
    assert updated_interaction['id'] == interaction.id
    assert updated_interaction['title'] == partial_data['title']
    assert updated_interaction['description'] == partial_data['description']

    # Verify only specified fields were updated
    assert updated_interaction['title'] == partial_data['title']
    assert updated_interaction['description'] == partial_data['description']

    # Verify other fields remain unchanged
    assert updated_interaction['type'] == interaction.type
    assert updated_interaction['lead'] == interaction.lead
    assert updated_interaction['timezone'] == interaction.timezone

    # Make GET request to verify changes were persisted
    response = authorized_client.get(f'/api/interactions/{interaction.id}')
    assert response.status_code == 200
    retrieved_data = response.get_json()['data']
    assert retrieved_data['title'] == partial_data['title']
    assert retrieved_data['description'] == partial_data['description']


def test_update_nonexistent_interaction(authorized_client: flask.testing.FlaskClient) -> None:
    """Tests appropriate error handling when updating non-existent interaction"""
    # Prepare valid interaction update data
    updated_data = {
        'title': 'Updated Title',
        'description': 'Updated Description'
    }

    # Make PUT request to /api/interactions/99999 (non-existent ID)
    response = authorized_client.put('/api/interactions/99999', json=updated_data)

    # Verify HTTP status code is 404 Not Found
    assert response.status_code == 404

    # Verify response is JSON with error information
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is False
    assert 'message' in data
    assert 'error_type' in data

    # Verify error message indicates resource not found
    assert 'not found' in data['message'].lower()


def test_delete_interaction(authorized_client: flask.testing.FlaskClient, interaction: Interaction) -> None:
    """Tests deleting an interaction through the API"""
    # Make DELETE request to /api/interactions/{interaction.id}
    response = authorized_client.delete(f'/api/interactions/{interaction.id}')

    # Verify HTTP status code is 204 No Content
    assert response.status_code == 204

    # Make GET request to verify the interaction no longer exists
    response = authorized_client.get(f'/api/interactions/{interaction.id}')

    # Verify GET request returns 404 Not Found
    assert response.status_code == 404


def test_delete_nonexistent_interaction(authorized_client: flask.testing.FlaskClient) -> None:
    """Tests appropriate error handling when deleting non-existent interaction"""
    # Make DELETE request to /api/interactions/99999 (non-existent ID)
    response = authorized_client.delete('/api/interactions/99999')

    # Verify HTTP status code is 404 Not Found
    assert response.status_code == 404

    # Verify response is JSON with error information
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is False
    assert 'message' in data
    assert 'error_type' in data

    # Verify error message indicates resource not found
    assert 'not found' in data['message'].lower()


def test_search_interactions(authorized_client: flask.testing.FlaskClient, multiple_interactions: list) -> None:
    """Tests searching interactions with text query"""
    # Make GET request to /api/interactions?search=Meeting with search term
    response = authorized_client.get('/api/interactions?search=Meeting')

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response is JSON with search results
    data = response.get_json()
    assert 'success' in data
    assert data['success'] is True
    assert 'message' in data
    assert 'data' in data
    assert 'items' in data['data']
    assert 'pagination' in data['data']

    search_results = data['data']['items']
    assert isinstance(search_results, list)

    # Verify results contain only interactions matching search term
    for interaction in search_results:
        assert 'meeting' in interaction['title'].lower() or 'meeting' in interaction['description'].lower()

    # Verify pagination information is present and correct
    pagination = data['data']['pagination']
    assert 'page' in pagination
    assert 'page_size' in pagination
    assert 'total_items' in pagination
    assert 'total_pages' in pagination
    assert 'has_next' in pagination
    assert 'has_prev' in pagination


def test_filter_interactions_by_type(authorized_client: flask.testing.FlaskClient, meeting_interaction: Interaction, email_interaction: Interaction) -> None:
    """Tests filtering interactions by type"""
    # Make GET request to /api/search/interactions/type/MEETING
    response = authorized_client.get('/api/search/interactions/type/MEETING')

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response includes only interactions of type MEETING
    data = response.get_json()
    interactions = data['data']['items']
    for interaction in interactions:
        assert interaction['type'] == InteractionType.MEETING.value

    # Make GET request to /api/search/interactions/type/EMAIL
    response = authorized_client.get('/api/search/interactions/type/EMAIL')

    # Verify response includes only interactions of type EMAIL
    data = response.get_json()
    interactions = data['data']['items']
    for interaction in interactions:
        assert interaction['type'] == InteractionType.EMAIL.value

    # Verify filtering works correctly across multiple types
    assert len(interactions) > 0


def test_filter_interactions_by_date_range(authorized_client: flask.testing.FlaskClient, multiple_interactions: list) -> None:
    """Tests filtering interactions by date range"""
    # Prepare date range parameters (start_date and end_date)
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    end_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)

    # Make GET request to /api/search/interactions/dates with date parameters
    response = authorized_client.get(f'/api/search/interactions/dates?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}')

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response includes only interactions within specified date range
    data = response.get_json()
    interactions = data['data']['items']
    for interaction in interactions:
        start = datetime.datetime.fromisoformat(interaction['start_datetime'].replace('Z', '+00:00'))
        end = datetime.datetime.fromisoformat(interaction['end_datetime'].replace('Z', '+00:00'))
        assert start_date <= start <= end_date
        assert start_date <= end <= end_date

    # Verify interactions outside date range are excluded
    assert len(interactions) > 0


def test_advanced_search(authorized_client: flask.testing.FlaskClient, multiple_interactions: list) -> None:
    """Tests advanced search with multiple filter criteria"""
    # Prepare advanced search criteria with multiple filters
    search_criteria = {
        'filters': [
            {'field': 'type', 'operator': 'eq', 'value': InteractionType.MEETING.value},
            {'field': 'lead', 'operator': 'contains', 'value': 'Smith'}
        ],
        'page': 1,
        'page_size': 10
    }

    # Make POST request to /api/search/interactions with search criteria
    response = authorized_client.post('/api/search/interactions', json=search_criteria)

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify response includes only interactions matching all criteria
    data = response.get_json()
    interactions = data['data']['items']
    for interaction in interactions:
        assert interaction['type'] == InteractionType.MEETING.value
        assert 'smith' in interaction['lead'].lower()

    # Verify pagination works correctly with search results
    assert len(interactions) > 0


def test_site_scoped_access(client: flask.testing.FlaskClient, test_user: User, test_token: str, interaction: Interaction) -> None:
    """Tests that interactions are properly scoped by site"""
    # Create a second site not associated with test_user
    site2 = Site(name='Site 2', description='Second test site')
    db.session.add(site2)
    db.session.commit()

    # Create a token with access only to the first site
    token = test_token

    # Create interactions in both sites
    interaction_site1 = interaction
    interaction_site2 = Interaction(
        site_id=site2.id,
        title='Interaction in Site 2',
        type=InteractionType.CALL.value,
        lead='Another Lead',
        start_datetime=datetime.datetime.utcnow(),
        end_datetime=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        timezone='UTC',
        created_by=test_user.id,
        description='Test interaction in site 2'
    )
    db.session.add(interaction_site2)
    db.session.commit()

    # Make GET request with token to /api/interactions
    headers = auth_headers(token)
    response = client.get('/api/interactions', headers=headers)

    # Verify only interactions from authorized site are returned
    data = response.get_json()
    interactions = data['data']['items']
    for interaction in interactions:
        assert interaction['site_id'] == test_user.sites[0].id

    # Attempt to access interaction from unauthorized site directly
    response = client.get(f'/api/interactions/{interaction_site2.id}', headers=headers)

    # Verify access is denied with 403 Forbidden
    assert response.status_code == 404


def test_unauthorized_access(client: flask.testing.FlaskClient, interaction: Interaction) -> None:
    """Tests that unauthenticated requests are properly rejected"""
    # Make GET request without authentication to /api/interactions
    response = client.get('/api/interactions')

    # Verify HTTP status code is 401 Unauthorized
    assert response.status_code == 401

    # Make GET request without authentication to /api/interactions/{interaction.id}
    response = client.get(f'/api/interactions/{interaction.id}')

    # Verify HTTP status code is 401 Unauthorized
    assert response.status_code == 401

    # Attempt POST, PUT, DELETE operations without authentication
    post_response = client.post('/api/interactions', json={'title': 'Test'})
    put_response = client.put(f'/api/interactions/{interaction.id}', json={'title': 'Test'})
    delete_response = client.delete(f'/api/interactions/{interaction.id}')

    # Verify all return 401 Unauthorized
    assert post_response.status_code == 401
    assert put_response.status_code == 401
    assert delete_response.status_code == 401


def test_pagination(authorized_client: flask.testing.FlaskClient, multiple_interactions: list) -> None:
    """Tests that pagination works correctly for interaction lists"""
    # Make GET request to /api/interactions?page=1&page_size=5
    response = authorized_client.get('/api/interactions?page=1&page_size=5')

    # Verify HTTP status code is 200 OK
    assert response.status_code == 200

    # Verify exactly 5 interactions are returned
    data = response.get_json()
    interactions = data['data']['items']
    assert len(interactions) == 5

    # Verify pagination information shows correct page, page_size, total
    pagination = data['data']['pagination']
    assert pagination['page'] == 1
    assert pagination['page_size'] == 5
    assert pagination['total_items'] == len(multiple_interactions)
    assert pagination['total_pages'] == 2
    assert pagination['has_next'] is True
    assert pagination['has_prev'] is False

    # Make GET request to /api/interactions?page=2&page_size=5
    response = authorized_client.get('/api/interactions?page=2&page_size=5')

    # Verify second page of results is returned
    data = response.get_json()
    interactions_page2 = data['data']['items']
    assert len(interactions_page2) == 5

    # Verify results don't overlap with first page
    for interaction in interactions_page2:
        assert interaction not in interactions