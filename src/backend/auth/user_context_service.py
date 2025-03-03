"""
Service that manages user context throughout the application.

This module maintains the current authenticated user's information in Flask's
request context, provides methods to retrieve user details, and enforces
site-scoped access control by validating site access permissions.
"""

from flask import g
from typing import Dict, List, Optional, Any

from ..repositories.user_repository import UserRepository
from ..models.user import User
from .token_service import TokenService
from ..utils.error_util import AuthenticationError
from ..logging.structured_logger import StructuredLogger
from ..cache.cache_keys import get_user_context_key
from ..cache.cache_service import get_cache_service

# Initialize logger
logger = StructuredLogger(__name__)


class UserContext:
    """Class representing the current user's context information"""
    
    def __init__(self, user_id: int, username: str, email: str, site_ids: List[int] = None):
        """
        Initialize user context with user information
        
        Args:
            user_id: Unique identifier of the user
            username: Username of the user
            email: Email address of the user
            site_ids: List of site IDs the user has access to (default empty list)
        """
        self.user_id = user_id
        self.username = username
        self.email = email
        self.site_ids = site_ids or []
        self.is_authenticated = bool(user_id)
        logger.debug(f"Created user context for user {username} (ID: {user_id})")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the user context to a dictionary for serialization
        
        Returns:
            Dictionary representation of user context
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'site_ids': self.site_ids,
            'is_authenticated': self.is_authenticated
        }
    
    def has_site_access(self, site_id: int) -> bool:
        """
        Check if the user has access to a specific site
        
        Args:
            site_id: ID of the site to check access for
            
        Returns:
            True if user has access to the site, False otherwise
        """
        return site_id in self.site_ids


class UserContextService:
    """Service responsible for managing user context throughout the application"""
    
    def __init__(self, user_repository: UserRepository, token_service: TokenService):
        """
        Initialize the user context service with required dependencies
        
        Args:
            user_repository: Repository for user data access
            token_service: Service for token validation and extraction
        """
        self._user_repository = user_repository
        self._token_service = token_service
        self._cache_service = get_cache_service()
        logger.info("UserContextService initialized")
    
    def get_current_user_context(self) -> Optional[UserContext]:
        """
        Get the current user context from Flask request context
        
        Returns:
            Current user context or None if not authenticated
        """
        if hasattr(g, 'user_id') and g.user_id:
            user_context = UserContext(
                user_id=g.user_id,
                username=g.username,
                email=g.email,
                site_ids=g.site_ids if hasattr(g, 'site_ids') else []
            )
            logger.debug(f"Retrieved user context for user {g.username} (ID: {g.user_id})")
            return user_context
        
        logger.debug("No user context found in request")
        return None
    
    def set_user_context_from_token(self, token_payload: Dict[str, Any]) -> UserContext:
        """
        Set user context in Flask request context based on token payload
        
        Args:
            token_payload: Decoded JWT token payload
            
        Returns:
            Created user context object
            
        Raises:
            AuthenticationError: If user ID is missing or user not found
        """
        # Extract user ID from token
        user_id = self._token_service.get_user_id_from_token(token_payload)
        
        if not user_id:
            logger.warning("Token payload does not contain user ID")
            raise AuthenticationError("Invalid token - missing user ID")
        
        # Get user from database
        user = self._user_repository.find_by_id(user_id)
        if not user:
            logger.warning(f"User with ID {user_id} not found in database")
            raise AuthenticationError(f"User with ID {user_id} not found")
        
        # Extract site IDs from token
        site_ids = self._token_service.get_site_ids_from_token(token_payload)
        
        # Create user context
        user_context = UserContext(
            user_id=user.id,
            username=user.username,
            email=user.email,
            site_ids=site_ids
        )
        
        # Store in Flask g object
        g.user_id = user.id
        g.username = user.username
        g.email = user.email
        g.site_ids = site_ids
        
        # Cache user context
        cache_key = get_user_context_key(user_id)
        self._cache_service.set(cache_key, user_context.to_dict())
        
        logger.info(f"Set user context for user {user.username} (ID: {user.id}) with access to {len(site_ids)} sites")
        return user_context
    
    def set_user_context(self, user: User) -> UserContext:
        """
        Set user context directly with user information
        
        Args:
            user: User model instance
            
        Returns:
            Created user context object
        """
        # Get user's site IDs
        site_ids = user.get_site_ids()
        
        # Create user context
        user_context = UserContext(
            user_id=user.id,
            username=user.username,
            email=user.email,
            site_ids=site_ids
        )
        
        # Store in Flask g object
        g.user_id = user.id
        g.username = user.username
        g.email = user.email
        g.site_ids = site_ids
        
        logger.info(f"Set user context for user {user.username} (ID: {user.id}) with access to {len(site_ids)} sites")
        return user_context
    
    def clear_user_context(self) -> None:
        """
        Clear user context from Flask request context
        
        This removes all user-related attributes from the request context
        """
        if hasattr(g, 'user_id'):
            logger.info(f"Clearing user context for user {g.username} (ID: {g.user_id})")
            for attr in ['user_id', 'username', 'email', 'site_ids']:
                if hasattr(g, attr):
                    delattr(g, attr)
    
    def get_current_user_id(self) -> Optional[int]:
        """
        Get the ID of the current authenticated user
        
        Returns:
            Current user ID or None if not authenticated
        """
        context = self.get_current_user_context()
        if context and context.is_authenticated:
            logger.debug(f"Retrieved current user ID: {context.user_id}")
            return context.user_id
        
        logger.debug("No authenticated user in current context")
        return None
    
    def get_current_user(self) -> Optional[User]:
        """
        Get the current authenticated user model from the database
        
        Returns:
            Current user model or None if not authenticated
        """
        user_id = self.get_current_user_id()
        if not user_id:
            logger.debug("Cannot get current user - no user ID in context")
            return None
        
        user = self._user_repository.find_by_id(user_id)
        if user:
            logger.debug(f"Retrieved current user: {user.username} (ID: {user_id})")
        else:
            logger.warning(f"User with ID {user_id} not found despite being in context")
        
        return user
    
    def get_current_user_site_ids(self) -> List[int]:
        """
        Get the site IDs the current user has access to
        
        Returns:
            List of site IDs the user has access to
        """
        context = self.get_current_user_context()
        if context and context.is_authenticated:
            logger.debug(f"Retrieved site IDs for current user: {context.site_ids}")
            return context.site_ids
        
        logger.debug("No authenticated user in current context - returning empty site list")
        return []
    
    def has_site_access(self, site_id: int) -> bool:
        """
        Check if the current user has access to a specific site
        
        Args:
            site_id: ID of the site to check access for
            
        Returns:
            True if user has access to the site, False otherwise
        """
        context = self.get_current_user_context()
        if not context or not context.is_authenticated:
            logger.debug(f"Site access check failed - no authenticated user in context")
            return False
        
        has_access = context.has_site_access(site_id)
        log_message = f"User {context.username} (ID: {context.user_id}) {'has' if has_access else 'does not have'} access to site {site_id}"
        logger.debug(log_message)
        
        return has_access
    
    def is_authenticated(self) -> bool:
        """
        Check if the current request has an authenticated user
        
        Returns:
            True if authenticated, False otherwise
        """
        context = self.get_current_user_context()
        is_auth = context is not None and context.is_authenticated
        
        logger.debug(f"Authentication check: {'authenticated' if is_auth else 'not authenticated'}")
        return is_auth
    
    def require_authentication(self) -> bool:
        """
        Require the current request to have an authenticated user or raise exception
        
        Returns:
            True if authenticated, raises AuthenticationError otherwise
        """
        if not self.is_authenticated():
            logger.warning("Authentication required but user is not authenticated")
            raise AuthenticationError("Authentication required")
        
        logger.debug("Authentication requirement satisfied")
        return True
    
    def require_site_access(self, site_id: int) -> bool:
        """
        Require the current user to have access to a specific site or raise exception
        
        Args:
            site_id: ID of the site to check access for
            
        Returns:
            True if user has site access, raises AuthenticationError otherwise
        """
        if not self.has_site_access(site_id):
            user_id = self.get_current_user_id()
            logger.warning(f"Site access required but user {user_id} does not have access to site {site_id}")
            raise AuthenticationError(f"Access to site {site_id} required")
        
        logger.debug(f"Site access requirement satisfied for site {site_id}")
        return True