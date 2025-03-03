"""
Auth0 authentication module for the Interaction Management System.

This module provides integration with Auth0 authentication service, handling
user authentication, token validation, and user profile management. It serves
as a bridge between Auth0 and the application's authentication system, supporting
site-scoped access control.
"""

import jwt  # PyJWT 2.6.0
import requests  # requests 2.31.0
from jose import jwt as jose_jwt  # python-jose 3.3.0
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import urllib.request
import json

from ..config import get_env_var, AUTH0_CONFIG
from ..repositories.user_repository import UserRepository
from ..utils.error_util import AuthenticationError
from ..cache.cache_service import get_cache_service
from ..logging.structured_logger import StructuredLogger

# Initialize structured logger
logger = StructuredLogger(__name__)

# JWKS cache time-to-live (1 hour)
JWKS_CACHE_TTL = 3600


def get_jwks(domain: str) -> dict:
    """
    Retrieves JSON Web Key Set (JWKS) from Auth0 for token validation.
    
    The JWKS contains the public keys used to verify JWT tokens issued by Auth0.
    This function also caches the JWKS to reduce API calls.
    
    Args:
        domain: Auth0 domain name
        
    Returns:
        JWKS dictionary containing public keys
        
    Raises:
        AuthenticationError: If unable to retrieve JWKS
    """
    cache_service = get_cache_service()
    cache_key = f"jwks:{domain}"
    
    # Try to get JWKS from cache first
    jwks = cache_service.get(cache_key, data_type='json')
    if jwks:
        logger.debug(f"Retrieved JWKS from cache for domain {domain}")
        return jwks
    
    try:
        # If not in cache, fetch from Auth0
        jwks_url = f"https://{domain}/.well-known/jwks.json"
        logger.debug(f"Fetching JWKS from {jwks_url}")
        
        with urllib.request.urlopen(jwks_url) as response:
            jwks = json.loads(response.read().decode('utf-8'))
        
        # Cache the JWKS
        cache_service.set(cache_key, jwks, JWKS_CACHE_TTL)
        logger.debug(f"Cached JWKS for domain {domain}")
        
        return jwks
    except Exception as e:
        error_message = f"Failed to retrieve JWKS from {domain}: {str(e)}"
        logger.error(error_message)
        raise AuthenticationError(error_message)


class Auth0Client:
    """
    Client for Auth0 authentication service with methods for authentication,
    token validation, and user information retrieval.
    
    This client handles the integration with Auth0, providing authentication,
    token validation, and user profile management. It also supports site-scoped
    access control by retrieving and synchronizing site access permissions.
    """
    
    def __init__(self, user_repository: UserRepository = None):
        """
        Initialize the Auth0 client with configuration and dependencies.
        
        Args:
            user_repository: Repository for user data storage and retrieval
        """
        # Load configuration from AUTH0_CONFIG or environment variables
        self._domain = AUTH0_CONFIG.get('domain')
        self._client_id = AUTH0_CONFIG.get('client_id')
        self._client_secret = AUTH0_CONFIG.get('client_secret')
        self._audience = AUTH0_CONFIG.get('api_audience')
        self._scope = "openid profile email"
        
        # Store user repository for local user management
        self._user_repository = user_repository
        
        # Get cache service for token and user info caching
        self._cache_service = get_cache_service()
        
        logger.info(f"Initialized Auth0 client for domain: {self._domain}")
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with Auth0 using username and password.
        
        This method authenticates a user against Auth0, retrieving tokens and
        user information. It also retrieves site access permissions and updates
        the user's last login timestamp.
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            Authentication result with tokens and user information
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.debug(f"Authenticating user: {username}")
            
            # Prepare authentication request payload
            payload = {
                'grant_type': 'password',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'username': username,
                'password': password,
                'scope': self._scope,
                'audience': self._audience
            }
            
            # Send authentication request to Auth0
            url = f"https://{self._domain}/oauth/token"
            response = requests.post(url, json=payload)
            
            # Check for successful response
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('error_description', 'Authentication failed')
                logger.warning(f"Authentication failed for user {username}: {error_message}")
                raise AuthenticationError(error_message)
            
            # Extract tokens from response
            token_data = response.json()
            access_token = token_data.get('access_token')
            id_token = token_data.get('id_token')
            refresh_token = token_data.get('refresh_token')
            
            # Decode the ID token to get user information
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            user_id = user_info.get('sub')
            
            # Get user's site access permissions
            site_access = self.get_site_access_for_user(user_id, user_info)
            
            # Cache tokens
            self._cache_service.store_auth_token(user_id, access_token, token_data.get('expires_in', 3600))
            
            # Update user's last login timestamp if they exist in the local database
            if self._user_repository:
                user = self._user_repository.find_by_username(username)
                if user:
                    user.update_last_login()
            
            # Construct authentication result
            result = {
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token,
                'expires_in': token_data.get('expires_in'),
                'user': {
                    'user_id': user_id,
                    'name': user_info.get('name'),
                    'email': user_info.get('email'),
                    'username': user_info.get('nickname'),
                    'picture': user_info.get('picture')
                },
                'site_access': site_access
            }
            
            logger.info(f"User {username} authenticated successfully")
            return result
            
        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            error_message = f"Error during authentication: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an Auth0 JWT token and return payload if valid.
        
        This method verifies the JWT token signature, issuer, audience, and
        expiration. It caches validated tokens to improve performance.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload if valid
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            # Check if token is already validated and cached
            cache_key = f"validated_token:{token[:64]}"  # Use partial token as key for security
            cached_payload = self._cache_service.get(cache_key, data_type='json')
            if cached_payload:
                logger.debug("Token validation successful (cached)")
                return cached_payload
            
            # Get JWKS for token validation
            jwks = get_jwks(self._domain)
            
            # Extract header data from token
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise AuthenticationError("Invalid token header: No 'kid' present")
            
            # Find the right key in the JWKS
            rsa_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    rsa_key = {
                        'kty': key.get('kty'),
                        'kid': key.get('kid'),
                        'use': key.get('use'),
                        'n': key.get('n'),
                        'e': key.get('e')
                    }
                    break
            
            if not rsa_key:
                raise AuthenticationError("Unable to find appropriate key in JWKS")
            
            # Verify the token
            try:
                payload = jose_jwt.decode(
                    token,
                    rsa_key,
                    algorithms=AUTH0_CONFIG.get('algorithms', ['RS256']),
                    audience=self._audience,
                    issuer=f"https://{self._domain}/"
                )
                
                # Cache the validated token payload
                ttl = payload.get('exp', 0) - payload.get('iat', 0)
                if ttl > 0:
                    self._cache_service.set(cache_key, payload, ttl)
                
                logger.debug("Token validation successful")
                return payload
                
            except jose_jwt.ExpiredSignatureError:
                raise AuthenticationError("Token has expired")
            except jose_jwt.JWTClaimsError as claims_error:
                raise AuthenticationError(f"Invalid claims: {str(claims_error)}")
            except Exception as e:
                raise AuthenticationError(f"Invalid token: {str(e)}")
                
        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            error_message = f"Error validating token: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get detailed user profile information from Auth0.
        
        This method retrieves the user's profile from Auth0 using the access token.
        It caches the result to improve performance for frequent requests.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User profile information
            
        Raises:
            AuthenticationError: If unable to retrieve user information
        """
        try:
            # Check if user info is cached
            cache_key = f"user_info:{access_token[:64]}"  # Use partial token as key for security
            cached_info = self._cache_service.get(cache_key, data_type='json')
            if cached_info:
                logger.debug("Retrieved user info from cache")
                return cached_info
            
            # Get user info from Auth0
            url = f"https://{self._domain}/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                error_message = f"Failed to retrieve user info: {response.text}"
                logger.error(error_message)
                raise AuthenticationError(error_message)
            
            user_info = response.json()
            
            # Cache user info
            self._cache_service.set(cache_key, user_info, 3600)  # Cache for 1 hour
            
            logger.debug(f"Retrieved user info for user {user_info.get('sub')}")
            return user_info
            
        except Exception as e:
            error_message = f"Error retrieving user info: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Get new access token using a refresh token.
        
        This method exchanges a refresh token for a new access token when
        the original access token expires.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New tokens and updated expiration
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            logger.debug("Refreshing access token")
            
            # Prepare refresh token request payload
            payload = {
                'grant_type': 'refresh_token',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'refresh_token': refresh_token
            }
            
            # Send refresh token request to Auth0
            url = f"https://{self._domain}/oauth/token"
            response = requests.post(url, json=payload)
            
            # Check for successful response
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('error_description', 'Token refresh failed')
                logger.warning(f"Token refresh failed: {error_message}")
                raise AuthenticationError(error_message)
            
            # Extract new tokens from response
            token_data = response.json()
            new_access_token = token_data.get('access_token')
            new_id_token = token_data.get('id_token')
            
            # Decode the ID token to get user information
            user_info = jwt.decode(new_id_token, options={"verify_signature": False})
            user_id = user_info.get('sub')
            
            # Cache new access token
            self._cache_service.store_auth_token(
                user_id, 
                new_access_token, 
                token_data.get('expires_in', 3600)
            )
            
            # Construct refresh result
            result = {
                'access_token': new_access_token,
                'id_token': new_id_token,
                'expires_in': token_data.get('expires_in')
            }
            
            logger.info(f"Access token refreshed for user {user_id}")
            return result
            
        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            error_message = f"Error refreshing token: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def get_site_access_for_user(self, user_id: str, user_data: Dict[str, Any] = None) -> List[int]:
        """
        Retrieve site access permissions for a user from Auth0 and local database.
        
        This method gets the site IDs a user has access to, first checking Auth0
        metadata and then falling back to the local database if necessary.
        
        Args:
            user_id: User identifier from Auth0
            user_data: Optional Auth0 user data containing app_metadata
            
        Returns:
            List of site IDs the user has access to
            
        Raises:
            AuthenticationError: If unable to retrieve site access
        """
        try:
            # Check if site access is cached
            cache_key = f"user:{user_id}:site_access"
            cached_sites = self._cache_service.get(cache_key, data_type='json')
            if cached_sites:
                logger.debug(f"Retrieved site access from cache for user {user_id}")
                return cached_sites
            
            site_ids = []
            
            # First check if site access is in Auth0 user metadata
            if user_data and 'app_metadata' in user_data:
                app_metadata = user_data.get('app_metadata', {})
                site_access = app_metadata.get('site_access', [])
                if isinstance(site_access, list):
                    # Convert string IDs to integers if needed
                    site_ids = [int(site_id) if isinstance(site_id, str) else site_id 
                               for site_id in site_access]
            
            # If no site access in Auth0 metadata and we have a user repository, check local database
            if not site_ids and self._user_repository:
                # Try to find user in local database by matching Auth0 ID
                # The actual implementation will depend on how user IDs are mapped
                local_user = None
                if user_data and 'email' in user_data:
                    local_user = self._user_repository.find_by_email(user_data.get('email'))
                
                if local_user:
                    # Get site IDs from local user
                    site_ids = local_user.get_site_ids()
                    logger.debug(f"Retrieved site access from local database for user {user_id}")
                    
                    # Optionally synchronize this back to Auth0
                    self.sync_user_site_access(user_id)
            
            # Cache the site access
            self._cache_service.store_user_site_access(user_id, site_ids, 3600)  # Cache for 1 hour
            
            logger.info(f"User {user_id} has access to {len(site_ids)} sites")
            return site_ids
            
        except Exception as e:
            error_message = f"Error retrieving site access for user {user_id}: {str(e)}"
            logger.error(error_message)
            # Don't block authentication for site access issues
            logger.warning("Returning empty site access list due to error")
            return []
    
    def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update user metadata in Auth0, including site access information.
        
        This method updates the app_metadata field for a user in Auth0, which
        can include site access permissions.
        
        Args:
            user_id: User identifier from Auth0
            metadata: Metadata to update, typically containing site_access
            
        Returns:
            True if update was successful
            
        Raises:
            AuthenticationError: If unable to update metadata
        """
        try:
            logger.debug(f"Updating metadata for user {user_id}")
            
            # Get management API token
            token = self.get_management_token()
            
            # Prepare update request
            url = f"https://{self._domain}/api/v2/users/{user_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "app_metadata": metadata
            }
            
            # Send update request to Auth0
            response = requests.patch(url, headers=headers, json=payload)
            
            # Check for successful response
            if response.status_code not in (200, 201):
                error_message = f"Failed to update user metadata: {response.text}"
                logger.error(error_message)
                raise AuthenticationError(error_message)
            
            # Invalidate user cache
            self._cache_service.invalidate_user_cache(user_id)
            
            logger.info(f"Updated metadata for user {user_id}")
            return True
            
        except Exception as e:
            error_message = f"Error updating user metadata: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def get_management_token(self) -> str:
        """
        Get an access token for Auth0 Management API.
        
        This method obtains an access token for the Auth0 Management API,
        which is required for operations like updating user metadata.
        
        Returns:
            Management API access token
            
        Raises:
            AuthenticationError: If unable to obtain management token
        """
        try:
            # Check if management token is cached
            cache_key = "auth0:management_token"
            cached_token = self._cache_service.get(cache_key, data_type='str')
            if cached_token:
                logger.debug("Retrieved management token from cache")
                return cached_token
            
            # Prepare token request payload
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'audience': f"https://{self._domain}/api/v2/"
            }
            
            # Send token request to Auth0
            url = f"https://{self._domain}/oauth/token"
            response = requests.post(url, json=payload)
            
            # Check for successful response
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('error_description', 'Management token request failed')
                logger.error(error_message)
                raise AuthenticationError(error_message)
            
            # Extract token from response
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 86400)  # Default to 24 hours
            
            # Cache the token
            self._cache_service.set(cache_key, access_token, expires_in - 300)  # Expire 5 minutes early
            
            logger.info("Obtained Auth0 Management API token")
            return access_token
            
        except Exception as e:
            error_message = f"Error obtaining management token: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def sync_user_site_access(self, user_id: str) -> bool:
        """
        Synchronize user's site access between local database and Auth0.
        
        This method gets the user's site access from the local database and
        updates their Auth0 metadata to match, ensuring consistency.
        
        Args:
            user_id: User identifier from Auth0
            
        Returns:
            True if synchronization was successful
            
        Raises:
            AuthenticationError: If synchronization fails
        """
        try:
            if not self._user_repository:
                logger.warning("User repository not available for site access synchronization")
                return False
            
            logger.debug(f"Synchronizing site access for user {user_id}")
            
            # Get user profile to find matching local user
            user_info = None
            try:
                # Try to get user info from Auth0
                management_token = self.get_management_token()
                url = f"https://{self._domain}/api/v2/users/{user_id}"
                headers = {"Authorization": f"Bearer {management_token}"}
                
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    user_info = response.json()
            except Exception as e:
                logger.warning(f"Could not retrieve user info from Auth0: {str(e)}")
            
            # Find local user
            local_user = None
            if user_info and 'email' in user_info:
                local_user = self._user_repository.find_by_email(user_info.get('email'))
            
            if not local_user:
                logger.warning(f"Local user not found for Auth0 user {user_id}")
                return False
            
            # Get site IDs from local user
            site_ids = local_user.get_site_ids()
            
            # Update Auth0 metadata with site access
            metadata = {
                "site_access": site_ids
            }
            
            # Update user metadata in Auth0
            success = self.update_user_metadata(user_id, metadata)
            
            # Invalidate site access cache
            self._cache_service.invalidate_user_site_access(user_id)
            
            logger.info(f"Synchronized site access for user {user_id}: {len(site_ids)} sites")
            return success
            
        except Exception as e:
            error_message = f"Error synchronizing site access: {str(e)}"
            logger.error(error_message)
            # Don't block authentication for sync issues
            return False