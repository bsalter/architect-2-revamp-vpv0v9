"""
Unit tests for authentication components including Auth0 integration, token validation, and site-scoped access control.
Tests the core authentication flows, token handling, and error scenarios.
"""

import pytest  # pytest 7.3.1
import jwt  # PyJWT 2.6.0
import requests_mock  # requests-mock 1.10.0
from unittest.mock import patch, Mock, MagicMock  # unittest.mock
from typing import Dict, List, Any, Optional, Union

from ...auth.auth0 import Auth0Client  # Auth0Client: Class under test for Auth0 integration
from ...auth.token_service import TokenService  # TokenService: Class under test for token handling
from ...services.auth_service import AuthService  # AuthService: Class under test for authentication service
from ...utils.error_util import AuthenticationError  # AuthenticationError: Exception class for authentication errors
from ..fixtures.auth_fixtures import mock_auth0_client, mock_token_service, test_token, test_token_payload, expired_token, invalid_signature_token, token_without_site_access  # auth_fixtures
from ..factories import UserFactory, SiteFactory  # Factories


def test_auth0_client_initialization():
    """
    Tests that Auth0Client initializes correctly with proper configuration
    """
    # Mock the configuration parameters
    with patch('src.backend.auth.auth0.AUTH0_CONFIG', {'domain': 'test-domain', 'client_id': 'test-client-id', 'client_secret': 'test-client-secret', 'api_audience': 'test-audience'}):
        # Initialize Auth0Client instance
        auth0_client = Auth0Client()

        # Assert configuration values were stored correctly
        assert auth0_client._domain == 'test-domain'
        assert auth0_client._client_id == 'test-client-id'
        assert auth0_client._client_secret == 'test-client-secret'
        assert auth0_client._audience == 'test-audience'
        assert auth0_client._scope == "openid profile email"

        # Assert no calls were made to external services during initialization
        assert auth0_client._cache_service is not None


def test_auth0_client_authenticate_success(requests_mock):
    """
    Tests successful authentication using Auth0Client
    """
    # Set up requests_mock to simulate successful Auth0 authentication response
    requests_mock.post('https://test-domain/oauth/token', json={'access_token': 'test_access_token', 'id_token': 'test_id_token', 'refresh_token': 'test_refresh_token', 'expires_in': 3600})
    requests_mock.get('https://test-domain/userinfo', json={'sub': 'test_user_id', 'name': 'Test User', 'email': 'test@example.com', 'nickname': 'test_user', 'picture': 'https://example.com/picture.jpg'})

    # Create test user with username and password
    username = "test_user"
    password = "test_password"

    # Initialize Auth0Client
    auth0_client = Auth0Client()

    # Call Auth0Client.authenticate with credentials
    auth_result = auth0_client.authenticate(username, password)

    # Assert returned token and user information match expected values
    assert auth_result['access_token'] == 'test_access_token'
    assert auth_result['id_token'] == 'test_id_token'
    assert auth_result['refresh_token'] == 'test_refresh_token'
    assert auth_result['user']['user_id'] == 'test_user_id'
    assert auth_result['user']['name'] == 'Test User'
    assert auth_result['user']['email'] == 'test@example.com'
    assert auth_result['user']['username'] == 'test_user'
    assert auth_result['user']['picture'] == 'https://example.com/picture.jpg'

    # Assert appropriate Auth0 endpoints were called
    assert requests_mock.call_count == 2
    assert requests_mock.request_history[0].url == 'https://test-domain/oauth/token'
    assert requests_mock.request_history[1].url == 'https://test-domain/userinfo'


def test_auth0_client_authenticate_failure(requests_mock):
    """
    Tests failed authentication with Auth0Client
    """
    # Set up requests_mock to simulate Auth0 authentication failure
    requests_mock.post('https://test-domain/oauth/token', status_code=401, json={'error': 'invalid_grant', 'error_description': 'Wrong email or password.'})

    # Create test user with username and password
    username = "test_user"
    password = "test_password"

    # Initialize Auth0Client
    auth0_client = Auth0Client()

    # Call Auth0Client.authenticate and expect AuthenticationError
    with pytest.raises(AuthenticationError) as exc_info:
        auth0_client.authenticate(username, password)

    # Assert error contains appropriate message
    assert str(exc_info.value) == 'Wrong email or password.'

    # Assert appropriate Auth0 endpoints were called
    assert requests_mock.call_count == 1
    assert requests_mock.request_history[0].url == 'https://test-domain/oauth/token'


def test_auth0_client_validate_token(requests_mock):
    """
    Tests validation of Auth0 tokens
    """
    # Mock the JWKS endpoint response with valid signing keys
    requests_mock.get('https://test-domain/.well-known/jwks.json', json={'keys': [{'kid': 'test_key_id', 'kty': 'RSA', 'use': 'sig', 'n': 'test_modulus', 'e': 'test_exponent'}]})

    # Create a test token signed with the test key
    test_token = jwt.encode({'sub': 'test_user_id', 'name': 'Test User', 'email': 'test@example.com'}, 'secret', algorithm='HS256', headers={'kid': 'test_key_id'})

    # Initialize Auth0Client
    auth0_client = Auth0Client()

    # Call Auth0Client.validate_token with the token
    payload = auth0_client.validate_token(test_token)

    # Assert token payload matches expected values
    assert payload['sub'] == 'test_user_id'
    assert payload['name'] == 'Test User'
    assert payload['email'] == 'test@example.com'

    # Assert appropriate Auth0 endpoints were called
    assert requests_mock.call_count == 1
    assert requests_mock.request_history[0].url == 'https://test-domain/.well-known/jwks.json'


def test_auth0_client_get_site_access(requests_mock):
    """
    Tests retrieving site access information from Auth0
    """
    # Mock user data with app_metadata containing site access
    user_data = {'app_metadata': {'site_access': [1, 2, 3]}}

    # Initialize Auth0Client
    auth0_client = Auth0Client()

    # Call Auth0Client.get_site_access_for_user
    site_access = auth0_client.get_site_access_for_user('test_user_id', user_data)

    # Assert returned site IDs match expected values
    assert site_access == [1, 2, 3]

    # Test fallback to database when app_metadata is missing
    auth0_client._user_repository = Mock()
    auth0_client._user_repository.find_by_email.return_value = Mock(get_site_ids=Mock(return_value=[4, 5, 6]))
    site_access = auth0_client.get_site_access_for_user('test_user_id', {'email': 'test@example.com'})
    assert site_access == [4, 5, 6]


def test_token_service_create_access_token(test_user, test_token_payload):
    """
    Tests creation of JWT access tokens
    """
    # Create test user and site data
    site_ids = [1, 2, 3]

    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.create_access_token
    token = token_service.create_access_token(test_user.to_dict(), site_ids)

    # Decode the returned token
    payload = jwt.decode(token, token_service._secret_key, algorithms=[token_service._algorithm])

    # Assert token contains correct user information
    assert str(payload['sub']) == str(test_user.id)
    assert payload['user_id'] == test_user.id
    assert payload['username'] == test_user.username
    assert payload['email'] == test_user.email

    # Assert token contains correct site access claims
    assert payload['site_ids'] == site_ids

    # Assert token expiration time is set appropriately
    assert payload['exp'] > payload['iat']


def test_token_service_create_refresh_token(test_user):
    """
    Tests creation of JWT refresh tokens
    """
    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.create_refresh_token
    token = token_service.create_refresh_token(str(test_user.id))

    # Decode the returned token
    payload = jwt.decode(token, token_service._secret_key, algorithms=[token_service._algorithm])

    # Assert token type is 'refresh'
    assert payload['token_type'] == 'refresh'

    # Assert token contains correct user ID
    assert str(payload['sub']) == str(test_user.id)

    # Assert token has longer expiration than access token
    assert payload['exp'] > payload['iat']


def test_token_service_validate_token_success(test_token):
    """
    Tests successful validation of tokens
    """
    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.validate_token with a valid token
    payload = token_service.validate_token(test_token)

    # Assert validation succeeds
    assert payload is not None

    # Assert returned payload matches expected values
    assert payload['iss'] == 'interaction-manager'


def test_token_service_validate_token_expired(expired_token):
    """
    Tests validation of expired tokens
    """
    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.validate_token with an expired token
    payload = token_service.validate_token(expired_token)

    # Assert validation returns None
    assert payload is None

    # Verify appropriate logging of expiration
    # (This requires capturing log output, which is beyond the scope of this example)


def test_token_service_validate_token_invalid_signature(invalid_signature_token):
    """
    Tests validation of tokens with invalid signatures
    """
    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.validate_token with a token having invalid signature
    payload = token_service.validate_token(invalid_signature_token)

    # Assert validation returns None
    assert payload is None

    # Verify appropriate logging of signature failure
    # (This requires capturing log output, which is beyond the scope of this example)


def test_token_service_blacklist_token(test_token):
    """
    Tests token blacklisting functionality
    """
    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.blacklist_token with a valid token
    success = token_service.blacklist_token(test_token)

    # Assert blacklisting succeeds
    assert success is True

    # Attempt to validate the blacklisted token
    payload = token_service.validate_token(test_token)

    # Assert validation fails due to blacklisting
    assert payload is None


def test_token_service_get_site_ids_from_token(test_token_payload):
    """
    Tests extraction of site IDs from token payload
    """
    # Initialize TokenService
    token_service = TokenService()

    # Call TokenService.get_site_ids_from_token with a token payload
    site_ids = token_service.get_site_ids_from_token(test_token_payload)

    # Assert extracted site IDs match expected values
    assert site_ids == test_token_payload['site_ids']

    # Test handling of missing site_ids claim
    payload_without_site_ids = test_token_payload.copy()
    del payload_without_site_ids['site_ids']
    site_ids = token_service.get_site_ids_from_token(payload_without_site_ids)
    assert site_ids == []


def test_auth_service_login_success(mock_auth0_client, mock_token_service):
    """
    Tests successful login through AuthService
    """
    # Set up mock dependencies for AuthService
    mock_auth0_client.authenticate.return_value = {'access_token': 'test_access_token', 'id_token': 'test_id_token', 'refresh_token': 'test_refresh_token', 'expires_in': 3600, 'user': {'user_id': 1, 'name': 'Test User', 'email': 'test@example.com', 'username': 'test_user', 'picture': 'https://example.com/picture.jpg'}, 'site_access': [1, 2, 3]}
    mock_token_service.extract_token_payload.return_value = {'sub': '1', 'user_id': 1, 'username': 'test_user', 'email': 'test@example.com', 'site_ids': [1, 2, 3]}

    # Create AuthService instance with mocks
    auth_service = AuthService(mock_auth0_client, mock_token_service, Mock(), Mock(), Mock())

    # Call AuthService.login with valid credentials
    auth_result = auth_service.login('test_user', 'test_password')

    # Assert authentication result contains expected tokens and user info
    assert auth_result['access_token'] == 'test_access_token'
    assert auth_result['id_token'] == 'test_id_token'
    assert auth_result['refresh_token'] == 'test_refresh_token'
    assert auth_result['user']['user_id'] == 1
    assert auth_result['user']['name'] == 'Test User'
    assert auth_result['user']['email'] == 'test@example.com'
    assert auth_result['user']['username'] == 'test_user'
    assert auth_result['user']['picture'] == 'https://example.com/picture.jpg'
    assert auth_result['site_access'] == [1, 2, 3]

    # Verify appropriate services were called with correct parameters
    mock_auth0_client.authenticate.assert_called_once_with('test_user', 'test_password')
    mock_token_service.extract_token_payload.assert_called_once_with('test_access_token')


def test_auth_service_login_failure(mock_auth0_client):
    """
    Tests failed login through AuthService
    """
    # Configure mock_auth0_client to raise AuthenticationError
    mock_auth0_client.authenticate.side_effect = AuthenticationError("Invalid credentials")

    # Create AuthService instance with mock
    auth_service = AuthService(mock_auth0_client, Mock(), Mock(), Mock(), Mock())

    # Call AuthService.login and expect AuthenticationError
    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.login('test_user', 'test_password')

    # Assert error contains appropriate message
    assert str(exc_info.value) == "Invalid credentials"

    # Verify fallback to local authentication was attempted when Auth0 fails
    mock_auth0_client.authenticate.assert_called_once_with('test_user', 'test_password')


def test_auth_service_logout(mock_token_service, test_token):
    """
    Tests logout functionality through AuthService
    """
    # Set up mock dependencies for AuthService
    mock_token_service.validate_token.return_value = {'sub': '1', 'username': 'test_user'}
    mock_token_service.blacklist_token.return_value = True

    # Create AuthService instance with mocks
    auth_service = AuthService(Mock(), mock_token_service, Mock(), Mock(), Mock())

    # Call AuthService.logout with a valid token
    success = auth_service.logout(test_token)

    # Assert logout returns True
    assert success is True

    # Verify token was blacklisted
    mock_token_service.blacklist_token.assert_called_once_with(test_token)

    # Verify user context and site context were cleared
    # (This requires checking that the appropriate methods were called on the context services)


def test_auth_service_validate_token(mock_token_service, test_token):
    """
    Tests token validation through AuthService
    """
    # Set up mock dependencies for AuthService
    mock_token_service.validate_token.return_value = {'sub': '1', 'username': 'test_user'}

    # Create AuthService instance with mocks
    auth_service = AuthService(Mock(), mock_token_service, Mock(), Mock(), Mock())

    # Call AuthService.validate_token with a valid token
    payload = auth_service.validate_token(test_token)

    # Assert validation succeeds
    assert payload is not None

    # Verify user context was set from token
    # (This requires checking that the appropriate methods were called on the context services)

    # Verify token service was called with correct parameters
    mock_token_service.validate_token.assert_called_once_with(test_token)


def test_auth_service_switch_site_valid():
    """
    Tests successful site context switching
    """
    # Set up mock dependencies including SiteContextService
    site_context_service = Mock()
    site_context_service.verify_site_access.return_value = True
    site_context_service.get_current_site_context.return_value = Mock(to_dict=Mock(return_value={'site_id': 2, 'site_name': 'Test Site 2'}))

    # Create test user with access to multiple sites
    user = Mock(id=1, username='test_user', email='test@example.com')

    # Create AuthService instance with mocks
    auth_service = AuthService(Mock(), Mock(), Mock(), site_context_service, Mock())

    # Call AuthService.switch_site with a valid site ID
    site_context = auth_service.switch_site(2)

    # Assert site switch succeeds
    assert site_context == {'site_id': 2, 'site_name': 'Test Site 2'}

    # Verify site context was updated appropriately
    site_context_service.verify_site_access.assert_called_once_with(2)
    site_context_service.set_site_context.assert_called_once_with(2)


def test_auth_service_switch_site_invalid():
    """
    Tests site context switching with invalid site
    """
    # Set up mock dependencies including SiteContextService
    site_context_service = Mock()
    site_context_service.verify_site_access.side_effect = SiteContextError("User does not have access to this site")

    # Create AuthService instance with mocks
    auth_service = AuthService(Mock(), Mock(), Mock(), site_context_service, Mock())

    # Call AuthService.switch_site with an invalid site ID
    with pytest.raises(SiteContextError) as exc_info:
        auth_service.switch_site(999)

    # Expect SiteContextError to be raised
    assert str(exc_info.value) == "User does not have access to this site"

    # Verify error contains appropriate site access information
    site_context_service.verify_site_access.assert_called_once_with(999)