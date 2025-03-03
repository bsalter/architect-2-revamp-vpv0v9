"""
Integration tests for the authentication API endpoints in the Interaction Management System.
Tests validate login, logout, token refresh, site selection, user profile retrieval,
and error handling for unauthorized and invalid requests.
"""
import pytest  # pytest==latest
import unittest.mock  # unittest==latest
import json  # json==latest

from ..conftest import app, client, db_setup, test_user, test_site, test_user_site  # src/backend/tests/conftest.py
from ..fixtures.auth_fixtures import test_token, expired_token, invalid_signature_token, token_without_site_access, auth_headers, authorized_client, mock_auth0_client  # src/backend/tests/fixtures/auth_fixtures.py


@pytest.mark.usefixtures('db_setup')
def test_login_success(client, test_user, db_setup, monkeypatch):
    """Tests successful user login with valid credentials"""
    # Create login credentials with test user's username and password
    login_credentials = {
        'username': test_user.username,
        'password': 'test_password'
    }

    # Mock the Auth0Client.authenticate method to return successful authentication
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service()._auth0_client.authenticate',
                  lambda username, password: {'access_token': 'test_access_token',
                                               'refresh_token': 'test_refresh_token',
                                               'id_token': 'test_id_token',
                                               'expires_in': 3600,
                                               'user': {'user_id': test_user.id,
                                                        'username': test_user.username,
                                                        'email': test_user.email},
                                               'site_access': [test_site.id]})

        # Send POST request to /api/auth/login with credentials
        response = client.post('/api/auth/login', json=login_credentials)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains access_token, refresh_token, and user information
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert 'user' in data['data']

        # Verify token_type is 'bearer'
        assert data['data']['token_type'] == 'bearer'

        # Verify user object contains correct test user details (id, username, email)
        assert data['data']['user']['user_id'] == test_user.id
        assert data['data']['user']['username'] == test_user.username
        assert data['data']['user']['email'] == test_user.email


@pytest.mark.usefixtures('db_setup')
def test_login_invalid_credentials(client, test_user, db_setup, monkeypatch):
    """Tests login failure with invalid credentials"""
    # Create login credentials with test user's username and incorrect password
    login_credentials = {
        'username': test_user.username,
        'password': 'wrong_password'
    }

    # Mock the Auth0Client.authenticate method to raise AuthenticationError
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service()._auth0_client.authenticate',
                  lambda username, password: (_ for _ in ()).throw(Exception('Invalid credentials')))

        # Send POST request to /api/auth/login with invalid credentials
        response = client.post('/api/auth/login', json=login_credentials)

        # Assert response status code is 401 (Unauthorized)
        assert response.status_code == 401

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains error message about invalid credentials
        assert 'Invalid credentials' in data['message']

        # Verify response success field is False
        assert data['success'] is False


@pytest.mark.usefixtures('db_setup')
def test_login_validation_error(client, db_setup):
    """Tests login request validation for missing or invalid fields"""
    # Create invalid login payload with missing username
    invalid_payload_username = {
        'password': 'test_password'
    }

    # Send POST request to /api/auth/login with invalid payload
    response = client.post('/api/auth/login', json=invalid_payload_username)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Verify response contains validation error message for username
    data = json.loads(response.data)
    assert 'username' in data['details']['errors']

    # Create another invalid login payload with missing password
    invalid_payload_password = {
        'username': 'test_user'
    }

    # Send POST request with this payload
    response = client.post('/api/auth/login', json=invalid_payload_password)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Verify response contains validation error message for password
    data = json.loads(response.data)
    assert 'password' in data['details']['errors']


def test_refresh_token_success(client, test_user, test_token, monkeypatch):
    """Tests successful token refresh with valid refresh token"""
    # Create refresh token payload with valid refresh token
    refresh_token_payload = {
        'refresh_token': test_token
    }

    # Mock the Auth0Client.refresh_token method to return new token data
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service()._auth0_client.refresh_token',
                  lambda refresh_token: {'access_token': 'new_access_token',
                                          'expires_in': 3600,
                                          'token_type': 'bearer'})

        # Send POST request to /api/auth/refresh with refresh token
        response = client.post('/api/auth/refresh', json=refresh_token_payload)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains new access_token, expires_in, and token_type
        assert 'access_token' in data['data']
        assert 'expires_in' in data['data']
        assert 'token_type' in data['data']

        # Verify token_type is 'bearer'
        assert data['data']['token_type'] == 'bearer'


def test_refresh_token_invalid(client, monkeypatch):
    """Tests token refresh failure with invalid refresh token"""
    # Create payload with invalid refresh token
    invalid_refresh_token_payload = {
        'refresh_token': 'invalid_refresh_token'
    }

    # Mock the Auth0Client.refresh_token method to raise AuthenticationError
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service()._auth0_client.refresh_token',
                  lambda refresh_token: (_ for _ in ()).throw(Exception('Invalid refresh token')))

        # Send POST request to /api/auth/refresh with invalid token
        response = client.post('/api/auth/refresh', json=invalid_refresh_token_payload)

        # Assert response status code is 401 (Unauthorized)
        assert response.status_code == 401

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains error message about invalid refresh token
        assert 'Invalid refresh token' in data['message']

        # Verify response success field is False
        assert data['success'] is False


def test_logout_success(client, test_token, monkeypatch):
    """Tests successful logout with valid token"""
    # Create logout payload with valid token
    logout_payload = {
        'token': test_token
    }

    # Mock the TokenService.blacklist_token method to return success
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().logout',
                  lambda token: True)

        # Send POST request to /api/auth/logout with token
        response = client.post('/api/auth/logout', json=logout_payload)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains success message about logout
        assert 'Logout successful' in data['message']

        # Verify response success field is True
        assert data['success'] is True


def test_logout_invalid_token(client, invalid_signature_token, monkeypatch):
    """Tests logout failure with invalid token"""
    # Create logout payload with invalid token
    logout_payload = {
        'token': invalid_signature_token
    }

    # Mock the TokenService.validate_token method to raise AuthenticationError
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().validate_token',
                  lambda token: (_ for _ in ()).throw(Exception('Invalid token')))

        # Send POST request to /api/auth/logout with invalid token
        response = client.post('/api/auth/logout', json=logout_payload)

        # Assert response status code is 401 (Unauthorized)
        assert response.status_code == 401

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains error message about invalid token
        assert 'Invalid token' in data['message']

        # Verify response success field is False
        assert data['success'] is False


def test_get_user_sites(client, test_token, test_user, test_site, monkeypatch):
    """Tests retrieval of user's available sites with valid token"""
    # Set up auth headers with valid token
    headers = auth_headers(test_token)

    # Mock SiteContextService.get_available_sites to return test sites
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().get_available_sites',
                  lambda: [{'id': test_site.id, 'name': test_site.name, 'role': 'admin'}])

        # Send GET request to /api/auth/sites with auth headers
        response = client.get('/api/auth/sites', headers=headers)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains list of sites with correct test site data
        assert len(data['data']['sites']) == 1
        assert data['data']['sites'][0]['id'] == test_site.id
        assert data['data']['sites'][0]['name'] == test_site.name

        # Verify site object contains id, name, and user's role fields
        assert 'id' in data['data']['sites'][0]
        assert 'name' in data['data']['sites'][0]
        assert 'role' in data['data']['sites'][0]


def test_get_user_sites_unauthorized(client):
    """Tests sites retrieval failure with missing authentication"""
    # Send GET request to /api/auth/sites without auth headers
    response = client.get('/api/auth/sites')

    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401

    # Parse response JSON data
    data = json.loads(response.data)

    # Verify response contains error message about missing authentication
    assert 'Authentication required' in data['message']

    # Verify response success field is False
    assert data['success'] is False


def test_switch_site_success(client, test_token, test_site, monkeypatch):
    """Tests successful site context switching with valid site ID"""
    # Create site selection payload with test site ID
    site_selection_payload = {
        'site_id': test_site.id
    }

    # Set up auth headers with valid token
    headers = auth_headers(test_token)

    # Mock SiteContextService.verify_site_access to return True
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().switch_site',
                  lambda site_id, token: {'site_id': site_id, 'site_name': 'Test Site'})

        # Send POST request to /api/auth/site with site selection payload and auth headers
        response = client.post('/api/auth/site', headers=headers, json=site_selection_payload)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains updated site context information
        assert 'site_context' in data['data']

        # Verify site context contains correct site ID and name
        assert data['data']['site_context']['site_id'] == test_site.id
        assert data['data']['site_context']['site_name'] == 'Test Site'


def test_switch_site_unauthorized(client, test_token, monkeypatch):
    """Tests site switching failure with unauthorized site access"""
    # Create site selection payload with unauthorized site ID
    site_selection_payload = {
        'site_id': 999  # Unauthorized site ID
    }

    # Set up auth headers with valid token
    headers = auth_headers(test_token)

    # Mock SiteContextService.verify_site_access to raise SiteContextError
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().switch_site',
                  lambda site_id, token: (_ for _ in ()).throw(Exception('Unauthorized site access')))

        # Send POST request to /api/auth/site with unauthorized site ID and auth headers
        response = client.post('/api/auth/site', headers=headers, json=site_selection_payload)

        # Assert response status code is 403 (Forbidden)
        assert response.status_code == 403

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains error message about unauthorized site access
        assert 'Unauthorized site access' in data['message']

        # Verify response success field is False
        assert data['success'] is False


def test_get_current_user(client, test_token, test_user, monkeypatch):
    """Tests retrieval of current authenticated user profile"""
    # Set up auth headers with valid token
    headers = auth_headers(test_token)

    # Mock UserContextService.get_current_user to return test user data
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().get_current_user',
                  lambda: {'id': test_user.id, 'username': test_user.username, 'email': test_user.email})

        # Send GET request to /api/auth/profile with auth headers
        response = client.get('/api/auth/profile', headers=headers)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains user data with correct test user details
        assert 'user' in data['data']
        assert data['data']['user']['id'] == test_user.id
        assert data['data']['user']['username'] == test_user.username
        assert data['data']['user']['email'] == test_user.email

        # Verify user object contains id, username, email, and site access information
        assert 'id' in data['data']['user']
        assert 'username' in data['data']['user']
        assert 'email' in data['data']['user']


def test_get_current_user_unauthorized(client):
    """Tests user profile retrieval failure with missing authentication"""
    # Send GET request to /api/auth/profile without auth headers
    response = client.get('/api/auth/profile')

    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401

    # Parse response JSON data
    data = json.loads(response.data)

    # Verify response contains error message about missing authentication
    assert 'Authentication required' in data['message']

    # Verify response success field is False
    assert data['success'] is False


def test_password_reset_request(client, test_user, monkeypatch):
    """Tests password reset request functionality"""
    # Create password reset payload with test user's email
    password_reset_payload = {
        'email': test_user.email
    }

    # Mock AuthService.request_password_reset to return success
    with monkeypatch.context() as m:
        m.setattr('src.backend.api.controllers.auth_controller.get_auth_service().request_password_reset',
                  lambda email: True)

        # Send POST request to /api/auth/password/reset with email payload
        response = client.post('/api/auth/password/reset', json=password_reset_payload)

        # Assert response status code is 200 (OK)
        assert response.status_code == 200

        # Parse response JSON data
        data = json.loads(response.data)

        # Verify response contains success message about reset email
        assert 'Password reset request initiated successfully' in data['message']

        # Verify response success field is True
        assert data['success'] is True

        # Verify non-existent email also returns 200 for security reasons
        password_reset_payload['email'] = 'nonexistent@example.com'
        response = client.post('/api/auth/password/reset', json=password_reset_payload)
        assert response.status_code == 200


def test_password_reset_invalid_email(client):
    """Tests password reset request validation for invalid email format"""
    # Create password reset payload with invalid email format
    password_reset_payload = {
        'email': 'invalid-email'
    }

    # Send POST request to /api/auth/password/reset with invalid email
    response = client.post('/api/auth/password/reset', json=password_reset_payload)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Parse response JSON data
    data = json.loads(response.data)

    # Verify response contains validation error message for email format
    assert 'email' in data['details']['errors']
    assert 'Invalid email format' in data['details']['errors']['email'][0]

    # Verify response success field is False
    assert data['success'] is False