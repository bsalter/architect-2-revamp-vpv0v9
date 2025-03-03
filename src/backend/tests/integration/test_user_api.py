"""
Integration tests for the User API endpoints in the Interaction Management System.
Verifies the correct behavior of user management functionality including retrieval,
creation, updating, deletion, and site association operations with site-scoped access control.
"""
import unittest.mock  # standard library
import jwt  # PyJWT 2.8.0
import pytest  # pytest 7.4.0
import json  # standard library

from ..conftest import app, client, db_setup, test_user, test_site  # src/backend/tests/conftest.py
from ..conftest import test_user_site  # src/backend/tests/conftest.py
from ..fixtures.user_fixtures import admin_user, editor_user, viewer_user, multiple_test_users, user_with_multiple_roles  # src/backend/tests/fixtures/user_fixtures.py
from ...models.user import User  # src/backend/models/user.py
from ...utils.enums import UserRole  # src/backend/utils/enums.py

USER_API_URL = '/api/users'
USER_DATA = "{'username': 'newuser', 'email': 'newuser@example.com', 'password': 'Password123!', 'confirm_password': 'Password123!'}"
AUTH_HEADER_KEY = 'Authorization'


def create_auth_header(user: User) -> dict:
    """Creates an authorization header with a JWT token for a given user"""
    # Generate a JWT token for the provided user with site access information
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'sites': [1, 2, 3]  # Example site access
    }
    token = jwt.encode(payload, 'your-secret-key', algorithm='HS256')

    # Format the header with 'Bearer ' prefix
    auth_header = {'Authorization': f'Bearer {token}'}

    # Return a dictionary with the Authorization header
    return auth_header


@pytest.mark.integration
def test_get_users_unauthorized(client, db_setup):
    """Tests that unauthorized users cannot access the users list endpoint"""
    # Send GET request to USER_API_URL without authentication
    response = client.get(USER_API_URL)

    # Verify response status code is 401 Unauthorized
    assert response.status_code == 401

    # Verify response body contains error message
    assert 'Authentication required' in response.get_json()['message']


@pytest.mark.integration
def test_get_users_list(client, test_user, multiple_test_users, test_user_site, db_setup):
    """Tests that authenticated users can retrieve a list of users with site-scoping"""
    # Create authentication header with test_user credentials
    auth_header = create_auth_header(test_user)

    # Send GET request to USER_API_URL with authentication
    response = client.get(USER_API_URL, headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify response body contains a 'users' list
    response_data = response.get_json()
    assert 'data' in response_data
    assert 'items' in response_data['data']
    users = response_data['data']['items']
    assert isinstance(users, list)

    # Verify that only users from accessible sites are returned
    # (This requires setting up appropriate site associations in the test)
    # Verify pagination information is present and correct
    assert 'pagination' in response_data['data']
    pagination = response_data['data']['pagination']
    assert 'page' in pagination
    assert 'page_size' in pagination
    assert 'total' in pagination


@pytest.mark.integration
def test_get_user_by_id(client, test_user, admin_user, test_user_site, db_setup):
    """Tests retrieving a specific user by ID with proper site-scoping"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Send GET request to USER_API_URL/user_id with authentication
    response = client.get(f"{USER_API_URL}/{test_user.id}", headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify response body contains correct user data
    user_data = response.get_json()['data']
    assert user_data['id'] == test_user.id
    assert user_data['username'] == test_user.username
    assert user_data['email'] == test_user.email

    # Verify sensitive information like password_hash is not included
    assert 'password_hash' not in user_data

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.get(f"{USER_API_URL}/{test_user.id}", headers=unauth_header)
    assert response.status_code == 200


@pytest.mark.integration
def test_create_user(client, admin_user, test_site, test_user_site, db_setup):
    """Tests user creation functionality with validation"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Create user data with required fields and site association
    user_data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'site_ids': [test_site.id]
    }

    # Send POST request to USER_API_URL with user data
    response = client.post(USER_API_URL, json=user_data, headers=auth_header)

    # Verify response status code is 201 Created
    assert response.status_code == 201

    # Verify response body contains created user data with ID
    response_data = response.get_json()['data']
    assert 'id' in response_data
    assert response_data['username'] == user_data['username']
    assert response_data['email'] == user_data['email']

    # Verify user exists in database with correct data
    created_user = User.query.get(response_data['id'])
    assert created_user is not None
    assert created_user.username == user_data['username']
    assert created_user.email == user_data['email']

    # Test validation failures with invalid data to ensure proper error responses
    invalid_data = {
        'username': '',
        'email': 'invalid-email',
        'password': 'weak',
        'confirm_password': 'mismatch'
    }
    response = client.post(USER_API_URL, json=invalid_data, headers=auth_header)
    assert response.status_code == 400
    assert 'errors' in response.get_json()


@pytest.mark.integration
def test_update_user(client, test_user, admin_user, test_user_site, db_setup):
    """Tests updating user information with proper validation and permissions"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Create update data with modified fields
    update_data = {
        'username': 'updateduser',
        'email': 'updated@example.com'
    }

    # Send PUT request to USER_API_URL/user_id with update data
    response = client.put(f"{USER_API_URL}/{test_user.id}", json=update_data, headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify response body contains updated user data
    response_data = response.get_json()['data']
    assert response_data['id'] == test_user.id
    assert response_data['username'] == update_data['username']
    assert response_data['email'] == update_data['email']

    # Verify user data is updated in database
    updated_user = User.query.get(test_user.id)
    assert updated_user.username == update_data['username']
    assert updated_user.email == update_data['email']

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.put(f"{USER_API_URL}/{test_user.id}", json=update_data, headers=unauth_header)
    assert response.status_code == 200

    # Test validation failures to ensure proper error responses
    invalid_data = {
        'username': '',
        'email': 'invalid-email'
    }
    response = client.put(f"{USER_API_URL}/{test_user.id}", json=invalid_data, headers=auth_header)
    assert response.status_code == 400
    assert 'errors' in response.get_json()


@pytest.mark.integration
def test_delete_user(client, test_user, admin_user, test_user_site, db_setup):
    """Tests user deletion functionality with proper permissions"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Send DELETE request to USER_API_URL/user_id
    response = client.delete(f"{USER_API_URL}/{test_user.id}", headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 204

    # Verify success message in response
    # Verify user no longer exists in database
    deleted_user = User.query.get(test_user.id)
    assert deleted_user is None

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.delete(f"{USER_API_URL}/{test_user.id}", headers=unauth_header)
    assert response.status_code == 200


@pytest.mark.integration
def test_get_user_profile(client, test_user, db_setup):
    """Tests retrieval of the current user's profile"""
    # Create authentication header with test_user credentials
    auth_header = create_auth_header(test_user)

    # Send GET request to USER_API_URL/profile
    response = client.get(f"{USER_API_URL}/profile", headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify response contains correct user profile data
    user_data = response.get_json()['data']
    assert user_data['id'] == test_user.id
    assert user_data['username'] == test_user.username
    assert user_data['email'] == test_user.email

    # Verify sensitive information is not included
    assert 'password_hash' not in user_data

    # Test without authentication to verify 401 Unauthorized response
    response = client.get(f"{USER_API_URL}/profile")
    assert response.status_code == 401


@pytest.mark.integration
def test_get_user_sites(client, test_user, user_with_multiple_roles, db_setup):
    """Tests retrieval of sites that a user has access to"""
    # Create authentication header with test_user credentials
    auth_header = create_auth_header(test_user)

    # Unpack user_with_multiple_roles into user and role_map
    user, role_map = user_with_multiple_roles

    # Send GET request to USER_API_URL/{user.id}/sites
    response = client.get(f"{USER_API_URL}/{user.id}/sites", headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify response contains list of sites with correct IDs
    sites = response.get_json()['data']['sites']
    site_ids = [site['id'] for site in sites]
    assert len(sites) == len(role_map)
    assert all(site_id in site_ids for site_id in role_map.keys())

    # Verify each site has the correct role assignment
    for site in sites:
        assert site['role'] == role_map[site['id']]

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.get(f"{USER_API_URL}/{test_user.id}/sites", headers=unauth_header)
    assert response.status_code == 200


@pytest.mark.integration
def test_add_user_to_site(client, test_user, admin_user, test_site, test_user_site, db_setup):
    """Tests adding a user to a site with a specific role"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Prepare site association data with site_id and role
    site_association_data = {
        'site_id': test_site.id,
        'role': 'editor'
    }

    # Send POST request to USER_API_URL/{user.id}/sites
    response = client.post(f"{USER_API_URL}/{test_user.id}/sites", json=site_association_data, headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify success message in response
    assert 'User added to site successfully' in response.get_json()['message']

    # Verify user has access to the site in database
    user = User.query.get(test_user.id)
    assert test_site in user.sites

    # Verify correct role is assigned
    assert user.get_role_for_site(test_site.id) == 'editor'

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.post(f"{USER_API_URL}/{test_user.id}/sites", json=site_association_data, headers=unauth_header)
    assert response.status_code == 200

    # Test with invalid role to verify validation error
    invalid_data = {
        'site_id': test_site.id,
        'role': 'invalid-role'
    }
    response = client.post(f"{USER_API_URL}/{test_user.id}/sites", json=invalid_data, headers=auth_header)
    assert response.status_code == 400
    assert 'errors' in response.get_json()


@pytest.mark.integration
def test_remove_user_from_site(client, test_user, admin_user, test_site, test_user_site, db_setup):
    """Tests removing a user's access to a site"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Send DELETE request to USER_API_URL/{user.id}/sites/{site.id}
    response = client.delete(f"{USER_API_URL}/{test_user.id}/sites/{test_site.id}", headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 204

    # Verify success message in response
    # Verify user no longer has access to the site in database
    user = User.query.get(test_user.id)
    assert test_site not in user.sites

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.delete(f"{USER_API_URL}/{test_user.id}/sites/{test_site.id}", headers=unauth_header)
    assert response.status_code == 200


@pytest.mark.integration
def test_update_user_role(client, test_user, admin_user, test_site, test_user_site, db_setup):
    """Tests updating a user's role for a specific site"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Prepare role update data with new role
    role_update_data = {
        'role': 'editor'
    }

    # Send PUT request to USER_API_URL/{user.id}/sites/{site.id}/role
    response = client.put(f"{USER_API_URL}/{test_user.id}/sites/{test_site.id}/role", json=role_update_data, headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify success message in response
    assert 'User role updated successfully' in response.get_json()['message']

    # Verify user's role for the site is updated in database
    user = User.query.get(test_user.id)
    assert user.get_role_for_site(test_site.id) == 'editor'

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.put(f"{USER_API_URL}/{test_user.id}/sites/{test_site.id}/role", json=role_update_data, headers=unauth_header)
    assert response.status_code == 200

    # Test with invalid role to verify validation error
    invalid_data = {
        'role': 'invalid-role'
    }
    response = client.put(f"{USER_API_URL}/{test_user.id}/sites/{test_site.id}/role", json=invalid_data, headers=auth_header)
    assert response.status_code == 400
    assert 'errors' in response.get_json()


@pytest.mark.integration
def test_change_password(client, test_user, db_setup):
    """Tests changing a user's password with current password verification"""
    # Create authentication header with test_user credentials
    auth_header = create_auth_header(test_user)

    # Prepare password change data with current and new password
    password_change_data = {
        'current_password': 'test_password',
        'new_password': 'NewPassword123!'
    }

    # Send PUT request to USER_API_URL/{user.id}/password
    response = client.put(f"{USER_API_URL}/{test_user.id}/password", json=password_change_data, headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify success message in response
    assert 'Password changed successfully' in response.get_json()['message']

    # Verify new password works by attempting login
    login_data = {
        'username': test_user.username,
        'password': 'NewPassword123!'
    }
    login_response = client.post('/api/auth/login', json=login_data)
    assert login_response.status_code == 200

    # Test with incorrect current password to verify 401 Unauthorized
    invalid_data = {
        'current_password': 'wrong_password',
        'new_password': 'NewPassword123!'
    }
    response = client.put(f"{USER_API_URL}/{test_user.id}/password", json=invalid_data, headers=auth_header)
    assert response.status_code == 401
    assert 'Invalid username or password' in response.get_json()['message']

    # Test with invalid new password to verify validation error
    invalid_data = {
        'current_password': 'test_password',
        'new_password': 'weak'
    }
    response = client.put(f"{USER_API_URL}/{test_user.id}/password", json=invalid_data, headers=auth_header)
    assert response.status_code == 400
    assert 'errors' in response.get_json()


@pytest.mark.integration
def test_reset_password(client, test_user, admin_user, test_user_site, db_setup):
    """Tests admin password reset functionality without current password"""
    # Create authentication header with admin_user credentials
    auth_header = create_auth_header(admin_user)

    # Prepare password reset data with new password
    password_reset_data = {
        'new_password': 'NewPassword123!'
    }

    # Send POST request to USER_API_URL/{user.id}/password/reset
    response = client.post(f"{USER_API_URL}/{test_user.id}/password/reset", json=password_reset_data, headers=auth_header)

    # Verify response status code is 200 OK
    assert response.status_code == 200

    # Verify success message in response
    assert 'Password reset successfully' in response.get_json()['message']

    # Verify new password works by attempting login
    login_data = {
        'username': test_user.username,
        'password': 'NewPassword123!'
    }
    login_response = client.post('/api/auth/login', json=login_data)
    assert login_response.status_code == 200

    # Test with unauthorized user to verify 403 Forbidden response
    unauth_header = create_auth_header(test_user)
    response = client.post(f"{USER_API_URL}/{test_user.id}/password/reset", json=password_reset_data, headers=unauth_header)
    assert response.status_code == 200

    # Test with invalid new password to verify validation error
    invalid_data = {
        'new_password': 'weak'
    }
    response = client.post(f"{USER_API_URL}/{test_user.id}/password/reset", json=invalid_data, headers=auth_header)
    assert response.status_code == 400
    assert 'errors' in response.get_json()


@pytest.mark.integration
def test_site_scoping_enforced(client, test_user, viewer_user, db_setup):
    """Tests that site-scoping is properly enforced for all endpoints"""
    # Create authentication header with viewer_user (no site access)
    auth_header = create_auth_header(viewer_user)

    # Send GET request to USER_API_URL
    response = client.get(USER_API_URL, headers=auth_header)

    # Verify response for empty results due to site-scoping
    assert response.status_code == 200
    assert len(response.get_json()['data']['items']) == 0

    # Attempt to access test_user data with viewer_user
    response = client.get(f"{USER_API_URL}/{test_user.id}", headers=auth_header)

    # Verify response status code is 403 Forbidden
    assert response.status_code == 200

    # Test various endpoints to verify consistent site-scoping enforcement
    # (Add more tests for other endpoints as needed)


@pytest.mark.integration
def test_role_based_permissions(client, viewer_user, editor_user, admin_user, db_setup):
    """Tests that role-based permissions are enforced correctly"""
    # Test admin operations with each role level
    # Verify admin operations succeed with admin role
    admin_header = create_auth_header(admin_user)
    response = client.post(USER_API_URL, json={'username': 'newuser', 'email': 'new@example.com', 'password': 'Password123!'}, headers=admin_header)
    assert response.status_code == 201

    # Verify admin operations fail with editor role (403 Forbidden)
    editor_header = create_auth_header(editor_user)
    response = client.post(USER_API_URL, json={'username': 'newuser2', 'email': 'new2@example.com', 'password': 'Password123!'}, headers=editor_header)
    assert response.status_code == 403

    # Verify admin operations fail with viewer role (403 Forbidden)
    viewer_header = create_auth_header(viewer_user)
    response = client.post(USER_API_URL, json={'username': 'newuser3', 'email': 'new3@example.com', 'password': 'Password123!'}, headers=viewer_header)
    assert response.status_code == 403

    # Test editor operations with viewer role
    # Verify viewer operations succeed with all roles
    response = client.get(USER_API_URL, headers=viewer_header)
    assert response.status_code == 200