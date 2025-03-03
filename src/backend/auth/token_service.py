"""
Token service module for the Interaction Management System.

This module provides the TokenService class for managing JWT tokens,
including token creation, validation, refresh, and blacklisting.
It supports both Auth0 tokens and locally issued tokens with site-based access control.
"""

import jwt  # PyJWT 2.6.0
import uuid
from typing import Dict, List, Optional, Any, Union

from ..utils.datetime_util import get_utc_now
from ..utils.constants import (
    JWT_ISSUER,
    JWT_AUDIENCE,
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES,
    TOKEN_BLACKLIST_TTL,
    CACHE_TTL_LONG
)
from .auth0 import Auth0Client
from ..cache.cache_keys import get_token_key, get_token_blacklist_key, TOKEN_TTL
from ..cache.cache_service import get_cache_service
from ..utils.error_util import AuthenticationError
from ..logging.structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)


class TokenService:
    """
    Service class for managing JWT tokens throughout the authentication lifecycle.
    
    This service handles token creation, validation, refresh, and blacklisting,
    supporting both Auth0 tokens and locally-issued tokens. It integrates with
    the caching layer to optimize token operations and implements site-scoped
    access control through token claims.
    """
    
    def __init__(self, auth0_client: Auth0Client = None):
        """
        Initialize the token service with Auth0 client and cache service.
        
        Args:
            auth0_client: Optional Auth0Client instance for Auth0 token validation
        """
        self._auth0_client = auth0_client
        self._cache_service = get_cache_service()
        
        # Get JWT secret key from environment or configuration
        # In a real application, this should be securely stored and accessed
        self._secret_key = "your-secret-key"  # TODO: Get from secure config
        
        # Set JWT algorithm (RS256 for Auth0 compatibility)
        self._algorithm = "RS256"
        
        logger.info("TokenService initialized")
    
    def create_access_token(self, user_data: Dict[str, Any], site_ids: List[int]) -> str:
        """
        Create a new JWT access token with user information and site access claims.
        
        Args:
            user_data: User information to include in the token
            site_ids: List of site IDs the user has access to
            
        Returns:
            Encoded JWT access token string
        """
        # Get current UTC time
        current_time = int(get_utc_now().timestamp())
        # Calculate expiration time
        expiry_time = current_time + JWT_ACCESS_TOKEN_EXPIRES
        # Generate unique token ID
        token_id = str(uuid.uuid4())
        
        # Create token payload with standard JWT claims
        payload = {
            'iss': JWT_ISSUER,                  # Issuer
            'sub': str(user_data.get('id')),    # Subject (user ID)
            'exp': expiry_time,                 # Expiration time
            'iat': current_time,                # Issued at time
            'jti': token_id,                    # JWT ID
            'aud': JWT_AUDIENCE,                # Audience
            
            # User information
            'user_id': user_data.get('id'),
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            
            # Site access information
            'site_ids': site_ids
        }
        
        # Encode token
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        
        # Store token in cache for faster validation
        cache_key = get_token_key(token_id)
        self._cache_service.set(cache_key, payload, JWT_ACCESS_TOKEN_EXPIRES)
        
        logger.info(f"Created access token for user {user_data.get('id')} with {len(site_ids)} site(s)")
        
        return token
    
    def create_refresh_token(self, user_id: str, token_type: str = 'refresh') -> str:
        """
        Create a refresh token with longer expiration for token renewal.
        
        Args:
            user_id: ID of the user
            token_type: Token type identifier (default: 'refresh')
            
        Returns:
            Encoded JWT refresh token string
        """
        # Get current UTC time
        current_time = int(get_utc_now().timestamp())
        # Calculate expiration time
        expiry_time = current_time + JWT_REFRESH_TOKEN_EXPIRES
        # Generate unique token ID
        token_id = str(uuid.uuid4())
        
        # Create token payload for refresh token
        payload = {
            'iss': JWT_ISSUER,          # Issuer
            'sub': str(user_id),        # Subject (user ID)
            'exp': expiry_time,         # Expiration time
            'iat': current_time,        # Issued at time
            'jti': token_id,            # JWT ID
            'aud': JWT_AUDIENCE,        # Audience
            'token_type': token_type    # Identify as refresh token
        }
        
        # Encode token
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        
        logger.info(f"Created refresh token for user {user_id}")
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return decoded payload if valid.
        
        This method handles both Auth0 tokens and locally-issued tokens.
        It checks token validity, expiration, and blacklist status.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload if valid, None if invalid
        """
        try:
            # Check if token is blacklisted
            token_payload = self.extract_token_payload(token)
            if not token_payload or 'jti' not in token_payload:
                logger.warning("Invalid token format: missing jti claim")
                return None
                
            token_id = token_payload.get('jti')
            blacklist_key = get_token_blacklist_key(token_id)
            
            if self._cache_service.exists(blacklist_key):
                logger.warning(f"Token {token_id[:8]}... is blacklisted")
                return None
            
            # Check if token payload is already in cache
            token_key = get_token_key(token_id)
            cached_payload = self._cache_service.get(token_key, data_type='json')
            
            if cached_payload:
                logger.debug(f"Using cached validation for token {token_id[:8]}...")
                return cached_payload
            
            # Determine if token is Auth0 token
            is_auth0_token = False
            if token_payload.get('iss') and 'auth0.com' in token_payload.get('iss', ''):
                is_auth0_token = True
            
            if is_auth0_token and self._auth0_client:
                # Validate using Auth0 client
                payload = self._auth0_client.validate_token(token)
            else:
                # Validate locally issued token
                payload = jwt.decode(
                    token,
                    self._secret_key,
                    algorithms=[self._algorithm],
                    audience=JWT_AUDIENCE,
                    issuer=JWT_ISSUER
                )
            
            # Cache successfully validated token
            if payload and 'jti' in payload:
                exp_time = payload.get('exp', 0)
                iat_time = payload.get('iat', 0)
                ttl = exp_time - iat_time if exp_time and iat_time else TOKEN_TTL
                
                self._cache_service.set(token_key, payload, ttl)
                logger.debug(f"Cached validated token {token_id[:8]}...")
            
            logger.info(f"Token validation successful for user {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token validation failed: Token has expired")
            return None
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Add a token to the blacklist to prevent reuse after logout.
        
        Args:
            token: JWT token to blacklist
            
        Returns:
            True if token was successfully blacklisted, False otherwise
        """
        try:
            # Extract token ID and expiry from token without validation
            payload = self.extract_token_payload(token)
            if not payload or 'jti' not in payload:
                logger.warning("Cannot blacklist token: invalid format or missing jti claim")
                return False
            
            token_id = payload.get('jti')
            expiry = payload.get('exp', 0)
            current_time = int(get_utc_now().timestamp())
            
            # Calculate time until expiry for TTL
            ttl = max(expiry - current_time, 0) if expiry > current_time else TOKEN_BLACKLIST_TTL
            
            # Add token to blacklist
            blacklist_key = get_token_blacklist_key(token_id)
            self._cache_service.set(blacklist_key, "blacklisted", ttl)
            
            # Remove any cached token payload to prevent reuse
            token_key = get_token_key(token_id)
            self._cache_service.delete(token_key)
            
            logger.info(f"Token {token_id[:8]}... blacklisted")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
            return False
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Create a new access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access token and expiration information
            
        Raises:
            AuthenticationError: If refresh token is invalid or expired
        """
        try:
            # Validate refresh token
            payload = self.validate_token(refresh_token)
            if not payload:
                raise AuthenticationError("Invalid refresh token")
            
            # Verify token type is 'refresh'
            if payload.get('token_type') != 'refresh':
                raise AuthenticationError("Token is not a refresh token")
            
            user_id = payload.get('sub')
            
            # For Auth0 tokens, use Auth0 client to refresh
            if self._auth0_client and 'auth0.com' in payload.get('iss', ''):
                return self._auth0_client.refresh_token(refresh_token)
            
            # For local tokens, fetch user data and site access
            user_data = {}
            site_ids = []
            
            # In a real implementation, this would fetch from a user repository
            # For now, we'll use the Auth0 client if available to get site access
            if self._auth0_client:
                site_ids = self._auth0_client.get_site_access_for_user(user_id)
                
                # This is a simplified implementation for demonstration
                # In a real application, we would fetch user data from a database
                user_data = {
                    'id': user_id,
                    'username': f"user_{user_id}",  # Placeholder
                    'email': f"user_{user_id}@example.com"  # Placeholder
                }
            
            # Create new access token
            new_token = self.create_access_token(user_data, site_ids)
            
            # Format response
            result = {
                'access_token': new_token,
                'expires_in': JWT_ACCESS_TOKEN_EXPIRES,
                'token_type': 'Bearer'
            }
            
            logger.info(f"Refreshed access token for user {user_id}")
            return result
            
        except AuthenticationError:
            # Re-raise authentication errors
            raise
            
        except Exception as e:
            error_message = f"Error refreshing token: {str(e)}"
            logger.error(error_message)
            raise AuthenticationError(error_message)
    
    def extract_token_payload(self, token: str) -> Dict[str, Any]:
        """
        Extract payload from token without validation for inspection.
        
        Args:
            token: JWT token to extract payload from
            
        Returns:
            Decoded token payload without validation
        """
        try:
            # Decode token without verifying signature
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Error extracting token payload: {str(e)}")
            return {}
    
    def get_token_expiration(self, token: str) -> Optional[int]:
        """
        Get the expiration timestamp from a token.
        
        Args:
            token: JWT token to extract expiration from
            
        Returns:
            Expiration timestamp in seconds or None if invalid
        """
        payload = self.extract_token_payload(token)
        return payload.get('exp')
    
    def get_site_ids_from_token(self, token_payload: Dict[str, Any]) -> List[int]:
        """
        Extract site IDs from a token payload.
        
        Args:
            token_payload: Decoded token payload
            
        Returns:
            List of site IDs the user has access to
        """
        site_ids = token_payload.get('site_ids', [])
        return site_ids
    
    def get_user_id_from_token(self, token_payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract user ID from a token payload.
        
        Args:
            token_payload: Decoded token payload
            
        Returns:
            User ID from the token or None if not found
        """
        return token_payload.get('sub')