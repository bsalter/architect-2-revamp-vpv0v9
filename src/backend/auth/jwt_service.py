"""
JWT service module for the Interaction Management System.

This module provides a service for handling JWT token generation, validation, and management.
It integrates with Auth0 for token verification and includes site-scoping claims in tokens to
enforce proper access control across the application.
"""

import jwt  # version 2.6.0
from typing import Dict, List, Optional, Any
import logging

from ..utils.datetime_util import get_utc_now, add_time_delta
from ..utils.constants import JWT_SECRET, JWT_ALGORITHM, JWT_TOKEN_LIFETIME_MINUTES, JWT_REFRESH_LIFETIME_DAYS
from .auth0 import Auth0Client
from ..cache.cache_service import CacheService
from ..cache.cache_keys import TOKEN_BLACKLIST, TOKEN_PAYLOAD

# Initialize logger
logger = logging.getLogger(__name__)

class JWTService:
    """Service class to handle JWT token operations for authentication and authorization"""
    
    def __init__(self, auth0_client: Auth0Client, cache_service: CacheService):
        """
        Initializes the JWT service with dependencies.
        
        Args:
            auth0_client: Auth0 client for token validation
            cache_service: Cache service for token storage
        """
        self._auth0_client = auth0_client
        self._cache_service = cache_service
    
    def create_token(self, user_data: Dict[str, Any], site_ids: List[int]) -> str:
        """
        Creates a new JWT token with user information and site access claims.
        
        Args:
            user_data: Dictionary containing user information
            site_ids: List of site IDs the user has access to
            
        Returns:
            JWT token string
        """
        # Get current time
        current_time = get_utc_now()
        
        # Calculate expiration time
        expiration_time = add_time_delta(current_time, minutes=JWT_TOKEN_LIFETIME_MINUTES)
        
        # Prepare payload with user data, site access, and standard claims
        payload = {
            'sub': user_data.get('id', user_data.get('user_id')),  # Subject: user ID
            'name': user_data.get('name', user_data.get('username')),  # User's name
            'email': user_data.get('email'),  # User's email
            'sites': site_ids,  # Site access claims
            'iat': current_time.timestamp(),  # Issued At
            'exp': expiration_time.timestamp()  # Expiration Time
        }
        
        # Encode token
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Cache token payload for faster validation
        cache_key = f"{TOKEN_PAYLOAD}:{token}"
        self._cache_service.set(cache_key, payload, JWT_TOKEN_LIFETIME_MINUTES * 60)
        
        logger.info(f"Created token for user {payload['sub']} with access to {len(site_ids)} sites")
        
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Creates a refresh token with a longer expiration time.
        
        Args:
            user_id: User ID to create refresh token for
            
        Returns:
            Refresh token string
        """
        # Get current time
        current_time = get_utc_now()
        
        # Calculate expiration time (longer than access token)
        expiration_time = add_time_delta(current_time, days=JWT_REFRESH_LIFETIME_DAYS)
        
        # Prepare refresh token payload
        payload = {
            'sub': user_id,  # Subject: user ID
            'type': 'refresh',  # Token type
            'iat': current_time.timestamp(),  # Issued At
            'exp': expiration_time.timestamp()  # Expiration Time
        }
        
        # Encode refresh token
        refresh_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        logger.info(f"Created refresh token for user {user_id}")
        
        return refresh_token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validates a JWT token and returns the decoded payload if valid.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload or None if invalid
        """
        # Check if token is blacklisted
        blacklist_key = f"{TOKEN_BLACKLIST}:{token}"
        if self._cache_service.get(blacklist_key):
            logger.warning("Token validation failed: Token is blacklisted")
            return None
        
        # Check if token payload is cached
        cache_key = f"{TOKEN_PAYLOAD}:{token}"
        cached_payload = self._cache_service.get(cache_key)
        if cached_payload:
            logger.debug("Token validation succeeded using cached payload")
            return cached_payload
        
        try:
            # Try to decode and validate token using JWT library
            try:
                # For locally issued tokens
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                
                # Cache validated payload
                ttl = int(payload.get('exp', 0) - get_utc_now().timestamp())
                if ttl > 0:
                    self._cache_service.set(cache_key, payload, ttl)
                    
                return payload
            except jwt.InvalidTokenError:
                # If not a local token, try validating with Auth0
                payload = self._auth0_client.validate_token(token)
                
                if payload:
                    # Cache validated token payload
                    ttl = int(payload.get('exp', 0) - get_utc_now().timestamp())
                    if ttl > 0:
                        self._cache_service.set(cache_key, payload, ttl)
                    
                    return payload
                
                # If Auth0 validation fails, propagate the failure
                return None
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Adds a token to the blacklist to prevent its further use.
        
        Args:
            token: JWT token to blacklist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Decode token without verification to extract jti (JWT ID) and exp (expiration)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Calculate time until expiration
            exp_time = payload.get('exp', 0)
            current_time = get_utc_now().timestamp()
            ttl = max(0, int(exp_time - current_time))
            
            # Add token to blacklist with expiration
            blacklist_key = f"{TOKEN_BLACKLIST}:{token}"
            self._cache_service.set(blacklist_key, True, ttl)
            
            # Delete any cached payload for this token
            cache_key = f"{TOKEN_PAYLOAD}:{token}"
            self._cache_service.delete(cache_key)
            
            logger.info(f"Token blacklisted with TTL of {ttl} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
            return False
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Creates a new access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access token and its expiration
        """
        # Validate refresh token
        payload = self.validate_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            logger.warning("Token refresh failed: Invalid refresh token")
            return None
        
        # Extract user ID from refresh token
        user_id = payload.get('sub')
        
        try:
            # Retrieve user data and site access information
            # This would typically involve database lookups in a real implementation
            user_info = self._auth0_client.get_token_payload(refresh_token)
            site_ids = self._auth0_client.get_site_access_for_user(user_id, user_info)
            
            # Create a new access token
            new_token = self.create_token(user_info, site_ids)
            
            # Return new token with expiration information
            return {
                'token': new_token,
                'expires_in': JWT_TOKEN_LIFETIME_MINUTES * 60
            }
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    def get_site_ids_from_token(self, token_payload: Dict[str, Any]) -> List[int]:
        """
        Extracts the site IDs from a validated token payload.
        
        Args:
            token_payload: Decoded token payload
            
        Returns:
            List of site IDs the user has access to
        """
        sites = token_payload.get('sites', [])
        # Ensure all site IDs are integers
        return [int(site_id) for site_id in sites] if sites else []
    
    def get_user_id_from_token(self, token_payload: Dict[str, Any]) -> str:
        """
        Extracts the user ID from a validated token payload.
        
        Args:
            token_payload: Decoded token payload
            
        Returns:
            User ID from the token
        """
        return token_payload.get('sub')