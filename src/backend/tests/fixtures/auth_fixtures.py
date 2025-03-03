"""
Authentication and authorization test fixtures for the Interaction Management System.

This module provides pytest fixtures for testing authentication and authorization
related functionality, including mock implementations of Auth0 integration,
token service, and JWT management for isolated testing of authentication flows,
site-scoped access control, and token validation.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock

from ...extensions import db
from ...models.user import User
from ...models.site import Site
from ...auth.token_service import TokenService
from ...auth.auth0 import Auth0Client
from ..factories import UserFactory, SiteFactory
from ...utils.enums import UserRole

# Constants for testing
TEST_SECRET_KEY = "test-jwt-secret-key-for-testing-only"
TEST_ALGORITHM = "HS256"


@pytest.fixture
def auth_headers(token: str) -> Dict[str, str]:
    """
    Creates HTTP authorization headers with JWT token for testing API endpoints.
    
    Args:
        token: JWT token string
        
    Returns:
        HTTP headers dictionary with Authorization
    """
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_token_service(test_user: User = None, site_ids: List[int] = None) -> Mock:
    """
    Creates a mocked TokenService for testing without actual JWT operations.
    
    Args:
        test_user: Optional User instance to associate with the token
        site_ids: Optional list of site IDs to include in token
        
    Returns:
        Mocked TokenService with predefined behavior
    """
    mock = Mock(spec=TokenService)
    
    # Default site_ids if not provided
    if site_ids is None and test_user is not None:
        site_ids = test_user.get_site_ids()
    elif site_ids is None:
        site_ids = [1, 2, 3]  # Default site IDs
    
    # Set up create_access_token to return a dummy token
    mock.create_access_token.return_value = "dummy_token"
    
    # Set up validate_token to return a predefined payload
    mock.validate_token.return_value = {
        "sub": str(test_user.id if test_user else 1),
        "user_id": test_user.id if test_user else 1,
        "username": test_user.username if test_user else "test_user",
        "email": test_user.email if test_user else "test@example.com",
        "site_ids": site_ids,
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "interaction-manager",
        "aud": "interaction-manager-api",
        "jti": "test-token-id"
    }
    
    # Set up get_site_ids_from_token to return site_ids
    mock.get_site_ids_from_token.return_value = site_ids
    
    # Set up get_user_id_from_token to return user ID
    mock.get_user_id_from_token.return_value = str(test_user.id if test_user else 1)
    
    return mock


@pytest.fixture
def mock_auth0_client(test_user: User = None, site_ids: List[int] = None) -> Mock:
    """
    Creates a mocked Auth0Client for testing without actual Auth0 API calls.
    
    Args:
        test_user: Optional User instance to associate with the token
        site_ids: Optional list of site IDs to include in token
        
    Returns:
        Mocked Auth0Client with predefined behavior
    """
    mock = Mock(spec=Auth0Client)
    
    # Default site_ids if not provided
    if site_ids is None and test_user is not None:
        site_ids = test_user.get_site_ids()
    elif site_ids is None:
        site_ids = [1, 2, 3]  # Default site IDs
    
    # Set up authenticate to return a success response
    mock.authenticate.return_value = {
        "access_token": "dummy_access_token",
        "id_token": "dummy_id_token",
        "refresh_token": "dummy_refresh_token",
        "expires_in": 3600,
        "user": {
            "user_id": test_user.id if test_user else 1,
            "name": test_user.username if test_user else "Test User",
            "email": test_user.email if test_user else "test@example.com",
            "username": test_user.username if test_user else "test_user",
            "picture": "https://example.com/picture.jpg"
        },
        "site_access": site_ids
    }
    
    # Set up validate_token to return a predefined payload
    mock.validate_token.return_value = {
        "sub": str(test_user.id if test_user else 1),
        "user_id": test_user.id if test_user else 1,
        "name": test_user.username if test_user else "Test User",
        "email": test_user.email if test_user else "test@example.com",
        "site_ids": site_ids,
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "https://your-domain.auth0.com/",
        "aud": "your-audience"
    }
    
    # Set up get_site_access_for_user to return site_ids
    mock.get_site_access_for_user.return_value = site_ids
    
    return mock


@pytest.fixture
def test_token_payload(test_user: User, site_ids: List[int] = None) -> Dict[str, Any]:
    """
    Generates a test JWT payload representing a valid authenticated user.
    
    Args:
        test_user: User instance to create token for
        site_ids: Optional list of site IDs to include in token
        
    Returns:
        JWT payload dictionary with user and site data
    """
    # Get site IDs from user if not provided
    if site_ids is None:
        site_ids = test_user.get_site_ids()
    
    # Create a JWT payload with standard claims
    return {
        "sub": str(test_user.id),
        "user_id": test_user.id,
        "username": test_user.username,
        "email": test_user.email,
        "site_ids": site_ids,
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "interaction-manager",
        "aud": "interaction-manager-api",
        "jti": "test-token-id"
    }


@pytest.fixture
def test_token(test_user: User, site_ids: List[int] = None) -> str:
    """
    Creates an actual JWT token for testing authentication flows.
    
    Args:
        test_user: User instance to create token for
        site_ids: Optional list of site IDs to include in token
        
    Returns:
        Encoded JWT token string
    """
    # Get site IDs from user if not provided
    if site_ids is None:
        site_ids = test_user.get_site_ids()
    
    # Create payload with user information and site access
    payload = {
        "sub": str(test_user.id),
        "user_id": test_user.id,
        "username": test_user.username,
        "email": test_user.email,
        "site_ids": site_ids,
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "interaction-manager",
        "aud": "interaction-manager-api",
        "jti": "test-token-id"
    }
    
    # Encode and return token
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)


@pytest.fixture
def expired_token(test_user: User) -> str:
    """
    Creates an expired JWT token for testing token expiration handling.
    
    Args:
        test_user: User instance to create token for
        
    Returns:
        Expired JWT token string
    """
    # Create payload with an expiration time in the past
    payload = {
        "sub": str(test_user.id),
        "user_id": test_user.id,
        "username": test_user.username,
        "email": test_user.email,
        "site_ids": test_user.get_site_ids(),
        "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),  # Expired
        "iat": int((datetime.utcnow() - timedelta(hours=2)).timestamp()),
        "iss": "interaction-manager",
        "aud": "interaction-manager-api",
        "jti": "expired-token-id"
    }
    
    # Encode and return token
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)


@pytest.fixture
def invalid_signature_token(test_user: User) -> str:
    """
    Creates a JWT token with invalid signature for testing signature verification.
    
    Args:
        test_user: User instance to create token for
        
    Returns:
        JWT token with invalid signature
    """
    # Create a valid payload
    payload = {
        "sub": str(test_user.id),
        "user_id": test_user.id,
        "username": test_user.username,
        "email": test_user.email,
        "site_ids": test_user.get_site_ids(),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "interaction-manager",
        "aud": "interaction-manager-api",
        "jti": "invalid-signature-token-id"
    }
    
    # Encode with a different secret key to create invalid signature
    return jwt.encode(payload, "wrong-secret-key", algorithm=TEST_ALGORITHM)


@pytest.fixture
def token_without_site_access(test_user: User) -> str:
    """
    Creates a JWT token without site access claims for testing authorization failures.
    
    Args:
        test_user: User instance to create token for
        
    Returns:
        JWT token without site access claims
    """
    # Create payload without site_ids
    payload = {
        "sub": str(test_user.id),
        "user_id": test_user.id,
        "username": test_user.username,
        "email": test_user.email,
        # No site_ids included
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "interaction-manager",
        "aud": "interaction-manager-api",
        "jti": "no-site-access-token-id"
    }
    
    # Encode and return token
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)


@pytest.fixture
def authorized_client(client, token: str):
    """
    Creates a Flask test client with authentication headers for authorized requests.
    
    Args:
        client: Flask test client instance
        token: JWT token for authentication
        
    Returns:
        Flask test client with authentication
    """
    # Create authentication headers
    headers = auth_headers(token)
    
    # Configure client to include headers in each request
    client.environ_base = {
        "HTTP_AUTHORIZATION": headers["Authorization"]
    }
    
    return client